"""Endpoints de proyectos y participantes. Solo validan la entrada y llaman al servicio."""
from fastapi import APIRouter, Depends

from ...db.database import get_db
from ..acceso.deps import requiere_funcion, usuario_actual
from . import service
from .deps import proyecto_autorizado
from .schemas import ParticipanteIn, ProyectoIn

router = APIRouter(prefix="/api/proyectos", tags=["proyectos"])


@router.get("")
def mis_proyectos(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.mis_proyectos(db, u["id"])


@router.post("", status_code=201)
def crear_proyecto(data: ProyectoIn, u: dict = Depends(requiere_funcion("Admin", "Responsable")), db=Depends(get_db)):
    return service.crear(db, u["id"], data.nombre, data.objetivo, data.responsable_id,
                         data.fecha_inicio, data.fecha_fin)


@router.get("/{proyecto_id}")
def ficha_proyecto(proyecto: dict = Depends(proyecto_autorizado), u: dict = Depends(usuario_actual)):
    return service.ficha(proyecto, u["id"])


@router.get("/{proyecto_id}/participantes")
def listar_participantes(proyecto: dict = Depends(proyecto_autorizado), db=Depends(get_db)):
    return service.listar_participantes(db, proyecto)


@router.post("/{proyecto_id}/participantes", status_code=201)
def agregar_participante(data: ParticipanteIn, proyecto: dict = Depends(proyecto_autorizado),
                         u: dict = Depends(usuario_actual), db=Depends(get_db)):
    service.agregar_participante(db, proyecto, u["id"], data.usuario_id)
    return {"mensaje": "Participante agregado"}


@router.delete("/{proyecto_id}/participantes/{usuario_id}")
def retirar_participante(usuario_id: int, proyecto: dict = Depends(proyecto_autorizado),
                         u: dict = Depends(usuario_actual), db=Depends(get_db)):
    service.retirar_participante(db, proyecto, u["id"], usuario_id)
    return {"mensaje": "Participante retirado"}
