# Guía de Despliegue y CI/CD

Este proyecto utiliza **GitHub Actions** para automatizar las pruebas y el despliegue hacia **Azure App Service**.

## 🔄 Flujo de Trabajo (Workflows)

El archivo de configuración principal se encuentra en `.github/workflows/master_triviaapi.yml`.

### Disparadores (Triggers)
1. **Push de Tags**: El despliegue automático se activa cuando se crea un tag con el patrón `v*` (ej: `v1.0.0`) o `rollback-*`.
2. **Manual (workflow_dispatch)**: Se puede disparar manualmente desde la pestaña "Actions" de GitHub, permitiendo elegir la rama o tag específico a desplegar.

## 🏗️ Pasos del Pipeline

### 1. Job: `test`
- Configura Python 3.11.
- Instala dependencias y herramientas de calidad (`ruff`, `pytest`).
- **Linting**: Ejecuta `ruff` para detectar errores críticos.
- **Unit Tests**: Ejecuta la suite de `pytest`.
- *Si este job falla, el despliegue se detiene.*

### 2. Job: `build`
- Prepara el entorno y empaqueta el código fuente en un archivo `release.zip`.
- Sube el artefacto para que esté disponible en el siguiente paso.

### 3. Job: `deploy`
- Se autentica en Azure usando un Service Principal (OIDC).
- Despliega el artefacto comprimido a la Web App de Azure llamada `TriviaAPI`.

## 🔐 Configuración de Secretos (GitHub Secrets)

Para que el despliegue funcione, se deben configurar los siguientes secretos en el repositorio de GitHub:

- `AZUREAPPSERVICE_CLIENTID_...`: ID del cliente de la aplicación registrada en Azure.
- `AZUREAPPSERVICE_TENANTID_...`: ID del inquilino de Azure.
- `AZUREAPPSERVICE_SUBSCRIPTIONID_...`: ID de la suscripción de Azure.

## 🚀 Variables de Entorno en Azure

Asegúrate de configurar las variables de entorno necesarias en la sección "Configuration" de la Web App en el Portal de Azure, replicando lo definido en el `.env.example`.

**Importante**: La variable `ENVIRONMENT` debe establecerse en `prod` para desactivar el modo debug de FastAPI.

## 🛠️ Rollback
En caso de error en producción, el pipeline soporta el despliegue de tags de rollback. Basta con disparar manualmente el workflow seleccionando un tag de una versión estable anterior.
