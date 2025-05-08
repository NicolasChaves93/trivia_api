CREATE OR REPLACE FUNCTION trivia.gestionar_participacion(
    p_nombre VARCHAR,
    p_cedula VARCHAR,
    p_grupo INT
)
RETURNS TABLE (
    action TEXT,
    id_part INT,
    respuestas JSONB,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    tiempo_tot INTERVAL
) AS $$
DECLARE
    v_user INT;
    v_part INT;
    v_estado trivia.estado_participacion;
    v_respuestas JSONB;
    v_start_ts TIMESTAMP;
    v_finished_at TIMESTAMP;
    v_result_ts TIMESTAMP;
    v_tiempo_total INTERVAL;
    v_grupo_valido BOOLEAN;
BEGIN
    -- Insertar o actualizar usuario
    INSERT INTO trivia.usuarios (nombre, cedula)
    VALUES (p_nombre, p_cedula)
    ON CONFLICT (cedula) DO UPDATE SET nombre = EXCLUDED.nombre
    RETURNING id_usuario INTO v_user;

    -- Validar que el grupo exista y esté dentro de las fechas válidas
    SELECT EXISTS (
        SELECT 1 FROM trivia.grupos g
        WHERE g.id_grupo = p_grupo 
        AND NOW() BETWEEN g.fecha_inicio AND g.fecha_cierre
    ) INTO v_grupo_valido;

    IF NOT v_grupo_valido THEN
        RAISE EXCEPTION 'Grupo no válido o fuera del período permitido';
    END IF;

    -- Consultar si ya tiene participación en el grupo
    SELECT p.id_participacion, p.estado, p.respuestas_usuario, p.started_at, p.finished_at, p.tiempo_total
    INTO v_part, v_estado, v_respuestas, v_start_ts, v_finished_at, v_tiempo_total
    FROM trivia.participaciones p
    WHERE p.id_usuario = v_user AND p.id_grupo = p_grupo;

    IF NOT FOUND THEN
        BEGIN
            INSERT INTO trivia.participaciones (
                id_usuario, id_grupo, respuestas_usuario, estado, started_at, tiempo_total
            )
            VALUES (
                v_user, p_grupo, '[]'::jsonb, 'pendiente', NOW(), NULL
            )
            RETURNING id_participacion INTO v_part;
            
            action := 'iniciar';
            id_part := v_part;
            respuestas := '[]'::jsonb;
            started_at := NOW();
            finished_at := NULL;
            tiempo_tot := NULL;
            RETURN NEXT;
        EXCEPTION WHEN unique_violation THEN
            SELECT p.id_participacion, p.estado, p.respuestas_usuario, p.started_at, p.finished_at, p.tiempo_total
            INTO v_part, v_estado, v_respuestas, v_start_ts, v_finished_at, v_tiempo_total
            FROM trivia.participaciones p
            WHERE p.id_usuario = v_user AND p.id_grupo = p_grupo;

            IF FOUND THEN
                action := CASE WHEN v_estado = 'pendiente' THEN 'continuar' ELSE 'finalizado' END;
                id_part := v_part;
                respuestas := v_respuestas;
                started_at := CASE WHEN v_estado = 'finalizado' THEN v_finished_at ELSE v_start_ts END;
                finished_at := v_finished_at;
                tiempo_tot := v_tiempo_total;
                RETURN NEXT;
            END IF;
        END;
    ELSE
        action := CASE WHEN v_estado = 'pendiente' THEN 'continuar' ELSE 'finalizado' END;
        id_part := v_part;
        respuestas := v_respuestas;
        started_at := CASE WHEN v_estado = 'finalizado' THEN v_finished_at ELSE v_start_ts END;
        finished_at := v_finished_at;
        tiempo_tot := v_tiempo_total;
        RETURN NEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;