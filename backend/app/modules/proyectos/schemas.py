from datetime import date
from typing import Literal, Optional

from pydantic import Field

from ...core.schemas import Base


class ProyectoIn(Base):
    nombre: str = Field(min_length=1, max_length=120)
    objetivo: str = Field(min_length=1, max_length=1000)
    responsable_id: int
    fecha_inicio: date
    fecha_fin: date


class ProyectoEditarIn(ProyectoIn):
    """HU-02-003: se envían todos los datos; solo se guardan los que cambian.
    HU-08-003: `anteriores` son los valores que se leyeron al abrir el formulario."""
    anteriores: Optional[ProyectoIn] = None


EstadoProyecto = Literal["planificado", "en_curso", "cerrado"]


class EstadoProyectoIn(Base):
    """HU-02-004. `anterior` es el estado que se veía al pulsar (HU-08-003)."""
    estado: EstadoProyecto
    anterior: Optional[EstadoProyecto] = None


class CierreIn(Base):
    """HU-02-005. `justificacion` es obligatoria si quedan tareas abiertas. `revisadas` son los
    ids de las tareas abiertas que se mostraron al revisar: si cambiaron mientras tanto → 409."""
    justificacion: Optional[str] = Field(None, max_length=1000)
    revisadas: Optional[list[int]] = None


class ParticipanteIn(Base):
    usuario_id: int
