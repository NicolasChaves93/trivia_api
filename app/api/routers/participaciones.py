"""
Módulo de rutas para la gestión de participaciones en eventos.

Este módulo maneja las operaciones relacionadas con la participación de usuarios
en eventos de trivia, incluyendo:
- Gestionar (iniciar o continuar) una participación
- Finalizar una participación con sus respuestas
- Eliminar una participación
- Consultar participaciones por estado
- Consultar participaciones por usuario y/o evento
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import get_db
from app.services import participacion
from app.schemas.participacion import (
    GestionarParticipacionRequest,
    FinalizarParticipacionRequest,
    ParticipacionResponse,
    ListarParticipacionesResponse
)
from app.models.participacion import EstadoParticipacion
from app.core.auth import crear_token, verificar_token

from app.core.logger import MyLogger
logger = MyLogger().get_logger()

router = APIRouter(prefix="/participaciones", tags=["Participaciones"])

@router.post(
    "/loginU",
    response_model=ParticipacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Gestionar participación en grupo"
)
async def gestionar_participante(
    data: GestionarParticipacionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Llama a la capa de CRUD para crear, continuar o finalizar
    una participación sin duplicar validaciones en el router.
    """
    try:
        result = await participacion.gestionar_participacion(
            db,
            nombre=data.nombre,
            cedula=data.cedula,
            grupo_id=data.grupo_id
        )
    except HTTPException:
        # Simplemente relanzamos la excepción original
        raise
    except Exception as e:
        # Aquí sí capturamos todo lo demás
        logger.exception(
            "Error inesperado al gestionar participación (grupo=%s)",
            data.grupo_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al gestionar la participación"
        ) from e

    token = crear_token({
        "cedula": data.cedula,
        "nombre": data.nombre,
        "id_grupo": data.grupo_id,
        "id_evento": data.evento_id,
        "id_participacion": result["id_participacion"]
    })

    return ParticipacionResponse(
        token            = token,
        action           = result["action"],
        id_participacion = result["id_participacion"],
        numero_intento   = result["numero_intento"],
        respuestas       = result["respuestas"],
        started_at       = result["started_at"],
        tiempo_total     = result.get("tiempo_total")
    )

@router.put(
    "/finalizar",
    status_code=status.HTTP_200_OK,
    summary="Finalizar participación"
)
async def finalizar(
    data: FinalizarParticipacionRequest,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(verificar_token)
):
    """
    Finaliza una participación registrando las respuestas y el tiempo.

    Args:
        data: Datos de finalización incluyendo respuestas y tiempo
        db: Sesión de base de datos

    Raises:
        HTTPException: 500 si hay error al finalizar la participación
    """
    # Validar que el token corresponda al evento solicitado
    if usuario["id_participacion"] != data.id_participacion:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para actualizar esta participación"
        )
    
    try:
        resultado = await participacion.finalizar_participacion(
            db,
            data.id_participacion,
            [resp.model_dump() for resp in data.respuestas],
            data.tiempo
        )
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al finalizar la participación: {str(e)}"
        ) from e

@router.delete(
    "/{id_participacion}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una participación"
)
async def eliminar(
    id_participacion: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina una participación y todos sus datos relacionados.

    Args:
        id_participacion: ID de la participación a eliminar
        db: Sesión de base de datos

    Raises:
        HTTPException: 404 si la participación no existe
    """
    await participacion.eliminar_participacion(db, id_participacion)

@router.get(
    "/estado/{estado}",
    response_model=ListarParticipacionesResponse,
    summary="Listar participaciones por estado"
)
async def listar_por_estado(
    estado: EstadoParticipacion,
    id_evento: Optional[int] = None,
    id_grupo: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene todas las participaciones que tienen un estado específico,
    opcionalmente filtradas por evento y/o grupo.

    Args:
        estado: Estado de las participaciones a buscar (pendiente o finalizado)
        id_evento (Optional[int]): ID del evento para filtrar
        id_grupo (Optional[int]): ID del grupo para filtrar
        db: Sesión de base de datos

    Returns:
        ListarParticipacionesResponse: Lista de participaciones y total
    """
    participaciones = await participacion.get_participaciones_por_estado(
        db, estado, id_evento=id_evento, id_grupo=id_grupo
    )
    return ListarParticipacionesResponse(
        participaciones=participaciones,
        total=len(participaciones)
    )

@router.get(
    "/buscar",
    response_model=ListarParticipacionesResponse,
    summary="Buscar participaciones por cédula, evento y/o grupo"
)
async def buscar_participaciones(
    cedula: Optional[str] = None,
    id_evento: Optional[int] = None,
    id_grupo: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca participaciones filtrando por cédula del usuario, evento y/o grupo.

    Args:
        cedula (Optional[str]): Cédula del usuario para filtrar
        id_evento (Optional[int]): ID del evento para filtrar
        id_grupo (Optional[int]): ID del grupo para filtrar
        db (AsyncSession): Sesión de base de datos

    Returns:
        ListarParticipacionesResponse: Lista de participaciones que coinciden con los filtros y total

    Raises:
        HTTPException: 400 si no se proporciona ningún filtro
    """
    participaciones = await participacion.get_participaciones_por_usuario_evento(
        db,
        cedula=cedula,
        id_evento=id_evento,
        id_grupo=id_grupo
    )
    return ListarParticipacionesResponse(
        participaciones=participaciones,
        total=len(participaciones)
    )

@router.get(
    "/",
    response_model=ListarParticipacionesResponse,
    summary="Listar todas las participaciones"
)
async def listar_participaciones(
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene todas las participaciones registradas.

    Args:
        db: Sesión de base de datos

    Returns:
        ListarParticipacionesResponse: Lista de todas las participaciones y total
    """
    participaciones = await participacion.get_all_participaciones(db)
    return ListarParticipacionesResponse(
        participaciones=participaciones,
        total=len(participaciones)
    )

@router.get(
    "/grupo/{id_grupo}",
    response_model=ListarParticipacionesResponse,
    summary="Listar participaciones por grupo"
)
async def listar_por_grupo(
    id_grupo: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene todas las participaciones de un grupo específico.

    Args:
        id_grupo (int): ID del grupo para filtrar
        db (AsyncSession): Sesión de base de datos

    Returns:
        ListarParticipacionesResponse: Lista de participaciones del grupo y total

    Raises:
        HTTPException: 404 si el grupo no existe
    """
    participaciones = await participacion.get_participaciones_por_grupo(db, id_grupo)
    return ListarParticipacionesResponse(
        participaciones=participaciones,
        total=len(participaciones)
    )
