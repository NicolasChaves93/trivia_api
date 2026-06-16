"""Healthcheck: estado del servicio y ping a la base de datos.

Útil para readiness/liveness de Azure App Service y para diagnóstico rápido.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Estado del servicio")
async def health(db: AsyncSession = Depends(get_db)):
    """Devuelve 200 si la app y la BD responden; 503 si la BD falla."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "error"})
