"""
Módulo de rutas para la gestión de eventos.

Incluye operaciones CRUD básicas:
- Listar todos los eventos
- Obtener un evento por ID
- Crear un nuevo evento (con validaciones)
- Eliminar un evento por ID

Las respuestas están documentadas automáticamente en Swagger (/docs).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import get_db
from app.crud import crud_eventos
from app.schemas.evento import EventoCreate, EventoOut

from app.core.logger import MyLogger
logger = MyLogger().get_logger()

EVENTO_NO_ENCONTRADO = "Evento no encontrado"
EVENTO_DUPLICADO    = "Ya existe un evento con ese nombre."

router = APIRouter(prefix="/eventos", tags=["Eventos"])
"""
Router de FastAPI para operaciones relacionadas con eventos.

Prefijo: `/eventos`
Tag: `Eventos` (para agrupar en Swagger)
"""

@router.get("/", response_model=List[EventoOut], summary="Listar todos los eventos")
async def listar_eventos(db: AsyncSession = Depends(get_db)):
    """
    Retorna una lista de todos los eventos registrados en la base de datos.

    Returns:
        List[Evento]: Lista de eventos disponibles.
    """
    return await crud_eventos.get_eventos(db)

@router.get("/{evento_id}", response_model=EventoOut, summary="Obtener un evento por ID")
async def obtener_evento(evento_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retorna la información de un evento específico por su ID.

    Args:
        evento_id (int): Identificador del evento.

    Returns:
        Evento: Objeto con los datos del evento.

    Raises:
        HTTPException: 404 si el evento no existe.
    """
    evento = await crud_eventos.get_by_id(db, evento_id)
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=EVENTO_NO_ENCONTRADO
        )
    return evento

@router.post("/", response_model=EventoOut, status_code=status.HTTP_201_CREATED, summary="Crear un nuevo evento")
async def crear_evento(
    evento_in: EventoCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo evento si no existe previamente.

    Validaciones:
    - El nombre del evento no debe repetirse.
    - El tipo de login debe ser válido (Enum: generico, localidad).

    Args:
        evento_in (EventoCreate): Objeto con nombre y tipo_login del evento.
        db (AsyncSession): Sesión asíncrona de base de datos.

    Returns:
        EventoOut: El evento recién creado.

    Raises:
        HTTPException: 400 si ya existe un evento con ese nombre.
                      500 si ocurre un error inesperado.
    """

    # Validar que no exista un evento con el mismo nombre
    existente = await crud_eventos.get_by_nombre(db, evento_in.nombre_evento)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=EVENTO_DUPLICADO
        )

    try:
        # Crear el evento usando el método del CRUD
        nuevo_evento = await crud_eventos.create_evento(
            db,
            evento_in.nombre_evento,
            evento_in.tipo_login
        )
        return nuevo_evento

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datos inválidos: {str(e)}"
        ) from e

    except Exception as e:
        logger.error("Error al crear evento: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el evento."
        ) from e

@router.delete("/{evento_id}", summary="Eliminar un evento", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_evento(evento_id: int, db: AsyncSession = Depends(get_db)):
    """
    Elimina un evento por su ID.

    Args:
        evento_id (int): Identificador del evento.
        db (AsyncSession): Sesión de base de datos.

    Raises:
        HTTPException: 404 si el evento no existe.
    """
    evento = await crud_eventos.get_by_id(db, evento_id)
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=EVENTO_NO_ENCONTRADO
        )
    
    await crud_eventos.delete_evento(db, evento)