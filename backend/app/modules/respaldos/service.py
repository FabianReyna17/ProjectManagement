"""Respaldo periódico de la información (HU-08-004).

Un respaldo es un .zip con:
- gestion.db: copia consistente de la BD en uso (API de respaldo de SQLite, sin detener el servidor).
  Contiene cuentas, funciones, accesos, proyectos, tareas, avances, bloqueos, comentarios,
  archivos (sus datos), avisos e historiales.
- archivos/: el contenido de los adjuntos (ARCHIVOS_DIR).
- manifiesto.json: fecha, versión del esquema, filas por tabla y huella sha256 de cada parte.

Se escribe como .parcial, se verifica (zip legible, integridad de la BD, huellas) y solo entonces
se renombra a .zip: un respaldo a medias o fallido nunca queda disponible. Cada ejecución queda
registrada con su resultado. Se guardan en RESPALDOS_DIR, separados de la BD y de los adjuntos
(en producción, en otro disco o equipo), con permisos solo para el usuario del servicio, y nunca
se sirven por HTTP. Se conservan los RESPALDOS_CONSERVAR más recientes.
"""
import hashlib
import json
import logging
import os
import secrets
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from ...core.errors import Prohibido
from ...db.database import BACKEND_DIR, database_url, transaccion
from ..colaboracion import almacen
from . import repository as repo

log = logging.getLogger("respaldos")

NOMBRE_BD = "gestion.db"
MANIFIESTO = "manifiesto.json"
FORMATO = 1


def carpeta() -> Path:
    return Path(os.getenv("RESPALDOS_DIR", str(BACKEND_DIR / "data" / "respaldos")))


def frecuencia_horas() -> float:
    """Cada cuántas horas toca respaldar (RP-08-04, propuesta: diario). 0 desactiva el ciclo del servidor."""
    return float(os.getenv("RESPALDO_CADA_HORAS", "24"))


def conservar() -> int:
    return max(1, int(os.getenv("RESPALDOS_CONSERVAR", "14")))


def _ahora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _texto(momento: datetime) -> str:
    return momento.strftime("%Y-%m-%d %H:%M:%S")


def ruta_bd() -> Path:
    url = database_url()
    if not url.startswith("sqlite:///"):
        raise RuntimeError("El respaldo solo admite la BD SQLite")
    return Path(url.removeprefix("sqlite:///"))


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def conteos(con: sqlite3.Connection) -> dict:
    tablas = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    return {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tablas}


def version_esquema(con: sqlite3.Connection) -> Optional[str]:
    try:
        return con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    except sqlite3.Error:
        return None


def _proteger(ruta: Path, modo: int) -> None:
    try:
        os.chmod(ruta, modo)  # en Windows solo aplica lectura/escritura; ahí protege la carpeta el sistema
    except OSError:
        pass


def _copiar_bd(destino: Path) -> None:
    """Copia consistente aunque el servidor esté escribiendo (API de respaldo de SQLite)."""
    origen = sqlite3.connect(ruta_bd())
    copia = sqlite3.connect(destino)
    try:
        origen.backup(copia)
    finally:
        copia.close()
        origen.close()


def _escribir(zip_parcial: Path, momento: datetime) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bd = Path(tmp) / NOMBRE_BD
        _copiar_bd(bd)
        con = sqlite3.connect(bd)
        try:
            filas, version = conteos(con), version_esquema(con)
        finally:
            con.close()
        adjuntos = sorted(p for p in almacen.carpeta().glob("*") if p.is_file() and p.suffix != ".parcial") \
            if almacen.carpeta().is_dir() else []
        manifiesto = {
            "formato": FORMATO, "creado_en": _texto(momento), "version_esquema": version,
            "filas": filas, "bd_sha256": sha256(bd),
            "archivos": {p.name: sha256(p) for p in adjuntos},
        }
        with zipfile.ZipFile(zip_parcial, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(bd, NOMBRE_BD)
            for p in adjuntos:
                z.write(p, f"archivos/{p.name}")
            z.writestr(MANIFIESTO, json.dumps(manifiesto, indent=2, ensure_ascii=False))


def leer_manifiesto(ruta_zip: Path) -> dict:
    with zipfile.ZipFile(ruta_zip) as z:
        return json.loads(z.read(MANIFIESTO))


def verificar(ruta_zip: Path) -> dict:
    """Comprueba que el respaldo se puede leer y está completo. Devuelve su manifiesto o lanza ValueError."""
    try:
        with zipfile.ZipFile(ruta_zip) as z:
            if z.testzip() is not None:
                raise ValueError("El archivo del respaldo está dañado")
            manifiesto = json.loads(z.read(MANIFIESTO))
            nombres = set(z.namelist())
            faltan = [n for n in manifiesto["archivos"] if f"archivos/{n}" not in nombres]
            if NOMBRE_BD not in nombres or faltan:
                raise ValueError("Al respaldo le faltan partes")
            for nombre, huella in manifiesto["archivos"].items():
                if hashlib.sha256(z.read(f"archivos/{nombre}")).hexdigest() != huella:
                    raise ValueError(f"El adjunto {nombre} no coincide con su huella")
            with tempfile.TemporaryDirectory() as tmp:
                z.extract(NOMBRE_BD, tmp)
                bd = Path(tmp) / NOMBRE_BD
                if sha256(bd) != manifiesto["bd_sha256"]:
                    raise ValueError("La BD del respaldo no coincide con su huella")
                con = sqlite3.connect(bd)
                try:
                    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise ValueError("La BD del respaldo no pasa la revisión de integridad")
                    if conteos(con) != manifiesto["filas"]:
                        raise ValueError("Las filas de la BD no coinciden con el manifiesto")
                finally:
                    con.close()
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, sqlite3.Error) as e:
        raise ValueError(f"El respaldo no se puede leer: {e}") from e
    return manifiesto


def _cantidad(n: int, nombre: str) -> str:
    return f"{n} {nombre}{'' if n == 1 else 's'}"


def _depurar(db) -> None:
    """Conserva solo los RESPALDOS_CONSERVAR válidos más recientes (los registros se mantienen)."""
    for viejo in repo.validos(db)[conservar():]:
        if viejo["archivo"]:
            (carpeta() / viejo["archivo"]).unlink(missing_ok=True)


def crear_respaldo(db, origen: str = "programado", actor_id: Optional[int] = None) -> dict:
    """Hace un respaldo y registra el resultado. No lanza: un fallo queda registrado como 'fallido'."""
    inicio = _ahora()
    nombre = f"respaldo-{inicio:%Y%m%d-%H%M%S}-{secrets.token_hex(3)}.zip"
    parcial = carpeta() / f"{nombre}.parcial"
    datos = {"iniciado_en": _texto(inicio), "origen": origen, "actor_id": actor_id,
             "archivo": None, "tamano": None, "detalle": None}
    try:
        carpeta().mkdir(parents=True, exist_ok=True)
        _proteger(carpeta(), 0o700)
        _escribir(parcial, inicio)
        manifiesto = verificar(parcial)
        final = carpeta() / nombre
        parcial.replace(final)  # solo ahora queda disponible
        _proteger(final, 0o600)
        filas = manifiesto["filas"]
        datos.update(resultado="ok", archivo=nombre, tamano=final.stat().st_size,
                     detalle=", ".join([_cantidad(filas.get("proyectos", 0), "proyecto"),
                                        _cantidad(filas.get("tareas", 0), "tarea"),
                                        _cantidad(len(manifiesto["archivos"]), "adjunto")]))
    except Exception as e:  # noqa: BLE001 — cualquier fallo se registra y se señala al Admin
        log.exception("Falló el respaldo")
        try:
            parcial.unlink(missing_ok=True)
        except OSError:
            pass
        datos.update(resultado="fallido", detalle=str(e)[:500] or type(e).__name__)
    datos["terminado_en"] = _texto(_ahora())
    with transaccion(db):
        nuevo = repo.registrar(db, datos)
    if datos["resultado"] == "ok":
        try:
            _depurar(db)
        except OSError:
            log.exception("No se pudieron borrar respaldos antiguos")
    return repo.obtener(db, nuevo)


def ultimo_valido(db) -> Optional[dict]:
    """El más reciente que terminó bien y cuyo archivo sigue existiendo."""
    for r in repo.validos(db):
        if (carpeta() / r["archivo"]).is_file():
            return r
    return None


def toca_respaldo(db, ahora: Optional[datetime] = None) -> bool:
    """True si no hay respaldo válido o el último tiene más de RESPALDO_CADA_HORAS."""
    horas = frecuencia_horas()
    if horas <= 0:
        return False
    ultimo = ultimo_valido(db)
    if not ultimo:
        return True
    return (ahora or _ahora()) - datetime.fromisoformat(ultimo["terminado_en"]) >= timedelta(hours=horas)


def respaldar_si_toca(db) -> Optional[dict]:
    return crear_respaldo(db) if toca_respaldo(db) else None


# --- Consulta para el Admin ---

def estado(db, funcion: str) -> dict:
    if funcion != "Admin":
        raise Prohibido()
    ultimo = ultimo_valido(db)
    historial = repo.listar(db)
    return {
        "frecuencia_horas": frecuencia_horas(),
        "ultimo_valido": ultimo,
        "atrasado": frecuencia_horas() > 0 and toca_respaldo(db),
        "ultimo_fallido": bool(historial) and historial[0]["resultado"] == "fallido",
        "respaldos": historial,
    }


def respaldar_ahora(db, actor: dict) -> dict:
    if actor["funcion"] != "Admin":
        raise Prohibido()
    return crear_respaldo(db, "manual", actor["id"])
