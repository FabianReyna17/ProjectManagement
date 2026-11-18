"""Procesos programados (HU-06-002: avisos de vencimiento cercano).

El servidor los corre al arrancar y luego cada AVISOS_CADA_MIN minutos (60 por defecto;
0 lo desactiva). También se pueden correr una vez desde el Programador de tareas o cron:

    python -m app.programado

Son idempotentes: correrlos de más no duplica avisos.
"""
import asyncio
import logging
import os

from .db.database import get_engine, migrar
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


if __name__ == "__main__":
    migrar()
    print(f"Avisos de vencimiento generados: {ejecutar_una_vez()}")
