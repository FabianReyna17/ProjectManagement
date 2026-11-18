"""Comentarios y archivos de proyectos y tareas (HU-05-001 a HU-05-004).

No importa FastAPI. El proyecto o la tarea llegan ya autorizados (participación activa,
comprobada en cada petición), así que quien perdió el acceso no puede leer ni publicar,
aunque use un enlace directo. Cualquier participante puede comentar y adjuntar.
La descarga de un archivo vuelve a comprobar el acceso al proyecto del archivo.
Solo su autor corrige o retira lo que publicó; nada se borra (HU-05-004).
"""
import hashlib
import os
import re
from typing import Optional

from ...core.errors import Conflicto, DatosInvalidos, NoEncontrado, Prohibido
from ...db.database import transaccion
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
    proyectos.exigir_abierto_id(db, proyecto_id)  # HU-02-005
    cid = crear_una_vez(db, autor_id, clave, "comentario",
                        lambda: repo.insertar_comentario(db, proyecto_id, tarea_id, texto, autor_id))
    return _comentario_publico(repo.obtener_comentario(db, cid))


def _comentario_publico(c: dict) -> dict:
    """HU-05-004: de un comentario retirado se ve quién y cuándo lo retiró, no su texto."""
    return {**c, "texto": None} if c["retirado_en"] else c


def comentarios(db, proyecto_id: int, tarea_id: Optional[int] = None) -> list:
    return [_comentario_publico(c) for c in repo.listar_comentarios(db, proyecto_id, tarea_id)]


# --- Corregir contenido propio (HU-05-004) ---

MSG_SOLO_AUTOR = "Solo quien lo publicó puede corregirlo o retirarlo"
MSG_RETIRADO = "Este comentario ya fue retirado: no se puede editar"
MSG_EDITADO = "El comentario cambió mientras lo editabas. Vuelve a abrirlo; tu cambio no se guardó"
MSG_ARCHIVO_RETIRADO = "Quien adjuntó este archivo lo retiró: ya no se puede descargar"


def _propio(db, elemento: Optional[dict], usuario_id: int) -> dict:
    """Solo con acceso vigente al proyecto (si no → Prohibido, sin revelar si existe), solo
    su autor (si no → Prohibido con el motivo) y solo si el proyecto sigue abierto."""
    if not elemento:
        raise Prohibido()
    proyectos.obtener_autorizado(db, elemento["proyecto_id"], usuario_id)
    if elemento["autor_id"] != usuario_id:
        raise Prohibido(MSG_SOLO_AUTOR)
    proyectos.exigir_abierto_id(db, elemento["proyecto_id"])
    return elemento


def editar_comentario(db, comentario_id: int, usuario_id: int, texto: str) -> dict:
    """El texto vigente cambia y el anterior queda en sus ediciones con quién y cuándo.
    Guardar el mismo texto no cuenta como edición."""
    c = _propio(db, repo.obtener_comentario(db, comentario_id), usuario_id)
    if c["retirado_en"]:
        raise DatosInvalidos(MSG_RETIRADO)
    if texto != c["texto"]:
        with transaccion(db):
            if not repo.editar_comentario(db, comentario_id, c["texto"], texto, usuario_id):
                raise Conflicto(MSG_EDITADO)
    return _comentario_publico(repo.obtener_comentario(db, comentario_id))


def retirar_comentario(db, comentario_id: int, usuario_id: int) -> dict:
    """Deja de mostrarse su texto; queda la constancia de quién lo retiró y cuándo. Repetir no cambia nada."""
    _propio(db, repo.obtener_comentario(db, comentario_id), usuario_id)
    with transaccion(db):
        repo.retirar(db, "comentarios", comentario_id, usuario_id)
    return _comentario_publico(repo.obtener_comentario(db, comentario_id))


def ediciones(db, comentario_id: int, usuario_id: int) -> list:
    """Textos anteriores de un comentario editado, para quien tiene acceso al proyecto.
    De un comentario retirado no se muestra ningún texto."""
    c = repo.obtener_comentario(db, comentario_id)
    if not c:
        raise Prohibido()
    proyectos.obtener_autorizado(db, c["proyecto_id"], usuario_id)
    return [] if c["retirado_en"] else repo.listar_ediciones(db, comentario_id)


def retirar_archivo(db, archivo_id: int, usuario_id: int) -> dict:
    """El archivo deja de listarse con su nombre y de poder descargarse; su registro (y el
    contenido, mientras se acuerda la política de conservación) se conservan."""
    _propio(db, repo.obtener_archivo(db, archivo_id), usuario_id)
    with transaccion(db):
        repo.retirar(db, "archivos", archivo_id, usuario_id)
    return _publico(repo.obtener_archivo(db, archivo_id))


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
    proyectos.exigir_abierto_id(db, proyecto_id)  # HU-02-005
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
    publico = {k: v for k, v in archivo.items() if k != "almacen"}
    return {**publico, "nombre": None} if archivo["retirado_en"] else publico  # HU-05-004


def archivos(db, proyecto_id: int, tarea_id: Optional[int] = None) -> list:
    return [_publico(a) for a in repo.listar_archivos(db, proyecto_id, tarea_id)]


def descargar(db, archivo_id: int, usuario_id: int) -> tuple[dict, bytes]:
    """Solo con acceso vigente al proyecto del archivo; un enlace guardado no basta.
    Inexistente o sin acceso → Prohibido (misma respuesta)."""
    archivo = repo.obtener_archivo(db, archivo_id)
    if not archivo:
        raise Prohibido()
    proyectos.obtener_autorizado(db, archivo["proyecto_id"], usuario_id)
    if archivo["retirado_en"]:
        raise NoEncontrado(MSG_ARCHIVO_RETIRADO)
    return _publico(archivo), almacen.leer(archivo["almacen"])


# --- Comentarios y archivos juntos (HU-05-003) ---

def actividad(db, proyecto_id: int, tarea_id: Optional[int] = None) -> list:
    """Comentarios y archivos del destino exacto en una sola línea de tiempo, en el orden en
    que se publicaron. Cada elemento lleva tipo 'comentario' o 'archivo' y conserva su autor:
    reasignar la tarea no cambia nada aquí."""
    elementos = ([{**c, "tipo": "comentario"} for c in comentarios(db, proyecto_id, tarea_id)]
                 + [{**a, "tipo_archivo": a["tipo"], "tipo": "archivo"} for a in archivos(db, proyecto_id, tarea_id)])
    return sorted(elementos, key=lambda e: (e["creado_en"], e["tipo"] == "archivo", e["id"]))
