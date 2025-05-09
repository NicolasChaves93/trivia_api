"""
Operaciones CRUD para los grupos de trivia.

Este módulo contiene las funciones para crear, leer, actualizar y eliminar grupos
en la base de datos usando SQLAlchemy de manera asíncrona.
"""
from datetime import datetime, timezone
from sqlalchemy import between
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.grupo import Grupo
from typing import Optional


def ensure_utc(dt: datetime) -> datetime:
    """
    Asegura que el objeto datetime tenga zona horaria UTC.
    """
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
    fecha_cierre: datetime,
    max_intentos: int = 1,
    cooldown = None
) -> Grupo:
    """Crea un nuevo grupo con cooldown e intentos máximos."""
    nuevo = Grupo(
        id_evento=id_evento,
        nombre_grupo=nombre_grupo.strip().title(),
        fecha_inicio=fecha_inicio,
        fecha_cierre=fecha_cierre,
        max_intentos=max_intentos,
        cooldown=cooldown
    )
    db.add(nuevo)
    try:
        await db.commit()
        await db.refresh(nuevo)
        return nuevo
    except IntegrityError:
        await db.rollback()
        raise

async def update_grupo(
    db: AsyncSession,
    id_grupo: int,
    nombre_grupo: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_cierre: Optional[datetime] = None,
    max_intentos: Optional[int] = None,
    cooldown = None
) -> Optional[Grupo]:
    """Actualiza propiedades de un grupo, incluyendo cooldown."""
    grupo = await db.get(Grupo, id_grupo)
    if not grupo:
        return None
    if nombre_grupo is not None:
        grupo.nombre_grupo = nombre_grupo.strip().title()
    if fecha_inicio is not None:
        grupo.fecha_inicio = fecha_inicio
    if fecha_cierre is not None:
        grupo.fecha_cierre = fecha_cierre
    if max_intentos is not None:
        grupo.max_intentos = max_intentos
    if cooldown is not None:
        grupo.cooldown = cooldown
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
    Recupera todos los grupos existentes en la base de datos, ordenados por fecha de inicio.
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