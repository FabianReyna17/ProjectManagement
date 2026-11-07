"""Reglas de cuentas, funciones y sesiones (HU-01-001 a HU-01-004).

No importa FastAPI: se puede probar sin peticiones HTTP. Abre y cierra la
transacción; los repositorios no hacen commit.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from ...core.errors import Conflicto, DatosInvalidos, DemasiadosIntentos, NoAutenticado
from ...core.intentos import Intentos
from ...core.security import hash_password, nuevo_token, verificar_password
from ...db.database import transaccion
from ...db.idempotencia import crear_una_vez
from . import repository as repo

MSG_LOGIN = "Usuario o contraseña incorrectos"
MSG_SESION = "Tu sesión ya no es válida. Vuelve a iniciar sesión"
MSG_EXPIRADA = "Tu sesión expiró por inactividad. Vuelve a iniciar sesión"
FUNCIONES_RESPONSABLE = ("Admin", "Responsable")

# La sesión expira tras este tiempo sin peticiones (por defecto, una jornada de 8 h)
INACTIVIDAD = timedelta(minutes=int(os.getenv("SESION_INACTIVIDAD_MIN", "480")))
TOQUE = timedelta(minutes=1)  # ultimo_uso se actualiza como mucho una vez por minuto

INTENTOS = Intentos()
# Se verifica contra este hash cuando la cuenta no existe: el tiempo de respuesta no la delata
HASH_FICTICIO = hash_password(nuevo_token())


def _ahora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _texto(momento: datetime) -> str:
    return momento.strftime("%Y-%m-%d %H:%M:%S")


def sesion_vigente(db, token: str) -> dict:
    """Cuenta dueña de la sesión. Sesión inexistente, cuenta inactiva o inactividad
    mayor a INACTIVIDAD → NoAutenticado (la sesión vencida se borra)."""
    row = repo.buscar_por_token(db, token)
    if not row or not row["activo"]:
        raise NoAutenticado(MSG_SESION)
    ahora = _ahora()
    ultimo = datetime.fromisoformat(row["ultimo_uso"])
    if ahora - ultimo > INACTIVIDAD:
        with transaccion(db):
            repo.borrar_sesion(db, token)
        raise NoAutenticado(MSG_EXPIRADA)
    if ahora - ultimo > TOQUE:
        with transaccion(db):
            repo.tocar_sesion(db, token, _texto(ahora))
    datos = {k: row[k] for k in ("id", "usuario", "nombre", "activo", "funcion")}
    return {**datos, "token": token}


def usuario_por_token(db, token: str) -> Optional[dict]:
    """Igual que sesion_vigente, pero devuelve None en lugar de lanzar el error."""
    try:
        return sesion_vigente(db, token)
    except NoAutenticado:
        return None


def iniciar_sesion(db, usuario: str, password: str) -> dict:
    clave = usuario.casefold()
    espera = INTENTOS.espera(clave)
    if espera:
        raise DemasiadosIntentos(f"Demasiados intentos fallidos. Espera {espera} s y vuelve a intentarlo")
    row = repo.buscar_por_usuario(db, usuario)
    valida = verificar_password(password, row["password_hash"] if row else HASH_FICTICIO)
    # Mensaje genérico: no revela si el usuario existe o está inactivo
    if not row or not row["activo"] or not valida:
        INTENTOS.fallo(clave)
        raise NoAutenticado(MSG_LOGIN)
    INTENTOS.exito(clave)
    token = nuevo_token()
    ahora = _ahora()
    with transaccion(db):
        repo.borrar_sesiones_inactivas(db, _texto(ahora - INACTIVIDAD))
        repo.crear_sesion(db, token, row["id"], _texto(ahora))
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


def registrar_usuario(db, usuario: str, nombre: str, password: str, funcion_id: int,
                      actor_id: Optional[int] = None, clave: Optional[str] = None) -> dict:
    """HU-01-001. Con clave (HU-08-002) el reintento devuelve la cuenta ya creada
    en lugar de responder que el identificador existe."""
    if not repo.existe_funcion(db, funcion_id):
        raise DatosInvalidos("La función seleccionada no existe")

    def insertar() -> int:
        return repo.insertar_usuario(db, usuario, nombre, hash_password(password), funcion_id)

    try:
        nuevo_id = crear_una_vez(db, actor_id, clave, "usuario", insertar)
    except repo.UsuarioDuplicado:
        raise Conflicto("El identificador de usuario ya existe")
    cuenta = repo.obtener_usuario(db, nuevo_id)
    return {**cuenta, "activo": bool(cuenta["activo"])}


# --- Consultas que usan otros módulos (nunca acceden a este repositorio directamente) ---

def cuenta_activa(db, usuario_id: int) -> bool:
    return repo.es_cuenta_activa(db, usuario_id)


def puede_ser_responsable(db, usuario_id: int) -> bool:
    return repo.tiene_funcion_activa(db, usuario_id, FUNCIONES_RESPONSABLE)
