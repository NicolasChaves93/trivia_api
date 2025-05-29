""" Modelo ORM para la tabla `respuestas` en el esquema `trivia`. """

from sqlalchemy import Column, Integer, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.connection import Base
from app.core.settings_instance import settings

class Respuesta(Base):
    """
    Modelo ORM que representa una respuesta posible dentro del sistema de trivia.

    Cada instancia de esta clase corresponde a una fila en la tabla `trivia.respuestas`.
    Las respuestas están asociadas a una pregunta específica (`id_pregunta`) y tienen un
    `orden` que indica su posición entre las opciones.

    Restricciones:
        - `UNIQUE(id_pregunta, orden)`: garantiza que no se repita 
            el mismo orden en respuestas de la misma pregunta.
        - `CHECK(orden > 0)`: asegura que el orden sea positivo.

    Atributos:
        id_respuesta (int): Identificador único de la respuesta (clave primaria).
        id_pregunta (int): Clave foránea que referencia la pregunta asociada.
        orden (int): Posición o número de la opción dentro de las respuestas de la pregunta.
        respuesta (str): Texto literal de la respuesta.

    Relaciones:
        - FK hacia `preguntas(id_pregunta)` con borrado en cascada.
        - Relación bidireccional con Pregunta.

    Tabla en base de datos:
        Nombre: respuestas
        Esquema: trivia
    """
    __tablename__ = "respuestas"
    __table_args__ = (
        UniqueConstraint("id_pregunta", "orden"),
        CheckConstraint("orden > 0"),
        {"schema": settings.postgres_db_schema}
    )

    id_respuesta = Column(Integer, primary_key=True, index=True)
    id_pregunta = Column(
        Integer,
        ForeignKey(
            f"{settings.postgres_db_schema}.preguntas.id_pregunta",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    orden = Column(Integer, nullable=False)
    respuesta = Column(Text, nullable=False)

    # Relación bidireccional con Pregunta
    pregunta = relationship("Pregunta", back_populates="respuestas")
