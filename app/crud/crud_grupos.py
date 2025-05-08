"""
Operaciones CRUD para los grupos de trivia.

Este módulo contiene las funciones para crear, leer, actualizar y eliminar grupos
en la base de datos usando SQLAlchemy de manera asíncrona.
"""

from sqlalchemy import between
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from app.models.grupo import Grupo


def ensure_utc(dt: datetime) -> datetime:
    """Asegura que un datetime tenga timezone UTC"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

async def get_grupos(db: AsyncSession):
    """
    Obtiene todos los grupos.

    Args:
        db (AsyncSession): Sesión de base de datos.

    Returns:
        List[Grupo]: Lista de todos los grupos.
    """
    result = await db.execute(select(Grupo).order_by(Grupo.fecha_inicio))
    return result.scalars().all()

async def get_grupos_by_evento(db: AsyncSession, id_evento: int):
    """
    Obtiene todos los grupos de un evento específico.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_evento (int): ID del evento.

    Returns:
        List[Grupo]: Lista de grupos del evento.
    """
    stmt = select(Grupo).where(Grupo.id_evento == id_evento).order_by(Grupo.fecha_inicio)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_grupo(db: AsyncSession, id_grupo: int):
    """
    Obtiene un grupo por su ID.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_grupo (int): ID del grupo a buscar.

    Returns:
        Optional[Grupo]: El grupo encontrado o None si no existe.
    """
    stmt = select(Grupo).where(Grupo.id_grupo == id_grupo)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_grupo(
    db: AsyncSession,
    id_evento: int,
    nombre_grupo: str,
    fecha_inicio: datetime,
    fecha_cierre: datetime
):
    """
    Crea un nuevo grupo.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_evento (int): ID del evento al que pertenece el grupo.
        nombre_grupo (str): Nombre del grupo.
        fecha_inicio (datetime): Fecha y hora de inicio.
        fecha_cierre (datetime): Fecha y hora de cierre.

    Returns:
        Grupo: El grupo creado.

    Raises:
        IntegrityError: Si ya existe un grupo con el mismo nombre en el evento.
    """
    nuevo_grupo = Grupo(
        id_evento=id_evento,
        nombre_grupo=nombre_grupo,
        fecha_inicio=ensure_utc(fecha_inicio),
        fecha_cierre=ensure_utc(fecha_cierre)
    )
    db.add(nuevo_grupo)
    try:
        await db.commit()
        await db.refresh(nuevo_grupo)
        return nuevo_grupo
    except IntegrityError:
        await db.rollback()
        raise

async def update_grupo(
    db: AsyncSession,
    id_grupo: int,
    nombre_grupo: str = None,
    fecha_inicio: datetime = None,
    fecha_cierre: datetime = None
):
    """
    Actualiza un grupo existente.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_grupo (int): ID del grupo a actualizar.
        nombre_grupo (str, optional): Nuevo nombre del grupo.
        fecha_inicio (datetime, optional): Nueva fecha de inicio.
        fecha_cierre (datetime, optional): Nueva fecha de cierre.

    Returns:
        Optional[Grupo]: El grupo actualizado o None si no existe.

    Raises:
        IntegrityError: Si el nuevo nombre ya existe en el evento.
    """
    grupo = await get_grupo(db, id_grupo)
    if not grupo:
        return None

    if nombre_grupo is not None:
        grupo.nombre_grupo = nombre_grupo
    if fecha_inicio is not None:
        grupo.fecha_inicio = ensure_utc(fecha_inicio)
    if fecha_cierre is not None:
        grupo.fecha_cierre = ensure_utc(fecha_cierre)

    try:
        await db.commit()
        await db.refresh(grupo)
        return grupo
    except IntegrityError:
        await db.rollback()
        raise

async def delete_grupo(db: AsyncSession, grupo: Grupo):
    """
    Elimina un grupo.

    Args:
        db (AsyncSession): Sesión de base de datos.
        grupo (Grupo): Instancia del grupo a eliminar.
    """
    await db.delete(grupo)
    await db.commit()

async def get_grupos_activos(db: AsyncSession, fecha: datetime = None, evento_id: int = None):
    """
    Obtiene todos los grupos que están activos en una fecha dada y opcionalmente por evento.

    Args:
        db (AsyncSession): Sesión de base de datos.
        fecha (datetime, optional): Fecha para verificar grupos activos.
        evento_id (int, optional): ID del evento para filtrar grupos.


    Returns:
        List[Grupo]: Lista de grupos activos.
    """
    if fecha is None:
        fecha = datetime.now(timezone.utc)
    else:
        fecha = ensure_utc(fecha)

    stmt = select(Grupo).where(
        between(fecha, Grupo.fecha_inicio, Grupo.fecha_cierre)
    )

    if evento_id is not None:
        stmt = stmt.where(Grupo.id_evento == evento_id)

    stmt = stmt.order_by(Grupo.fecha_inicio)

    result = await db.execute(stmt)
    return result.scalars().all()