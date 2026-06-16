from typing import List
from sqlalchemy import Column, Integer, SmallInteger, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped

from app.db.connection import Base
from app.models.respuesta import Respuesta
from app.models.seccion import Seccion
from app.core.settings_instance import settings

class Pregunta(Base):
    __tablename__ = "preguntas"
    __table_args__ = (
        UniqueConstraint("id_seccion", "pregunta", name="uq_seccion_pregunta"),
        {"schema": settings.postgres_db_schema}
    )

    id_pregunta = Column(Integer, primary_key=True, index=True)
    id_seccion = Column(Integer, ForeignKey(f"{settings.postgres_db_schema}.secciones.id_seccion", ondelete="CASCADE"), nullable=False)
    pregunta = Column(Text, nullable=False)
    opcion_correcta = Column(SmallInteger)

    # Relaciones
    respuestas: Mapped[List[Respuesta]] = relationship(
        "Respuesta", 
        back_populates="pregunta", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    seccion: Mapped["Seccion"] = relationship(
        "Seccion",
        lazy="selectin"
    )
