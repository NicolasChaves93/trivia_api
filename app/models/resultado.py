"""
Modelo que representa el resultado final de una participación de trivia.

Cada registro está vinculado a una única `participación` y se calcula automáticamente
cuando la participación cambia a estado `finalizado` mediante un trigger.
"""

from sqlalchemy import Column, Integer, ForeignKey, Interval, Numeric, UniqueConstraint
from app.db.connection import Base

class Resultado(Base):
    """
    Modelo que representa los resultados finales de una participación.

    Relaciones:
        - FK a `participaciones` con `ON DELETE CASCADE`
    """

    __tablename__ = "resultados"
    __table_args__ = (
        UniqueConstraint("id_participacion", name="uq_resultado_participacion"),
        {"schema": "trivia"}
    )

    id_resultado = Column(
        Integer,
        primary_key=True,
        index=True,
        doc="Identificador único del resultado"
    )

    id_participacion = Column(
        Integer,
        ForeignKey("trivia.participaciones.id_participacion", ondelete="CASCADE"),
        nullable=False,
        doc="ID de la participación asociada a este resultado"
    )

    total_preguntas = Column(
        Integer,
        nullable=False,
        doc="Cantidad total de preguntas respondidas"
    )

    respuestas_correctas = Column(
        Integer,
        nullable=False,
        doc="Cantidad de respuestas correctas"
    )

    porcentaje_acierto = Column(
        Numeric(5, 2),
        nullable=False,
        doc="Porcentaje de acierto del usuario en el evento"
    )

    tiempo_total = Column(
        Interval,
        nullable=False,
        doc="Duración total que tomó la participación"
    )