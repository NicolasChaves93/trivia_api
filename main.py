"""
Main entry point for the FastAPI application.

This module initializes the FastAPI app and includes the API routers.
It also sets up the database connection on startup and configures Swagger authentication.

Attributes:
    app (FastAPI): The FastAPI application instance.
Methods:
    lifespan(): Lifecycle handler that runs on startup to initialize database.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.db.init_db import init
from app.api.routers import api_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Lifecycle handler for the FastAPI app.

    This function runs automatically on app startup and shutdown.
    It's useful for initializing connections, loading configs, etc.
    """
    await init()  # Initializes database or other services
    yield
    # You can optionally clean up resources here

# Create FastAPI instance with custom lifespan
app = FastAPI(
    title="API Trivia App",
    description="API para gestionar eventos, usuarios y trivias",
    version="1.0.0",
    debug=True,
    lifespan=lifespan
)

# Enable CORS (recommended for frontend-backend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, access_log=True)