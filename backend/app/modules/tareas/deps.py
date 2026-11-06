from fastapi import Depends

from ...db.database import get_db
from ..acceso.deps import usuario_actual
from . import service


def tarea_autorizada(tarea_id: int, u: dict = Depends(usuario_actual), db=Depends(get_db)) -> dict:
    """Tarea de la ruta, solo si el usuario participa en su proyecto (si no → 403)."""
    return service.obtener_autorizada(db, tarea_id, u["id"])
