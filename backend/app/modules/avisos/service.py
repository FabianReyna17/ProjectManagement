"""Avisos dentro de la aplicación (HU-06-001).

No importa FastAPI ni otros módulos. Las funciones que generan avisos no abren
transacción: se llaman dentro de la del cambio que los origina, así un cambio que
no se confirma no deja aviso y uno confirmado siempre lo tiene.
"""
from typing import Optional

from . import repository as repo

ASIGNACION = "asignacion"


def avisar_asignacion(db, proyecto_id: int, tarea_id: int, usuario_id: Optional[int],
                      actor_id: int, evento_id: int) -> None:
    """HU-06-001: la nueva persona responsable recibe un aviso con tarea, proyecto y fecha.
    Quien se asigna una tarea a sí mismo no recibe aviso de su propia acción."""
    if usuario_id is None or usuario_id == actor_id:
        return
    repo.insertar(db, usuario_id, ASIGNACION, proyecto_id, tarea_id, evento_id, actor_id)


def mis_avisos(db, usuario_id: int) -> list:
    return repo.listar_de_usuario(db, usuario_id)
