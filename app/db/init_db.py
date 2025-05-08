"""Inicializa las tablas, funciones y triggers para el esquema 'trivia'."""
import os
from sqlalchemy.ext.asyncio import AsyncEngine  # Terceros
from sqlalchemy import text
from app.db import get_engine  # Proyecto propio
from app.models import Base

async def init_models(engine: AsyncEngine):
    """
    Inicializa los modelos ORM y crea el esquema en la base de datos si no existe.

    Esta función se ejecuta al iniciar la aplicación. Crea el esquema 'trivia' y las tablas
    asociadas a los modelos declarados. También puede ejecutar scripts SQL adicionales como funciones o triggers.

    Args:
        engine (AsyncEngine): Motor asincrónico de SQLAlchemy conectado a la base de datos.
    """
    async with engine.begin() as conn:
        # Siempre crear esquema y tablas
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS trivia"))
        await conn.run_sync(Base.metadata.create_all)

        # Solo en entorno que no sea producción
        env = os.getenv("APP_ENV", "dev")
        if env != "prod":
            await conn.execute(text("SET search_path = trivia, public"))
            await run_sql_scripts(conn, [
                    "app/sql/create_function_gestionar_participacion.sql",
                    "app/sql/create_function_trg_participacion_finalizada.sql",
                    "app/sql/drop_trigger_participacion.sql",
                    "app/sql/create_trigger_participacion.sql"
                ])

async def run_sql_scripts(conn, script_paths):
    """
    Ejecuta scripts SQL individuales, uno por sentencia, para compatibilidad con asyncpg.
    """

    for path in script_paths:
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read().strip()
            if sql:
                await conn.execute(text(sql))

async def init():
    """Función externa para lanzar la inicialización de base de datos."""
    engine = get_engine()
    await init_models(engine)

