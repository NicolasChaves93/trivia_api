"""
Modelo de datos para los eventos del sistema de trivia.

Cada evento puede tener un método de autenticación configurado (`tipo_login`)
que determina cómo los usuarios se autentican en el frontend.

Este modelo incluye:
- Clave primaria `id_evento`
- Nombre único del evento
- Tipo de login (ENUM PostgreSQL: generico, localidad)
"""

import enum
from sqlalchemy import Column, Integer, String
from sqlalchemy import Enum as PgEnum
from app.db.connection import Base

class TipoEvento(str, enum.Enum):
    """
    Enum que define los tipos de autenticación permitidos por evento.

    Valores:
        - generico: Permite login libre, sin verificación
        - sorteo_general: Evento de tipo sorteo general
    """
    TRIVIA_GENERAL = "trivia-general"
    SORTEO_GENERAL = "sorteo-general"

class Evento(Base):
    """
    Modelo SQLAlchemy que representa un evento de trivia.

    Atributos:
        id_evento (int): Identificador único del evento.
        nombre_evento (str): Nombre del evento (único).
        tipo_login (TipoLogin): Método de login habilitado para este evento.

    Este modelo se encuentra bajo el schema `trivia`.
    """

    __tablename__ = "eventos"
    __table_args__ = {"schema": "trivia"}

    id_evento = Column(
        Integer,
        primary_key=True,
        index=True,
        doc="Identificador único del evento"
    )

    nombre_evento = Column(
        String(255),
        unique=True,
        nullable=False,
        doc="Nombre del evento (único por sistema)"
    )

    tipo_evento = Column(
        PgEnum(TipoEvento, name="tipo_login", schema="trivia"),
        nullable=False,
        default=TipoEvento.TRIVIA_GENERAL,
        doc="Tipo de evento"
    )