import enum
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Enum as PgEnum,
    TIMESTAMP,
    Interval,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.connection import Base

class EstadoParticipacion(str, enum.Enum):
    """
    Enum que representa el estado de una participación de trivia.

    Valores:
        - pendiente: Participación activa o en progreso.
        - finalizado: Participación cerrada con respuestas registradas.
    """
    pendiente = "pendiente"
    finalizado = "finalizado"

class Participacion(Base):
    """
    Modelo de SQLAlchemy que representa una participación de un usuario en un evento de trivia.

    Esta tabla almacena la información de cada intento de participación,
    incluyendo las respuestas en bruto (formato JSON), el estado de la participación,
    y las marcas de tiempo asociadas.

    Relaciones:
        - FK a `usuarios` con ON DELETE CASCADE
        - FK a `grupos` con ON DELETE CASCADE

    Restricciones:
        - Cada usuario puede tener solo una participación por grupo (UNIQUE en `id_usuario`, `id_grupo`)
        - La tabla es LOGGED por defecto, lo cual permite integridad referencial total
    """

    __tablename__ = "participaciones"
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_grupo", name="uq_usuario_grupo"),
        {"schema": "trivia"}
    )

    id_participacion = Column(
        Integer,
        primary_key=True,
        index=True,
        doc="Identificador único de la participación"
    )

    id_usuario = Column(
        Integer,
        ForeignKey("trivia.usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        doc="ID del usuario que participa"
    )

    id_grupo = Column(
        Integer,
        ForeignKey("trivia.grupos.id_grupo", ondelete="CASCADE"),
        nullable=False,
        doc="ID del grupo al que pertenece la participación"
    )

    respuestas_usuario = Column(
        JSONB,
        nullable=False,
        doc="Respuestas crudas del usuario en formato JSONB (id_pregunta + respuesta)"
    )

    estado = Column(
        PgEnum(EstadoParticipacion, name="estado_participacion" , schema="trivia"),
        nullable=False,
        default=EstadoParticipacion.pendiente,
        doc="Estado de la participación: pendiente o finalizado"
    )

    started_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        doc="Fecha y hora en que comenzó la participación"
    )

    finished_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="Fecha y hora en que finalizó la participación (si aplica)"
    )

    tiempo_total = Column(
        Interval,
        nullable=True,
        doc="Duración total de la participación (diferencia entre inicio y fin)"
    )

    # Relaciones
    usuario = relationship(
        "Usuario",
        back_populates="participaciones",
        lazy="joined"
    )
    grupo = relationship("Grupo", backref="participaciones", lazy="joined")