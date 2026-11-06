from pydantic import Field

from ...core.schemas import Base


class LoginIn(Base):
    usuario: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UsuarioIn(Base):
    usuario: str = Field(min_length=3, max_length=50)
    nombre: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=100)
    funcion_id: int
