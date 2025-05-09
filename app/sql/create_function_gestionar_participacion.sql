CREATE OR REPLACE FUNCTION trivia.gestionar_participacion(
    p_nombre VARCHAR,
    p_cedula  VARCHAR,
    p_grupo   INT
)
RETURNS TABLE (
    action      TEXT,
    id_part     INT,
    respuestas  JSONB,
    started_at  TIMESTAMP,
    finished_at TIMESTAMP,
    tiempo_tot  INTERVAL,
    remaining   INTERVAL
) AS $$
DECLARE
    v_user         INT;
    v_part         INT;
    v_respuestas   JSONB;
    v_start_ts     TIMESTAMP;
    v_finished_at  TIMESTAMP;
    v_tiempo_total INTERVAL;
    v_intento      SMALLINT;
    v_max_intentos SMALLINT;
    v_cooldown     INTERVAL;
BEGIN
    -- 1. Upsert usuario
    INSERT INTO trivia.usuarios (nombre, cedula)
    VALUES (p_nombre, p_cedula)
    ON CONFLICT (cedula) DO UPDATE SET nombre = EXCLUDED.nombre
    RETURNING id_usuario INTO v_user;

    -- 2. Obtener config del grupo
    SELECT g.max_intentos, g.cooldown
      INTO v_max_intentos, v_cooldown
      FROM trivia.grupos g
     WHERE g.id_grupo = p_grupo
       AND NOW() BETWEEN g.fecha_inicio AND g.fecha_cierre;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Grupo no válido o fuera del período permitido';
    END IF;

    -- 3. Calcular último intento
    SELECT MAX(p.numero_intento)
      INTO v_intento
      FROM trivia.participaciones p
     WHERE p.id_usuario = v_user
       AND p.id_grupo   = p_grupo;

    -- 4. Primer intento: crear y salir
    IF v_intento IS NULL THEN
        v_intento := 1;
        INSERT INTO trivia.participaciones (
            id_usuario, id_grupo, numero_intento,
            respuestas_usuario, estado, started_at, tiempo_total
        ) VALUES (
            v_user, p_grupo, v_intento,
            '[]'::jsonb, 'pendiente', NOW(), NULL
        ) RETURNING id_participacion INTO v_part;

        action      := 'iniciar';
        id_part     := v_part;
        respuestas  := '[]'::jsonb;
        started_at  := NOW();
        finished_at := NULL;
        tiempo_tot  := NULL;
        remaining   := '00:00:00'::interval;
        RETURN NEXT;
        RETURN;
    END IF;

    -- 5. Continuar intento pendiente
    IF EXISTS (
        SELECT 1
          FROM trivia.participaciones p2
         WHERE p2.id_usuario     = v_user
           AND p2.id_grupo       = p_grupo
           AND p2.numero_intento = v_intento
           AND p2.estado         = 'pendiente'
    ) THEN
        SELECT p3.id_participacion,
               p3.respuestas_usuario,
               p3.started_at,
               p3.finished_at,
               p3.tiempo_total
          INTO v_part, v_respuestas, v_start_ts, v_finished_at, v_tiempo_total
          FROM trivia.participaciones p3
         WHERE p3.id_usuario     = v_user
           AND p3.id_grupo       = p_grupo
           AND p3.numero_intento = v_intento;

        action      := 'continuar';
        id_part     := v_part;
        respuestas  := v_respuestas;
        started_at  := v_start_ts;
        finished_at := v_finished_at;
        tiempo_tot  := v_tiempo_total;
        remaining   := '00:00:00'::interval;
        RETURN NEXT;
        RETURN;
    END IF;

    -- 6. Verificar cooldown antes de nuevo intento
    IF v_intento < v_max_intentos THEN
        SELECT p4.id_participacion,
               p4.respuestas_usuario,
               p4.started_at,
               p4.finished_at,
               p4.tiempo_total
          INTO v_part, v_respuestas, v_start_ts, v_finished_at, v_tiempo_total
          FROM trivia.participaciones p4
         WHERE p4.id_usuario     = v_user
           AND p4.id_grupo       = p_grupo
           AND p4.numero_intento = v_intento;

        IF NOW() < v_finished_at + v_cooldown THEN
            remaining := (v_finished_at + v_cooldown) - NOW();

            action      := 'esperar';
            id_part     := v_part;
            respuestas  := v_respuestas;
            started_at  := v_start_ts;
            finished_at := v_finished_at;
            tiempo_tot  := v_tiempo_total;
            RETURN NEXT;
            RETURN;
        END IF;

        -- superado cooldown, incrementar para crear nuevo
        v_intento := v_intento + 1;
    ELSE
        -- 7. Máximo de intentos alcanzado: finalizar
        SELECT p5.id_participacion,
               p5.respuestas_usuario,
               p5.started_at,
               p5.finished_at,
               p5.tiempo_total
          INTO v_part, v_respuestas, v_start_ts, v_finished_at, v_tiempo_total
          FROM trivia.participaciones p5
         WHERE p5.id_usuario     = v_user
           AND p5.id_grupo       = p_grupo
           AND p5.numero_intento = v_intento;

        action      := 'finalizado';
        id_part     := v_part;
        respuestas  := v_respuestas;
        started_at  := v_start_ts;
        finished_at := v_finished_at;
        tiempo_tot  := v_tiempo_total;
        remaining   := '00:00:00'::interval;
        RETURN NEXT;
        RETURN;
    END IF;

    -- 8. Crear nuevo intento tras cooldown
    INSERT INTO trivia.participaciones (
        id_usuario, id_grupo, numero_intento,
        respuestas_usuario, estado, started_at, tiempo_total
    ) VALUES (
        v_user, p_grupo, v_intento,
        '[]'::jsonb, 'pendiente', NOW(), NULL
    ) RETURNING id_participacion INTO v_part;

    action      := 'iniciar';
    id_part     := v_part;
    respuestas  := '[]'::jsonb;
    started_at  := NOW();
    finished_at := NULL;
    tiempo_tot  := NULL;
    remaining   := '00:00:00'::interval;
    RETURN NEXT;
    RETURN;
END;
$$ LANGUAGE plpgsql;