"""Endpoints de comentarios de proyectos y tareas. Solo validan la entrada y llaman al servicio."""
from fastapi import APIRouter, Depends

from ...core.cabeceras import clave_idempotencia
from ...db.database import get_db
from ..acceso.deps import usuario_actual
from ..proyectos.deps import proyecto_autorizado
from ..tareas.deps import tarea_autorizada
from . import service
from .schemas import ComentarioIn

router = APIRouter(prefix="/api", tags=["colaboración"])


@router.post("/proyectos/{proyecto_id}/comentarios", status_code=201)
def comentar_proyecto(data: ComentarioIn, proyecto: dict = Depends(proyecto_autorizado),
                      u: dict = Depends(usuario_actual), clave=Depends(clave_idempotencia), db=Depends(get_db)):
    return service.comentar(db, proyecto["id"], None, u["id"], data.texto, clave)


@router.get("/proyectos/{proyecto_id}/comentarios")
def comentarios_proyecto(proyecto: dict = Depends(proyecto_autorizado), db=Depends(get_db)):
    return service.comentarios(db, proyecto["id"])


@router.post("/tareas/{tarea_id}/comentarios", status_code=201)
def comentar_tarea(data: ComentarioIn, tarea: dict = Depends(tarea_autorizada),
                   u: dict = Depends(usuario_actual), clave=Depends(clave_idempotencia), db=Depends(get_db)):
    return service.comentar(db, tarea["proyecto_id"], tarea["id"], u["id"], data.texto, clave)


@router.get("/tareas/{tarea_id}/comentarios")
def comentarios_tarea(tarea: dict = Depends(tarea_autorizada), db=Depends(get_db)):
    return service.comentarios(db, tarea["proyecto_id"], tarea["id"])
