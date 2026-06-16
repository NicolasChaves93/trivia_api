from sqlalchemy import (
    Column, Integer, String, ForeignKey, ForeignKeyConstraint, Index, text
)
from app.db.connection import Base
from app.core.settings_instance import settings

class Seccion(Base):
    """
    Representa una sección ('seccion') de un evento.

    Una sección puede ser:
      - **Común del evento** (`id_grupo` NULL): la ven todos los grupos del evento.
      - **Específica de un grupo** (`id_grupo` definido): solo la ve ese grupo.

    Las preguntas cuelgan de la sección, por lo que heredan su alcance (evento o grupo).

    Atributos:
        id_seccion (int): Clave primaria.
        id_evento (int): FK al evento. Cascade delete.
        id_grupo (int | None): FK opcional al grupo. NULL = sección común del evento.
        nombre_seccion (str): Nombre de la sección.

    Constraints:
        - Único (id_evento, nombre_seccion) para secciones comunes (id_grupo IS NULL).
        - Único (id_evento, id_grupo, nombre_seccion) para secciones de grupo.
    Schema:
        - Definido por 'settings.postgres_db_schema'.
    """
    __tablename__ = "secciones"
    __table_args__ = (
        # Integridad: si id_grupo está definido, el par (evento, grupo) debe existir
        # en grupos -> garantiza que el grupo pertenezca al mismo evento.
        # Con id_grupo NULL el FK compuesto no se evalúa (MATCH SIMPLE).
        ForeignKeyConstraint(
            ["id_evento", "id_grupo"],
            [
                f"{settings.postgres_db_schema}.grupos.id_evento",
                f"{settings.postgres_db_schema}.grupos.id_grupo",
            ],
            ondelete="CASCADE",
            name="fk_seccion_evento_grupo",
        ),
        Index(
            "uq_seccion_evento_comun",
            "id_evento", "nombre_seccion",
            unique=True,
            postgresql_where=text("id_grupo IS NULL"),
        ),
        Index(
            "uq_seccion_evento_grupo",
            "id_evento", "id_grupo", "nombre_seccion",
            unique=True,
            postgresql_where=text("id_grupo IS NOT NULL"),
        ),
        {"schema": settings.postgres_db_schema},
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
    id_grupo = Column(
        Integer,
        nullable=True,
        doc="Grupo dueño de la sección. NULL = sección común a todo el evento."
    )
    nombre_seccion = Column(String(255), nullable=False)
