# Guía de Uso de la API: Flujo de Participación

Esta guía describe el flujo de trabajo principal para que un usuario participe en una trivia.

## 1. Identificación y Estado de Participación

Antes de iniciar, el sistema debe determinar si el usuario puede jugar. Se utiliza el endpoint de gestión de participación.

- **Endpoint**: `POST /participaciones/gestionar`
- **Body**:
  ```json
  {
    "nombre": "Juan Perez",
    "cedula": "12345678",
    "grupo_id": 1
  }
  ```

### Acciones de Respuesta (`action`):

| Acción | Significado | Siguiente Paso |
|--------|-------------|----------------|
| **`iniciar`** | El usuario no tiene intentos o el anterior terminó y pasó el cooldown. | Se creó una nueva `id_participacion`. Mostrar preguntas. |
| **`continuar`** | El usuario tiene un intento `pendiente` (no terminado). | Usar la `id_participacion` devuelta para retomar. |
| **`esperar`** | Intento previo finalizado pero aún está en periodo de *cooldown*. | Bloquear acceso y mostrar tiempo restante (`remaining`). |
| **`FINALIZADO`** | El usuario ya agotó su máximo de intentos permitidos. | Mostrar mensaje de fin de participación. |

## 2. Obtención de Preguntas

Una vez que se tiene una participación válida (`iniciar` o `continuar`), se deben obtener las preguntas correspondientes al grupo y evento.

- **Endpoint**: `GET /preguntas/participante/{id_participacion}`
- **Seguridad**: Requiere Token JWT de participante (obtenido al gestionar la participación).

Este endpoint devuelve una lista de preguntas que incluye tanto las "comunes" del evento como las "específicas" del grupo del usuario.

## 3. Envío de Respuestas y Finalización

Cuando el usuario completa la trivia, se envían todas las respuestas juntas para procesar el resultado.

- **Endpoint**: `POST /participaciones/finalizar`
- **Body**:
  ```json
  {
    "id_participacion": 105,
    "tiempo_total": "00:05:30",
    "respuestas": [
      {"id_pregunta": 1, "respuesta_seleccionada": 2},
      {"id_pregunta": 2, "respuesta_abierta": "Mi opinión es..."}
    ]
  }
  ```

### Procesamiento Interno:
1. Se validan las opciones correctas.
2. Se calcula el puntaje (solo para `opcion_unica`).
3. Se cierra el estado de la participación a `FINALIZADO`.
4. Se genera un registro en la tabla `resultados` para consultas rápidas de informes.

## 4. Consulta de Resultados (Opcional)

Si el usuario desea ver su desempeño histórico o el del intento actual.

- **Endpoint**: `GET /participaciones/resultados/{id_participacion}`
- **Resumen**: Devuelve total de preguntas, aciertos, errores y porcentaje.

---

## 🔒 Notas de Seguridad

1. **Tokens**: La mayoría de los endpoints de participación requieren un `Authorization: Bearer <token>`.
2. **Concurrencia**: El sistema utiliza bloqueos a nivel de base de datos. Si un usuario intenta "iniciar" dos veces al mismo tiempo desde dispositivos distintos, el sistema serializará las peticiones para evitar que consuma más intentos de los permitidos.
