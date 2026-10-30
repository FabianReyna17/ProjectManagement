from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Base(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class LoginIn(Base):
    usuario: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UsuarioIn(Base):
    usuario: str = Field(min_length=3, max_length=50)
    nombre: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=100)
    funcion_id: int


class ProyectoIn(Base):
    nombre: str = Field(min_length=1, max_length=120)
    objetivo: str = Field(min_length=1, max_length=1000)
    responsable_id: int
    fecha_inicio: date
    fecha_fin: date


class ParticipanteIn(Base):
    usuario_id: int
