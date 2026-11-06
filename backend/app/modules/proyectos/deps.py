from fastapi import Depends

from ...db.database import get_db
from ..acceso.deps import usuario_actual
from . import service


def proyecto_autorizado(proyecto_id: int, u: dict = Depends(usuario_actual), db=Depends(get_db)) -> dict:
    """Proyecto de la ruta, solo si el usuario actual participa (si no → 403)."""
    return service.obtener_autorizado(db, proyecto_id, u["id"])
