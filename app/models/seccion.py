from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.connection import Base

class Seccion(Base):
    __tablename__ = "secciones"
    __table_args__ = (
        UniqueConstraint("id_evento", "nombre_seccion"),
        {"schema": "trivia"}
    )

    id_seccion = Column(Integer, primary_key=True, index=True)
    id_evento = Column(Integer, ForeignKey("trivia.eventos.id_evento", ondelete="CASCADE"), nullable=False)
    nombre_seccion = Column(String(255), nullable=False)
