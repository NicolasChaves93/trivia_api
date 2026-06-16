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

# Ruta a alembic.ini en la raíz del proyecto (init_db.py está en app/db/)
_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def _upgrade_to_head() -> None:
    """Aplica las migraciones pendientes hasta la última revisión (síncrono)."""
    cfg = Config(str(_ALEMBIC_INI))
    command.upgrade(cfg, "head")


async def init() -> None:
    """Ejecuta `alembic upgrade head` en un thread aparte.

    El runner online de Alembic usa `asyncio.run()` internamente, que no puede invocarse
    dentro del event loop ya activo de FastAPI; por eso se ejecuta en un executor.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _upgrade_to_head)
