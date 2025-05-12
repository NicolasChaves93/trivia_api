from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import get_db
from app.services import informes
from app.schemas.informes import RankingUsuarioOut

router = APIRouter(prefix="/informes", tags=["Informes"])

@router.get("/pendientes")
async def listar_pendientes(db: AsyncSession = Depends(get_db)):
    return await informes.usuarios_pendientes(db)

@router.get("/finalizados")
async def listar_finalizados(db: AsyncSession = Depends(get_db)):
    return await informes.usuarios_finalizados(db)

@router.get(
    "/ranking",
    response_model=List[RankingUsuarioOut],
    summary="Obtener ranking de usuarios",
    description="Devuelve un ranking de usuarios basado en el número de respuestas correctas " \
    "y el tiempo total de juego, con filtros opcionales por grupo e intento."
)
async def obtener_ranking(
    grupo_id: int = Query(None, description="ID del grupo al que pertenecen los usuarios"),
    numero_intento: int = Query(None, description="Número del intento realizado por los usuarios"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna un ranking ordenado de usuarios que han finalizado la trivia.

    - Ordena primero por `respuestas_correctas` (descendente)
    - Luego por `tiempo_total` (ascendente)
    - Permite filtrar por `grupo_id` y `numero_intento`

    Esta información es útil para informes y visualización de resultados.
    """
    return await informes.ranking_usuarios(db, grupo_id, numero_intento)
