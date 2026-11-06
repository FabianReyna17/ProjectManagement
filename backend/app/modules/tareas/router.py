"""Endpoints de tareas. Solo validan la entrada y llaman al servicio."""
from fastapi import APIRouter, Depends

from ...db.database import get_db
from ..acceso.deps import usuario_actual
from ..proyectos.deps import proyecto_autorizado
from . import service
from .deps import tarea_autorizada
from .schemas import BloqueoIn, EstadoIn, PlanificacionIn, ResolucionIn, ResponsableIn, TareaIn

router = APIRouter(prefix="/api", tags=["tareas"])


@router.post("/proyectos/{proyecto_id}/tareas", status_code=201)
def crear_tarea(data: TareaIn, proyecto: dict = Depends(proyecto_autorizado),
                u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.crear(db, proyecto, u["id"], data.nombre, data.descripcion, data.resultado_esperado,
                         data.responsable_id, data.fecha_limite, data.prioridad)


@router.get("/proyectos/{proyecto_id}/tareas")
def tareas_del_proyecto(proyecto: dict = Depends(proyecto_autorizado), db=Depends(get_db)):
    return service.listar_de_proyecto(db, proyecto)


@router.get("/mis-tareas")
def mis_tareas(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.mis_tareas(db, u["id"])


@router.get("/tareas/{tarea_id}")
def detalle_tarea(tarea: dict = Depends(tarea_autorizada), u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.con_bloqueo(db, tarea, u["id"])


@router.put("/tareas/{tarea_id}/responsable")
def asignar_responsable(data: ResponsableIn, tarea: dict = Depends(tarea_autorizada),
                        u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.asignar(db, tarea, u["id"], data.usuario_id)


@router.put("/tareas/{tarea_id}/planificacion")
def planificar_tarea(data: PlanificacionIn, tarea: dict = Depends(tarea_autorizada),
                     u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.planificar(db, tarea, u["id"], data.fecha_limite, data.prioridad)


@router.put("/tareas/{tarea_id}/estado")
def cambiar_estado(data: EstadoIn, tarea: dict = Depends(tarea_autorizada),
                   u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.cambiar_estado(db, tarea, u["id"], data.estado)


@router.post("/tareas/{tarea_id}/bloqueos", status_code=201)
def registrar_bloqueo(data: BloqueoIn, tarea: dict = Depends(tarea_autorizada),
                      u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.registrar_bloqueo(db, tarea, u["id"], data.motivo)


@router.get("/tareas/{tarea_id}/bloqueos")
def bloqueos_de_tarea(tarea: dict = Depends(tarea_autorizada), db=Depends(get_db)):
    return service.bloqueos(db, tarea)


@router.post("/tareas/{tarea_id}/bloqueos/{bloqueo_id}/resolver")
def resolver_bloqueo(bloqueo_id: int, data: ResolucionIn, tarea: dict = Depends(tarea_autorizada),
                     u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.resolver_bloqueo(db, tarea, u["id"], bloqueo_id, data.resolucion)


@router.get("/tareas/{tarea_id}/historial")
def historial_tarea(tarea: dict = Depends(tarea_autorizada), db=Depends(get_db)):
    return service.historial(db, tarea)
