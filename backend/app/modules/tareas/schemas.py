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


class PlanLeido(Base):
    responsable_id: Optional[int]
    fecha_limite: Optional[date]
    prioridad: Prioridad


class ReplanificarIn(PlanLeido):
    """HU-03-006: se envía el plan completo; solo se guardan los valores que cambian.
    responsable_id null deja la tarea sin asignar; fecha_limite null, sin fecha.
    HU-08-003: `anteriores` son los valores que se leyeron al abrir el formulario."""
    anteriores: Optional[PlanLeido] = None


class EstadoIn(Base):
    estado: Estado
    anterior: Optional[Estado] = None  # HU-08-003: el estado que se veía al pulsar


class AvanceIn(Base):
    texto: str = Field(min_length=1, max_length=1000)


class BloqueoIn(Base):
    motivo: str = Field(min_length=1, max_length=1000)


class ResolucionIn(Base):
    resolucion: str = Field(min_length=1, max_length=1000)
