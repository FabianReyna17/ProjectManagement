"""Reglas de tareas (HU-03-001).

No importa FastAPI. Para proyectos y cuentas usa sus servicios, nunca sus repositorios.
Planificar (crear, asignar, fechar) es exclusivo del responsable del proyecto.
"""
from typing import Optional

from ...core.errors import Prohibido
from ...db.database import transaccion
from ..proyectos import service as proyectos
from . import repository as repo


def crear(db, proyecto: dict, actor_id: int, nombre: str, descripcion: str,
          resultado_esperado: Optional[str]) -> dict:
    proyectos.exigir_responsable(proyecto, actor_id)
    with transaccion(db):
        tid = repo.insertar(db, proyecto["id"], nombre, descripcion, resultado_esperado or None, actor_id)
    return repo.obtener(db, tid)


def obtener_autorizada(db, tarea_id: int, usuario_id: int) -> dict:
    """Tarea si el usuario participa en su proyecto. Si no existe o no participa → Prohibido."""
    tarea = repo.obtener(db, tarea_id)
    if not tarea:
        raise Prohibido()
    proyecto = proyectos.obtener_autorizado(db, tarea["proyecto_id"], usuario_id)
    return {**tarea, "proyecto_responsable_id": proyecto["responsable_id"]}


def detalle(tarea: dict, usuario_id: int) -> dict:
    return {**tarea, "puedo_planificar": tarea["proyecto_responsable_id"] == usuario_id}
