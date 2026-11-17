"""Fecha de la organización (HU-04-005).

Las fechas límite son días de calendario: si una tarea está vencida se decide con el día
actual en la zona horaria de la organización, no con la del servidor ni con UTC.
"""
import os
from datetime import date, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

ZONA = ZoneInfo(os.getenv("ZONA_HORARIA", "America/Guatemala"))
DIAS_POR_VENCER = int(os.getenv("DIAS_POR_VENCER", "3"))


def hoy(ahora: Optional[datetime] = None) -> date:
    """Día actual en la organización. `ahora` (con zona) solo se pasa en pruebas."""
    return (ahora or datetime.now(timezone.utc)).astimezone(ZONA).date()


def vencimiento(fecha_limite: Optional[str], terminada: bool, dia: date) -> dict:
    """'vencida' si la fecha límite ya pasó; 'por_vencer' si vence hoy o en los próximos
    DIAS_POR_VENCER días. Sin fecha o terminada → sin marca. dias_restantes < 0 si está vencida."""
    if not fecha_limite or terminada:
        return {"vencimiento": None, "dias_restantes": None}
    dias = (date.fromisoformat(fecha_limite) - dia).days
    marca = "vencida" if dias < 0 else "por_vencer" if dias <= DIAS_POR_VENCER else None
    return {"vencimiento": marca, "dias_restantes": dias}
