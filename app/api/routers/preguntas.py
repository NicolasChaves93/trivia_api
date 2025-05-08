"""
Módulo de rutas para la gestión de preguntas.

Incluye operaciones CRUD:
- Listar todas las preguntas
- Listar preguntas por sección
- Obtener una pregunta por ID
- Crear una nueva pregunta con sus respuestas
- Actualizar una pregunta existente
- Eliminar una pregunta

Las respuestas están documentadas automáticamente en Swagger (/docs).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db.connection import get_db
from app.crud import crud_preguntas, crud_secciones, crud_eventos
from app.schemas.pregunta import PreguntaCreate, PreguntaOut, RespuestaCreate
from app.core.auth import verificar_token

PREGUNTA_NO_ENCONTRADA = "Pregunta no encontrada"

router = APIRouter(prefix="/preguntas", tags=["Preguntas"])

@router.get("/", response_model=List[PreguntaOut])
async def listar_preguntas(db: AsyncSession = Depends(get_db)):
    """
    Retorna una lista de todas las preguntas registradas.

    Returns:
        List[PreguntaOut]: Lista de preguntas disponibles.
    """
    return await crud_preguntas.get_preguntas(db)

@router.get("/seccion/{seccion_id}", response_model=List[PreguntaOut])
async def listar_preguntas_por_seccion(seccion_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retorna todas las preguntas de una sección específica.

    Args:
        seccion_id (int): ID de la sección.

    Returns:
        List[PreguntaOut]: Lista de preguntas de la sección.

    Raises:
        HTTPException: 404 si la sección no existe.
    """
    seccion = await crud_secciones.get_seccion(db, seccion_id)
    if not seccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sección no encontrada"
        )
    return await crud_preguntas.get_preguntas_by_seccion(db, seccion_id)

@router.get(
    "/evento/{evento_id}",
    response_model=List[PreguntaOut],
    status_code=status.HTTP_200_OK,
    summary="Listar preguntas por evento",
    tags=["Preguntas"]
)
async def listar_preguntas_por_evento(
    evento_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(verificar_token)
):
    """
    Obtiene todas las preguntas del evento especificado, incluyendo sus secciones y respuestas.

    Este endpoint requiere autenticación por token JWT. El usuario solo puede acceder a eventos
    autorizados según su token.

    Args:
        evento_id (int): ID del evento del que se desean obtener las preguntas.
        db (AsyncSession): Sesión de base de datos inyectada.
        usuario (dict): Información extraída del token JWT.

    Returns:
        List[PreguntaOut]: Lista de preguntas asociadas al evento, agrupadas por sección.

    Raises:
        HTTPException:
            - 403: Si el usuario intenta acceder a un evento que no le corresponde.
            - 404: Si el evento no existe en la base de datos.
    """

    # Validar que el token corresponda al evento solicitado
    if usuario["id_evento"] != evento_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para acceder a este evento"
        )

    # Validar que el evento exista en la base de datos
    evento = await crud_eventos.get_by_id(db, evento_id)
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evento con ID {evento_id} no encontrado"
        )

    # Obtener preguntas asociadas al evento
    preguntas = await crud_preguntas.get_preguntas_by_evento(db, evento_id)
    return preguntas

@router.get("/{pregunta_id}", response_model=PreguntaOut)
async def obtener_pregunta(pregunta_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retorna la información de una pregunta específica.

    Args:
        pregunta_id (int): ID de la pregunta.

    Returns:
        PreguntaOut: Datos de la pregunta.

    Raises:
        HTTPException: 404 si la pregunta no existe.
    """
    pregunta = await crud_preguntas.get_pregunta(db, pregunta_id)
    if not pregunta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PREGUNTA_NO_ENCONTRADA
        )
    return pregunta

@router.post("/", response_model=PreguntaOut, status_code=status.HTTP_201_CREATED)
async def crear_pregunta(pregunta: PreguntaCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea una nueva pregunta en una sección con sus respuestas.

    Args:
        pregunta (PreguntaCreate): Datos de la pregunta y respuestas a crear.

    Returns:
        PreguntaOut: La pregunta creada con sus respuestas.

    Raises:
        HTTPException: 
            - 404 si la sección no existe.
            - 400 si ya existe una pregunta con el mismo texto en la sección.
    """
    # Verificar que la sección existe
    seccion = await crud_secciones.get_seccion(db, pregunta.id_seccion)
    if not seccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sección no encontrada"
        )
    
    try:
        return await crud_preguntas.create_pregunta(
            db,
            pregunta.id_seccion,
            pregunta.pregunta,
            pregunta.respuestas,
            pregunta.opcion_correcta
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una pregunta con el mismo texto en esta sección"
        ) from exc

@router.put("/{pregunta_id}", response_model=PreguntaOut)
async def actualizar_pregunta(
    pregunta_id: int,
    pregunta: str = None,
    opcion_correcta: int = None,
    respuestas: List[RespuestaCreate] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza una pregunta existente y sus respuestas.

    Args:
        pregunta_id (int): ID de la pregunta a actualizar.
        pregunta (str, optional): Nuevo texto para la pregunta.
        opcion_correcta (int, optional): Nueva opción correcta (1-4).
        respuestas (List[RespuestaCreate], optional): Lista de respuestas a actualizar o agregar.

    Returns:
        PreguntaOut: La pregunta actualizada.

    Raises:
        HTTPException: 
            - 404 si la pregunta no existe.
            - 400 si el texto está vacío después de quitar espacios.
            - 400 si la opción correcta no es válida.
            - 400 si las respuestas no tienen órdenes consecutivos.
    """
    # Obtener la pregunta existente
    pregunta_db = await crud_preguntas.get_pregunta(db, pregunta_id)
    if not pregunta_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PREGUNTA_NO_ENCONTRADA
        )
    
    # Validar y actualizar el texto de la pregunta
    if pregunta is not None:
        pregunta = pregunta.strip()
        if not pregunta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La pregunta no puede estar vacía"
            )
    
    # Validar y actualizar las respuestas si se proporcionan
    if respuestas is not None:
        # Validar que los órdenes sean consecutivos
        ordenes = [r.orden for r in respuestas]
        if sorted(ordenes) != list(range(1, len(respuestas) + 1)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los órdenes de las respuestas deben ser números consecutivos empezando desde 1"
            )
        
        # Si se proporciona opción_correcta, validar que corresponda a una respuesta
        if opcion_correcta is not None and opcion_correcta not in ordenes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La opción correcta debe corresponder al orden de una de las respuestas"
            )
    
    # Actualizar la pregunta con sus respuestas en la base de datos
    try:
        return await crud_preguntas.update_pregunta(
            db,
            pregunta_id,
            pregunta=pregunta,
            opcion_correcta=opcion_correcta,
            respuestas=respuestas
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una pregunta con el mismo texto en esta sección"
        ) from exc

@router.delete("/{pregunta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_pregunta(pregunta_id: int, db: AsyncSession = Depends(get_db)):
    """
    Elimina una pregunta por su ID.

    Args:
        pregunta_id (int): ID de la pregunta a eliminar.

    Raises:
        HTTPException: 404 si la pregunta no existe.
    """
    pregunta = await crud_preguntas.get_pregunta(db, pregunta_id)
    if not pregunta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PREGUNTA_NO_ENCONTRADA
        )
    
    await crud_preguntas.delete_pregunta(db, pregunta)