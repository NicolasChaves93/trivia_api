"""Inicializa el esquema y las tablas para el esquema 'trivia'.

La lógica de negocio de las participaciones (gestión de intentos, cooldown y cálculo
de resultados) vive ahora en la capa de servicios de Python (app/services/participacion.py),
no en funciones/triggers PL/pgSQL. El arranque solo se ocupa del esquema y las tablas.
"""
from sqlalchemy.ext.asyncio import AsyncEngine  # Terceros
from sqlalchemy import text
from app.db import get_engine  # Proyecto propio
from app.models import Base

async def init_models(engine: AsyncEngine):
    """
    Crea el esquema 'trivia' (si no existe) y todas las tablas declaradas en los modelos ORM.

    Args:
        engine (AsyncEngine): Motor asincrónico de SQLAlchemy conectado a la base de datos.
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS trivia"))
        await conn.run_sync(Base.metadata.create_all)

async def init():
    """Función externa para lanzar la inicialización de base de datos."""
    engine = get_engine()
    await init_models(engine)

