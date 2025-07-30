"""
Operaciones CRUD para las preguntas de trivia.

Este módulo contiene las funciones para crear, leer, actualizar y eliminar preguntas
en la base de datos usando SQLAlchemy de manera asíncrona.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.models.pregunta import Pregunta
from app.models.respuesta import Respuesta
from app.schemas.pregunta import RespuestaCreate
from app.models.seccion import Seccion

async def get_preguntas(db: AsyncSession):
    """
    Obtiene todas las preguntas con sus respuestas.

    Args:
        db (AsyncSession): Sesión de base de datos.

    Returns:
        List[Pregunta]: Lista de todas las preguntas.
    """
    stmt = select(Pregunta).options(selectinload(Pregunta.respuestas)).order_by(Pregunta.id_pregunta)
    result = await db.execute(stmt)
    preguntas = result.scalars().all()
    
    # Ordenar las respuestas de cada pregunta
    for pregunta in preguntas:
        if pregunta.respuestas:
            pregunta.respuestas.sort(key=lambda x: getattr(x, "orden", 0))
    
    return preguntas

async def get_preguntas_by_seccion(db: AsyncSession, id_seccion: int):
    """
    Obtiene todas las preguntas de una sección específica.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_seccion (int): ID de la sección.

    Returns:
        List[Pregunta]: Lista de preguntas de la sección.
    """
    stmt = select(Pregunta).options(selectinload(Pregunta.respuestas)).where(Pregunta.id_seccion == id_seccion)
    result = await db.execute(stmt)
    preguntas = result.scalars().all()
    
    # Ordenar las respuestas de cada pregunta
    for pregunta in preguntas:
        if pregunta.respuestas:
            pregunta.respuestas.sort(key=lambda x: getattr(x, "orden", 0))
    
    return preguntas

async def get_pregunta(db: AsyncSession, id_pregunta: int):
    """
    Obtiene una pregunta por su ID.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_pregunta (int): ID de la pregunta a buscar.

    Returns:
        Optional[Pregunta]: La pregunta encontrada con sus respuestas ordenadas o None si no existe.
    """
    stmt = (
        select(Pregunta)
        .options(
            selectinload(Pregunta.respuestas).selectinload(Respuesta.pregunta)
        )
        .where(Pregunta.id_pregunta == id_pregunta)
    )
    result = await db.execute(stmt)
    pregunta = result.scalar_one_or_none()
    
    if pregunta and pregunta.respuestas:
        pregunta.respuestas.sort(key=lambda x: getattr(x, "orden", 0))
    
    return pregunta

async def create_pregunta(
    db: AsyncSession,
    id_seccion: int,
    pregunta: str,
    tipo_pregunta: str,
    respuestas: Optional[List[RespuestaCreate]] = None,
    opcion_correcta: Optional[int] = None
):
    """
    Crea una nueva pregunta con sus respuestas.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_seccion (int): ID de la sección a la que pertenece la pregunta.
        pregunta (str): Texto de la pregunta.
        respuestas (List[RespuestaCreate]): Lista de respuestas a crear.
        opcion_correcta (int): Número de la opción correcta (1-4).

    Returns:
        Pregunta: La pregunta creada con sus respuestas.

    Raises:
        IntegrityError: Si ya existe una pregunta con el mismo texto en la sección.
    """
    # Crear la pregunta
    nueva_pregunta = Pregunta(
        id_seccion=id_seccion,
        pregunta=pregunta,
        tipo_pregunta=tipo_pregunta,
        opcion_correcta=opcion_correcta if tipo_pregunta == "opcion_unica" else None
    )
    db.add(nueva_pregunta)
    try:
        await db.flush()  # Para obtener el id_pregunta y validar duplicados

        # Crear las respuestas solo si es opción única
        if tipo_pregunta == "opcion_unica" and respuestas:
            for resp in respuestas:
                respuesta = Respuesta(
                    id_pregunta=nueva_pregunta.id_pregunta,
                    orden=resp.orden,
                    respuesta=resp.respuesta
                )
                db.add(respuesta)

        await db.commit()
        await db.refresh(nueva_pregunta)
        return nueva_pregunta
    except IntegrityError:
        await db.rollback()
        raise

async def update_pregunta(
db: AsyncSession,
id_pregunta: int,
pregunta: Optional[str] = None,
opcion_correcta: Optional[int] = None,
respuestas: Optional[List[RespuestaCreate]] = None
):
    """
    Actualiza una pregunta existente y opcionalmente sus respuestas.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_pregunta (int): ID de la pregunta a actualizar.
        pregunta (str, optional): Nuevo texto de la pregunta.
        opcion_correcta (int, optional): Número de la opción correcta.
        respuestas (List[RespuestaCreate], optional): Lista de respuestas a actualizar o agregar.

    Returns:
        Optional[Pregunta]: La pregunta actualizada o None si no existe.
    """
    pregunta_db = await get_pregunta(db, id_pregunta)
    if not pregunta_db:
        return None

    try:
        # Determinar tipo de pregunta
        tipo_pregunta = getattr(pregunta_db, "tipo_pregunta", None)

        # Actualizar respuestas solo si es opción única y se proporcionan
        if tipo_pregunta == "opcion_unica" and respuestas is not None:
            # Eliminar respuestas existentes
            for resp in pregunta_db.respuestas:
                await db.delete(resp)
            await db.flush()
            # Crear nuevas respuestas
            for resp in respuestas:
                nueva_resp = Respuesta(
                    id_pregunta=id_pregunta,
                    orden=resp.orden,
                    respuesta=resp.respuesta
                )
                db.add(nueva_resp)
            await db.flush()

        # Actualizar la opción correcta solo si es opción única
        if tipo_pregunta == "opcion_unica" and opcion_correcta is not None:
            setattr(pregunta_db, "opcion_correcta", opcion_correcta)
            await db.flush()

        # Actualizar el texto de la pregunta si se proporciona
        if pregunta is not None and pregunta != getattr(pregunta_db, "pregunta"):
            setattr(pregunta_db, "pregunta", pregunta)
            await db.flush()

        await db.commit()
        await db.refresh(pregunta_db)
        return pregunta_db
    except IntegrityError as e:
        await db.rollback()
        if pregunta is not None and pregunta != pregunta_db.pregunta:
            raise
        raise ValueError("Error al actualizar la pregunta: violación de restricción de integridad") from e

async def delete_pregunta(db: AsyncSession, pregunta: Pregunta):
    """
    Elimina una pregunta y sus respuestas.

    Args:
        db (AsyncSession): Sesión de base de datos.
        pregunta (Pregunta): Instancia de la pregunta a eliminar.
    """
    await db.delete(pregunta)
    await db.commit()

async def get_preguntas_by_evento(db: AsyncSession, id_evento: int):
    """
    Obtiene todas las preguntas de un evento, incluyendo el nombre de la sección.

    Args:
        db (AsyncSession): Sesión de base de datos.
        id_evento (int): ID del evento.

    Returns:
        List[Pregunta]: Preguntas del evento con relaciones cargadas.
    """
    stmt = (
        select(Pregunta)
        .join(Seccion)
        .options(
            selectinload(Pregunta.respuestas),
            selectinload(Pregunta.seccion)
        )
        .where(Seccion.id_evento == id_evento)
    )
    result = await db.execute(stmt)
    preguntas = result.scalars().all()

    # Ordenar las respuestas de cada pregunta
    for pregunta in preguntas:
        if pregunta.respuestas:
            pregunta.respuestas.sort(key=lambda x: getattr(x, "orden", 0))

    return preguntas