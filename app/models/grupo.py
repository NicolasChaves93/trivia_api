from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, CheckConstraint, UniqueConstraint
from app.db.connection import Base

class Grupo(Base):
    __tablename__ = "grupos"
    __table_args__ = (
        UniqueConstraint("id_evento", "nombre_grupo"),
        CheckConstraint("fecha_cierre > fecha_inicio"),
        {"schema": "trivia"}
    )

    id_grupo = Column(Integer, primary_key=True, index=True)
    id_evento = Column(Integer, ForeignKey("trivia.eventos.id_evento", ondelete="CASCADE"), nullable=False)
    nombre_grupo = Column(String(255), nullable=False)
    fecha_inicio = Column(TIMESTAMP(timezone=True), nullable=False)
    fecha_cierre = Column(TIMESTAMP(timezone=True), nullable=False)
