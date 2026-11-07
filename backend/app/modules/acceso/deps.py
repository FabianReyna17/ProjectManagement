"""Dependencias de autenticación y autorización por función.

Regla: denegar por defecto. Todo endpoint (salvo login) exige usuario_actual,
y los permisos se consultan en la BD en cada petición, por lo que un cambio de
permisos aplica aunque la sesión ya esté abierta.
"""
from typing import Optional

from fastapi import Depends, Header

from ...core.errors import NoAutenticado, Prohibido
from ...db.database import get_db
from . import service


def usuario_actual(authorization: Optional[str] = Header(None), db=Depends(get_db)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise NoAutenticado(service.MSG_SESION)
    return service.sesion_vigente(db, authorization[7:])


def requiere_funcion(*funciones: str):
    def dep(u: dict = Depends(usuario_actual)) -> dict:
        if u["funcion"] not in funciones:
            raise Prohibido()
        return u
    return dep
