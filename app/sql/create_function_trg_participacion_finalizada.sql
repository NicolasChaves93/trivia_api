CREATE OR REPLACE FUNCTION trivia.trg_participacion_finalizada()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.estado = 'finalizado' AND OLD.estado <> 'finalizado' THEN
        -- Desglosar respuestas del JSONB
        WITH cte AS (
            SELECT 
                (elem->>'id_pregunta')::INT AS id_pregunta,
                (elem->>'respuesta_seleccionada')::SMALLINT AS respuesta_seleccionada
            FROM jsonb_array_elements(NEW.respuestas_usuario) AS elem
        ), insert_respuestas AS (
            INSERT INTO trivia.respuestas_usuarios (
                id_participacion, id_pregunta, orden_seleccionado
            )
            SELECT NEW.id_participacion, id_pregunta, respuesta_seleccionada
            FROM cte
            ON CONFLICT (id_participacion, id_pregunta) DO UPDATE
            SET orden_seleccionado = EXCLUDED.orden_seleccionado
        )
        -- Insertar o actualizar resultado
        INSERT INTO trivia.resultados (
            id_participacion,
            total_preguntas,
            respuestas_correctas,
            porcentaje_acierto,
            tiempo_total
        )
        SELECT 
            NEW.id_participacion,
            COUNT(*) AS total_preguntas,
            SUM(CASE WHEN c.respuesta_seleccionada = p.opcion_correcta THEN 1 ELSE 0 END),
            ROUND(
                100.0 * SUM(CASE WHEN c.respuesta_seleccionada = p.opcion_correcta THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0),
                2
            ),
            NEW.tiempo_total
        FROM cte c
        JOIN trivia.preguntas p ON p.id_pregunta = c.id_pregunta
        ON CONFLICT (id_participacion) DO UPDATE
        SET 
            total_preguntas = EXCLUDED.total_preguntas,
            respuestas_correctas = EXCLUDED.respuestas_correctas,
            porcentaje_acierto = EXCLUDED.porcentaje_acierto,
            tiempo_total = EXCLUDED.tiempo_total;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;