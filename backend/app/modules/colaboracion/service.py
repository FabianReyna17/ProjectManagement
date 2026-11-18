"""Comentarios de proyectos y tareas (HU-05-001).

No importa FastAPI. El proyecto o la tarea llegan ya autorizados (participación activa,
comprobada en cada petición), así que quien perdió el acceso no puede leer ni publicar,
aunque use un enlace directo. Cualquier participante puede comentar.
"""
from typing import Optional

from ...db.idempotencia import crear_una_vez
from . import repository as repo


def comentar(db, proyecto_id: int, tarea_id: Optional[int], autor_id: int, texto: str,
             clave: Optional[str] = None) -> dict:
    """Guarda el comentario con autor y fecha. Un reintento con la misma clave no lo duplica."""
    cid = crear_una_vez(db, autor_id, clave, "comentario",
                        lambda: repo.insertar_comentario(db, proyecto_id, tarea_id, texto, autor_id))
    return repo.obtener_comentario(db, cid)


def comentarios(db, proyecto_id: int, tarea_id: Optional[int] = None) -> list:
    return repo.listar_comentarios(db, proyecto_id, tarea_id)
