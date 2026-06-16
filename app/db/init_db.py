"""Inicialización del esquema de base de datos vía Alembic.

El esquema (schema `trivia` y todas las tablas) se gestiona con migraciones Alembic,
no con `Base.metadata.create_all`. Al arrancar la aplicación se aplican las migraciones
pendientes (`alembic upgrade head`), de modo que Alembic es la única fuente de verdad.

La lógica de negocio de las participaciones vive en la capa de servicios de Python
(app/services/participacion.py), no en funciones/triggers PL/pgSQL.
"""
import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.db import get_engine

# Ruta a alembic.ini en la raíz del proyecto (init_db.py está en app/db/)
_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

# Clave fija para el advisory lock que serializa las migraciones entre workers.
_MIGRATION_LOCK_KEY = 947563


def _upgrade_to_head() -> None:
    """Aplica las migraciones pendientes hasta la última revisión (síncrono)."""
    cfg = Config(str(_ALEMBIC_INI))
    command.upgrade(cfg, "head")


async def init() -> None:
    """Ejecuta `alembic upgrade head` serializado entre workers.

    Con varios workers de gunicorn, todos llaman a init() al arrancar. Para que no
    corran `upgrade` en paralelo (y eviten carreras en un primer deploy con BD nueva),
    se toma un advisory lock de Postgres: el primer worker migra; los demás esperan y,
    al obtener el lock, la BD ya está en head (upgrade no-op).

    El runner online de Alembic usa `asyncio.run()` internamente, que no puede invocarse
    dentro del event loop ya activo de FastAPI; por eso `upgrade` corre en un executor.
    El advisory lock es a nivel de sesión: se mantiene en `conn` mientras Alembic migra
    en su propia conexión, sin afectar el DDL.
    """
    loop = asyncio.get_event_loop()
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": _MIGRATION_LOCK_KEY})
        try:
            await loop.run_in_executor(None, _upgrade_to_head)
        finally:
            await conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _MIGRATION_LOCK_KEY})
            await conn.commit()
