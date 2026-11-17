from datetime import date

from pydantic import Field

from ...core.schemas import Base


class ProyectoIn(Base):
    nombre: str = Field(min_length=1, max_length=120)
    objetivo: str = Field(min_length=1, max_length=1000)
    responsable_id: int
    fecha_inicio: date
    fecha_fin: date


class ProyectoEditarIn(ProyectoIn):
    """HU-02-003: se envían todos los datos; solo se guardan los que cambian."""


class ParticipanteIn(Base):
    usuario_id: int
