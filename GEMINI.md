# Gemini Project Instructions: Trivia API

This project is a REST API built with FastAPI for managing trivia events, user participations, and scoring. It uses an asynchronous stack with SQLAlchemy 2.0 and PostgreSQL.

## Project Overview

- **Core Functionality**: Managing trivia events, sections, groups, and questions. Handling user participation lifecycle (attempts, cooldowns, state management) and calculating results.
- **Technology Stack**:
  - **Language**: Python 3.x
  - **Framework**: FastAPI
  - **Database**: PostgreSQL (schema `trivia`)
  - **ORM**: SQLAlchemy 2.0 (Async)
  - **Driver**: `asyncpg`
  - **Configuration**: Pydantic-Settings (loads from `.env`)
  - **Authentication**: JWT (HS256 for participants, RS256 for admins)
  - **Testing**: Pytest with `pytest-asyncio`
  - **Logging**: Custom singleton logger (console + rotating file)

## Architecture

The project follows a strict layered architecture:

- `main.py`: Entry point, CORS configuration, custom OpenAPI schema, and application lifespan.
- `app/api/routers/`: HTTP endpoints, request validation, and exception mapping. Routers are aggregated in `app/api/routers/__init__.py`.
- `app/services/`: High-level business logic spanning multiple entities (e.g., participation flow, report generation).
- `app/crud/`: Low-level, per-entity data access queries.
- `app/schemas/`: Pydantic models for request/response validation.
- `app/models/`: SQLAlchemy ORM models (all registered in `app/models/__init__.py`).
- `app/core/`: Centralized settings, authentication logic, and logging configuration.
- `app/db/`: Database engine setup, session management, and schema initialization.

### Key Domain Logic: Participations

The core logic lives in `app/services/participacion.py`. It uses a state machine to manage attempts and cooldowns.
- **Concurrency**: Uses PostgreSQL transactional advisory locks (`pg_advisory_xact_lock`) to serialize participations per user/group.
- **Pure Functions**: Business rules for deciding actions and calculating results are implemented as pure, DB-free functions for easy unit testing.

## Building and Running

### Prerequisites
- Python 3.x
- PostgreSQL database

### Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables in a `.env` file (refer to `.env.example`).

### Running the Application
- Start the development server:
  ```bash
  python main.py
  ```
  Or using uvicorn directly:
  ```bash
  uvicorn main:app --reload --port 8000
  ```
- Swagger documentation is available at `http://localhost:8000/docs`.

### Database Migrations
- The project uses Alembic for migrations, but the `lifespan` event in `main.py` also calls `app/db/init_db.py:init()` which creates the schema and tables automatically using `Base.metadata.create_all`.

### Testing
- Run all tests:
  ```bash
  pytest
  ```
- Unit tests are located in `tests/` and focus on pure business logic. `tests/conftest.py` handles environment setup for testing.

## Development Conventions

- **Asynchronous Code**: Use `async def` for all endpoints, CRUD operations, and services. Avoid blocking calls.
- **Language**: Codebase, docstrings, and domain vocabulary are in **Spanish**.
- **Configuration**: Always import the settings instance from `app.core.settings_instance.settings`. Do not instantiate `Settings()` directly.
- **Logging**: Use the logger singleton: `MyLogger().get_logger(name=...)`.
- **Error Handling**: Map domain/DB errors to `HTTPException` at the router layer.
- **Reporting**: Raw SQL (`text()`) is allowed in `app/services/informes.py` for read-only aggregation queries only.
