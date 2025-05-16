from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.evento import Evento, TipoEvento
from app.schemas.evento import EventoRequest

from app.core.logger import MyLogger
logger = MyLogger().get_logger()

async def get_eventos(db: AsyncSession):
    result = await db.execute(select(Evento))
    return result.scalars().all()

async def get_by_id(db: AsyncSession, id_evento: int):
    stmt = select(Evento).where(Evento.id_evento == id_evento)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_by_nombre(db: AsyncSession, nombre_evento: str):
    stmt = select(Evento).where(Evento.nombre_evento == nombre_evento)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_evento(db: AsyncSession, evento_in: EventoRequest) -> Evento:
    """
    Crea un nuevo evento si el nombre es único y el tipo es válido.
    """

    # Validación del tipo de evento sin mutar el modelo Pydantic
    try:
        tipo_evento_validado = TipoEvento(evento_in.tipo_evento)
    except ValueError as exc:
        msg_error = f"Tipo de evento inválido: {evento_in.tipo_evento}"
        logger.warning(msg_error)
        raise ValueError(msg_error) from exc

    # Verifica duplicado
    existente = await get_by_nombre(db, evento_in.nombre_evento)
    if existente:
        msg_error = f"Ya existe un evento con el nombre: {evento_in.nombre_evento}"
        logger.warning(msg_error)
        raise ValueError(msg_error)

    # Crear y guardar el nuevo evento
    nuevo_evento = Evento(
        nombre_evento=evento_in.nombre_evento,
        tipo_evento=tipo_evento_validado
    )
    db.add(nuevo_evento)

    try:
        await db.commit()
        await db.refresh(nuevo_evento)
        logger.info("Evento creado: %s", nuevo_evento.nombre_evento)
        return nuevo_evento

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al guardar evento '%s': %s", evento_in.nombre_evento, str(e))
        raise

async def delete_evento(db: AsyncSession, evento: Evento):
    """
    Elimina una instancia de Evento de la base de datos.

    Args:
        db (AsyncSession): Sesión de base de datos asíncrona.
        evento (Evento): Objeto Evento a eliminar.

    Returns:
        None
    """
    await db.delete(evento)
    await db.commit()
    logger.info("Evento eliminado: id=%s", evento.id_evento)