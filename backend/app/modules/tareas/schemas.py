from datetime import date
from typing import Literal, Optional

from pydantic import Field

from ...core.schemas import Base


Prioridad = Literal["alta", "media", "baja"]
Estado = Literal["pendiente", "en_curso", "terminada"]


class TareaIn(Base):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(min_length=1, max_length=2000)
    resultado_esperado: Optional[str] = Field(None, max_length=1000)
    responsable_id: Optional[int] = None
    fecha_limite: Optional[date] = None
    prioridad: Prioridad = "media"


class ResponsableIn(Base):
    usuario_id: int


class PlanificacionIn(Base):
    """Se envían ambos valores; fecha_limite null deja la tarea sin fecha."""
    fecha_limite: Optional[date]
    prioridad: Prioridad


class EstadoIn(Base):
    estado: Estado


class BloqueoIn(Base):
    motivo: str = Field(min_length=1, max_length=1000)


class ResolucionIn(Base):
    resolucion: str = Field(min_length=1, max_length=1000)
