from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.evento import Evento, TipoLogin

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

async def create_evento(db: AsyncSession, nombre_evento: str, tipo_login: TipoLogin) -> Evento:
    """
    Crea un nuevo evento en la base de datos.

    Args:
        db (AsyncSession): Sesión de base de datos.
        nombre_evento (str): Nombre único del evento.
        tipo_login (TipoLogin): Enum que indica el tipo de login asociado.

    Returns:
        Evento: Objeto de evento creado.

    Raises:
        ValueError: Si el tipo_login es inválido.
        IntegrityError: Si ocurre un conflicto de integridad al guardar.
    """
    # Validación defensiva por si llega un string en lugar del Enum
    if isinstance(tipo_login, str):
        try:
            tipo_login = TipoLogin(tipo_login)
        except ValueError as e:
            logger.warning("Tipo de login inválido: %s", tipo_login)
            raise ValueError(f"Tipo de login inválido: {tipo_login}") from e

    nuevo_evento = Evento(nombre_evento=nombre_evento, tipo_login=tipo_login)
    logger.info("Creando evento: %s (tipo_login=%s)", nombre_evento, tipo_login)

    db.add(nuevo_evento)

    try:
        await db.commit()
        await db.refresh(nuevo_evento)
        logger.info("Evento creado exitosamente: id=%s", nuevo_evento.id_evento)
        return nuevo_evento

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error al crear evento '%s': %s", nombre_evento, str(e), exc_info=True)
        raise IntegrityError(f"Conflicto al guardar el evento: {nombre_evento}", e.params, e.orig) from e

async def delete_evento(db: AsyncSession, evento: Evento):
    await db.delete(evento)
    await db.commit()