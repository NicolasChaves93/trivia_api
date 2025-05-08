"""
Módulo de rutas para la gestión de secciones.

Incluye operaciones CRUD:
- Listar todas las secciones
- Listar secciones por evento
- Obtener una sección por ID
- Crear una nueva sección
- Actualizar una sección existente
- Eliminar una sección

Las respuestas están documentadas automáticamente en Swagger (/docs).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.db.connection import get_db
from app.crud import crud_eventos, crud_secciones
from app.schemas.seccion import SeccionCreate, SeccionOut

SECCION_NO_ENCONTRADA = "Sección no encontrada"

router = APIRouter(prefix="/secciones", tags=["Secciones"])

@router.get("/", response_model=List[SeccionOut])
async def listar_secciones(db: AsyncSession = Depends(get_db)):
    """
    Retorna una lista de todas las secciones registradas.

    Returns:
        List[SeccionOut]: Lista de secciones disponibles.
    """
    return await crud_secciones.get_secciones(db)

@router.get("/evento/{evento_id}", response_model=List[SeccionOut])
async def listar_secciones_por_evento(evento_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retorna todas las secciones de un evento específico.

    Args:
        evento_id (int): ID del evento.

    Returns:
        List[SeccionOut]: Lista de secciones del evento.

    Raises:
        HTTPException: 404 si el evento no existe.
    """
    evento = await crud_eventos.get_by_id(db, evento_id)
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    return await crud_secciones.get_secciones_by_evento(db, evento_id)

@router.get("/{seccion_id}", response_model=SeccionOut)
async def obtener_seccion(seccion_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retorna la información de una sección específica.

    Args:
        seccion_id (int): ID de la sección.

    Returns:
        SeccionOut: Datos de la sección.

    Raises:
        HTTPException: 404 si la sección no existe.
    """
    seccion = await crud_secciones.get_seccion(db, seccion_id)
    if not seccion:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SECCION_NO_ENCONTRADA
        )
    return seccion

@router.post("/", response_model=SeccionOut, status_code=status.HTTP_201_CREATED)
async def crear_seccion(seccion: SeccionCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea una nueva sección en un evento.

    Args:
        seccion (SeccionCreate): Datos de la sección a crear.

    Returns:
        SeccionOut: La sección creada.

    Raises:
        HTTPException: 
            - 404 si el evento no existe.
            - 400 si ya existe una sección con el mismo nombre en el evento.
    """
    # Verificar que el evento existe
    evento = await crud_eventos.get_by_id(db, seccion.id_evento)
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    try:
        return await crud_secciones.create_seccion(
            db,
            seccion.id_evento,
            seccion.nombre_seccion
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una sección con ese nombre en el evento"
        ) from exc

@router.put("/{seccion_id}", response_model=SeccionOut)
async def actualizar_seccion(
    seccion_id: int,
    nombre_seccion: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza el nombre de una sección existente.

    Args:
        seccion_id (int): ID de la sección a actualizar.
        nombre_seccion (str): Nuevo nombre para la sección.

    Returns:
        SeccionOut: La sección actualizada.

    Raises:
        HTTPException: 
            - 404 si la sección no existe.
            - 400 si ya existe otra sección con el mismo nombre en el evento.
            - 400 si el nombre está vacío después de quitar espacios.
    """
    # Limpiar espacios y validar que no esté vacío
    nombre_seccion = nombre_seccion.strip()
    if not nombre_seccion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de la sección no puede estar vacío"
        )
    
    # Convertir a título
    nombre_seccion = nombre_seccion.title()
    
    try:
        seccion = await crud_secciones.update_seccion(db, seccion_id, nombre_seccion)
        if not seccion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=SECCION_NO_ENCONTRADA
            )
        return seccion
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe otra sección con ese nombre en el evento"
        ) from exc

@router.delete("/{seccion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_seccion(seccion_id: int, db: AsyncSession = Depends(get_db)):
    """
    Elimina una sección por su ID.

    Args:
        seccion_id (int): ID de la sección a eliminar.

    Raises:
        HTTPException: 404 si la sección no existe.
    """
    seccion = await crud_secciones.get_seccion(db, seccion_id)
    if not seccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SECCION_NO_ENCONTRADA
        )
    
    await crud_secciones.delete_seccion(db, seccion)