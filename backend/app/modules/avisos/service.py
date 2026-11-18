"""Avisos dentro de la aplicación (HU-06-001, HU-06-003).

No importa FastAPI ni otros módulos. Las funciones que generan avisos no abren
transacción: se llaman dentro de la del cambio que los origina, así un cambio que
no se confirma no deja aviso y uno confirmado siempre lo tiene.
"""
from typing import Optional

from . import repository as repo

ASIGNACION = "asignacion"
BLOQUEO = "bloqueo"


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


def _con_estado(aviso: dict) -> dict:
    """bloqueo_resuelto como booleano; un aviso de bloqueo resuelto se conserva."""
    if aviso["bloqueo_resuelto"] is not None:
        aviso["bloqueo_resuelto"] = bool(aviso["bloqueo_resuelto"])
    return aviso


def mis_avisos(db, usuario_id: int) -> list:
    return [_con_estado(a) for a in repo.listar_de_usuario(db, usuario_id)]
