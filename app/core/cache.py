"""Caché TTL simple en memoria (por proceso/worker).

Pensada para datos de lectura intensiva que cambian poco (p. ej. las preguntas de
un evento, que todos los usuarios consultan al jugar). Reduce la presión sobre la BD
en picos de concurrencia.

Limitación: la caché es por worker. Tras una mutación se invalida la del worker
actual; en otros workers la entrada expira por TTL. Como las preguntas cambian poco,
un TTL corto acota la inconsistencia. No usar para datos que deban ser exactos al instante.
"""
import time
import threading
from typing import Any, Callable, Optional


class TTLCache:
    """Caché clave->valor con expiración por tiempo. Segura entre hilos."""

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._store: dict[Any, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: Any) -> Optional[Any]:
        """Devuelve el valor si existe y no ha expirado; si no, None."""
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expira, valor = item
            if time.monotonic() >= expira:
                self._store.pop(key, None)
                return None
            return valor

    def set(self, key: Any, valor: Any) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, valor)

    def clear(self) -> None:
        """Vacía toda la caché (usar al mutar los datos cacheados)."""
        with self._lock:
            self._store.clear()


# Caché dedicada a las preguntas por (evento, grupo).
from app.core.settings_instance import settings

preguntas_cache = TTLCache(ttl_seconds=getattr(settings, "preguntas_cache_ttl", 300))
