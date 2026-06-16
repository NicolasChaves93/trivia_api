"""
Modelo de datos para las participaciones de los usuarios en grupos de trivia.

Cada participación está asociada a un grupo y a un usuario. Si se elimina el usuario o el grupo,
las participaciones relacionadas se eliminan automáticamente (ON DELETE CASCADE).
"""
import enum
from sqlalchemy import (
    Column, Integer, ForeignKey, Enum as PgEnum, TIMESTAMP,
    Interval, SmallInteger, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.connection import Base
from app.core.settings_instance import settings

class EstadoParticipacion(str, enum.Enum):
    """Enum para el estado de una participación."""
    PENDIENTE = "pendiente"
    FINALIZADO = "finalizado"

class Participacion(Base):
    """
    Modelo SQLAlchemy que representa una participación de un usuario en un grupo de trivia.

    Atributos:
        id_participacion (int): ID de la participación.
        id_usuario (int): ID del usuario que participa.
        id_grupo (int): ID del grupo en el que participa.
        numero_intento (int): Número de intento de participación.
        respuestas_usuario (jsonb): JSON con las respuestas dadas.
        estado (enum): Estado de la participación (pendiente o finalizado).
        started_at (timestamp): Fecha y hora de inicio de la participación.
        finished_at (timestamp): Fecha y hora de finalización.
        tiempo_total (interval): Duración total de la participación.

    Relaciones:
        usuario (Usuario): Usuario asociado a la participación.
        grupo (Grupo): Grupo en el que participa.
    """
    __tablename__ = "participaciones"
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_grupo", "numero_intento", name="uq_usuario_grupo_intento"),
        {"schema": settings.postgres_db_schema}
    )

    id_participacion = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(
        Integer,
        ForeignKey(f"{settings.postgres_db_schema}.usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False
    )
    id_grupo = Column(
        Integer,
        ForeignKey(f"{settings.postgres_db_schema}.grupos.id_grupo", ondelete="CASCADE"),
        nullable=False
    )
    numero_intento = Column(SmallInteger, nullable=False, default=1)
    respuestas_usuario = Column(JSONB, nullable=False)
    estado = Column(
        PgEnum(EstadoParticipacion, name="estado_participacion", schema= settings.postgres_db_schema),
        nullable=False,
        default=EstadoParticipacion.PENDIENTE
    )
    started_at = Column(TIMESTAMP(timezone=True), nullable=False)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    tiempo_total = Column(Interval, nullable=True)

    # Relaciones
    grupo = relationship(
        "Grupo",
        back_populates="participaciones",
        lazy="joined",
        passive_deletes=True
    )

    usuario = relationship(
        "Usuario",
        back_populates="participaciones",
        lazy="joined",
        passive_deletes=True
    )
    