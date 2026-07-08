from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.settings_instance import settings

# Única fuente de verdad para la conexión: la configuración centralizada (pydantic).
DATABASE_URL = settings.database_url

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,                # True solo en desarrollo
    future=True,               # API moderna
    pool_pre_ping=True,        # Verifica conexiones
    pool_size=20,              # Pool base
    max_overflow=10,           # Extra en carga pico
    pool_recycle=1800          # Evita timeouts
)

def get_engine():
    """
    Retorna la instancia única del motor asíncrono de SQLAlchemy.

    Returns:
        AsyncEngine: Motor configurado para conexión a la base de datos.
    """
    return engine

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    """
    Dependencia de FastAPI para obtener una sesión de base de datos asíncrona.

    Yields:
        AsyncSession: Sesión activa para consultas o transacciones en la base de datos.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()