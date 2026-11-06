from typing import Optional

from pydantic import Field

from ...core.schemas import Base


class TareaIn(Base):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(min_length=1, max_length=2000)
    resultado_esperado: Optional[str] = Field(None, max_length=1000)
