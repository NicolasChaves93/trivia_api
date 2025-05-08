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
    respuestas: List[RespuestaCreate] = Field(..., min_items=1, max_items=4, description="Lista de 1 a 4 respuestas posibles")
    opcion_correcta: int = Field(..., gt=0, le=4, description="Número de la opción correcta (1-4)")

    @field_validator("pregunta")
    @classmethod
    def validar_pregunta(cls, value: str) -> str:
        """Valida que la pregunta no esté vacía"""
        value = value.strip()
        if not value:
            raise ValueError("La pregunta no puede estar vacía")
        return value

    @field_validator("respuestas")
    @classmethod
    def validar_respuestas(cls, respuestas: List[RespuestaCreate]) -> List[RespuestaCreate]:
        """Valida que los órdenes de las respuestas sean únicos y consecutivos del 1 al número de respuestas"""
        ordenes = [r.orden for r in respuestas]
        if sorted(ordenes) != list(range(1, len(respuestas) + 1)):
            raise ValueError("Los órdenes de las respuestas deben ser números consecutivos empezando desde 1")
        return respuestas

    @field_validator("opcion_correcta")
    @classmethod
    def validar_opcion_correcta(cls, opcion: int, info) -> int:
        """Valida que la opción correcta corresponda a una de las respuestas"""
        respuestas = info.data.get("respuestas", [])
        if respuestas and opcion not in [r.orden for r in respuestas]:
            raise ValueError("La opción correcta debe corresponder al orden de una de las respuestas")
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
    respuestas: List[RespuestaOut]
    opcion_correcta: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)