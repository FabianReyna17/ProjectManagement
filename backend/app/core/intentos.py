"""Freno a intentos fallidos de inicio de sesión (fuerza bruta).

Cuenta los fallos por identificador escrito, exista o no la cuenta, para no revelar
cuáles existen. Tras LIBRES fallos seguidos cada intento exige esperar un tiempo que
se duplica (2 s, 4 s, 8 s… hasta 5 min). Un inicio correcto limpia el contador.
Vive en memoria del proceso: si la API corre con varios procesos, cada uno lleva su cuenta.
"""
import math
import threading
import time

LIBRES = 5
ESPERA_BASE = 2
ESPERA_MAX = 300
OLVIDO = 15 * 60  # sin fallos durante este tiempo, el contador se olvida


class Intentos:
    def __init__(self, reloj=time.monotonic):
        self.reloj = reloj
        self._fallos: dict[str, tuple[int, float]] = {}  # clave → (fallos, momento del último)
        self._candado = threading.Lock()

    def _vigente(self, clave: str) -> tuple[int, float]:
        fallos, ultimo = self._fallos.get(clave, (0, 0.0))
        if fallos and self.reloj() - ultimo > OLVIDO:
            self._fallos.pop(clave, None)
            return 0, 0.0
        return fallos, ultimo

    def espera(self, clave: str) -> int:
        """Segundos que faltan para poder intentar de nuevo (0 = puede intentar)."""
        with self._candado:
            fallos, ultimo = self._vigente(clave)
            if fallos < LIBRES:
                return 0
            bloqueo = min(ESPERA_BASE * 2 ** (fallos - LIBRES), ESPERA_MAX)
            return max(0, math.ceil(ultimo + bloqueo - self.reloj()))

    def fallo(self, clave: str) -> None:
        with self._candado:
            fallos, _ = self._vigente(clave)
            self._fallos[clave] = (fallos + 1, self.reloj())
            if len(self._fallos) > 10_000:  # evita crecer sin límite
                ahora = self.reloj()
                self._fallos = {k: v for k, v in self._fallos.items() if ahora - v[1] <= OLVIDO}

    def exito(self, clave: str) -> None:
        with self._candado:
            self._fallos.pop(clave, None)

    def limpiar(self) -> None:
        with self._candado:
            self._fallos.clear()
