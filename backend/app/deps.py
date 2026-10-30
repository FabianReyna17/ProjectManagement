"""Dependencias comunes: conexión a BD, usuario autenticado y autorización.

Regla: denegar por defecto. Todo endpoint (salvo login) exige usuario_actual,
y los permisos se consultan en la BD en cada petición, por lo que un cambio de
permisos aplica aunque la sesión ya esté abierta.
"""
from typing import Optional

from fastapi import Depends, Header, HTTPException

from .database import get_conn

MSG_PROHIBIDO = "No tienes permiso para realizar esta acción"


def prohibido() -> HTTPException:
    return HTTPException(status_code=403, detail=MSG_PROHIBIDO)


def get_db():
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()


def usuario_actual(authorization: Optional[str] = Header(None), db=Depends(get_db)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesión no válida")
    token = authorization[7:]
    row = db.execute(
        """SELECT u.id, u.usuario, u.nombre, u.activo, f.nombre AS funcion
           FROM sesiones s
           JOIN usuarios u  ON u.id = s.usuario_id
           JOIN funciones f ON f.id = u.funcion_id
           WHERE s.token = ?""",
        (token,),
    ).fetchone()
    if not row or not row["activo"]:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    return {**dict(row), "token": token}


def requiere_funcion(*funciones: str):
    def dep(u: dict = Depends(usuario_actual)) -> dict:
        if u["funcion"] not in funciones:
            raise prohibido()
        return u
    return dep


def es_participante(db, proyecto_id: int, usuario_id: int) -> bool:
    return db.execute(
        "SELECT 1 FROM participantes WHERE proyecto_id=? AND usuario_id=? AND activo=1",
        (proyecto_id, usuario_id),
    ).fetchone() is not None


def proyecto_autorizado(proyecto_id: int, u: dict = Depends(usuario_actual), db=Depends(get_db)) -> dict:
    """Devuelve el proyecto si el usuario participa; si no existe o no participa → 403
    (misma respuesta en ambos casos para no revelar qué proyectos existen)."""
    if not es_participante(db, proyecto_id, u["id"]):
        raise prohibido()
    row = db.execute(
        """SELECT p.*, r.nombre AS responsable_nombre
           FROM proyectos p JOIN usuarios r ON r.id = p.responsable_id
           WHERE p.id = ?""",
        (proyecto_id,),
    ).fetchone()
    if not row:
        raise prohibido()
    return dict(row)
