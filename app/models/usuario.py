"""
Modelo de datos para los usuarios en el sistema de trivia.

Cada usuario está identificado de forma única por su `cedula` 
y puede tener múltiples participaciones.

Al eliminar un usuario, sus participaciones también se eliminan 
automáticamente gracias al ondelete="CASCADE".
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.connection import Base

class Usuario(Base):
    """
    Modelo SQLAlchemy que representa un usuario participante en el sistema de trivia.

    Atributos:
        id_usuario (int): ID interno del sistema.
        cedula (str): Cédula o documento único del usuario.
        nombre (str): Nombre completo del usuario.

    Relaciones:
        participaciones (List[Participacion]): Lista de participaciones asociadas.
            Al eliminar el usuario, se eliminan automáticamente las participaciones 
            (ON DELETE CASCADE).
            Eliminar una participación no afecta al usuario.
    """
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("cedula", name="uq_usuario_cedula"),
        {"schema": "trivia"}
    )

    id_usuario = Column(
        Integer,
        primary_key=True,
        index=True,
        doc="Identificador interno único del usuario"
    )

    cedula = Column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        doc="Número de cédula o documento del usuario"
    )

    nombre = Column(
        String(255),
        nullable=False,
        doc="Nombre completo del usuario"
    )

    # Relaciones
    participaciones = relationship(
        "Participacion",
        back_populates="usuario",
        passive_deletes=True,
        lazy="selectin"
    )
