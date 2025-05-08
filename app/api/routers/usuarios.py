"""
Módulo de rutas para la gestión de usuarios.

Incluye operaciones CRUD:
- Listar todos los usuarios
- Obtener un usuario por cédula
- Crear un nuevo usuario
- Eliminar un usuario por cédula
- Eliminar todos los usuarios
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.db.connection import get_db
from app.crud import crud_usuarios
from app.schemas.usuario import UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/", response_model=List[UsuarioOut])
async def listar_usuarios(db: AsyncSession = Depends(get_db)):
    """
    Retorna una lista de todos los usuarios registrados.

    Returns:
        List[UsuarioOut]: Lista de usuarios disponibles.
    """
    return await crud_usuarios.get_usuarios(db)

@router.get("/{cedula}", response_model=UsuarioOut)
async def obtener_usuario(cedula: str, db: AsyncSession = Depends(get_db)):
    """
    Obtiene un usuario específico por su número de cédula.

    Args:
        cedula (str): Número de cédula del usuario a buscar

    Returns:
        UsuarioOut: Datos del usuario

    Raises:
        HTTPException: 404 si el usuario no existe
    """
    usuario = await crud_usuarios.get_usuario_by_cedula(db, cedula)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario

@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def crear_usuario(usuario: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo usuario.

    Args:
        usuario (UsuarioCreate): Datos del usuario a crear

    Returns:
        UsuarioOut: El usuario creado

    Raises:
        HTTPException: 400 si ya existe un usuario con la misma cédula
    """
    try:
        return await crud_usuarios.create_usuario(db, usuario.cedula, usuario.nombre)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con esa cédula"
        ) from exc

@router.delete("/{cedula}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(cedula: str, db: AsyncSession = Depends(get_db)):
    """
    Elimina un usuario específico por su número de cédula.
    
    Args:
        cedula (str): Número de cédula del usuario a eliminar
        db (AsyncSession): Sesión de base de datos
        
    Raises:
        HTTPException: 404 si el usuario no existe
    """
    usuario = await crud_usuarios.delete_usuario_by_cedula(db, cedula)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_todos_usuarios(db: AsyncSession = Depends(get_db)):
    """
    Elimina todos los usuarios de la base de datos.
    Esta operación no se puede deshacer.
    """
    await crud_usuarios.delete_all_usuarios(db)
