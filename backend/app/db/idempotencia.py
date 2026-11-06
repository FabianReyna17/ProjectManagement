"""Operación única: reintentar una creación sin duplicarla (HU-08-002, RP-08-02).

El cliente manda la cabecera Idempotency-Key con cada creación y repite la misma clave
en los reintentos. La clave se guarda en la misma transacción que el registro creado:
- si el primer envío se confirmó, el reintento devuelve el registro existente;
- si no se confirmó, el reintento lo crea una sola vez;
- dos acciones distintas llevan claves distintas y no se confunden.
Sin clave, la creación funciona como siempre.
"""
from typing import Callable, Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ..core.errors import Conflicto
from .database import transaccion, uno


def _buscar(db, usuario_id: int, clave: str, tipo: str) -> Optional[int]:
    previo = uno(db, "SELECT tipo, recurso_id FROM claves_idempotencia WHERE usuario_id = :u AND clave = :c",
                 u=usuario_id, c=clave)
    if previo is None:
        return None
    if previo["tipo"] != tipo:
        raise Conflicto("La clave de la operación ya se usó para otra acción")
    return previo["recurso_id"]


def crear_una_vez(db, usuario_id: int, clave: Optional[str], tipo: str, crear: Callable[[], int]) -> int:
    """Ejecuta crear() (que inserta y devuelve el id) en una transacción junto con la clave.
    Devuelve el id creado, o el del primer envío si la clave ya existía."""
    if clave:
        previo = _buscar(db, usuario_id, clave, tipo)
        if previo is not None:
            return previo
    try:
        with transaccion(db):
            recurso_id = crear()
            if clave:
                db.execute(text("""INSERT INTO claves_idempotencia (usuario_id, clave, tipo, recurso_id)
                                   VALUES (:u, :c, :t, :r)"""),
                           {"u": usuario_id, "c": clave, "t": tipo, "r": recurso_id})
    except IntegrityError:
        # Dos envíos simultáneos con la misma clave: el otro ganó y el nuestro se deshizo.
        previo = _buscar(db, usuario_id, clave, tipo) if clave else None
        if previo is None:
            raise
        return previo
    return recurso_id
