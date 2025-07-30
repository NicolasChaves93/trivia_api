"""
Servicios para gestionar las participaciones en eventos de trivia.

Este módulo contiene la lógica de negocio para:
- Gestionar participaciones (crear/continuar)
- Finalizar participaciones con respuestas
- Eliminar participaciones
- Consultar participaciones por estado
- Consultar participaciones por usuario y/o evento
- Listar todas las participaciones
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from asyncpg import PostgresError
import asyncpg
from fastapi import HTTPException, status
from sqlalchemy import update, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.models.participacion import Participacion, EstadoParticipacion
from app.models.usuario import Usuario
from app.models.grupo import Grupo
from app.crud.crud_grupos import get_grupo_by_id

from app.core.logger import MyLogger
logger = MyLogger().get_logger()


async def gestionar_participacion(
    db: AsyncSession,
    nombre: str,
    cedula: str,
    grupo_id: int
) -> Dict[str, Any]:
    """
    Gestiona la participación de un usuario en un grupo:
    - Valida existencia y vigencia del grupo
    - Llama a la función PL/pgSQL que controla intentos y cooldown
    - Lee el campo `remaining` devuelto para el tiempo restante
    """
    # 1. Validar que el grupo exista y esté activo
    grupo = await  get_grupo_by_id(db, grupo_id)
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado"
        )

    now = datetime.now(timezone.utc)
    if not (grupo.fecha_inicio <= now <= grupo.fecha_cierre):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El grupo está cerrado o aún no ha iniciado"
        )

    try:
        # 3. Invocar la función almacenada
        func = text("""
            SELECT action, id_part, respuestas, started_at, finished_at, tiempo_tot, remaining
            FROM trivia.gestionar_participacion(:nombre, :cedula, :grupo_id)
        """).bindparams(nombre=nombre, cedula=cedula, grupo_id=grupo_id)
        result = await db.execute(func)
        row = result.fetchone()

        if not row or row.id_part is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo iniciar o recuperar la participación"
            )

        # 3. Obtener número de intento
        intento_res = await db.execute(
            text("""
                SELECT numero_intento
                FROM trivia.participaciones
                WHERE id_participacion = :id_part
            """).bindparams(id_part=row.id_part)
        )
        numero_intento = intento_res.scalar_one_or_none() or 1

        # 4. Commit y retornar
        await db.commit()

        return {
            "action":            row.action,
            "id_participacion":  row.id_part,
            "numero_intento":    numero_intento,
            "respuestas":        row.respuestas or [],
            "started_at":        row.started_at,
            "finished_at":       row.finished_at,
            "tiempo_total":      str(row.tiempo_tot) if row.tiempo_tot else None,
            "remaining":         str(row.remaining)
        }
    except HTTPException:
        await db.rollback()
        raise

async def finalizar_participacion(
    db: AsyncSession,
    id_participacion: int,
    respuestas_usuario: list[dict],  # Puede incluir abiertas y opción única
    tiempo_total: str
) -> dict:
    """
    Finaliza una participación de trivia actualizando su estado y registrando las respuestas.

    Esta función realiza las siguientes acciones:
    - Valida la existencia de la participación.
    - Verifica que no esté ya finalizada.
    - Registra las respuestas seleccionadas por el usuario en formato JSONB.
    - Establece el tiempo total de resolución.
    - Marca la participación como finalizada (`estado = 'Finalizado'`).
    - El trigger de base de datos se encarga de calcular:
        - Las respuestas desglosadas (`respuestas_usuarios`)
        - Los resultados (`resultados`)

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        id_participacion (int): ID de la participación a finalizar.
        respuestas_usuario (list[dict]): Lista de objetos con `id_pregunta` y `respuesta_seleccionada`.
        tiempo_total (str): Duración total en formato "HH:MM:SS".

    Returns:
        dict: Un mensaje de éxito con el ID de participación finalizada.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la participación.
            - 400: Si la participación ya está finalizada.
    """
    # Obtener participación existente
    stmt = select(Participacion).where(Participacion.id_participacion == id_participacion)
    result = await db.execute(stmt)
    participacion = result.scalar_one_or_none()

    if not participacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participación no encontrada."
        )

    if participacion.estado == "finalizado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La participación ya está finalizada."
        )

    # Preparar datos para actualizar
    # Parsear el string "HH:MM:SS" a timedelta
    horas, minutos, segundos = map(int, tiempo_total.split(":"))
    duracion = timedelta(hours=horas, minutes=minutos, seconds=segundos)

    # Separar respuestas abiertas y de opción única
    respuestas_opcion = []
    respuestas_abiertas = []
    for resp in respuestas_usuario:
        if resp.get("tipo_pregunta") == "abierta":
            respuestas_abiertas.append({
                "id_pregunta": resp["id_pregunta"],
                "respuesta_abierta": resp.get("respuesta_abierta")
            })
        else:
            respuestas_opcion.append(resp)

    # Guardar ambas en la BD (puedes ajustar el modelo para soportar ambos campos si es necesario)
    stmt_update = (
        update(Participacion)
        .where(Participacion.id_participacion == id_participacion)
        .values(
            respuestas_usuario=respuestas_opcion,
            respuestas_abiertas=respuestas_abiertas,
            tiempo_total=duracion,
            finished_at = datetime.now(timezone.utc),
            estado="finalizado"
        )
    )

    await db.execute(stmt_update)
    await db.commit()

    return {"mensaje": "Participación finalizada correctamente", "id": id_participacion}

async def eliminar_participacion(db: AsyncSession, id_participacion: int) -> None:
    """
    Elimina una participación por su ID.

    Args:
        db (AsyncSession): Sesión de base de datos
        id_participacion (int): ID de la participación a eliminar

    Raises:
        HTTPException: 404 si la participación no existe
    """
    participacion = await db.get(Participacion, id_participacion)
    if not participacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participación no encontrada"
        )
    
    await db.delete(participacion)
    await db.commit()

async def get_participaciones_por_estado(
    db: AsyncSession,
    estado: EstadoParticipacion,
    id_evento: Optional[int] = None,
    id_grupo: Optional[int] = None
) -> List[Participacion]:
    """
    Obtiene todas las participaciones que tienen un estado específico.

    Args:
        db (AsyncSession): Sesión de base de datos
        estado (EstadoParticipacion): Estado de las participaciones a buscar

    Returns:
        List[Participacion]: Lista de participaciones con el estado especificado y datos del usuario
    """
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .where(Participacion.estado == estado)
        .order_by(Participacion.id_participacion.asc())
    )

    # Aplicar filtros según los parámetros proporcionados
    if id_evento is not None:
        stmt = (
            stmt.join(Grupo)
            .where(Grupo.id_evento == id_evento)
        )
    if id_grupo is not None:
        stmt = stmt.where(Participacion.id_grupo == id_grupo)

    result = await db.execute(stmt)
    return result.scalars().all()

async def get_participaciones_por_usuario_evento(
    db: AsyncSession,
    cedula: Optional[str] = None,
    id_evento: Optional[int] = None,
    id_grupo: Optional[int] = None
) -> List[Participacion]:
    """
    Obtiene participaciones filtrando por cédula del usuario, evento y/o grupo.

    Args:
        db (AsyncSession): Sesión de base de datos
        cedula (Optional[str]): Cédula del usuario para filtrar (opcional)
        id_evento (Optional[int]): ID del evento para filtrar (opcional)
        id_grupo (Optional[int]): ID del grupo para filtrar (opcional)

    Returns:
        List[Participacion]: Lista de participaciones que coinciden con los filtros

    Raises:
        HTTPException: 400 si no se proporciona ningún filtro
    """
    if cedula is None and id_evento is None and id_grupo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos un criterio de búsqueda (cedula, id_evento o id_grupo)"
        )

    # Construir la consulta base con joins necesarios
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .options(joinedload(Participacion.grupo))
    )
    
    # Aplicar filtros según los parámetros proporcionados
    if cedula is not None:
        stmt = stmt.join(Usuario).where(Usuario.cedula == cedula)
    if id_evento is not None:
        stmt = (
            stmt.join(Grupo)
            .where(Grupo.id_evento == id_evento)
        )
    if id_grupo is not None:
        stmt = stmt.where(Participacion.id_grupo == id_grupo)
    
    # Ordenar por fecha de inicio descendente (más recientes primero)
    stmt = stmt.order_by(Participacion.started_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_all_participaciones(db: AsyncSession) -> List[Participacion]:
    """
    Obtiene todas las participaciones registradas.

    Args:
        db (AsyncSession): Sesión de base de datos

    Returns:
        List[Participacion]: Lista de todas las participaciones con datos del usuario y grupo
    """
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .options(joinedload(Participacion.grupo))
        .order_by(Participacion.started_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_participaciones_por_grupo(db: AsyncSession, id_grupo: int) -> List[Participacion]:
    """
    Obtiene todas las participaciones de un grupo específico.

    Args:
        db (AsyncSession): Sesión de base de datos
        id_grupo (int): ID del grupo para filtrar

    Returns:
        List[Participacion]: Lista de participaciones del grupo con datos del usuario
    """
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .where(Participacion.id_grupo == id_grupo)
        .order_by(Participacion.started_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
