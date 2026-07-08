# Arquitectura de Infraestructura Compartida

Este proyecto utiliza una **Infraestructura Externa** centralizada. Los servicios se gestionan en un proyecto independiente para ser compartidos entre múltiples aplicaciones.

## 📂 1. El Proyecto de Infraestructura Base

Ubicación recomendada: `C:\Users\ASUS-PC\Documents\Trabajo\ColombianCode\Compensar\Desarrollos\infra-global\`

Archivo `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:17-alpine
    container_name: shared_db_postgres
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password123
      POSTGRES_DB: shared_db
    ports:
      - "5432:5432"
    volumes:
      - shared_postgres_data:/var/lib/postgresql/data
    networks:
      - shared_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d shared_db"]
      interval: 5s
      timeout: 5s
      retries: 5

networks:
  shared_network:
    name: database_share_network  # Red compartida para todos los proyectos
    driver: bridge

volumes:
  shared_postgres_data:
```

### Para iniciar la infra:
```bash
docker-compose up -d
```

### Paso 1.1: Crear la Base de Datos para este Proyecto
Como este proyecto usa su propia base de datos dedicada (`trivia_db`), debes crearla en el servidor compartido (solo la primera vez):

```bash
docker exec -it shared_db_postgres psql -U admin -c "CREATE DATABASE trivia_db;"
```

---

## 🚀 2. El Proyecto Trivia API

La API se unirá a la red compartida y se conectará al host `shared_db_postgres`.

```bash
docker-compose up --build
```

## 🎭 Gestión de Perfiles (Entornos)

La aplicación soporta perfiles dinámicos. Puedes alternar entre archivos de configuración (`.env.prod`, `.env.test`) sin cambiar el código ni el `docker-compose.yml`.

### Uso con Docker Compose

Para arrancar con un perfil específico, pasa las variables antes del comando:

| Entorno | Comando | Archivo Cargado |
|---------|---------|-----------------|
| **Producción** | `ENV_FILE=.env.prod APP_PROFILE=prod docker-compose up` | `.env.prod` |
| **Pruebas/QA** | `ENV_FILE=.env.test APP_PROFILE=test docker-compose up` | `.env.test` |
| **Desarrollo** | `docker-compose up` | `.env` |

> **Nota**: `ENV_FILE` le dice a Docker qué variables inyectar, y `APP_PROFILE` le dice a la aplicación Python qué archivo de configuración adicional leer para validaciones internas.

---

## 🏆 Ventajas del Modelo Compartido

1. **Eficiencia**: Un solo motor de base de datos para N proyectos.
2. **Desacoplamiento**: La infraestructura tiene su propio ciclo de vida.
3. **Escalabilidad**: Fácil de añadir servicios adicionales (Redis, etc.) a la red compartida.
