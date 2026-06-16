from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import get_db
from app.services import informes
from app.services import informe_excel
from app.schemas.informes import RankingUsuarioOut

router = APIRouter(prefix="/informes", tags=["Informes"])


@router.get(
    "/exportar",
    summary="Exportar informe de resultados a Excel (.xlsx)",
    description="Genera un Excel de 4 hojas (ranking/métricas, detalle por pregunta, "
                "pivote por sección y histograma de puntuación) para un evento, con "
                "filtro opcional por grupo y manejo de intentos.",
)
async def exportar_informe(
    evento_id: int = Query(..., description="ID del evento a exportar"),
    grupo_id: int = Query(None, description="ID del grupo (opcional; todos si se omite)"),
    intentos: str = Query(
        "todos",
        description="Intentos a incluir: 'todos' | 'primero' | 'ultimo' | 'mejor'",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve el archivo .xlsx del informe."""
    try:
        contenido = await informe_excel.generar_informe_excel(
            db, evento_id, grupo_id, intentos
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    nombre = f"informe_evento_{evento_id}" + (f"_g{grupo_id}" if grupo_id else "") + ".xlsx"
    return StreamingResponse(
        BytesIO(contenido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )

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
