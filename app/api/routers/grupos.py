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
from datetime import datetime, timedelta
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
    """Retorna una lista de todos los grupos registrados."""
    return await crud_grupos.get_grupos(db)

@router.get("/evento/{evento_id}", response_model=List[GrupoOut])
async def listar_grupos_por_evento(evento_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna todos los grupos de un evento específico."""
    evento = await crud_eventos.get_by_id(db, evento_id)
    if not evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EVENTO_NO_ENCONTRADO)
    return await crud_grupos.get_grupos_by_evento(db, evento_id)

@router.get("/activos", response_model=List[GrupoOut])
async def listar_grupos_activos(
    fecha: Optional[datetime] = Query(None, description="Fecha para verificar grupos activos"),
    evento_id: Optional[int] = Query(None, description="ID del evento para filtrar grupos"),
    db: AsyncSession = Depends(get_db)
):
    """Retorna todos los grupos activos en una fecha específica."""
    return await crud_grupos.get_grupos_activos(db, fecha, evento_id)

@router.get("/{grupo_id}", response_model=GrupoOut)
async def obtener_grupo(grupo_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna la información de un grupo específico."""
    grupo = await crud_grupos.get_grupo(db, grupo_id)
    if not grupo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GRUPO_NO_ENCONTRADO)
    return grupo

@router.post("/", response_model=GrupoOut, status_code=status.HTTP_201_CREATED)
async def crear_grupo(grupo: GrupoCreate, db: AsyncSession = Depends(get_db)):
    """Crea un nuevo grupo en un evento."""
    evento = await crud_eventos.get_by_id(db, grupo.id_evento)
    if not evento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EVENTO_NO_ENCONTRADO)
    try:
        return await crud_grupos.create_grupo(
            db,
            grupo.id_evento,
            grupo.nombre_grupo,
            grupo.fecha_inicio,
            grupo.fecha_cierre,
            grupo.max_intentos,
            grupo.cooldown
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=GRUPO_NOMBRE_DUPLICADO) from exc

@router.put("/{grupo_id}", response_model=GrupoOut)
async def actualizar_grupo_endpoint(
    grupo_id: int,
    nombre_grupo: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_cierre: Optional[datetime] = None,
    max_intentos: Optional[int] = None,
    cooldown: Optional[timedelta] = None,
    db: AsyncSession = Depends(get_db)
):
    """Actualiza un grupo existente, incluyendo cooldown."""
    grupo = await crud_grupos.update_grupo(
        db,
        grupo_id,
        nombre_grupo,
        fecha_inicio,
        fecha_cierre,
        max_intentos,
        cooldown
    )
    if not grupo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GRUPO_NO_ENCONTRADO)
    return grupo

@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_grupo(grupo_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina un grupo por su ID."""
    grupo = await crud_grupos.get_grupo(db, grupo_id)
    if not grupo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GRUPO_NO_ENCONTRADO)
    await crud_grupos.delete_grupo(db, grupo)