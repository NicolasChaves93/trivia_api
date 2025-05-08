"""
Módulo de rutas para la gestión de grupos.

Incluye operaciones CRUD:
- Listar todos los grupos
- Listar grupos por evento
- Obtener grupos activos
- Obtener un grupo por ID
- Crear un nuevo grupo
- Actualizar un grupo existente
- Eliminar un grupo
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.db.connection import get_db
from app.crud import crud_grupos, crud_eventos
from app.schemas.grupo import GrupoCreate, GrupoOut

router = APIRouter(prefix="/grupos", tags=["Grupos"])

# Constantes para mensajes de error
GRUPO_NO_ENCONTRADO = "Grupo no encontrado"
EVENTO_NO_ENCONTRADO = "Evento no encontrado"
GRUPO_NOMBRE_DUPLICADO = "Ya existe un grupo con ese nombre en el evento"
GRUPO_NOMBRE_VACIO = "El nombre del grupo no puede estar vacío"
FECHA_CIERRE_INVALIDA = "La fecha de cierre debe ser posterior a la fecha de inicio"

@router.get("/", response_model=List[GrupoOut])
async def listar_grupos(db: AsyncSession = Depends(get_db)):
    """
    Retorna una lista de todos los grupos registrados.

    Returns:
        List[GrupoOut]: Lista de grupos disponibles.
    """
    return await crud_grupos.get_grupos(db)

@router.get("/evento/{evento_id}", response_model=List[GrupoOut])
async def listar_grupos_por_evento(evento_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retorna todos los grupos de un evento específico.

    Args:
        evento_id (int): ID del evento

    Returns:
        List[GrupoOut]: Lista de grupos del evento

    Raises:
        HTTPException: 404 si el evento no existe
    """
    evento = await crud_eventos.get_by_id(db, evento_id)
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=EVENTO_NO_ENCONTRADO
        )
    return await crud_grupos.get_grupos_by_evento(db, evento_id)

@router.get("/activos", response_model=List[GrupoOut])
async def listar_grupos_activos(
    fecha: Optional[datetime] = Query(None, description="Fecha para verificar grupos activos"),
    evento_id: Optional[int] = Query(None, description="ID del evento para filtrar grupos"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna todos los grupos activos en una fecha específica.
    Si no se proporciona fecha, usa la fecha actual.

    Args:
        fecha (Optional[datetime]): Fecha para verificar grupos activos
        evento_id (Optional[int]): ID del evento para filtrar grupos

    Returns:
        List[GrupoOut]: Lista de grupos activos
    """
    return await crud_grupos.get_grupos_activos(db, fecha, evento_id)

@router.get("/{grupo_id}", response_model=GrupoOut)
async def obtener_grupo(grupo_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retorna la información de un grupo específico.

    Args:
        grupo_id (int): ID del grupo

    Returns:
        GrupoOut: Datos del grupo

    Raises:
        HTTPException: 404 si el grupo no existe
    """
    grupo = await crud_grupos.get_grupo(db, grupo_id)
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=GRUPO_NO_ENCONTRADO
        )
    return grupo

@router.post("/", response_model=GrupoOut, status_code=status.HTTP_201_CREATED)
async def crear_grupo(grupo: GrupoCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo grupo en un evento.

    Args:
        grupo (GrupoCreate): Datos del grupo a crear

    Returns:
        GrupoOut: El grupo creado

    Raises:
        HTTPException:
            - 404 si el evento no existe
            - 400 si ya existe un grupo con el mismo nombre en el evento
            - 400 si la fecha de cierre es anterior a la fecha de inicio
    """
    # Verificar que el evento existe
    evento = await crud_eventos.get_by_id(db, grupo.id_evento)
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=EVENTO_NO_ENCONTRADO
        )
    
    try:
        return await crud_grupos.create_grupo(
            db,
            grupo.id_evento,
            grupo.nombre_grupo,
            grupo.fecha_inicio,
            grupo.fecha_cierre
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=GRUPO_NOMBRE_DUPLICADO
        ) from exc

@router.put("/{grupo_id}", response_model=GrupoOut)
async def actualizar_grupo(
    grupo_id: int,
    nombre_grupo: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_cierre: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un grupo existente.

    Args:
        grupo_id (int): ID del grupo a actualizar
        nombre_grupo (Optional[str]): Nuevo nombre para el grupo
        fecha_inicio (Optional[datetime]): Nueva fecha de inicio
        fecha_cierre (Optional[datetime]): Nueva fecha de cierre

    Returns:
        GrupoOut: El grupo actualizado

    Raises:
        HTTPException:
            - 404 si el grupo no existe
            - 400 si ya existe otro grupo con el mismo nombre en el evento
            - 400 si la fecha de cierre es anterior a la fecha de inicio
    """
    # Obtener el grupo existente
    grupo_actual = await crud_grupos.get_grupo(db, grupo_id)
    if not grupo_actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=GRUPO_NO_ENCONTRADO
        )

    # Validar fechas si se proporcionan ambas
    if fecha_inicio and fecha_cierre and fecha_cierre <= fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=FECHA_CIERRE_INVALIDA
        )
    
    # Validar nombre si se proporciona
    if nombre_grupo:
        nombre_grupo = nombre_grupo.strip()
        if not nombre_grupo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=GRUPO_NOMBRE_VACIO
            )
        nombre_grupo = nombre_grupo.title()

    try:
        grupo = await crud_grupos.update_grupo(
            db,
            grupo_id,
            nombre_grupo=nombre_grupo,
            fecha_inicio=fecha_inicio,
            fecha_cierre=fecha_cierre
        )
        if not grupo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=GRUPO_NO_ENCONTRADO
            )
        return grupo
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=GRUPO_NOMBRE_DUPLICADO
        ) from exc

@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_grupo(grupo_id: int, db: AsyncSession = Depends(get_db)):
    """
    Elimina un grupo por su ID.

    Args:
        grupo_id (int): ID del grupo a eliminar

    Raises:
        HTTPException: 404 si el grupo no existe
    """
    grupo = await crud_grupos.get_grupo(db, grupo_id)
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=GRUPO_NO_ENCONTRADO
        )
    
    await crud_grupos.delete_grupo(db, grupo)