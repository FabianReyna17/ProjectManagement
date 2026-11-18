"""Comentarios y archivos de proyectos y tareas (HU-05-001, HU-05-002).

No importa FastAPI. El proyecto o la tarea llegan ya autorizados (participación activa,
comprobada en cada petición), así que quien perdió el acceso no puede leer ni publicar,
aunque use un enlace directo. Cualquier participante puede comentar y adjuntar.
La descarga de un archivo vuelve a comprobar el acceso al proyecto del archivo.
"""
import hashlib
import os
import re
from typing import Optional

from ...core.errors import DatosInvalidos, Prohibido
from ...db.idempotencia import crear_una_vez
from ..proyectos import service as proyectos
from . import almacen
from . import repository as repo

# Reglas de archivos (por confirmar con el cliente): tamaño máximo y tipos por extensión.
# El tipo se deduce de la extensión permitida; nunca se confía en el que envía el navegador.
MAX_MB = int(os.getenv("ARCHIVO_MAX_MB", "10"))
MAX_BYTES = MAX_MB * 1024 * 1024
TIPOS = {
    "pdf": "application/pdf", "txt": "text/plain", "csv": "text/csv", "md": "text/markdown",
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "odt": "application/vnd.oasis.opendocument.text",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "zip": "application/zip",
}
MSG_TAMANO = f"El archivo supera el tamaño máximo de {MAX_MB} MB. No se adjuntó"
MSG_TIPO = "Ese tipo de archivo no está permitido. No se adjuntó"


def comentar(db, proyecto_id: int, tarea_id: Optional[int], autor_id: int, texto: str,
             clave: Optional[str] = None) -> dict:
    """Guarda el comentario con autor y fecha. Un reintento con la misma clave no lo duplica."""
    cid = crear_una_vez(db, autor_id, clave, "comentario",
                        lambda: repo.insertar_comentario(db, proyecto_id, tarea_id, texto, autor_id))
    return repo.obtener_comentario(db, cid)


def comentarios(db, proyecto_id: int, tarea_id: Optional[int] = None) -> list:
    return repo.listar_comentarios(db, proyecto_id, tarea_id)


# --- Archivos (HU-05-002) ---

def reglas() -> dict:
    return {"max_bytes": MAX_BYTES, "extensiones": sorted(TIPOS)}


def _nombre_seguro(nombre: str) -> str:
    """Solo el nombre final (sin carpetas), sin caracteres de control y con largo acotado."""
    nombre = re.sub(r"[\x00-\x1f\x7f]", "", nombre.replace("\\", "/").rsplit("/", 1)[-1]).strip()
    if not nombre or nombre in (".", ".."):
        raise DatosInvalidos("Datos inválidos o incompletos: nombre")
    base, punto, ext = nombre.rpartition(".")
    return (base[:150] + punto + ext[:10]) if punto else nombre[:160]


def _tipo(nombre: str) -> str:
    ext = nombre.rpartition(".")[2].lower() if "." in nombre else ""
    if ext not in TIPOS:
        raise DatosInvalidos(MSG_TIPO)
    return TIPOS[ext]


def adjuntar(db, proyecto_id: int, tarea_id: Optional[int], autor_id: int, nombre: str, contenido: bytes,
             clave: Optional[str] = None) -> dict:
    """Valida tipo y tamaño, guarda el contenido y luego el registro en una transacción.
    Si el registro no se confirma, el contenido se borra: no queda un adjunto a medias.
    Un reintento con la misma clave devuelve el primer adjunto y no guarda una copia."""
    nombre = _nombre_seguro(nombre)
    tipo = _tipo(nombre)
    if len(contenido) > MAX_BYTES:
        raise DatosInvalidos(MSG_TAMANO)
    if not contenido:
        raise DatosInvalidos("El archivo está vacío. No se adjuntó")
    interno = almacen.guardar(contenido)
    try:
        aid = crear_una_vez(db, autor_id, clave, "archivo", lambda: repo.insertar_archivo(
            db, proyecto_id, tarea_id, nombre, tipo, len(contenido), hashlib.sha256(contenido).hexdigest(),
            interno, autor_id))
    except Exception:
        almacen.borrar(interno)
        raise
    archivo = repo.obtener_archivo(db, aid)
    if archivo["almacen"] != interno:  # reintento: ya existía
        almacen.borrar(interno)
    return _publico(archivo)


def _publico(archivo: dict) -> dict:
    return {k: v for k, v in archivo.items() if k != "almacen"}


def archivos(db, proyecto_id: int, tarea_id: Optional[int] = None) -> list:
    return [_publico(a) for a in repo.listar_archivos(db, proyecto_id, tarea_id)]


def descargar(db, archivo_id: int, usuario_id: int) -> tuple[dict, bytes]:
    """Solo con acceso vigente al proyecto del archivo; un enlace guardado no basta.
    Inexistente o sin acceso → Prohibido (misma respuesta)."""
    archivo = repo.obtener_archivo(db, archivo_id)
    if not archivo:
        raise Prohibido()
    proyectos.obtener_autorizado(db, archivo["proyecto_id"], usuario_id)
    return _publico(archivo), almacen.leer(archivo["almacen"])
