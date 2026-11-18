"""Endpoints de autenticación y cuentas. Solo validan la entrada y llaman al servicio."""
from fastapi import APIRouter, Depends

from ...core.cabeceras import clave_idempotencia
from ...db.database import get_db
from . import service
from .deps import requiere_funcion, usuario_actual
from .schemas import LoginIn, UsuarioIn

router = APIRouter(prefix="/api")


# --- Sesión (HU-01-003, HU-01-004) ---

@router.post("/auth/login", tags=["auth"])
def login(data: LoginIn, db=Depends(get_db)):
    return service.iniciar_sesion(db, data.usuario, data.password)


@router.post("/auth/logout", tags=["auth"])
def logout(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    service.cerrar_sesion(db, u["token"])
    return {"mensaje": "Sesión cerrada"}


@router.get("/auth/me", tags=["auth"])
def me(u: dict = Depends(usuario_actual)):
    return {k: u[k] for k in ("id", "usuario", "nombre", "funcion")}


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


# --- Mantenimiento de cuentas (HU-01-009) ---

@router.post("/usuarios/{usuario_id}/desactivacion", tags=["usuarios"])
def desactivar_cuenta(usuario_id: int, u: dict = Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    return service.desactivar_cuenta(db, usuario_id, u["id"])
