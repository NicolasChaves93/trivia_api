"""
Esquema de validación para los usuarios en la API de trivia.

Define los modelos Pydantic para validar los datos de entrada y salida
relacionados con los usuarios.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict

class UsuarioBase(BaseModel):
    """
    Esquema base para los usuarios.

    Atributos:
        cedula (str): Número de cédula del usuario. Solo números, entre 4 y 20 dígitos.
        nombre (str): Nombre completo del usuario. No puede estar vacío.
    """
    cedula: str = Field(..., min_length=4, max_length=20, description="Número de cédula del usuario")
    nombre: str = Field(..., min_length=1, description="Nombre completo del usuario")

    @field_validator("cedula")
    @classmethod
    def validar_cedula(cls, v: str) -> str:
        """Valida que la cédula solo contenga números"""
        v = v.strip()
        if not v.isdigit():
            raise ValueError("La cédula debe contener solo números")
        return v

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        """Valida que el nombre no esté vacío y lo convierte a formato título"""
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        return v.title()

class UsuarioCreate(UsuarioBase):
    """Esquema para crear un nuevo usuario"""

class UsuarioOut(UsuarioBase):
    """
    Esquema de salida para representar un usuario.

    Atributos:
        id_usuario (int): Identificador único del usuario
        cedula (str): Número de cédula del usuario
        nombre (str): Nombre completo del usuario en formato título
    """
    id_usuario: int

    model_config = ConfigDict(from_attributes=True)