"""
Main entry point for the FastAPI application.

This module initializes the FastAPI app and includes the API routers.
It also sets up the database connection on startup and configures Swagger authentication.

Attributes:
    app (FastAPI): The FastAPI application instance.
Methods:
    lifespan(): Lifecycle handler that runs on startup to initialize database.
"""

import time
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.db.init_db import init
from app.api.routers import api_router
from app.core.logger import MyLogger
from app.core.settings_instance import settings

# Configurar el logger al inicio de la aplicación
logger = MyLogger().get_logger(name="main")

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Lifecycle handler for the FastAPI app.

    This function runs automatically on app startup and shutdown.
    It's useful for initializing connections, loading configs, etc.
    """
    logger.info("Inicializando aplicación...")
    logger.info(
        "Config pool BD: pool_size=%s max_overflow=%s pool_timeout=%s",
        settings.db_pool_size, settings.db_max_overflow, settings.db_pool_timeout,
    )
    await init()
    logger.info("Base de datos inicializada correctamente")
    yield
    logger.info("Cerrando aplicación...")

# Create FastAPI instance with custom lifespan.
# debug se activa solo fuera de producción (evita exponer tracebacks/config en prod).
app = FastAPI(
    title="API Trivia App",
    description="API para gestionar eventos, usuarios y trivias",
    version="1.0.0",
    debug=not settings.is_prod,
    lifespan=lifespan
)

# CORS: orígenes parametrizables por env (ALLOWED_ORIGINS, separados por coma).
# allow_credentials solo aplica con orígenes explícitos; con "*" el navegador lo rechaza.
_origins = settings.origins_list or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials="*" not in _origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI for JWT Bearer auth in Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi

# Register API routers
app.include_router(api_router)


@app.middleware("http")
async def medir_tiempo(request: Request, call_next):
    """Mide la duración de cada petición y la registra (marca las lentas).

    Expone el tiempo en el header X-Process-Time-ms y registra en WARNING las
    que superan SLOW_REQUEST_MS, para detectar cuellos de botella en Azure.
    """
    inicio = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - inicio) * 1000
    response.headers["X-Process-Time-ms"] = f"{ms:.0f}"
    if ms >= settings.slow_request_ms:
        logger.warning("LENTA %s %s -> %.0f ms (status %s)",
                       request.method, request.url.path, ms, response.status_code)
    else:
        logger.info("%s %s -> %.0f ms", request.method, request.url.path, ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Registra cualquier excepción no controlada con traceback y contexto.

    Garantiza que los fallos queden en los logs (stdout -> Log Stream de Azure)
    para poder diagnosticar, especialmente bajo concurrencia.
    """
    logger.exception(
        "Error no controlado en %s %s: %s",
        request.method, request.url.path, exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )

if __name__ == "__main__":
    logger.info("Iniciando servidor...")
    uvicorn.run(app, host='0.0.0.0', port=8000, access_log=True)