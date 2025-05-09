"""
Esquemas de validación para las participaciones en la API de trivia.

Define los modelos Pydantic para validar los datos de entrada y salida
relacionados con la gestión de participaciones de usuarios en eventos.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

class GestionarParticipacionRequest(BaseModel):
    """
    Esquema de entrada para gestionar una participación.
    
    Attributes:
        nombre (str): Nombre del participante
        cedula (str): Número de cédula del participante
        grupo_id (int): ID del grupo al que pertenece la participación
    """
    nombre: str = Field(..., min_length=1, description="Nombre del participante")
    cedula: str = Field(..., min_length=4, max_length=20, description="Número de cédula del participante")
    grupo_id: int = Field(..., gt=0, description="ID del grupo al que pertenece la participación")
    evento_id: int = Field(..., gt=0, description="ID del evento al que pertenece la participación")

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        """Valida que el nombre no esté vacío después de quitar espacios"""
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        return v.title()

    @field_validator("cedula")
    @classmethod
    def validar_cedula(cls, v: str) -> str:
        """Valida que la cédula solo contenga números"""
        v = v.strip()
        if not v.isdigit():
            raise ValueError("La cédula debe contener solo números")
        return v

class RespuestaUsuario(BaseModel):
    """
    Esquema para una respuesta individual del usuario.
    
    Attributes:
        id_pregunta (int): ID de la pregunta respondida
        respuesta_seleccionada (int): Número de la opción seleccionada (1-4)
    """
    id_pregunta: int = Field(..., gt=0)
    respuesta_seleccionada: int = Field(..., ge=1, le=4)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_pregunta": 1,
                "respuesta_seleccionada": 1
            }
        }
    )

class FinalizarParticipacionRequest(BaseModel):
    """
    Esquema de entrada para finalizar una participación.
    
    Attributes:
        id_participacion (int): ID de la participación a finalizar
        respuestas (List[RespuestaUsuario]): Lista de respuestas del usuario
        tiempo (str): Tiempo total en formato 'HH:MM:SS'
    """
    id_participacion: int = Field(..., gt=0)
    respuestas: List[RespuestaUsuario]
    tiempo: str = Field(..., pattern=r'^\d{2}:\d{2}:\d{2}$')

    @field_validator("respuestas")
    @classmethod
    def validar_respuestas(cls, v: List[RespuestaUsuario]) -> List[RespuestaUsuario]:
        """Valida que haya al menos una respuesta"""
        if not v:
            raise ValueError("Debe proporcionar al menos una respuesta")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_participacion": 1,
                "respuestas": [
                    {"id_pregunta": 1, "respuesta_seleccionada": 1}
                ],
                "tiempo": "00:05:30"
            }
        }
    )

class ParticipacionResponse(BaseModel):
    """
    Esquema de salida para las operaciones de participación.
    
    Attributes:
        action (str): Acción realizada ("iniciar", "continuar", "esperar" o "finalizado")
        id_participacion (int): ID de la participación
        respuestas (List[Dict]): Lista de respuestas del usuario
        started_at (datetime): Timestamp de inicio
        tiempo_total (Optional[str]): Tiempo total transcurrido
    """
    token           : str
    action          : str
    id_participacion: int
    numero_intento  : int
    respuestas      : List[Dict[str, Any]]
    started_at      : datetime
    finished_at     : Optional[datetime] = None
    tiempo_total    : Optional[str]     = None
    remaining       : str

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class UsuarioInfo(BaseModel):
    """
    Esquema para mostrar información básica del usuario.
    
    Attributes:
        id_usuario (int): ID del usuario
        nombre (str): Nombre del usuario
        cedula (str): Número de cédula
    """
    id_usuario: int
    nombre: str
    cedula: str

    model_config = ConfigDict(from_attributes=True)

class ParticipacionOut(BaseModel):
    """
    Esquema de salida básico para una participación.
    """
    id_participacion: int
    id_grupo: int
    numero_intento: int
    estado: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    tiempo_total: Optional[str] = None
    usuario: UsuarioInfo

    @field_validator("tiempo_total", mode="before")
    @classmethod
    def convert_timedelta_to_str(cls, v: Any) -> Optional[str]:
        """Convierte timedelta a string en formato HH:MM:SS"""
        if v is None:
            return None
        if isinstance(v, timedelta):
            return f"{int(v.total_seconds() // 3600):02d}:{int((v.total_seconds() % 3600) // 60):02d}:{int(v.total_seconds() % 60):02d}"
        return v

    model_config = ConfigDict(from_attributes=True)

class ListarParticipacionesResponse(BaseModel):
    """
    Esquema de respuesta para listar participaciones.
    
    Attributes:
        participaciones (List[ParticipacionOut]): Lista de participaciones
        total (int): Número total de participaciones
    """
    participaciones: List[ParticipacionOut]
    total: int