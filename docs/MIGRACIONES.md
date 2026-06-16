# Migraciones de base de datos (Alembic)

El esquema se gestiona con **Alembic** (no con `create_all`). Cada cambio de modelo
se versiona como una migración en `alembic/versions/`.

## Configuración

- `alembic.ini` + `alembic/env.py` (template **async**, usa `asyncpg`).
- `env.py` toma la URL de conexión de `app.core.settings` (`settings.database_url`),
  por lo que **respeta el `.env`** del entorno. No se hardcodea la URL.
- Crea el schema `trivia` automáticamente (`CREATE SCHEMA IF NOT EXISTS`) y guarda la
  tabla de versiones (`alembic_version`) dentro de ese schema.
- `target_metadata = Base.metadata`, con `include_schemas=True` para autogenerate.

## Entorno local de desarrollo

La BD de producción del `.env` original **no se usa** para desarrollo. Se trabaja contra
una PostgreSQL local (Docker). El `.env` de desarrollo apunta a ella:

```env
ENVIRONMENT=dev
POSTGRES_DB_SCHEMA_TRIVIA=trivia
POSTGRES_DB_USER=docueditor
POSTGRES_DB_PASSWORD=BD123456
POSTGRES_DB_NAME=trivia_local
POSTGRES_DB_HOST=localhost
POSTGRES_DB_PORT=5433
SECRET_KEY=clave-local-dev-no-usar-en-prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_CONSOLA_LEVEL=INFO
```

> El `.env` original (producción) se respaldó en `.env.prod.bak` (ignorado por git).

## Comandos

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Ver la revisión actual / historial
alembic current
alembic history

# Crear una migración nueva tras cambiar los modelos
alembic revision --autogenerate -m "descripcion del cambio"

# Revertir la última migración
alembic downgrade -1
```

> Revisa siempre el archivo generado por `--autogenerate` antes de aplicarlo: Alembic no
> detecta todo (renombres de columnas, cambios de tipo sutiles, datos).

## Migraciones existentes

1. `4bbfb7c3085b` — **baseline**: crea el esquema completo (eventos, secciones, grupos,
   preguntas, respuestas, usuarios, participaciones, respuestas_usuarios, resultados).
2. `ead95424665b` — **secciones por grupo**: agrega `secciones.id_grupo`, el `UNIQUE
   (id_evento, id_grupo)` en `grupos`, el FK compuesto y los índices únicos parciales.

## Arranque de la aplicación

El arranque ejecuta las migraciones (`alembic upgrade head`) en lugar de `create_all`,
para que Alembic sea la única fuente de verdad del esquema.
