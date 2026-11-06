"""Reglas de cuentas, funciones y sesiones (HU-01-001 a HU-01-004).

No importa FastAPI: se puede probar sin peticiones HTTP. Abre y cierra la
transacción; los repositorios no hacen commit.
"""
from typing import Optional

from ...core.errors import Conflicto, DatosInvalidos, NoAutenticado
from ...core.security import hash_password, nuevo_token, verificar_password
from ...db.database import transaccion
from . import repository as repo

MSG_LOGIN = "Usuario o contraseña incorrectos"
FUNCIONES_RESPONSABLE = ("Admin", "Responsable")


def usuario_por_token(db, token: str) -> Optional[dict]:
    """Cuenta dueña de la sesión, o None si la sesión no existe o la cuenta está inactiva."""
    row = repo.buscar_por_token(db, token)
    if not row or not row["activo"]:
        return None
    return {**dict(row), "token": token}


def iniciar_sesion(db, usuario: str, password: str) -> dict:
    row = repo.buscar_por_usuario(db, usuario)
    # Mensaje genérico: no revela si el usuario existe o está inactivo
    if not row or not row["activo"] or not verificar_password(password, row["password_hash"]):
        raise NoAutenticado(MSG_LOGIN)
    token = nuevo_token()
    with transaccion(db):
        repo.crear_sesion(db, token, row["id"])
    return {
        "token": token,
        "usuario": {"id": row["id"], "usuario": row["usuario"], "nombre": row["nombre"], "funcion": row["funcion"]},
    }


def cerrar_sesion(db, token: str) -> None:
    with transaccion(db):
        repo.borrar_sesion(db, token)


def listar_funciones(db) -> list:
    return repo.listar_funciones(db)


def listar_usuarios(db) -> list:
    return repo.listar_usuarios_activos(db)


def registrar_usuario(db, usuario: str, nombre: str, password: str, funcion_id: int) -> dict:
    if not repo.existe_funcion(db, funcion_id):
        raise DatosInvalidos("La función seleccionada no existe")
    try:
        with transaccion(db):
            nuevo_id = repo.insertar_usuario(db, usuario, nombre, hash_password(password), funcion_id)
    except repo.UsuarioDuplicado:
        raise Conflicto("El identificador de usuario ya existe")
    return {"id": nuevo_id, "usuario": usuario, "nombre": nombre, "activo": True}


# --- Consultas que usan otros módulos (nunca acceden a este repositorio directamente) ---

def cuenta_activa(db, usuario_id: int) -> bool:
    return repo.es_cuenta_activa(db, usuario_id)


def puede_ser_responsable(db, usuario_id: int) -> bool:
    return repo.tiene_funcion_activa(db, usuario_id, FUNCIONES_RESPONSABLE)
