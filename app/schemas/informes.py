from pydantic import BaseModel, Field

class RankingUsuarioOut(BaseModel):
    ranking: int = Field(..., description="Posición en el ranking (1 = mejor puntuación)")
    cedula: str = Field(..., description="Número de cédula del usuario")
    nombre: str = Field(..., description="Nombre completo del usuario")
    grupo: str = Field(..., description="Nombre del grupo al que pertenece el usuario")
    tiempo_juego: str = Field(..., description="Duración del intento en formato hh:mm:ss")
    total_preguntas: int = Field(..., description="Cantidad total de preguntas respondidas")
    respuestas_correctas: int = Field(..., description="Número de respuestas correctas")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "ranking": 1,
                "cedula": "1234567890",
                "nombre": "Juan Pérez",
                "grupo": "Grupo A",
                "tiempo_juego": "00:02:45",
                "total_preguntas": 10,
                "respuestas_correctas": 9
            }
        }