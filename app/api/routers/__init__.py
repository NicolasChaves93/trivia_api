from fastapi import APIRouter
from app.api.routers import (
    eventos,
    usuarios,
    participaciones,
    informes,
    secciones,
    preguntas,
    grupos
)

api_router = APIRouter()
# Rutas principales
api_router.include_router(eventos.router)
api_router.include_router(secciones.router)
api_router.include_router(grupos.router)
api_router.include_router(preguntas.router)
api_router.include_router(participaciones.router)
api_router.include_router(usuarios.router)

# General
api_router.include_router(informes.router)