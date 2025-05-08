-- Crear el trigger para actualizar resultados al finalizar una participación
CREATE TRIGGER on_participacion_update
AFTER UPDATE OF estado ON trivia.participaciones
FOR EACH ROW
EXECUTE FUNCTION trivia.trg_participacion_finalizada();