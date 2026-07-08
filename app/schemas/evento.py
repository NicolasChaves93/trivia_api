"""
Esquema de validación para la creación de eventos en la API de trivia.

Contiene la clase `EventoCreate` que valida el campo `nombre_evento`:
- No puede estar vacío.
- Se convierte a formato título.
- Documenta la intención del campo para la interfaz Swagger/OpenAPI.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum

class TipoEvento(str, Enum):
    TRIVIA_GENERAL = "trivia-general"
    SORTEO_GENERAL = "sorteo-general"

class EventoRequest(BaseModel):
    """
    Esquema de entrada para crear un nuevo evento.

    Atributos:
        nombre_evento (str): Nombre del evento. No puede estar vacío y se convierte automáticamente a título.
    """
    model_config = ConfigDict(extra="forbid")

    nombre_evento: str = Field(..., min_length=1, description="Nombre del evento")
    tipo_evento: TipoEvento = Field(default=TipoEvento.TRIVIA_GENERAL, description="Tipo de evento")

    @field_validator("nombre_evento")
    @classmethod
    def formato_titulo(cls, value: str) -> str:
        """
        Validador que limpia y transforma el nombre del evento.

        - Elimina espacios iniciales y finales.
        - Verifica que no esté vacío.
        - Convierte el texto a formato título.

        Args:
            value (str): Nombre del evento ingresado.

        Returns:
            str: Nombre formateado.

        Raises:
            ValueError: Si el campo está vacío tras hacer strip().
        """
        value = value.strip()
        if not value:
            raise ValueError("El nombre del evento no puede estar vacío")
        return value.title()
    
class EventoUpdate(BaseModel):
    """
    Esquema de entrada para actualizar parcialmente un evento existente.

    Atributos:
        nombre_evento (str | None): Nuevo nombre del evento, si se desea cambiar.
        tipo_evento (TipoEvento | None): Nuevo tipo de evento, si se desea cambiar.
    """
    model_config = ConfigDict(extra="forbid")

    nombre_evento: str | None = Field(default=None, min_length=1, description="Nombre del evento")
    tipo_evento: TipoEvento | None = Field(default=None, description="Tipo de evento")

    @field_validator("nombre_evento")
    @classmethod
    def formato_titulo(cls, value: str | None) -> str | None:
        """
        Limpia y transforma el nombre del evento, igual que en EventoRequest.
        """
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("El nombre del evento no puede estar vacío")
        return value.title()

class EventoResponse(BaseModel):
    """
    Esquema de salida para representar un evento en las respuestas de la API.

    Atributos:
        id_evento (int): Identificador único del evento.
        nombre_evento (str): Nombre del evento en formato Título.
    """
    id_evento    : int
    nombre_evento: str
    tipo_evento  : TipoEvento

    class Config:
        from_attributes = True  # Habilita compatibilidad con SQLAlchemy