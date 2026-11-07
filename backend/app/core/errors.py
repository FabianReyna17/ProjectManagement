"""Errores de negocio.

Los servicios lanzan estas excepciones sin saber nada de HTTP; main.py las
traduce a códigos de estado con el mismo formato que usa FastAPI ({"detail": ...}).
"""

MSG_PROHIBIDO = "No tienes permiso para realizar esta acción"


class ErrorNegocio(Exception):
    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class DatosInvalidos(ErrorNegocio):
    """Los datos no cumplen una regla de negocio (400)."""


class NoAutenticado(ErrorNegocio):
    """Credenciales o sesión no válidas (401)."""


class Prohibido(ErrorNegocio):
    """El usuario no tiene permiso (403)."""

    def __init__(self, mensaje: str = MSG_PROHIBIDO):
        super().__init__(mensaje)


class NoEncontrado(ErrorNegocio):
    """El recurso no existe (404)."""


class Conflicto(ErrorNegocio):
    """La operación choca con el estado actual de los datos (409)."""


class DemasiadosIntentos(ErrorNegocio):
    """Demasiados intentos fallidos seguidos; hay que esperar (429)."""


CODIGO_HTTP = {
    DatosInvalidos: 400,
    NoAutenticado: 401,
    Prohibido: 403,
    NoEncontrado: 404,
    Conflicto: 409,
    DemasiadosIntentos: 429,
}


def codigo_http(exc: ErrorNegocio) -> int:
    for clase, codigo in CODIGO_HTTP.items():
        if isinstance(exc, clase):
            return codigo
    return 400
