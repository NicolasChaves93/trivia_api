"""
Operaciones CRUD (acceso a datos) para las participaciones de trivia.

Este módulo contiene únicamente consultas/operaciones simples contra la base de datos.
Las reglas de negocio (gestión de intentos, cooldown, cálculo de resultados) viven en
`app/services/participacion.py`.
"""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.participacion import Participacion, EstadoParticipacion
from app.models.usuario import Usuario
from app.models.grupo import Grupo


async def upsert_usuario(db: AsyncSession, nombre: str, cedula: str) -> int:
    """
    Inserta el usuario o actualiza su nombre si la cédula ya existe.

    Returns:
        int: id_usuario resultante.
    """
    stmt = (
        pg_insert(Usuario)
        .values(nombre=nombre, cedula=cedula)
        .on_conflict_do_update(
            index_elements=[Usuario.cedula],
            set_={"nombre": nombre},
        )
        .returning(Usuario.id_usuario)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def lock_participaciones_usuario_grupo(
    db: AsyncSession, id_usuario: int, id_grupo: int
) -> None:
    """
    Serializa el acceso concurrente para un par (usuario, grupo) usando un advisory lock
    transaccional. Evita condiciones de carrera al crear intentos simultáneos.
    El lock se libera automáticamente al finalizar la transacción.
    """
    await db.execute(select(func.pg_advisory_xact_lock(id_usuario, id_grupo)))


async def get_ultimo_intento(
    db: AsyncSession, id_usuario: int, id_grupo: int
) -> Optional[Participacion]:
    """
    Devuelve la participación con el mayor `numero_intento` para el par (usuario, grupo),
    o None si el usuario aún no ha participado en ese grupo.
    """
    stmt = (
        select(Participacion)
        .where(
            Participacion.id_usuario == id_usuario,
            Participacion.id_grupo == id_grupo,
        )
        .order_by(Participacion.numero_intento.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def crear_participacion(
    db: AsyncSession,
    id_usuario: int,
    id_grupo: int,
    numero_intento: int,
    started_at,
) -> Participacion:
    """Crea una nueva participación en estado PENDIENTE."""
    participacion = Participacion(
        id_usuario=id_usuario,
        id_grupo=id_grupo,
        numero_intento=numero_intento,
        respuestas_usuario=[],
        estado=EstadoParticipacion.PENDIENTE,
        started_at=started_at,
        tiempo_total=None,
    )
    db.add(participacion)
    await db.flush()
    return participacion


async def get_participacion_by_id(
    db: AsyncSession, id_participacion: int
) -> Optional[Participacion]:
    """Obtiene una participación por su ID."""
    return await db.get(Participacion, id_participacion)


async def get_opciones_correctas(
    db: AsyncSession, ids_pregunta: List[int]
) -> dict[int, int]:
    """
    Devuelve un mapa {id_pregunta: opcion_correcta} para las preguntas indicadas.
    """
    if not ids_pregunta:
        return {}
    from app.models.pregunta import Pregunta
    # Solo preguntas con opción correcta definida puntúan. Las de opinión
    # ('opcion_opinion') y abiertas tienen opcion_correcta NULL y se excluyen.
    stmt = select(Pregunta.id_pregunta, Pregunta.opcion_correcta).where(
        Pregunta.id_pregunta.in_(ids_pregunta),
        Pregunta.opcion_correcta.isnot(None),
    )
    result = await db.execute(stmt)
    return {row.id_pregunta: row.opcion_correcta for row in result.all()}


async def upsert_respuestas_usuario(
    db: AsyncSession, id_participacion: int, respuestas: List[dict]
) -> None:
    """
    Inserta/actualiza las respuestas desglosadas del usuario en `respuestas_usuarios`.
    """
    from app.models.respuesta_usuario import RespuestaUsuario
    for resp in respuestas:
        stmt = (
            pg_insert(RespuestaUsuario)
            .values(
                id_participacion=id_participacion,
                id_pregunta=resp["id_pregunta"],
                orden_seleccionado=resp["respuesta_seleccionada"],
            )
            .on_conflict_do_update(
                constraint="uq_participacion_pregunta",
                set_={"orden_seleccionado": resp["respuesta_seleccionada"]},
            )
        )
        await db.execute(stmt)


async def upsert_resultado(
    db: AsyncSession, id_participacion: int, datos: dict, tiempo_total
) -> None:
    """
    Inserta/actualiza el resultado calculado de una participación.
    """
    from app.models.resultado import Resultado
    stmt = (
        pg_insert(Resultado)
        .values(
            id_participacion=id_participacion,
            total_preguntas=datos["total_preguntas"],
            respuestas_correctas=datos["respuestas_correctas"],
            respuestas_incorrectas=datos["respuestas_incorrectas"],
            porcentaje_acierto=datos["porcentaje_acierto"],
            tiempo_total=tiempo_total,
        )
        .on_conflict_do_update(
            constraint="uq_resultado_participacion",
            set_={
                "total_preguntas": datos["total_preguntas"],
                "respuestas_correctas": datos["respuestas_correctas"],
                "respuestas_incorrectas": datos["respuestas_incorrectas"],
                "porcentaje_acierto": datos["porcentaje_acierto"],
                "tiempo_total": tiempo_total,
            },
        )
    )
    await db.execute(stmt)


# --- Lecturas para los endpoints de consulta -------------------------------------------

async def get_participaciones_por_estado(
    db: AsyncSession,
    estado: EstadoParticipacion,
    id_evento: Optional[int] = None,
    id_grupo: Optional[int] = None,
) -> List[Participacion]:
    """Lista participaciones por estado, con filtros opcionales por evento/grupo."""
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .where(Participacion.estado == estado)
        .order_by(Participacion.id_participacion.asc())
    )
    if id_evento is not None:
        stmt = stmt.join(Grupo).where(Grupo.id_evento == id_evento)
    if id_grupo is not None:
        stmt = stmt.where(Participacion.id_grupo == id_grupo)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_participaciones_por_usuario_evento(
    db: AsyncSession,
    cedula: Optional[str] = None,
    id_evento: Optional[int] = None,
    id_grupo: Optional[int] = None,
) -> List[Participacion]:
    """Lista participaciones filtrando por cédula, evento y/o grupo."""
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .options(joinedload(Participacion.grupo))
    )
    if cedula is not None:
        stmt = stmt.join(Usuario).where(Usuario.cedula == cedula)
    if id_evento is not None:
        stmt = stmt.join(Grupo).where(Grupo.id_evento == id_evento)
    if id_grupo is not None:
        stmt = stmt.where(Participacion.id_grupo == id_grupo)
    stmt = stmt.order_by(Participacion.started_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_all_participaciones(db: AsyncSession) -> List[Participacion]:
    """Lista todas las participaciones."""
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .options(joinedload(Participacion.grupo))
        .order_by(Participacion.started_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_participaciones_por_grupo(
    db: AsyncSession, id_grupo: int
) -> List[Participacion]:
    """Lista las participaciones de un grupo específico."""
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .where(Participacion.id_grupo == id_grupo)
        .order_by(Participacion.started_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
