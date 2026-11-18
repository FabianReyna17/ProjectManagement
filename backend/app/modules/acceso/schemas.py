from typing import Annotated

from pydantic import Field, StringConstraints

from ...core.schemas import Base

# Las contraseñas se guardan tal cual: el resto de textos se recortan (str_strip_whitespace),
# pero un espacio al inicio o al final de una contraseña es parte de ella.
Clave = Annotated[str, StringConstraints(strip_whitespace=False)]


class LoginIn(Base):
    usuario: str = Field(min_length=1)
    password: Clave = Field(min_length=1)


class UsuarioIn(Base):
    usuario: str = Field(min_length=3, max_length=50)
    nombre: str = Field(min_length=1, max_length=100)
    password: Clave = Field(min_length=6, max_length=100)
    funcion_id: int


class FuncionIn(Base):
    funcion_id: int


class PasswordIn(Base):
    actual: Clave = Field(min_length=1)
    nueva: Clave = Field(min_length=6, max_length=100)
