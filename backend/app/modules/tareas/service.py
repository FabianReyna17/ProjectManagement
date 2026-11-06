"""Reglas de tareas (HU-03-001 a HU-03-005, HU-04-001).

No importa FastAPI. Para proyectos y cuentas usa sus servicios, nunca sus repositorios.
Planificar (crear, asignar, fechar) es exclusivo del responsable del proyecto.
Todo cambio del plan queda en el historial con valor anterior, nuevo y actor.
"""
from datetime import date
from typing import Optional

from ...core.errors import DatosInvalidos, Prohibido
from ...db.database import transaccion
from ..acceso import service as acceso
from ..proyectos import service as proyectos
from . import repository as repo

MSG_RESPONSABLE = "El responsable debe ser una cuenta activa con acceso al proyecto"
MSG_ESTADO_PERMISO = "Solo la persona asignada o el responsable del proyecto pueden cambiar el estado"

NOMBRE_ESTADO = {"pendiente": "Pendiente", "en_curso": "En curso", "terminada": "Terminada"}
# Transiciones permitidas (HU-04-001). Terminar requiere haber iniciado; una terminada se puede reabrir.
TRANSICIONES = {
    "pendiente": {"en_curso"},
    "en_curso": {"pendiente", "terminada"},
    "terminada": {"en_curso"},
}


def _validar_responsable(db, proyecto_id: int, usuario_id: int) -> None:
    if not acceso.cuenta_activa(db, usuario_id) or not proyectos.es_participante(db, proyecto_id, usuario_id):
        raise DatosInvalidos(MSG_RESPONSABLE)


def _exigir_planificador(tarea: dict, actor_id: int) -> None:
    if tarea["proyecto_responsable_id"] != actor_id:
        raise Prohibido()


def _iso(fecha: Optional[date]) -> Optional[str]:
    return fecha.isoformat() if fecha else None


def crear(db, proyecto: dict, actor_id: int, nombre: str, descripcion: str,
          resultado_esperado: Optional[str], responsable_id: Optional[int] = None,
          fecha_limite: Optional[date] = None, prioridad: str = "media") -> dict:
    proyectos.exigir_responsable(proyecto, actor_id)
    if responsable_id is not None:
        _validar_responsable(db, proyecto["id"], responsable_id)
    with transaccion(db):
        tid = repo.insertar(db, proyecto["id"], nombre, descripcion, resultado_esperado or None,
                            responsable_id, _iso(fecha_limite), prioridad, actor_id)
        if responsable_id is not None:
            repo.registrar_cambio(db, tid, "responsable", None, responsable_id, actor_id)
    return repo.obtener(db, tid)


def obtener_autorizada(db, tarea_id: int, usuario_id: int) -> dict:
    """Tarea si el usuario participa en su proyecto. Si no existe o no participa → Prohibido."""
    tarea = repo.obtener(db, tarea_id)
    if not tarea:
        raise Prohibido()
    proyecto = proyectos.obtener_autorizado(db, tarea["proyecto_id"], usuario_id)
    return {**tarea, "proyecto_responsable_id": proyecto["responsable_id"]}


def _puede_cambiar_estado(tarea: dict, usuario_id: int) -> bool:
    return usuario_id in (tarea["responsable_id"], tarea["proyecto_responsable_id"])


def detalle(tarea: dict, usuario_id: int) -> dict:
    puede = _puede_cambiar_estado(tarea, usuario_id)
    return {**tarea,
            "puedo_planificar": tarea["proyecto_responsable_id"] == usuario_id,
            "soy_asignado": tarea["responsable_id"] == usuario_id,
            "transiciones": sorted(TRANSICIONES[tarea["estado"]]) if puede else []}


def listar_de_proyecto(db, proyecto: dict) -> list:
    """HU-03-005: tareas del proyecto (ya autorizado); responsable_id null = sin asignar."""
    return repo.listar_de_proyecto(db, proyecto["id"])


def mis_tareas(db, usuario_id: int) -> list:
    """HU-03-004: al reasignar la tarea o perder acceso al proyecto deja de aparecer."""
    return repo.listar_asignadas(db, usuario_id)


def asignar(db, tarea: dict, actor_id: int, usuario_id: int) -> dict:
    """HU-03-002: si la validación falla no se toca al responsable anterior."""
    _exigir_planificador(tarea, actor_id)
    _validar_responsable(db, tarea["proyecto_id"], usuario_id)
    if tarea["responsable_id"] != usuario_id:
        with transaccion(db):
            repo.actualizar_responsable(db, tarea["id"], usuario_id)
            repo.registrar_cambio(db, tarea["id"], "responsable", tarea["responsable_id"], usuario_id, actor_id)
    return detalle(obtener_autorizada(db, tarea["id"], actor_id), actor_id)


def planificar(db, tarea: dict, actor_id: int, fecha_limite: Optional[date], prioridad: str) -> dict:
    """HU-03-003: fecha límite (puede quedar sin fecha) y prioridad. Cada valor que cambia
    se registra con su valor anterior. La validación de formato y catálogo la hace el esquema."""
    _exigir_planificador(tarea, actor_id)
    nueva_fecha = _iso(fecha_limite)
    cambios = [(campo, tarea[campo], nuevo)
               for campo, nuevo in (("fecha_limite", nueva_fecha), ("prioridad", prioridad))
               if tarea[campo] != nuevo]
    if cambios:
        with transaccion(db):
            repo.actualizar_plan(db, tarea["id"], nueva_fecha, prioridad)
            for campo, anterior, nuevo in cambios:
                repo.registrar_cambio(db, tarea["id"], campo, anterior, nuevo, actor_id)
    return detalle(obtener_autorizada(db, tarea["id"], actor_id), actor_id)


def cambiar_estado(db, tarea: dict, actor_id: int, estado: str) -> dict:
    """HU-04-001: solo transiciones permitidas, por la persona asignada o el responsable del proyecto.
    Repetir el mismo estado no hace nada (un reintento no duplica el historial)."""
    if not _puede_cambiar_estado(tarea, actor_id):
        raise Prohibido(MSG_ESTADO_PERMISO)
    actual = tarea["estado"]
    if estado != actual:
        if estado not in TRANSICIONES[actual]:
            raise DatosInvalidos(f"No se puede pasar de «{NOMBRE_ESTADO[actual]}» a «{NOMBRE_ESTADO[estado]}»")
        with transaccion(db):
            repo.actualizar_estado(db, tarea["id"], estado)
            repo.registrar_cambio(db, tarea["id"], "estado", actual, estado, actor_id)
    return detalle(obtener_autorizada(db, tarea["id"], actor_id), actor_id)


def historial(db, tarea: dict) -> list:
    return repo.listar_historial(db, tarea["id"])
