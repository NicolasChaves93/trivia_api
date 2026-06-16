"""
Configuración compartida para los tests.

Inyecta variables de entorno mínimas antes de importar la aplicación, de modo que
`app.core.settings` pueda instanciarse sin un archivo `.env` real. Los tests de lógica
pura (decidir_accion / calcular_resultado) no abren conexiones a la base de datos.
"""
import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("POSTGRES_DB_SCHEMA_TRIVIA", "trivia")
os.environ.setdefault("POSTGRES_DB_USER", "test")
os.environ.setdefault("POSTGRES_DB_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB_NAME", "test")
os.environ.setdefault("POSTGRES_DB_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB_PORT", "5432")
os.environ.setdefault("SECRET_KEY", "clave-de-prueba")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("LOG_CONSOLA_LEVEL", "INFO")
