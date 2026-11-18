"""Endpoints de autenticación y cuentas. Solo validan la entrada y llaman al servicio."""
from typing import Optional

from fastapi import APIRouter, Depends

from ...core.cabeceras import clave_idempotencia
from ...db.database import get_db
from . import service
from .deps import requiere_funcion, sesion_actual
from .schemas import FuncionIn, LoginIn, PasswordIn, UsuarioIn

router = APIRouter(prefix="/api")


# --- Sesión (HU-01-003, HU-01-004) ---

@router.post("/auth/login", tags=["auth"])
def login(data: LoginIn, db=Depends(get_db)):
    return service.iniciar_sesion(db, data.usuario, data.password)


@router.post("/auth/logout", tags=["auth"])
def logout(u: dict = Depends(sesion_actual), db=Depends(get_db)):
    service.cerrar_sesion(db, u["token"])
    return {"mensaje": "Sesión cerrada"}


@router.get("/auth/me", tags=["auth"])
def me(u: dict = Depends(sesion_actual)):
    return {k: u[k] for k in ("id", "usuario", "nombre", "funcion", "debe_cambiar_password")}


@router.post("/auth/password", tags=["auth"])
def cambiar_password(data: PasswordIn, u: dict = Depends(sesion_actual), db=Depends(get_db)):
    """Cambiar la propia contraseña; obligatorio tras un restablecimiento (HU-01-011)."""
    service.cambiar_password(db, u, data.actual, data.nueva)
    return {"mensaje": "Contraseña actualizada"}


# --- Cuentas y funciones (HU-01-001, HU-01-002) ---

@router.get("/funciones", tags=["usuarios"])
def listar_funciones(_=Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    return service.listar_funciones(db)


@router.get("/usuarios", tags=["usuarios"])
def listar_usuarios(todas: bool = False, u: dict = Depends(requiere_funcion("Admin", "Responsable")),
                    db=Depends(get_db)):
    """Cuentas activas; ?todas=1 incluye las desactivadas (solo Admin, HU-01-009)."""
    return service.listar_usuarios(db, todas, u["funcion"])


@router.post("/usuarios", status_code=201, tags=["usuarios"])
def registrar_usuario(data: UsuarioIn, u: dict = Depends(requiere_funcion("Admin")),
                      clave=Depends(clave_idempotencia), db=Depends(get_db)):
    return service.registrar_usuario(db, data.usuario, data.nombre, data.password, data.funcion_id, u["id"], clave)


# --- Mantenimiento de cuentas (HU-01-008, HU-01-009, HU-01-011) ---

@router.post("/usuarios/{usuario_id}/desactivacion", tags=["usuarios"])
def desactivar_cuenta(usuario_id: int, u: dict = Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    return service.desactivar_cuenta(db, usuario_id, u["id"])


@router.put("/usuarios/{usuario_id}/funcion", tags=["usuarios"])
def cambiar_funcion(usuario_id: int, data: FuncionIn, u: dict = Depends(requiere_funcion("Admin")),
                    db=Depends(get_db)):
    return service.cambiar_funcion(db, usuario_id, data.funcion_id, u["id"])


@router.post("/usuarios/{usuario_id}/restablecimiento", tags=["usuarios"])
def restablecer_acceso(usuario_id: int, u: dict = Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    return service.restablecer_acceso(db, usuario_id, u["id"])


# --- Historial de cambios de acceso (HU-01-010) ---

@router.get("/cambios-acceso", tags=["usuarios"])
def historial_accesos(usuario_id: Optional[int] = None, proyecto_id: Optional[int] = None,
                      u: dict = Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    return service.historial_accesos(db, u["funcion"], usuario_id, proyecto_id)
