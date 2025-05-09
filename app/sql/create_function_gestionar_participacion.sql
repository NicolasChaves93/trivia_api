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
    tiempo_tot  INTERVAL
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
    ON CONFLICT (cedula) DO UPDATE
      SET nombre = EXCLUDED.nombre
    RETURNING id_usuario INTO v_user;

    -- 2. Validar grupo, obtener max_intentos y cooldown
    SELECT g.max_intentos, g.cooldown
      INTO v_max_intentos, v_cooldown
      FROM trivia.grupos AS g
     WHERE g.id_grupo = p_grupo
       AND NOW() BETWEEN g.fecha_inicio AND g.fecha_cierre;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Grupo no válido o fuera del período permitido';
    END IF;

    -- 3. Calcular número de intento actual
    SELECT MAX(p.numero_intento)
      INTO v_intento
      FROM trivia.participaciones AS p
     WHERE p.id_usuario = v_user
       AND p.id_grupo   = p_grupo;

    IF v_intento IS NULL THEN
        -- Primer intento
        v_intento := 1;

    ELSIF EXISTS (
        -- Si hay uno pendiente, lo continuamos
        SELECT 1
          FROM trivia.participaciones AS p2
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
          FROM trivia.participaciones AS p3
         WHERE p3.id_usuario     = v_user
           AND p3.id_grupo       = p_grupo
           AND p3.numero_intento = v_intento;

        action      := 'continuar';
        id_part     := v_part;
        respuestas  := v_respuestas;
        started_at  := v_start_ts;
        finished_at := v_finished_at;
        tiempo_tot  := v_tiempo_total;
        RETURN NEXT;

    ELSIF v_intento < v_max_intentos THEN
        -- Ya finalizó el anterior, verificar cooldown
        SELECT p4.finished_at
          INTO v_finished_at
          FROM trivia.participaciones AS p4
         WHERE p4.id_usuario     = v_user
           AND p4.id_grupo       = p_grupo
           AND p4.numero_intento = v_intento;

        -- Si no ha pasado el cooldown, calculamos texto dinámico
        IF NOW() < v_finished_at + v_cooldown THEN
            DECLARE
                total_secs   BIGINT := EXTRACT(EPOCH FROM v_cooldown)::BIGINT;
                hrs          INT    := total_secs / 3600;
                mins         INT    := (total_secs % 3600) / 60;
                segs         INT    := total_secs % 60;
                text_cd      TEXT   := '';
            BEGIN
                IF hrs > 0 THEN
                    text_cd := text_cd
                        || hrs || ' hora' || CASE WHEN hrs <> 1 THEN 's' ELSE '' END;
                END IF;

                IF mins > 0 THEN
                    IF hrs > 0 THEN
                        text_cd := text_cd || ' y ';
                    END IF;
                    text_cd := text_cd
                        || mins || ' minuto' || CASE WHEN mins <> 1 THEN 's' ELSE '' END;
                END IF;

                IF hrs = 0 AND mins = 0 AND segs > 0 THEN
                    text_cd := segs || ' segundo' || CASE WHEN segs <> 1 THEN 's' ELSE '' END;
                END IF;

                RAISE EXCEPTION 'Debe esperar % antes de un nuevo intento', text_cd;
            END;
        END IF;

        -- Permitimos un nuevo intento
        v_intento := v_intento + 1;

    ELSE
        -- Límite de intentos alcanzado
        SELECT p5.id_participacion,
               p5.respuestas_usuario,
               p5.started_at,
               p5.finished_at,
               p5.tiempo_total
          INTO v_part, v_respuestas, v_start_ts, v_finished_at, v_tiempo_total
          FROM trivia.participaciones AS p5
         WHERE p5.id_usuario     = v_user
           AND p5.id_grupo       = p_grupo
           AND p5.numero_intento = v_intento;

        action      := 'finalizado';
        id_part     := v_part;
        respuestas  := v_respuestas;
        started_at  := v_start_ts;
        finished_at := v_finished_at;
        tiempo_tot  := v_tiempo_total;
        RETURN NEXT;
    END IF;

    -- 4. Crear nueva participación, controlando duplicados
    BEGIN
        INSERT INTO trivia.participaciones (
            id_usuario,
            id_grupo,
            numero_intento,
            respuestas_usuario,
            estado,
            started_at,
            tiempo_total
        ) VALUES (
            v_user,
            p_grupo,
            v_intento,
            '[]'::jsonb,
            'pendiente',
            NOW(),
            NULL
        )
        RETURNING id_participacion INTO v_part;
    EXCEPTION WHEN unique_violation THEN
        SELECT id_participacion
          INTO v_part
          FROM trivia.participaciones
         WHERE id_usuario     = v_user
           AND id_grupo       = p_grupo
           AND numero_intento = v_intento;
    END;

    action      := 'iniciar';
    id_part     := v_part;
    respuestas  := '[]'::jsonb;
    started_at  := NOW();
    finished_at := NULL;
    tiempo_tot  := NULL;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;