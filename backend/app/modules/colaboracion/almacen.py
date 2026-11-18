"""Contenido de los archivos adjuntos en disco (HU-05-002).

Cada archivo se guarda con un nombre interno aleatorio, nunca con el nombre que envió
el usuario, dentro de ARCHIVOS_DIR (por omisión backend/data/archivos, fuera del repositorio).
Solo el servicio de colaboración usa este módulo.
"""
import os
import secrets
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]


def carpeta() -> Path:
    return Path(os.getenv("ARCHIVOS_DIR", str(BACKEND_DIR / "data" / "archivos")))


def _ruta(nombre_interno: str) -> Path:
    if not nombre_interno.isalnum():  # solo los nombres que genera guardar()
        raise ValueError("Nombre interno inválido")
    return carpeta() / nombre_interno


def guardar(contenido: bytes) -> str:
    """Escribe el contenido completo y devuelve su nombre interno."""
    carpeta().mkdir(parents=True, exist_ok=True)
    nombre = secrets.token_hex(16)
    temporal = carpeta() / f"{nombre}.parcial"
    temporal.write_bytes(contenido)
    temporal.replace(_ruta(nombre))  # nunca queda a la vista un archivo a medio escribir
    return nombre


def leer(nombre_interno: str) -> bytes:
    return _ruta(nombre_interno).read_bytes()


def borrar(nombre_interno: str) -> None:
    _ruta(nombre_interno).unlink(missing_ok=True)
