"""Endpoints de avisos. Solo llaman al servicio; cada persona ve y abre solo los suyos."""
from fastapi import APIRouter, Depends

from ...db.database import get_db
from ..acceso.deps import usuario_actual
from . import service

router = APIRouter(prefix="/api", tags=["avisos"])


@router.get("/avisos")
def mis_avisos(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.mis_avisos(db, u["id"])


@router.get("/avisos/resumen")
def resumen_avisos(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return {"no_leidos": service.no_leidos(db, u["id"])}


@router.post("/avisos/leer-todos")
def leer_todos(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return {"marcados": service.marcar_todos_leidos(db, u["id"])}


@router.post("/avisos/{aviso_id}/abrir")
def abrir_aviso(aviso_id: int, u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.abrir(db, aviso_id, u["id"])
