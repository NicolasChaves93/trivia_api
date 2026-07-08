# Trivia API

API REST profesional para la gestión integral de eventos de trivia, concursos de conocimiento y encuestas. Diseñada con un enfoque de alto rendimiento, concurrencia segura y arquitectura limpia.

## 🚀 Características Principales

- **Gestión Multi-Evento**: Soporta múltiples eventos simultáneos, cada uno con sus propios grupos y reglas.
- **Modelo de Preguntas Mixto**: Permite definir secciones de preguntas comunes para todo un evento o específicas para un grupo determinado.
- **Ciclo de Vida de Participación**: Máquina de estados robusta que gestiona intentos, tiempos de espera (*cooldown*) y estados de finalización.
- **Seguridad y Concurrencia**: Implementa bloqueos transaccionales (*advisory locks*) en PostgreSQL para garantizar la integridad en participaciones simultáneas.
- **Carga Masiva**: Servicio de importación de preguntas y opciones desde archivos Excel (.xlsx).
- **Reportes y Exportación**: Generación de informes de resultados y exportación a formatos compatibles para análisis.
- **Autenticación JWT**: Seguridad basada en tokens para participantes y administradores.

## 🛠️ Stack Tecnológico

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asíncrono)
- **Base de Datos**: PostgreSQL 15+
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async)
- **Migraciones**: [Alembic](https://alembic.sqlalchemy.org/)
- **Validación de Datos**: Pydantic v2
- **Testing**: Pytest con Pytest-Asyncio
- **Despliegue**: Azure App Service con GitHub Actions

## 🏁 Inicio Rápido

### Requisitos Previos
- Python 3.9+
- PostgreSQL

### Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repositorio>
   cd trivia_api
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   Copia el archivo `.env.example` a `.env` y completa tus credenciales de base de datos y claves secretas.

5. **Ejecutar migraciones**:
   ```bash
   alembic upgrade head
   ```

### Ejecución en Desarrollo

```bash
python main.py
```
El servidor iniciará en `http://localhost:8000`. Puedes acceder a la documentación interactiva en:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🏗️ Arquitectura

El proyecto sigue una estructura de capas para facilitar el mantenimiento y escalabilidad:

- **`/app/api`**: Definición de rutas y mapeo de excepciones HTTP.
- **`/app/services`**: Lógica de negocio compleja y orquestación de servicios.
- **`/app/crud`**: Operaciones atómicas de acceso a datos.
- **`/app/models`**: Definición de tablas y relaciones de base de datos.
- **`/app/schemas`**: Modelos de validación Pydantic.

## 🧪 Testing

Para ejecutar la suite de pruebas:
```bash
pytest
```

## 📖 Documentación Adicional

- [Modelo de Datos](docs/MODELO_DATOS.md)
- [Gestión de Migraciones](docs/MIGRACIONES.md)
- [Manual de Carga Masiva](docs/CARGA_MASIVA.md) (Próximamente)
