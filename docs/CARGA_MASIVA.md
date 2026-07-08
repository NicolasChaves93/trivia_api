# Guía de Carga Masiva de Preguntas

La Trivia API permite importar grandes volúmenes de preguntas y respuestas mediante archivos Excel (.xlsx). Este proceso automatiza la creación de eventos, secciones y la asociación de preguntas a grupos específicos.

## 📄 Formato del Archivo Excel

El archivo debe ser un `.xlsx` con una hoja activa que contenga los siguientes encabezados en la primera fila:

| Columna | Descripción | Obligatorio |
|---------|-------------|-------------|
| **evento** | Nombre exacto del evento (debe existir previamente). | Sí |
| **grupo** | Nombre del grupo dentro del evento. Si se deja vacío, la pregunta será "común" para todo el evento. | No |
| **seccion** | Nombre de la sección (ej: "Conocimientos Generales"). Se crea automáticamente si no existe. | Sí |
| **tipo_pregunta** | Tipo de pregunta: `opcion_unica`, `abierta` o `opcion_opinion`. | Sí |
| **pregunta** | El texto de la pregunta. | Sí |
| **opcion_1** | Texto de la primera opción. | Solo en `opcion_unica` / `opinion` |
| **opcion_2** | Texto de la segunda opción. | Solo en `opcion_unica` / `opinion` |
| **opcion_3** | Texto de la tercera opción. | No |
| **opcion_4** | Texto de la cuarta opción. | No |
| **opcion_correcta** | Número (1-4) que indica cuál de las opciones es la correcta. | Solo en `opcion_unica` |

## 🧩 Tipos de Pregunta

1. **`opcion_unica`**: Preguntas clásicas de trivia con una sola respuesta correcta. Requiere al menos 2 opciones y el índice de la correcta. **Suma puntos**.
2. **`abierta`**: Permite al usuario escribir texto libre. No requiere opciones ni puntúa automáticamente.
3. **`opcion_opinion`**: Preguntas tipo encuesta donde el usuario elige una opción pero no hay una "correcta". No suma puntos.

## ⚠️ Reglas de Validación e Integridad

- **Duplicados**: El sistema evita cargar la misma pregunta (mismo texto) dos veces dentro de la misma sección para evitar redundancia.
- **Alcance Mixto**: 
    - Si la columna `grupo` está vacía, la sección se marca como global para el evento.
    - Si la columna `grupo` tiene un valor, la sección se vincula exclusivamente a ese grupo.
- **Transaccionalidad**: Cada fila se procesa de forma independiente. Si una fila falla, el sistema registra el error y continúa con la siguiente, garantizando que los datos válidos se carguen correctamente.

## ❌ Errores Comunes

- **Evento no existe**: El nombre del evento en el Excel debe coincidir exactamente con uno ya creado en el sistema.
- **Índice fuera de rango**: Poner `5` en `opcion_correcta` cuando solo se definieron 4 opciones.
- **Falta de opciones**: Intentar cargar una `opcion_unica` sin completar `opcion_1` y `opcion_2`.

## 🛠️ Cómo Usar

1. Descarga la plantilla de ejemplo (si está disponible en la interfaz administrativa).
2. Completa los datos siguiendo las reglas mencionadas.
3. Sube el archivo a través del endpoint `POST /preguntas/carga-masiva`.
4. Revisa el JSON de respuesta para confirmar cuántas preguntas se crearon y ver el detalle de posibles errores por fila.
