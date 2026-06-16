"""
Tests unitarios de la lógica de negocio de participaciones (funciones puras, sin BD).

Cubren la máquina de estados de intentos/cooldown (`decidir_accion`) y el cálculo de
resultados (`calcular_resultado`), que antes vivían en PL/pgSQL.
"""
from datetime import datetime, timedelta, timezone

from app.models.participacion import EstadoParticipacion
from app.services.participacion import (
    ACCION_CONTINUAR,
    ACCION_ESPERAR,
    ACCION_FINALIZADO,
    ACCION_INICIAR,
    calcular_resultado,
    decidir_accion,
)

NOW = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
COOLDOWN = timedelta(minutes=5)


def test_sin_intentos_previos_inicia_intento_1():
    d = decidir_accion(None, None, None, max_intentos=3, cooldown=COOLDOWN, now=NOW)
    assert d.accion == ACCION_INICIAR
    assert d.numero_intento == 1
    assert d.crear_nuevo is True
    assert d.remaining == timedelta(0)


def test_ultimo_pendiente_continua():
    d = decidir_accion(
        EstadoParticipacion.PENDIENTE, 2, None,
        max_intentos=3, cooldown=COOLDOWN, now=NOW,
    )
    assert d.accion == ACCION_CONTINUAR
    assert d.numero_intento == 2
    assert d.crear_nuevo is False


def test_finalizado_dentro_de_cooldown_espera():
    finished = NOW - timedelta(minutes=2)  # cooldown de 5 min aún no se cumple
    d = decidir_accion(
        EstadoParticipacion.FINALIZADO, 1, finished,
        max_intentos=3, cooldown=COOLDOWN, now=NOW,
    )
    assert d.accion == ACCION_ESPERAR
    assert d.crear_nuevo is False
    assert d.remaining == timedelta(minutes=3)


def test_finalizado_superado_cooldown_inicia_nuevo_intento():
    finished = NOW - timedelta(minutes=10)  # cooldown ya cumplido
    d = decidir_accion(
        EstadoParticipacion.FINALIZADO, 1, finished,
        max_intentos=3, cooldown=COOLDOWN, now=NOW,
    )
    assert d.accion == ACCION_INICIAR
    assert d.numero_intento == 2
    assert d.crear_nuevo is True


def test_maximo_intentos_alcanzado_finalizado():
    finished = NOW - timedelta(hours=1)
    d = decidir_accion(
        EstadoParticipacion.FINALIZADO, 3, finished,
        max_intentos=3, cooldown=COOLDOWN, now=NOW,
    )
    assert d.accion == ACCION_FINALIZADO
    assert d.crear_nuevo is False


def test_calcular_resultado_todas_correctas():
    respuestas = [
        {"id_pregunta": 1, "respuesta_seleccionada": 2},
        {"id_pregunta": 2, "respuesta_seleccionada": 1},
    ]
    correctas = {1: 2, 2: 1}
    r = calcular_resultado(respuestas, correctas)
    assert r["total_preguntas"] == 2
    assert r["respuestas_correctas"] == 2
    assert r["respuestas_incorrectas"] == 0
    assert r["porcentaje_acierto"] == 100.0


def test_calcular_resultado_mixto_y_redondeo():
    respuestas = [
        {"id_pregunta": 1, "respuesta_seleccionada": 2},  # correcta
        {"id_pregunta": 2, "respuesta_seleccionada": 4},  # incorrecta
        {"id_pregunta": 3, "respuesta_seleccionada": 1},  # correcta
    ]
    correctas = {1: 2, 2: 1, 3: 1}
    r = calcular_resultado(respuestas, correctas)
    assert r["total_preguntas"] == 3
    assert r["respuestas_correctas"] == 2
    assert r["respuestas_incorrectas"] == 1
    assert r["porcentaje_acierto"] == 66.67


def test_calcular_resultado_ignora_preguntas_inexistentes():
    respuestas = [
        {"id_pregunta": 1, "respuesta_seleccionada": 2},
        {"id_pregunta": 99, "respuesta_seleccionada": 1},  # no existe
    ]
    correctas = {1: 2}
    r = calcular_resultado(respuestas, correctas)
    assert r["total_preguntas"] == 1
    assert r["respuestas_correctas"] == 1


def test_calcular_resultado_sin_respuestas():
    r = calcular_resultado([], {})
    assert r["total_preguntas"] == 0
    assert r["porcentaje_acierto"] == 0.0
