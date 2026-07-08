# Catálogo de Endpoints - Trivia API

Este catálogo contiene ejemplos de uso con `curl` para los flujos principales de la API, organizados por módulos. Puedes importar estos ejemplos directamente en Postman.

## 🔐 1. Participantes y Juego

### A. Iniciar/Gestionar Participación
Este endpoint identifica al usuario y decide si puede jugar (crea un nuevo intento o continúa uno pendiente).

```bash
curl --request POST \
  --url http://localhost:8000/participaciones/loginU \
  --header 'Content-Type: application/json' \
  --data '{
	"nombre": "Estudiante Ejemplo",
	"cedula": "10203040",
	"grupo_id": 1,
	"evento_id": 1
}'
```
> **Nota**: La respuesta contiene un `token` JWT que debe usarse en los siguientes pasos.

### B. Obtener Preguntas del Participante
Obtiene las preguntas (comunes + grupo) autorizadas por el token.

```bash
curl --request GET \
  --url http://localhost:8000/preguntas/evento/1 \
  --header 'Authorization: Bearer <TU_TOKEN_AQUÍ>'
```

### C. Finalizar Participación
Envía las respuestas y cierra el intento.

```bash
curl --request PUT \
  --url http://localhost:8000/participaciones/finalizar \
  --header 'Authorization: Bearer <TU_TOKEN_AQUÍ>' \
  --header 'Content-Type: application/json' \
  --data '{
	"id_participacion": 10,
	"tiempo": "00:04:15",
	"respuestas": [
		{"id_pregunta": 1, "respuesta_seleccionada": 2, "tipo_pregunta": "opcion_unica"},
		{"id_pregunta": 2, "respuesta_abierta": "Mi comentario libre...", "tipo_pregunta": "abierta"}
	]
}'
```

---

## 📅 2. Gestión de Eventos (Admin)

### Listar Eventos
```bash
curl --request GET \
  --url http://localhost:8000/eventos/
```

### Crear Evento
```bash
curl --request POST \
  --url http://localhost:8000/eventos/ \
  --header 'Content-Type: application/json' \
  --data '{
	"nombre_evento": "Gran Trivia 2026",
	"tipo_evento": "conocimiento"
}'
```

---

## ❓ 3. Gestión de Preguntas (Admin)

### Carga Masiva (Excel)
Importa cientos de preguntas desde un archivo `.xlsx`.

```bash
curl --request POST \
  --url http://localhost:8000/preguntas/cargar-masivo \
  --header 'Content-Type: multipart/form-data' \
  --form 'archivo=@/ruta/a/tu/archivo.xlsx'
```

### Crear Pregunta Individual
```bash
curl --request POST \
  --url http://localhost:8000/preguntas/ \
  --header 'Content-Type: application/json' \
  --data '{
	"id_seccion": 1,
	"pregunta": "¿Qué framework usa esta API?",
	"tipo_pregunta": "opcion_unica",
	"opcion_correcta": 1,
	"respuestas": [
		{"respuesta": "FastAPI", "orden": 1},
		{"respuesta": "Django", "orden": 2}
	]
}'
```

---

## 📊 4. Reportes y Consultas

### Listar Participaciones Finalizadas
```bash
curl --request GET \
  --url 'http://localhost:8000/participaciones/estado/finalizado?id_evento=1'
```

### Buscar por Cédula
```bash
curl --request GET \
  --url 'http://localhost:8000/participaciones/buscar?cedula=10203040'
```

---

## 💓 5. Salud del Sistema
```bash
curl --request GET \
  --url http://localhost:8000/health/
```
