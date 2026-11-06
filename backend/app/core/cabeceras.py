"""Cabeceras HTTP comunes."""
from typing import Optional

from fastapi import Header


def clave_idempotencia(idempotency_key: Optional[str] = Header(None, max_length=100)) -> Optional[str]:
    """Cabecera Idempotency-Key (HU-08-002). Opcional; la misma clave en un reintento no duplica."""
    return idempotency_key or None
