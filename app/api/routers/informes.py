from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import get_db
from app.services import informes

router = APIRouter(prefix="/informes", tags=["Informes"])

@router.get("/pendientes")
async def listar_pendientes(db: AsyncSession = Depends(get_db)):
    return await informes.usuarios_pendientes(db)

@router.get("/finalizados")
async def listar_finalizados(db: AsyncSession = Depends(get_db)):
    return await informes.usuarios_finalizados(db)
