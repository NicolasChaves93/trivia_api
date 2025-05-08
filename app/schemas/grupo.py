"""
Esquema de validación para los grupos en la API de trivia.

Contiene las clases `GrupoCreate` y `GrupoOut` que validan y representan los grupos:
- GrupoCreate: Para crear nuevos grupos
- GrupoOut: Para la respuesta de la API
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, ConfigDict

class GrupoCreate(BaseModel):
    """
    Esquema de entrada para crear un nuevo grupo.

    Atributos:
        id_evento (int): ID del evento al que pertenece el grupo
        nombre_grupo (str): Nombre del grupo. No puede estar vacío.
        fecha_inicio (datetime): Fecha y hora de inicio del grupo
        fecha_cierre (datetime): Fecha y hora de cierre del grupo
    """
    id_evento: int = Field(..., gt=0, description="ID del evento al que pertenece el grupo")
    nombre_grupo: str = Field(..., min_length=1, description="Nombre del grupo")
    fecha_inicio: datetime = Field(..., description="Fecha y hora de inicio del grupo")
    fecha_cierre: datetime = Field(..., description="Fecha y hora de cierre del grupo")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

    @field_validator("nombre_grupo")
    @classmethod
    def formato_titulo(cls, value: str) -> str:
        """
        Validador que limpia y transforma el nombre del grupo.

        Args:
            value (str): Nombre del grupo ingresado

        Returns:
            str: Nombre formateado

        Raises:
            ValueError: Si el campo está vacío tras hacer strip()
        """
        value = value.strip()
        if not value:
            raise ValueError("El nombre del grupo no puede estar vacío")
        return value.title()

    @field_validator("fecha_inicio", "fecha_cierre")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        """
        Asegura que las fechas tengan zona horaria UTC.
        """
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("fecha_cierre")
    @classmethod
    def validar_fecha_cierre(cls, value: datetime, values: dict) -> datetime:
        """
        Validador que asegura que la fecha de cierre sea posterior a la fecha de inicio.

        Args:
            value (datetime): Fecha de cierre
            values (dict): Valores ya validados, incluyendo fecha_inicio

        Returns:
            datetime: Fecha de cierre validada

        Raises:
            ValueError: Si la fecha de cierre es anterior o igual a la fecha de inicio
        """
        if "fecha_inicio" in values.data and value <= values.data["fecha_inicio"]:
            raise ValueError("La fecha de cierre debe ser posterior a la fecha de inicio")
        return value

class GrupoOut(BaseModel):
    """
    Esquema de salida para representar un grupo en las respuestas de la API.

    Atributos:
        id_grupo (int): Identificador único del grupo
        id_evento (int): ID del evento al que pertenece
        nombre_grupo (str): Nombre del grupo en formato Título
        fecha_inicio (datetime): Fecha y hora de inicio del grupo
        fecha_cierre (datetime): Fecha y hora de cierre del grupo
    """
    id_grupo: int
    id_evento: int
    nombre_grupo: str
    fecha_inicio: datetime
    fecha_cierre: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )