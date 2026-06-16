"""
Servicios (reglas de negocio) para las participaciones en eventos de trivia.

Toda la lógica de negocio vive aquí, en Python — ya no en funciones/triggers PL/pgSQL:
- Gestionar participaciones (iniciar / continuar / esperar por cooldown / finalizado por
  máximo de intentos).
- Finalizar una participación: registrar respuestas y calcular el resultado.
- Eliminar participaciones.

Las lecturas simples se delegan en `app.crud.crud_participaciones`.

Funciones puras (sin acceso a BD), aisladas para poder probarlas con tests unitarios:
- `decidir_accion`: máquina de estados de intentos/cooldown.
- `calcular_resultado`: cálculo de aciertos/porcentaje.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_participaciones as crud
from app.crud.crud_grupos import get_grupo_by_id
from app.models.participacion import EstadoParticipacion

from app.core.logger import MyLogger

logger = MyLogger().get_logger()

# Cadenas de acción expuestas a la API (contrato con el frontend; se conservan tal cual).
ACCION_INICIAR = "iniciar"
ACCION_CONTINUAR = "continuar"
ACCION_ESPERAR = "esperar"
ACCION_FINALIZADO = "FINALIZADO"

CERO = timedelta(0)


@dataclass
class DecisionParticipacion:
    """Resultado de la máquina de estados de participación (objeto puro, sin BD)."""
    accion: str
    numero_intento: int
    crear_nuevo: bool
    remaining: timedelta


def decidir_accion(
    estado_ultimo: Optional[EstadoParticipacion],
    numero_intento_ultimo: Optional[int],
    finished_at_ultimo: Optional[datetime],
    max_intentos: int,
    cooldown: timedelta,
    now: datetime,
) -> DecisionParticipacion:
    """
    Decide qué hacer ante una solicitud de participación, replicando las reglas de negocio:

    - Sin intentos previos -> iniciar intento 1.
    - Último intento PENDIENTE -> continuar ese intento.
    - Último intento FINALIZADO y quedan intentos:
        - dentro del cooldown -> esperar (devuelve tiempo restante).
        - superado el cooldown -> iniciar nuevo intento.
    - Último intento FINALIZADO y se alcanzó el máximo -> FINALIZADO (sin más intentos).

    Es una función pura: no toca la base de datos.
    """
    if estado_ultimo is None:
        return DecisionParticipacion(ACCION_INICIAR, 1, True, CERO)

    if estado_ultimo == EstadoParticipacion.PENDIENTE:
        return DecisionParticipacion(
            ACCION_CONTINUAR, numero_intento_ultimo, False, CERO
        )

    # Último intento finalizado
    if numero_intento_ultimo < max_intentos:
        disponible_en = (finished_at_ultimo + cooldown) if finished_at_ultimo else now
        if now < disponible_en:
            return DecisionParticipacion(
                ACCION_ESPERAR, numero_intento_ultimo, False, disponible_en - now
            )
        return DecisionParticipacion(
            ACCION_INICIAR, numero_intento_ultimo + 1, True, CERO
        )

    return DecisionParticipacion(
        ACCION_FINALIZADO, numero_intento_ultimo, False, CERO
    )


def calcular_resultado(
    respuestas: List[dict], opciones_correctas: Dict[int, int]
) -> Dict[str, Any]:
    """
    Calcula el resultado de una participación a partir de las respuestas del usuario.

    Solo se cuentan las respuestas cuya pregunta exista (presente en `opciones_correctas`),
    igual que el JOIN contra `preguntas` del trigger original.

    Es una función pura: no toca la base de datos.
    """
    validas = [r for r in respuestas if r["id_pregunta"] in opciones_correctas]
    total = len(validas)
    correctas = sum(
        1
        for r in validas
        if r["respuesta_seleccionada"] == opciones_correctas[r["id_pregunta"]]
    )
    incorrectas = total - correctas
    porcentaje = round(100.0 * correctas / total, 2) if total else 0.0
    return {
        "total_preguntas": total,
        "respuestas_correctas": correctas,
        "respuestas_incorrectas": incorrectas,
        "porcentaje_acierto": porcentaje,
    }


async def gestionar_participacion(
    db: AsyncSession,
    nombre: str,
    cedula: str,
    grupo_id: int,
) -> Dict[str, Any]:
    """
    Gestiona la participación de un usuario en un grupo: crea, continúa, hace esperar o marca
    como finalizado el intento según las reglas de negocio. Todo en una única transacción,
    serializada por (usuario, grupo) mediante advisory lock para evitar carreras.
    """
    grupo = await get_grupo_by_id(db, grupo_id)
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado"
        )

    now = datetime.now(timezone.utc)
    if not (grupo.fecha_inicio <= now <= grupo.fecha_cierre):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El grupo está cerrado o aún no ha iniciado",
        )

    try:
        id_usuario = await crud.upsert_usuario(db, nombre=nombre, cedula=cedula)
        await crud.lock_participaciones_usuario_grupo(db, id_usuario, grupo_id)

        ultimo = await crud.get_ultimo_intento(db, id_usuario, grupo_id)
        decision = decidir_accion(
            estado_ultimo=ultimo.estado if ultimo else None,
            numero_intento_ultimo=ultimo.numero_intento if ultimo else None,
            finished_at_ultimo=ultimo.finished_at if ultimo else None,
            max_intentos=grupo.max_intentos,
            cooldown=grupo.cooldown,
            now=now,
        )

        if decision.crear_nuevo:
            participacion = await crud.crear_participacion(
                db,
                id_usuario=id_usuario,
                id_grupo=grupo_id,
                numero_intento=decision.numero_intento,
                started_at=now,
            )
        else:
            participacion = ultimo

        await db.commit()

        return {
            "action": decision.accion,
            "id_participacion": participacion.id_participacion,
            "numero_intento": participacion.numero_intento,
            "respuestas": participacion.respuestas_usuario or [],
            "started_at": participacion.started_at,
            "finished_at": participacion.finished_at,
            "tiempo_total": (
                str(participacion.tiempo_total) if participacion.tiempo_total else None
            ),
            "remaining": str(decision.remaining),
        }
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        # Carrera al crear el primer intento simultáneamente: lo tratamos como conflicto.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto al gestionar la participación, intente nuevamente",
        )


async def finalizar_participacion(
    db: AsyncSession,
    id_participacion: int,
    respuestas_usuario: list[dict],  # Puede incluir abiertas y opción única
    tiempo_total: str,
) -> dict:
    """
    Finaliza una participación: registra las respuestas, marca el estado como finalizado y
    calcula el resultado (respuestas desglosadas + agregados), todo en Python y en una sola
    transacción. Reemplaza al trigger `trg_participacion_finalizada`.

    Args:
        db: Sesión asíncrona de SQLAlchemy.
        id_participacion: ID de la participación a finalizar.
        respuestas_usuario: Lista de objetos con `id_pregunta` y `respuesta_seleccionada`.
        tiempo_total: Duración total en formato "HH:MM:SS".

    Raises:
        HTTPException: 404 si no existe; 400 si ya está finalizada.
    """
    participacion = await crud.get_participacion_by_id(db, id_participacion)
    if not participacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participación no encontrada.",
        )

    if participacion.estado == EstadoParticipacion.FINALIZADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La participación ya está finalizada.",
        )

    horas, minutos, segundos = map(int, tiempo_total.split(":"))
    duracion = timedelta(hours=horas, minutes=minutos, seconds=segundos)

    # Separar respuestas abiertas y de opción única
    respuestas_opcion = []
    respuestas_abiertas = []
    for resp in respuestas_usuario:
        if resp.get("tipo_pregunta") == "abierta":
            respuestas_abiertas.append({
                "id_pregunta": resp["id_pregunta"],
                "respuesta_abierta": resp.get("respuesta_abierta"),
            })
        else:
            respuestas_opcion.append(resp)

    # 1. Actualizar la participación (opción única y abiertas por separado).
    participacion.respuestas_usuario = respuestas_opcion
    participacion.respuestas_abiertas = respuestas_abiertas
    participacion.tiempo_total = duracion
    participacion.finished_at = datetime.now(timezone.utc)
    participacion.estado = EstadoParticipacion.FINALIZADO

    # 2. Desglosar respuestas y calcular el resultado en Python (antes lo hacía el trigger).
    #    Solo las de opción única puntúan; las abiertas no tienen opción correcta.
    await crud.upsert_respuestas_usuario(db, id_participacion, respuestas_opcion)
    ids_pregunta = [r["id_pregunta"] for r in respuestas_opcion]
    opciones_correctas = await crud.get_opciones_correctas(db, ids_pregunta)
    datos = calcular_resultado(respuestas_opcion, opciones_correctas)
    await crud.upsert_resultado(db, id_participacion, datos, duracion)

    await db.commit()

    return {
        "mensaje": "Participación finalizada correctamente",
        "id": id_participacion,
    }


async def eliminar_participacion(db: AsyncSession, id_participacion: int) -> None:
    """
    Elimina una participación por su ID.

    Raises:
        HTTPException: 404 si la participación no existe.
    """
    participacion = await crud.get_participacion_by_id(db, id_participacion)
    if not participacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participación no encontrada",
        )
    await db.delete(participacion)
    await db.commit()
