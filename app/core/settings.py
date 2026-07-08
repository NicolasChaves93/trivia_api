from typing import Literal
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Carga automática de .env
load_dotenv()

class Settings(BaseSettings):
    # Tipo de entorno
    environment: Literal["dev", "prod", "test"] = Field(
        default="dev",
        alias="ENVIRONMENT",
        description="Entorno de ejecución"
    )

    # Base de datos
    postgres_db_schema  : str = Field(..., alias="POSTGRES_DB_SCHEMA_TRIVIA")
    postgres_db_user    : str = Field(..., alias="POSTGRES_DB_USER")
    postgres_db_password: str = Field(..., alias="POSTGRES_DB_PASSWORD")
    postgres_db_name    : str = Field(..., alias="POSTGRES_DB_NAME")
    postgres_db_host    : str = Field(..., alias="POSTGRES_DB_HOST")
    postgres_db_port    : int = Field(5432, alias="POSTGRES_DB_PORT")

    # Configuración de JWT
    secret_key            : str = Field( default="tu_clave_secreta_super_segura", alias="SECRET_KEY")
    jwt_algorithm         : str = Field(default="HS256", alias="ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Logging
    log_consola_level: str = Field("INFO", alias="LOG_CONSOLA_LEVEL")

    # Validadores personalizados
    @field_validator("postgres_db_port", mode="before")
    @classmethod
    def convert_port(cls, v):
        """
        Converts the input value to an integer if it represents a valid port number.

        Args:
            v (str or int): The value to be converted. 
            Can be a string containing digits or an integer.

        Returns:
            int: The port number as an integer.

        Raises:
            ValueError: 
            If the input value is neither an integer nor a string representing a valid integer.
        """
        if isinstance(v, str) and v.isdigit():
            return int(v)
        if isinstance(v, int):
            return v
        raise ValueError("POSTGRES_DB_PORT debe ser un número entero")

    @field_validator(
        "postgres_db_schema", "postgres_db_user", "postgres_db_password",
        "postgres_db_name", "postgres_db_host", "log_consola_level",
        "secret_key", "jwt_algorithm", "jwt_expiration_minutes",
        mode="before"
    )
    @classmethod
    def not_empty(cls, v, info):
        if not v or not str(v).strip():
            raise ValueError(f"El campo '{info.field_name}' no puede estar vacío")
        return v

    # Conexión a BD
    @property
    def database_url(self) -> str:
        """
        Constructs and returns the asynchronous PostgreSQL database URL using the configured
        user, password, host, port, and database name.

        Returns:
            str: The formatted database URL for connecting with asyncpg.
        """
        return (
            f"postgresql+asyncpg://{self.postgres_db_user}:{self.postgres_db_password}"
            f"@{self.postgres_db_host}:{self.postgres_db_port}/{self.postgres_db_name}"
        )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="forbid"
    )