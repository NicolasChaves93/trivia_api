"""
Modelo de datos para registrar las respuestas seleccionadas por un usuario en una participación específica.

Cada respuesta está vinculada a una `participación` concreta, simplificando la integridad referencial y 
permitiendo respuestas independientes incluso si el usuario participa varias veces en distintos eventos.

La eliminación en cascada permite que al eliminar una participación, se borren automáticamente sus respuestas.
"""

from sqlalchemy import Column, Integer, SmallInteger, ForeignKey, UniqueConstraint
from app.db.connection import Base

class RespuestaUsuario(Base):
    """
    Modelo que representa una respuesta específica dentro de una participación de trivia.

    Relaciones:
        - FK a `participaciones` con `ON DELETE CASCADE`
        - FK a `preguntas` con `ON DELETE CASCADE`
    """

    __tablename__ = "respuestas_usuarios"
    __table_args__ = (
        UniqueConstraint("id_participacion", "id_pregunta", name="uq_participacion_pregunta"),
        {"schema": "trivia"}
    )

    id_respuesta_usuario = Column(
        Integer,
        primary_key=True,
        index=True,
        doc="Identificador único de la respuesta del usuario"
    )

    id_participacion = Column(
        Integer,
        ForeignKey("trivia.participaciones.id_participacion", ondelete="CASCADE"),
        nullable=False,
        doc="ID de la participación a la que pertenece esta respuesta"
    )

    id_pregunta = Column(
        Integer,
        ForeignKey("trivia.preguntas.id_pregunta", ondelete="CASCADE"),
        nullable=False,
        doc="ID de la pregunta que fue respondida"
    )

    orden_seleccionado = Column(
        SmallInteger,
        nullable=False,
        doc="Número de orden de la respuesta seleccionada por el usuario"
    )
