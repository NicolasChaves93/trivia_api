from datetime import timedelta
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, SmallInteger, CheckConstraint, UniqueConstraint, Interval
from app.db.connection import Base

class Grupo(Base):
    __tablename__ = "grupos"
    __table_args__ = (
        UniqueConstraint("id_evento", "nombre_grupo"),
        CheckConstraint("fecha_cierre > fecha_inicio", name="ck_fecha"),
        CheckConstraint("max_intentos > 0", name="ck_max_intentos"),
        CheckConstraint("cooldown >= interval '0 seconds'", name="ck_cooldown"),
        {"schema": "trivia"}
    )

    id_grupo = Column(Integer, primary_key=True, index=True)
    id_evento = Column(Integer, ForeignKey("trivia.eventos.id_evento", ondelete="CASCADE"), nullable=False)
    nombre_grupo = Column(String(255), nullable=False)
    fecha_inicio = Column(TIMESTAMP(timezone=True), nullable=False)
    fecha_cierre = Column(TIMESTAMP(timezone=True), nullable=False)
    max_intentos = Column(SmallInteger, nullable=False, default=1)
    cooldown = Column(Interval, nullable=False, default=timedelta(minutes=5),
                      doc="Tiempo mínimo de espera entre intentos (Interval)")
