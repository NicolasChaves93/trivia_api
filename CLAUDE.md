# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

REST API (FastAPI) for managing trivia events, sections, groups, questions, user participations, and reports. Async stack throughout: FastAPI + async SQLAlchemy 2.0 + asyncpg over PostgreSQL. Codebase, docstrings, and domain vocabulary are in Spanish.

## Commands

```bash
# Run dev server (Swagger at http://localhost:8000/docs)
python main.py                              # runs uvicorn on 0.0.0.0:8000
uvicorn main:app --reload --port 8000       # with hot reload

# Install deps
pip install -r requirements.txt

# Tests (pytest config in pytest.ini, asyncio_mode=auto, testpaths=tests)
pytest                                      # run all
pytest tests/test_participacion.py::test_calcular_resultado_mixto_y_redondeo  # single test
```

Unit tests live in `tests/` and cover the **pure** business-logic functions (no DB needed) — `tests/conftest.py` injects dummy env vars so settings can load without a `.env`. There is no configured linter.

## Configuration

Settings are loaded from a `.env` file via `app/core/settings.py` (pydantic-settings, `extra="forbid"` — unknown env vars raise). Required vars (note env aliases differ from field names):

- DB: `POSTGRES_DB_SCHEMA_TRIVIA`, `POSTGRES_DB_USER`, `POSTGRES_DB_PASSWORD`, `POSTGRES_DB_NAME`, `POSTGRES_DB_HOST`, `POSTGRES_DB_PORT`
- JWT: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- Other: `ENVIRONMENT` (`dev|prod|test`), `LOG_CONSOLA_LEVEL`

The canonical settings instance is `app.core.settings_instance.settings` — import that, don't instantiate `Settings()` directly. Both `connection.py` (DB URL) and the rest of the app read configuration through this single instance. A `.env.example` documents the required variables.

## Architecture

Strict layering — keep responsibilities in their layer:

```
main.py                  → app bootstrap, CORS, custom OpenAPI (JWT Bearer), lifespan → init() DB
app/api/routers/*.py     → HTTP endpoints, validation, HTTPException mapping. Aggregated in app/api/routers/__init__.py:api_router
app/crud/*.py            → data-access only: simple per-entity queries (eventos, grupos, preguntas, secciones, usuarios, participaciones)
app/services/*.py        → business logic spanning multiple entities (participacion, informes)
app/schemas/*.py         → Pydantic request/response models
app/models/*.py          → SQLAlchemy ORM models, registered in app/models/__init__.py
app/db/                  → engine, session, schema init
app/core/                → settings, auth (JWT), logger
```

### Participation flow (the core domain logic)

`app/services/participacion.py` holds the trivia attempt lifecycle. Two pure, DB-free functions encapsulate the rules and are the right place to change behavior (they have direct unit tests):
- `decidir_accion(...)` → state machine deciding `iniciar` / `continuar` / `esperar` (cooldown) / `FINALIZADO` (max attempts reached). **Note:** these exact action strings are the frontend contract — don't rename casually.
- `calcular_resultado(...)` → scoring (correct/incorrect/percentage).

`gestionar_participacion` runs in a single transaction serialized per `(usuario, grupo)` via a PostgreSQL transactional advisory lock (`pg_advisory_xact_lock`) to avoid race conditions on concurrent attempts. `finalizar_participacion` writes the answer breakdown (`respuestas_usuarios`) and the aggregated `resultados` in Python. The `EstadoParticipacion` enum (`pendiente`/`finalizado`) is the single source of truth for state — use the enum members, not string literals.

To add an endpoint: create the router, then register it in `app/api/routers/__init__.py`. CRUD-only flows go through `app/crud/`; multi-entity logic goes through `app/services/`.

### Database

- Single async engine in `app/db/connection.py` (`get_engine()`); inject sessions into endpoints via `Depends(get_db)`.
- All tables live in the PostgreSQL schema **`trivia`** (not `public`).
- On startup, `lifespan` → `app/db/init_db.py:init()` creates the `trivia` schema and runs `Base.metadata.create_all` (no Alembic migrations — schema is created from ORM models).
- **All business logic lives in Python**, not in the database. Participation handling (attempts, cooldown, state machine, result scoring) is implemented in `app/services/participacion.py`; there are no PL/pgSQL functions or triggers. The DB enforces only data integrity (FKs, unique/check constraints, `ON DELETE CASCADE`).
- The reporting service `app/services/informes.py` still uses raw `text()` SQL — but only for **read-only aggregation queries**, not business rules. That's an acceptable use of SQL.

### Auth

JWT (HS256) in `app/core/auth.py`. `crear_token()` issues tokens; protect endpoints with `Depends(verificar_token)` (used in `preguntas` and `participaciones` routers). The OAuth2 token URL registered for Swagger is `/loginU`.

### Logging

Use the singleton `MyLogger().get_logger(name=...)` from `app/core/logger.py` (console + rotating file handler under `logs/`). Don't configure logging ad hoc.

## Conventions

- Async everywhere — endpoints, CRUD, and services are `async def`; never use blocking DB calls.
- Routers translate domain/DB errors into `HTTPException` with explicit status codes (e.g. `IntegrityError` → 400 for duplicates); keep that mapping at the router layer.
