"""
Operaciones CRUD para las secciones de trivia.

Este módulo contiene las funciones para crear, leer, actualizar y eliminar secciones
en la base de datos usando SQLAlchemy de manera asíncrona.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.seccion import Seccion

async def get_secciones(db: AsyncSession):
    """
    Obtiene todas las secciones.

    Args:
        db (AsyncSession): Sesión de base de datos.

    Returns:
        List[Seccion]: Lista de todas las secciones.
    """
    result = await db.execute(select(Seccion).order_by(Seccion.id_seccion))
    return result.scalars().all()

async def get_secciones_by_evento(db: AsyncSession, id_evento: int):
    """
    Obtiene todas las secciones de un evento específico.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_evento (int): ID del evento.

    Returns:
        List[Seccion]: Lista de secciones del evento.
    """
    stmt = select(Seccion).where(Seccion.id_evento == id_evento)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_seccion(db: AsyncSession, id_seccion: int):
    """
    Obtiene una sección por su ID.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_seccion (int): ID de la sección a buscar.

    Returns:
        Optional[Seccion]: La sección encontrada o None si no existe.
    """
    stmt = select(Seccion).where(Seccion.id_seccion == id_seccion)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_seccion(db: AsyncSession, id_evento: int, nombre_seccion: str):
    """
    Crea una nueva sección.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_evento (int): ID del evento al que pertenece la sección.
        nombre_seccion (str): Nombre de la sección.

    Returns:
        Seccion: La sección creada.

    Raises:
        IntegrityError: Si ya existe una sección con el mismo nombre en el evento.
    """
    nueva_seccion = Seccion(id_evento=id_evento, nombre_seccion=nombre_seccion)
    db.add(nueva_seccion)
    try:
        await db.commit()
        await db.refresh(nueva_seccion)
        return nueva_seccion
    except IntegrityError:
        await db.rollback()
        raise

async def update_seccion(db: AsyncSession, id_seccion: int, nombre_seccion: str):
    """
    Actualiza el nombre de una sección existente.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_seccion (int): ID de la sección a actualizar.
        nombre_seccion (str): Nuevo nombre de la sección.

    Returns:
        Optional[Seccion]: La sección actualizada o None si no existe.

    Raises:
        IntegrityError: Si ya existe otra sección con el mismo nombre en el evento.
    """
    seccion = await get_seccion(db, id_seccion)
    if not seccion:
        return None
    
    seccion.nombre_seccion = nombre_seccion
    try:
        await db.commit()
        await db.refresh(seccion)
        return seccion
    except IntegrityError:
        await db.rollback()
        raise

async def delete_seccion(db: AsyncSession, seccion: Seccion):
    """
    Elimina una sección.

    Args:
        db (AsyncSession): Sesión de base de datos.
        seccion (Seccion): Instancia de la sección a eliminar.
    """
    await db.delete(seccion)
    await db.commit()