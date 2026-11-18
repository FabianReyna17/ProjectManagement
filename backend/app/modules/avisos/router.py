"""Endpoints de avisos. Solo llaman al servicio."""
from fastapi import APIRouter, Depends

from ...db.database import get_db
from ..acceso.deps import usuario_actual
from . import service

router = APIRouter(prefix="/api", tags=["avisos"])


@router.get("/avisos")
def mis_avisos(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    return service.mis_avisos(db, u["id"])
