import enum
from sqlalchemy import (
    Column, Integer, ForeignKey, Enum as PgEnum, TIMESTAMP,
    Interval, SmallInteger, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.connection import Base

TRIVIA_SCHEMA = "trivia"

class EstadoParticipacion(str, enum.Enum):
    pendiente = "pendiente"
    finalizado = "finalizado"

class Participacion(Base):
    __tablename__ = "participaciones"
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_grupo", "numero_intento", name="uq_usuario_grupo_intento"),
        {"schema": TRIVIA_SCHEMA}
    )

    id_participacion = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("trivia.usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    id_grupo = Column(Integer, ForeignKey("trivia.grupos.id_grupo", ondelete="CASCADE"), nullable=False)
    numero_intento = Column(SmallInteger, nullable=False, default=1)
    respuestas_usuario = Column(JSONB, nullable=False)
    estado = Column(PgEnum(EstadoParticipacion, name="estado_participacion", schema=TRIVIA_SCHEMA), nullable=False, default=EstadoParticipacion.pendiente)
    started_at = Column(TIMESTAMP(timezone=True), nullable=False)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    tiempo_total = Column(Interval, nullable=True)

    usuario = relationship("Usuario", back_populates="participaciones", lazy="joined")
    grupo = relationship("Grupo", backref="participaciones", lazy="joined")