"""Procesos programados.

- HU-06-002: avisos de vencimiento cercano, al arrancar y luego cada AVISOS_CADA_MIN minutos
  (60 por defecto; 0 lo desactiva).
- HU-08-004: respaldo de la BD y los adjuntos cuando el último válido tiene más de
  RESPALDO_CADA_HORAS horas (24 por defecto; 0 lo desactiva). Se revisa cada hora.

También se pueden correr una vez desde el Programador de tareas de Windows o cron:

    python -m app.programado            # avisos de vencimiento
    python -m app.programado respaldo   # un respaldo ahora (aunque no toque)

Son seguros de repetir: correrlos de más no duplica avisos y cada respaldo es un archivo nuevo.
"""
import asyncio
import logging
import os
import sys

from .db.database import get_engine, migrar
from .modules.respaldos import service as respaldos
from .modules.tareas import service as tareas

log = logging.getLogger("programado")


def intervalo_minutos() -> int:
    return int(os.getenv("AVISOS_CADA_MIN", "60"))


def ejecutar_una_vez() -> int:
    with get_engine().connect() as db:
        return tareas.generar_avisos_vencimiento(db)


async def ciclo(minutos: int) -> None:
    while True:
        try:
            n = await asyncio.to_thread(ejecutar_una_vez)
            if n:
                log.info("Avisos de vencimiento generados: %s", n)
        except Exception:  # un fallo no detiene el servidor; se reintenta en la siguiente vuelta
            log.exception("Falló el proceso de avisos de vencimiento")
        await asyncio.sleep(minutos * 60)


def respaldar_si_toca() -> dict | None:
    with get_engine().connect() as db:
        return respaldos.respaldar_si_toca(db)


async def ciclo_respaldos(horas: float) -> None:
    """Revisa cada hora (o más seguido si la frecuencia es menor) si toca respaldar."""
    espera = min(3600, horas * 3600)
    while True:
        try:
            r = await asyncio.to_thread(respaldar_si_toca)
            if r:
                log.info("Respaldo %s: %s", r["resultado"], r["archivo"] or r["detalle"])
        except Exception:
            log.exception("Falló el proceso de respaldo")
        await asyncio.sleep(espera)


if __name__ == "__main__":
    migrar()
    if sys.argv[1:] == ["respaldo"]:
        with get_engine().connect() as conn:
            r = respaldos.crear_respaldo(conn)
        print(f"Respaldo {r['resultado']}: {r['archivo'] or r['detalle']}")
        sys.exit(0 if r["resultado"] == "ok" else 1)
    print(f"Avisos de vencimiento generados: {ejecutar_una_vez()}")
