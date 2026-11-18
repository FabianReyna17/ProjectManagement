"""Reglas de cuentas, funciones y sesiones (HU-01-001 a HU-01-004 y HU-01-008 a HU-01-011).

No importa FastAPI: se puede probar sin peticiones HTTP. Abre y cierra la
transacción; los repositorios no hacen commit.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from ...core.errors import Conflicto, DatosInvalidos, DemasiadosIntentos, NoAutenticado, NoEncontrado, Prohibido
from ...core.intentos import Intentos
from ...core.security import hash_password, nuevo_token, verificar_password
from ...db.database import transaccion
from ...db.idempotencia import crear_una_vez
from . import repository as repo

MSG_LOGIN = "Usuario o contraseña incorrectos"
MSG_SESION = "Tu sesión ya no es válida. Vuelve a iniciar sesión"
MSG_EXPIRADA = "Tu sesión expiró por inactividad. Vuelve a iniciar sesión"
MSG_CAMBIO = "Debes cambiar tu contraseña temporal antes de continuar"
FUNCIONES_RESPONSABLE = ("Admin", "Responsable")

# La sesión expira tras este tiempo sin peticiones (por defecto, una jornada de 8 h)
INACTIVIDAD = timedelta(minutes=int(os.getenv("SESION_INACTIVIDAD_MIN", "480")))
TOQUE = timedelta(minutes=1)  # ultimo_uso se actualiza como mucho una vez por minuto

INTENTOS = Intentos()
LARGO_TEMPORAL = 12
ALFABETO_TEMPORAL = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O ni 1/l/I


class CambioPendiente(Prohibido):
    """HU-01-011: la cuenta entró con una contraseña temporal y aún no la cambia (403)."""

    def __init__(self):
        super().__init__(MSG_CAMBIO)
        self.datos = {"cambiar_password": True}
# Se verifica contra este hash cuando la cuenta no existe: el tiempo de respuesta no la delata
HASH_FICTICIO = hash_password(nuevo_token())


def _ahora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _texto(momento: datetime) -> str:
    return momento.strftime("%Y-%m-%d %H:%M:%S")


def password_correcta(password: str, guardado: str) -> bool:
    """Antes de la v1 las contraseñas se recortaban al guardarse: si la escrita tiene espacios
    al inicio o al final y no coincide, se prueba también recortada (cuentas anteriores)."""
    if verificar_password(password, guardado):
        return True
    return password != password.strip() and verificar_password(password.strip(), guardado)


def validar_password_nueva(password: str) -> None:
    if not password.strip():
        raise DatosInvalidos("La contraseña no puede ser solo espacios")


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
    return {**datos, "debe_cambiar_password": bool(row["debe_cambiar_password"]), "token": token}


def exigir_sin_cambio_pendiente(u: dict) -> dict:
    """Con contraseña temporal solo se permite ver la cuenta, cambiar la contraseña y salir."""
    if u["debe_cambiar_password"]:
        raise CambioPendiente()
    return u


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
    valida = password_correcta(password, row["password_hash"] if row else HASH_FICTICIO)
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
        "usuario": {"id": row["id"], "usuario": row["usuario"], "nombre": row["nombre"], "funcion": row["funcion"],
                    "debe_cambiar_password": bool(row["debe_cambiar_password"])},
    }


def cerrar_sesion(db, token: str) -> None:
    with transaccion(db):
        repo.borrar_sesion(db, token)


def cambiar_password(db, u: dict, actual: str, nueva: str) -> None:
    """La persona cambia su contraseña (obligatorio tras un restablecimiento, HU-01-011).
    Las demás sesiones de la cuenta se cierran; la actual sigue."""
    if not password_correcta(actual, repo.hash_de(db, u["id"]) or HASH_FICTICIO):
        raise DatosInvalidos("La contraseña actual no es correcta")
    validar_password_nueva(nueva)
    if nueva == actual:
        raise DatosInvalidos("La nueva contraseña debe ser distinta de la actual")
    with transaccion(db):
        repo.poner_password(db, u["id"], hash_password(nueva), temporal=False)
        repo.borrar_otras_sesiones(db, u["id"], u["token"])


def listar_funciones(db) -> list:
    return repo.listar_funciones(db)


def listar_usuarios(db, todas: bool = False, funcion: Optional[str] = None) -> list:
    """Cuentas activas (para elegir personas). Con todas=True, también las desactivadas: solo Admin."""
    if not todas:
        return repo.listar_usuarios_activos(db)
    if funcion != "Admin":
        raise Prohibido()
    return [_cuenta(c) for c in repo.listar_cuentas(db)]


def _cuenta(row: dict) -> dict:
    return {**row, "activo": bool(row["activo"])}


def desactivar_cuenta(db, usuario_id: int, actor_id: int) -> dict:
    """HU-01-009. La cuenta deja de entrar y sus sesiones abiertas dejan de servir; no se borra
    nada de lo que hizo. Desactivar una cuenta ya desactivada no cambia nada (ni fecha ni actor)."""
    if usuario_id == actor_id:
        raise DatosInvalidos("No puedes desactivar tu propia cuenta")
    if not repo.obtener_cuenta(db, usuario_id):
        raise NoEncontrado("La cuenta no existe")
    ahora = _texto(_ahora())
    with transaccion(db):
        if repo.marcar_desactivada(db, usuario_id, actor_id, ahora):
            repo.borrar_sesiones_de(db, usuario_id)
            repo.registrar_evento(db, usuario_id, "desactivacion", "activa", "desactivada", actor_id, ahora)
    return _cuenta(repo.obtener_cuenta(db, usuario_id))


def registrar_usuario(db, usuario: str, nombre: str, password: str, funcion_id: int,
                      actor_id: Optional[int] = None, clave: Optional[str] = None) -> dict:
    """HU-01-001. Con clave (HU-08-002) el reintento devuelve la cuenta ya creada
    en lugar de responder que el identificador existe."""
    if not repo.existe_funcion(db, funcion_id):
        raise DatosInvalidos("La función seleccionada no existe")
    validar_password_nueva(password)

    def insertar() -> int:
        nuevo = repo.insertar_usuario(db, usuario, nombre, hash_password(password), funcion_id)
        # HU-01-010: el alta queda en el historial en la misma transacción (un reintento no la repite)
        repo.registrar_evento(db, nuevo, "cuenta_alta", None, repo.nombre_funcion(db, funcion_id),
                              actor_id, _texto(_ahora()))
        return nuevo

    try:
        nuevo_id = crear_una_vez(db, actor_id, clave, "usuario", insertar)
    except repo.UsuarioDuplicado:
        raise Conflicto("El identificador de usuario ya existe")
    cuenta = repo.obtener_usuario(db, nuevo_id)
    return {**cuenta, "activo": bool(cuenta["activo"])}


def cambiar_funcion(db, usuario_id: int, funcion_id: int, actor_id: int) -> dict:
    """HU-01-008. Los permisos se leen de la BD en cada petición, así que la nueva función
    aplica de inmediato, aunque la persona tenga la sesión abierta. Nadie cambia su propia
    función: así siempre queda al menos un Admin. Elegir la misma función no registra nada."""
    if usuario_id == actor_id:
        raise DatosInvalidos("No puedes cambiar tu propia función")
    nueva = repo.nombre_funcion(db, funcion_id)
    if not nueva:
        raise DatosInvalidos("La función seleccionada no existe")
    cuenta = repo.obtener_cuenta(db, usuario_id)
    if not cuenta:
        raise NoEncontrado("La cuenta no existe")
    if not cuenta["activo"]:
        raise Conflicto("La cuenta está desactivada: no se puede cambiar su función")
    with transaccion(db):
        if repo.cambiar_funcion(db, usuario_id, funcion_id):
            repo.registrar_evento(db, usuario_id, "funcion", cuenta["funcion"], nueva, actor_id, _texto(_ahora()))
    return _cuenta(repo.obtener_cuenta(db, usuario_id))


def restablecer_acceso(db, usuario_id: int, actor_id: int) -> dict:
    """HU-01-011. El Admin genera una contraseña temporal para una cuenta activa: la anterior y
    las sesiones abiertas dejan de servir, y al entrar la persona debe cambiarla. No toca su
    función, sus proyectos ni su autoría. La temporal se devuelve una sola vez y no se registra."""
    if usuario_id == actor_id:
        raise DatosInvalidos("Para tu propia cuenta usa «Cambiar contraseña»")
    cuenta = repo.obtener_cuenta(db, usuario_id)
    if not cuenta:
        raise NoEncontrado("La cuenta no existe")
    if not cuenta["activo"]:
        raise Conflicto("La cuenta está desactivada: no se puede restablecer su acceso")
    temporal = "".join(secrets.choice(ALFABETO_TEMPORAL) for _ in range(LARGO_TEMPORAL))
    with transaccion(db):
        repo.poner_password(db, usuario_id, hash_password(temporal), temporal=True)
        repo.borrar_sesiones_de(db, usuario_id)
        repo.registrar_evento(db, usuario_id, "restablecimiento", None, None, actor_id, _texto(_ahora()))
    INTENTOS.exito(cuenta["usuario"].casefold())  # el freno de intentos no le impide entrar con la nueva
    return {**_cuenta(repo.obtener_cuenta(db, usuario_id)), "password_temporal": temporal}


# --- Historial de cambios de acceso (HU-01-010) ---

LIMITE_HISTORIAL = 500


def historial_accesos(db, funcion: str, usuario_id: Optional[int] = None, proyecto_id: Optional[int] = None) -> dict:
    """Altas, retiros y cambios de acceso con persona, actor, fecha y valores. Solo Admin."""
    if funcion != "Admin":
        raise Prohibido()
    eventos = repo.listar_eventos(db, usuario_id, proyecto_id, LIMITE_HISTORIAL)
    return {"eventos": eventos, "proyectos": repo.listar_proyectos_con_accesos(db), "limite": LIMITE_HISTORIAL}


def registrar_cambio_acceso(db, usuario_id: int, proyecto_id: int, alta: bool, actor_id: Optional[int],
                            detalle: str = "") -> None:
    """Para el módulo de proyectos: anota un alta o retiro de acceso dentro de SU transacción."""
    con, sin = "con acceso" + (f" ({detalle})" if detalle else ""), "sin acceso"
    repo.registrar_evento(db, usuario_id, "acceso_alta" if alta else "acceso_retiro",
                          sin if alta else con, con if alta else sin, actor_id, _texto(_ahora()), proyecto_id)


# --- Consultas que usan otros módulos (nunca acceden a este repositorio directamente) ---

def cuenta_activa(db, usuario_id: int) -> bool:
    return repo.es_cuenta_activa(db, usuario_id)


def puede_ser_responsable(db, usuario_id: int) -> bool:
    return repo.tiene_funcion_activa(db, usuario_id, FUNCIONES_RESPONSABLE)
