from pydantic import Field

from ...core.schemas import Base


class ComentarioIn(Base):
    texto: str = Field(min_length=1, max_length=2000)
