"""
Esquema de validación para los grupos en la API de trivia.

Contiene las clases `GrupoCreate` y `GrupoOut` que validan y representan los grupos:
- GrupoCreate: Para crear nuevos grupos
- GrupoOut: Para la respuesta de la API
"""

from datetime import datetime, timezone, timedelta
from typing import Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

class GrupoCreate(BaseModel):
    id_evento: int = Field(..., gt=0)
    nombre_grupo: str = Field(..., min_length=1)
    fecha_inicio: datetime
    fecha_cierre: datetime
    max_intentos: int = Field(default=1, ge=1, le=100)
    cooldown: Union[timedelta, str, int] = Field(default=timedelta(minutes=5), description="Intervalo mínimo entre intentos")

    model_config = ConfigDict(
        json_encoders={
            datetime: datetime.isoformat,
            timedelta: str
        }
    )

    @field_validator("fecha_inicio", "fecha_cierre")
    @classmethod
    def ensure_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @field_validator("fecha_cierre")
    @classmethod
    def validar_fechas(cls, v: datetime, values: dict) -> datetime:
        if "fecha_inicio" in values.data and v <= values.data["fecha_inicio"]:
            raise ValueError("fecha_cierre debe ser posterior a fecha_inicio")
        return v

    @field_validator("cooldown", mode="before")
    @classmethod
    def parse_cooldown(cls, v: Union[timedelta, str, int]) -> timedelta:
        if isinstance(v, timedelta):
            return v
        if isinstance(v, int):
            return timedelta(minutes=v)
        if isinstance(v, str):
            parts = v.split(":")
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return timedelta(hours=h, minutes=m, seconds=s)
        raise ValueError("cooldown inválido, debe ser timedelta, 'HH:MM:SS' o entero (minutos)")

class GrupoOut(BaseModel):
    id_grupo: int
    id_evento: int
    nombre_grupo: str
    fecha_inicio: datetime
    fecha_cierre: datetime
    max_intentos: int
    cooldown: timedelta

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: datetime.isoformat,
            timedelta: str
        }
    )
