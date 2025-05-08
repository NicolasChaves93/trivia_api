"""
Esquema de validación para las secciones en la API de trivia.

Contiene las clases `SeccionCreate` y `SeccionOut` que validan y representan las secciones:
- SeccionCreate: Para crear nuevas secciones
- SeccionOut: Para la respuesta de la API
"""

from pydantic import BaseModel, Field, field_validator

class SeccionCreate(BaseModel):
    """
    Esquema de entrada para crear una nueva sección.

    Atributos:
        id_evento (int): ID del evento al que pertenece la sección
        nombre_seccion (str): Nombre de la sección. No puede estar vacío.
    """
    id_evento: int = Field(..., description="ID del evento al que pertenece la sección")
    nombre_seccion: str = Field(..., min_length=1, description="Nombre de la sección")

    @field_validator("nombre_seccion")
    @classmethod
    def formato_titulo(cls, value: str) -> str:
        """
        Validador que limpia y transforma el nombre de la sección.

        - Elimina espacios iniciales y finales
        - Verifica que no esté vacío
        - Convierte el texto a formato título

        Args:
            value (str): Nombre de la sección ingresado

        Returns:
            str: Nombre formateado

        Raises:
            ValueError: Si el campo está vacío tras hacer strip()
        """
        value = value.strip()
        if not value:
            raise ValueError("El nombre de la sección no puede estar vacío")
        return value.title()

class SeccionOut(BaseModel):
    """
    Esquema de salida para representar una sección en las respuestas de la API.

    Atributos:
        id_seccion (int): Identificador único de la sección
        id_evento (int): ID del evento al que pertenece
        nombre_seccion (str): Nombre de la sección en formato Título
    """
    id_seccion: int
    id_evento: int
    nombre_seccion: str

    class Config:
        from_attributes = True  # Para compatibilidad con SQLAlchemy