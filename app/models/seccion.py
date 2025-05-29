from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.connection import Base
from app.core.settings_instance import settings

class Seccion(Base):
    """
    Represents a section ('seccion') within an event in the database.
    Attributes:
        id_seccion (int): Primary key for the section.
        id_evento (int): Foreign key referencing the associated event. Enforces cascade delete.
        nombre_seccion (str): Name of the section. Must be unique per event.
    Table Constraints:
        - Unique constraint on the combination of 'id_evento' and 'nombre_seccion' to ensure
          that each section name is unique within an event.
    Table Schema:
        - Defined by 'settings.postgres_db_schema'.
    """
    __tablename__ = "secciones"
    __table_args__ = (
        UniqueConstraint("id_evento", "nombre_seccion"),
        {"schema": settings.postgres_db_schema}
    )

    id_seccion = Column(Integer, primary_key=True, index=True)
    id_evento = Column(
        Integer,
        ForeignKey(
            f"{settings.postgres_db_schema}.eventos.id_evento",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    nombre_seccion = Column(String(255), nullable=False)
