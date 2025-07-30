"""
Esquema de validación para las preguntas en la API de trivia.

Contiene las clases `PreguntaCreate` y `PreguntaOut` que validan y representan las preguntas:
- PreguntaCreate: Para crear nuevas preguntas
- PreguntaOut: Para la respuesta de la API
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

class RespuestaBase(BaseModel):
    """
    Esquema base para las respuestas.
    """
    respuesta: str = Field(..., min_length=1, description="Texto de la respuesta")
    orden: int = Field(..., gt=0, le=4, description="Orden de la respuesta (1-4)")

class RespuestaCreate(RespuestaBase):
    """Esquema para crear una respuesta"""
    model_config = ConfigDict(from_attributes=True)

class RespuestaOut(RespuestaBase):
    """Esquema para mostrar una respuesta"""
    id_respuesta: int
    id_pregunta: int

    model_config = ConfigDict(from_attributes=True)

class PreguntaCreate(BaseModel):
    """
    Esquema de entrada para crear una nueva pregunta.

    Atributos:
        id_seccion (int): ID de la sección a la que pertenece la pregunta
        pregunta (str): Texto de la pregunta. No puede estar vacío.
        respuestas (List[RespuestaCreate]): Lista de 1 a 4 respuestas posibles
        opcion_correcta (int): Número de la opción correcta (1-4)
    """
    id_seccion: int = Field(..., description="ID de la sección a la que pertenece la pregunta")
    pregunta: str = Field(..., min_length=1, description="Texto de la pregunta")
    tipo_pregunta: str = Field(..., description="Tipo de pregunta: 'abierta' o 'opcion_unica'")
    respuestas: Optional[List[RespuestaCreate]] = Field(default=None, description="Lista de 1 a 4 respuestas posibles (solo para opción única)")
    opcion_correcta: Optional[int] = Field(default=None, description="Número de la opción correcta (1-4, solo para opción única)")

    @field_validator("pregunta")
    @classmethod
    def validar_pregunta(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La pregunta no puede estar vacía")
        return value

    @field_validator("tipo_pregunta")
    @classmethod
    def validar_tipo(cls, value: str) -> str:
        if value not in ("abierta", "opcion_unica"):
            raise ValueError("El tipo de pregunta debe ser 'abierta' o 'opcion_unica'")
        return value

    @field_validator("respuestas")
    @classmethod
    def validar_respuestas(cls, respuestas: Optional[List[RespuestaCreate]], info) -> Optional[List[RespuestaCreate]]:
        tipo = info.data.get("tipo_pregunta")
        if tipo == "opcion_unica":
            if not respuestas or not (1 <= len(respuestas) <= 4):
                raise ValueError("Debe haber entre 1 y 4 respuestas para preguntas de opción única")
            ordenes = [r.orden for r in respuestas]
            if sorted(ordenes) != list(range(1, len(respuestas) + 1)):
                raise ValueError("Los órdenes de las respuestas deben ser números consecutivos empezando desde 1")
        elif tipo == "abierta":
            if respuestas:
                raise ValueError("Las preguntas abiertas no deben tener respuestas")
        return respuestas

    @field_validator("opcion_correcta")
    @classmethod
    def validar_opcion_correcta(cls, opcion: Optional[int], info) -> Optional[int]:
        tipo = info.data.get("tipo_pregunta")
        respuestas = info.data.get("respuestas", [])
        if tipo == "opcion_unica":
            if opcion is None:
                raise ValueError("Debes indicar la opción correcta para preguntas de opción única")
            if respuestas and opcion not in [r.orden for r in respuestas]:
                raise ValueError("La opción correcta debe corresponder al orden de una de las respuestas")
        elif tipo == "abierta":
            if opcion is not None:
                raise ValueError("Las preguntas abiertas no deben tener opción correcta")
        return opcion

class SeccionInfo(BaseModel):
    """Información básica de una sección"""
    id_seccion: int
    nombre_seccion: str

    model_config = ConfigDict(from_attributes=True)

class PreguntaOut(BaseModel):
    """
    Esquema de salida para representar una pregunta en las respuestas de la API.

    Atributos:
        id_pregunta (int): Identificador único de la pregunta
        seccion (SeccionInfo): Información de la sección a la que pertenece
        pregunta (str): Texto de la pregunta
        respuestas: List[RespuestaOut]
        opcion_correcta (Optional[int]): Número de la opción correcta (1-4)
    """
    id_pregunta: int
    seccion: SeccionInfo
    pregunta: str
    tipo_pregunta: str
    respuestas: Optional[List[RespuestaOut]] = None
    opcion_correcta: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)