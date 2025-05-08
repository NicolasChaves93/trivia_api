"""
Servicios para gestionar las participaciones en eventos de trivia.

Este módulo contiene la lógica de negocio para:
- Gestionar participaciones (crear/continuar)
- Finalizar participaciones con respuestas
- Eliminar participaciones
- Consultar participaciones por estado
- Consultar participaciones por usuario y/o evento
- Listar todas las participaciones
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.models.participacion import Participacion, EstadoParticipacion
from app.models.usuario import Usuario
from app.models.grupo import Grupo


async def gestionar_participacion(
    db: AsyncSession, 
    nombre: str, 
    cedula: str, 
    grupo_id: int
) -> Optional[Dict[str, Any]]:
    """
    Gestiona la participación de un usuario en un grupo.

    Llama a la función de base de datos 'gestionar_participacion' que:
    1. Crea o actualiza el usuario
    2. Valida que el grupo exista y esté en período válido
    3. Obtiene o crea la participación

    Args:
        db: Sesión de base de datos
        nombre: Nombre del participante
        cedula: Número de cédula
        grupo_id: ID del grupo en el que participa

    Returns:
        Dict con los datos de la participación o None si hay error:
        - action: "iniciar", "continuar" o "finalizado"
        - id_participacion: ID de la participación
        - respuestas: Lista de respuestas del usuario
        - started_at: Timestamp de inicio
        - tiempo_total: Tiempo transcurrido (si aplica)

    Raises:
        SQLAlchemyError: Si hay error de base de datos
        ValueError: Si los datos retornados son inválidos
    """
    try:
        result = await db.execute(
            text("SELECT * FROM trivia.gestionar_participacion(:nombre, :cedula, :grupo_id)"),
            {"nombre": nombre, "cedula": cedula, "grupo_id": grupo_id}
        )
        row = result.fetchone()
        if row and row[1] is not None:  # Verificar que id_participacion no sea null
            # Confirmar la transacción explícitamente
            await db.commit()
            return {
                "action": row[0],
                "id_participacion": row[1],
                "respuestas": row[2] or [],  # Asegurar lista vacía si es NULL
                "started_at": row[3],
                "tiempo_total": str(row[4]) if row[4] else None
            }
        await db.rollback()
        raise ValueError("Error: la participación no pudo ser creada o recuperada correctamente")
    except SQLAlchemyError as e:
        await db.rollback()
        raise SQLAlchemyError(f"Error al gestionar participación: {str(e)}") from e

async def finalizar_participacion(
    db: AsyncSession,
    id_participacion: int,
    respuestas_usuario: list[dict],
    tiempo_total: str
) -> dict:
    """
    Finaliza una participación de trivia actualizando su estado y registrando las respuestas.

    Esta función realiza las siguientes acciones:
    - Valida la existencia de la participación.
    - Verifica que no esté ya finalizada.
    - Registra las respuestas seleccionadas por el usuario en formato JSONB.
    - Establece el tiempo total de resolución.
    - Marca la participación como finalizada (`estado = 'Finalizado'`).
    - El trigger de base de datos se encarga de calcular:
        - Las respuestas desglosadas (`respuestas_usuarios`)
        - Los resultados (`resultados`)

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        id_participacion (int): ID de la participación a finalizar.
        respuestas_usuario (list[dict]): Lista de objetos con `id_pregunta` y `respuesta_seleccionada`.
        tiempo_total (str): Duración total en formato "HH:MM:SS".

    Returns:
        dict: Un mensaje de éxito con el ID de participación finalizada.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la participación.
            - 400: Si la participación ya está finalizada.
    """
    # Obtener participación existente
    stmt = select(Participacion).where(Participacion.id_participacion == id_participacion)
    result = await db.execute(stmt)
    participacion = result.scalar_one_or_none()

    if not participacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participación no encontrada."
        )

    if participacion.estado == "finalizado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La participación ya está finalizada."
        )

    # Preparar datos para actualizar
    # Parsear el string "HH:MM:SS" a timedelta
    horas, minutos, segundos = map(int, tiempo_total.split(":"))
    duracion = timedelta(hours=horas, minutes=minutos, seconds=segundos)

    stmt_update = (
        update(Participacion)
        .where(Participacion.id_participacion == id_participacion)
        .values(
            respuestas_usuario=respuestas_usuario,
            tiempo_total=duracion,
            finished_at = datetime.now(timezone.utc),
            estado="finalizado"
        )
    )

    await db.execute(stmt_update)
    await db.commit()

    return {"mensaje": "Participación finalizada correctamente", "id": id_participacion}

async def eliminar_participacion(db: AsyncSession, id_participacion: int) -> None:
    """
    Elimina una participación por su ID.

    Args:
        db (AsyncSession): Sesión de base de datos
        id_participacion (int): ID de la participación a eliminar

    Raises:
        HTTPException: 404 si la participación no existe
    """
    participacion = await db.get(Participacion, id_participacion)
    if not participacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participación no encontrada"
        )
    
    await db.delete(participacion)
    await db.commit()

async def get_participaciones_por_estado(
    db: AsyncSession,
    estado: EstadoParticipacion,
    id_evento: Optional[int] = None,
    id_grupo: Optional[int] = None
) -> List[Participacion]:
    """
    Obtiene todas las participaciones que tienen un estado específico.

    Args:
        db (AsyncSession): Sesión de base de datos
        estado (EstadoParticipacion): Estado de las participaciones a buscar

    Returns:
        List[Participacion]: Lista de participaciones con el estado especificado y datos del usuario
    """
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .where(Participacion.estado == estado)
        .order_by(Participacion.id_participacion.asc())
    )

    # Aplicar filtros según los parámetros proporcionados
    if id_evento is not None:
        stmt = (
            stmt.join(Grupo)
            .where(Grupo.id_evento == id_evento)
        )
    if id_grupo is not None:
        stmt = stmt.where(Participacion.id_grupo == id_grupo)

    result = await db.execute(stmt)
    return result.scalars().all()

async def get_participaciones_por_usuario_evento(
    db: AsyncSession,
    cedula: Optional[str] = None,
    id_evento: Optional[int] = None,
    id_grupo: Optional[int] = None
) -> List[Participacion]:
    """
    Obtiene participaciones filtrando por cédula del usuario, evento y/o grupo.

    Args:
        db (AsyncSession): Sesión de base de datos
        cedula (Optional[str]): Cédula del usuario para filtrar (opcional)
        id_evento (Optional[int]): ID del evento para filtrar (opcional)
        id_grupo (Optional[int]): ID del grupo para filtrar (opcional)

    Returns:
        List[Participacion]: Lista de participaciones que coinciden con los filtros

    Raises:
        HTTPException: 400 si no se proporciona ningún filtro
    """
    if cedula is None and id_evento is None and id_grupo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos un criterio de búsqueda (cedula, id_evento o id_grupo)"
        )

    # Construir la consulta base con joins necesarios
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .options(joinedload(Participacion.grupo))
    )
    
    # Aplicar filtros según los parámetros proporcionados
    if cedula is not None:
        stmt = stmt.join(Usuario).where(Usuario.cedula == cedula)
    if id_evento is not None:
        stmt = (
            stmt.join(Grupo)
            .where(Grupo.id_evento == id_evento)
        )
    if id_grupo is not None:
        stmt = stmt.where(Participacion.id_grupo == id_grupo)
    
    # Ordenar por fecha de inicio descendente (más recientes primero)
    stmt = stmt.order_by(Participacion.started_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_all_participaciones(db: AsyncSession) -> List[Participacion]:
    """
    Obtiene todas las participaciones registradas.

    Args:
        db (AsyncSession): Sesión de base de datos

    Returns:
        List[Participacion]: Lista de todas las participaciones con datos del usuario y grupo
    """
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .options(joinedload(Participacion.grupo))
        .order_by(Participacion.started_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_participaciones_por_grupo(db: AsyncSession, id_grupo: int) -> List[Participacion]:
    """
    Obtiene todas las participaciones de un grupo específico.

    Args:
        db (AsyncSession): Sesión de base de datos
        id_grupo (int): ID del grupo para filtrar

    Returns:
        List[Participacion]: Lista de participaciones del grupo con datos del usuario
    """
    stmt = (
        select(Participacion)
        .options(joinedload(Participacion.usuario))
        .where(Participacion.id_grupo == id_grupo)
        .order_by(Participacion.started_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
