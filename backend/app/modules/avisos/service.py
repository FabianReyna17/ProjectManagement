"""Avisos dentro de la aplicación (HU-06-001 a HU-06-005).

No importa FastAPI ni otros módulos. Las funciones que generan avisos no abren
transacción: se llaman dentro de la del cambio que los origina, así un cambio que
no se confirma no deja aviso y uno confirmado siempre lo tiene.

Política de acceso (HU-06-005): un aviso nunca se borra. Si la persona ya no participa
en el proyecto, el aviso sigue en su lista pero sin datos del proyecto, la tarea ni quién
lo originó, y abrirlo no lleva a ningún recurso.
"""
from typing import Optional

from ...core.errors import Prohibido
from ...db.database import transaccion
from . import repository as repo

ASIGNACION = "asignacion"
BLOQUEO = "bloqueo"
VENCIMIENTO = "vencimiento"
CAMBIO_PLAN = "cambio_plan"
REASIGNACION = "reasignacion"

# Datos que solo se muestran con acceso vigente al proyecto
PROTEGIDOS = ("proyecto_id", "proyecto_nombre", "tarea_id", "tarea_nombre", "actor_id", "actor_nombre",
              "bloqueo_id", "bloqueo_motivo", "bloqueo_resuelto", "fecha_limite",
              "cambio_campo", "cambio_anterior", "cambio_nuevo", "cambio_nuevo_nombre")


def avisar_asignacion(db, proyecto_id: int, tarea_id: int, usuario_id: Optional[int],
                      actor_id: int, evento_id: int) -> None:
    """HU-06-001: la nueva persona responsable recibe un aviso con tarea, proyecto y fecha.
    Quien se asigna una tarea a sí mismo no recibe aviso de su propia acción."""
    if usuario_id is None or usuario_id == actor_id:
        return
    repo.insertar(db, usuario_id, ASIGNACION, proyecto_id, tarea_id, evento_id, actor_id)


def avisar_bloqueo(db, proyecto_id: int, tarea_id: int, responsable_proyecto_id: int,
                   actor_id: int, evento_id: int, bloqueo_id: int) -> None:
    """HU-06-003: el responsable del proyecto recibe un aviso que identifica la tarea bloqueada.
    Si él mismo reportó el bloqueo no se le avisa de su propia acción."""
    if responsable_proyecto_id == actor_id:
        return
    repo.insertar(db, responsable_proyecto_id, BLOQUEO, proyecto_id, tarea_id, evento_id, actor_id, bloqueo_id)


def avisar_cambio_plan(db, proyecto_id: int, tarea_id: int, usuario_id: Optional[int],
                       actor_id: int, evento_id: int) -> None:
    """HU-06-004: a la persona asignada le cambiaron la fecha límite o la prioridad de su tarea.
    El aviso apunta al evento del historial (qué cambió, valor anterior y nuevo); quien hizo
    el cambio no se avisa a sí mismo. Quien llama comprueba que la persona aún tenga acceso."""
    if usuario_id is None or usuario_id == actor_id:
        return
    repo.insertar(db, usuario_id, CAMBIO_PLAN, proyecto_id, tarea_id, evento_id, actor_id)


def avisar_reasignacion(db, proyecto_id: int, tarea_id: int, anterior_id: Optional[int],
                        actor_id: int, evento_id: int) -> None:
    """HU-06-004: a quien tenía la tarea le avisa que pasó a otra persona (o quedó sin asignar)."""
    if anterior_id is None or anterior_id == actor_id:
        return
    repo.insertar(db, anterior_id, REASIGNACION, proyecto_id, tarea_id, evento_id, actor_id)


def avisar_vencimiento(db, proyecto_id: int, tarea_id: int, usuario_id: int, fecha_limite: str) -> bool:
    """HU-06-002: la persona asignada recibe un aviso con la fecha límite vigente. Un mismo
    vencimiento (tarea + fecha) se le avisa una sola vez. True si se generó el aviso."""
    return repo.insertar_vencimiento(db, usuario_id, proyecto_id, tarea_id, fecha_limite)


def _publico(aviso: dict) -> dict:
    """Lo que la persona puede ver del aviso según su acceso vigente."""
    a = {k: v for k, v in aviso.items() if k not in ("usuario_id", "leido_en")}
    a["leido"] = aviso["leido_en"] is not None
    a["con_acceso"] = bool(aviso["con_acceso"])
    if not a["con_acceso"]:
        a.update(dict.fromkeys(PROTEGIDOS))
    elif a["bloqueo_resuelto"] is not None:
        a["bloqueo_resuelto"] = bool(a["bloqueo_resuelto"])  # resuelto: se conserva sin quedar pendiente
    return a


def mis_avisos(db, usuario_id: int) -> list:
    return [_publico(a) for a in repo.listar_de_usuario(db, usuario_id)]


def no_leidos(db, usuario_id: int) -> int:
    return repo.contar_no_leidos(db, usuario_id)


def abrir(db, aviso_id: int, usuario_id: int) -> dict:
    """Marca el aviso como leído y dice a dónde lleva: la tarea (o el proyecto) si el acceso
    sigue vigente; si no, ningún destino. El aviso de otra persona o inexistente → Prohibido."""
    aviso = repo.obtener(db, aviso_id)
    if not aviso or aviso["usuario_id"] != usuario_id:
        raise Prohibido()
    with transaccion(db):
        repo.marcar_leido(db, aviso_id)
    a = _publico({**aviso, "leido_en": aviso["leido_en"] or "ahora"})
    destino = None
    if a["con_acceso"]:
        destino = ({"tipo": "tarea", "id": a["tarea_id"]} if a["tarea_id"]
                   else {"tipo": "proyecto", "id": a["proyecto_id"]})
    return {**a, "destino": destino}


def marcar_todos_leidos(db, usuario_id: int) -> int:
    with transaccion(db):
        return repo.marcar_todos_leidos(db, usuario_id)
