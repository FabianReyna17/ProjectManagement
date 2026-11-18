"""Respaldos (HU-08-004): estado e historial, y respaldo inmediato. Solo Admin."""
from fastapi import APIRouter, Depends

from ...db.database import get_db
from ..acceso.deps import requiere_funcion
from . import service

router = APIRouter(prefix="/api", tags=["respaldos"])


@router.get("/respaldos")
def estado(u: dict = Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    return service.estado(db, u["funcion"])


@router.post("/respaldos", status_code=201)
def respaldar_ahora(u: dict = Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    return service.respaldar_ahora(db, u)
