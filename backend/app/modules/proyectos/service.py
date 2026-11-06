"""Reglas de proyectos y participantes (HU-01-005, HU-01-006, HU-02-001, HU-02-002, HU-08-002).

No importa FastAPI. Para datos de cuentas usa el servicio de acceso, nunca su repositorio.
"""
from datetime import date
from typing import Optional

from ...core.errors import Conflicto, DatosInvalidos, NoEncontrado, Prohibido
from ...db.database import transaccion
from ...db.idempotencia import crear_una_vez
from ..acceso import service as acceso
from . import repository as repo


def mis_proyectos(db, usuario_id: int) -> list:
    return repo.listar_de_participante(db, usuario_id)


def crear(db, actor_id: int, nombre: str, objetivo: str, responsable_id: int,
          fecha_inicio: date, fecha_fin: date, clave: Optional[str] = None) -> dict:
    if fecha_fin < fecha_inicio:
        raise DatosInvalidos("La fecha de fin no puede ser anterior a la de inicio")
    if not acceso.puede_ser_responsable(db, responsable_id):
        raise DatosInvalidos("El responsable debe ser una cuenta activa con función Responsable o Admin")

    def insertar() -> int:
        pid = repo.insertar(db, nombre, objetivo, responsable_id,
                            fecha_inicio.isoformat(), fecha_fin.isoformat(), actor_id)
        repo.activar_participante(db, pid, responsable_id)
        if actor_id != responsable_id:
            repo.activar_participante(db, pid, actor_id)
        return pid

    return repo.obtener(db, crear_una_vez(db, actor_id, clave, "proyecto", insertar))


def obtener_autorizado(db, proyecto_id: int, usuario_id: int) -> dict:
    """Proyecto si el usuario participa. Si no existe o no participa → Prohibido
    (misma respuesta en ambos casos para no revelar qué proyectos existen)."""
    if not repo.es_participante(db, proyecto_id, usuario_id):
        raise Prohibido()
    proyecto = repo.obtener_con_responsable(db, proyecto_id)
    if not proyecto:
        raise Prohibido()
    return proyecto


def es_participante(db, proyecto_id: int, usuario_id: int) -> bool:
    return repo.es_participante(db, proyecto_id, usuario_id)


def ficha(proyecto: dict, usuario_id: int) -> dict:
    return {**proyecto, "soy_responsable": proyecto["responsable_id"] == usuario_id}


def listar_participantes(db, proyecto: dict) -> list:
    return repo.listar_participantes(db, proyecto["id"])


def exigir_responsable(proyecto: dict, actor_id: int) -> None:
    """Solo el responsable del proyecto administra participantes y planifica tareas."""
    if proyecto["responsable_id"] != actor_id:
        raise Prohibido()


def agregar_participante(db, proyecto: dict, actor_id: int, usuario_id: int) -> None:
    exigir_responsable(proyecto, actor_id)
    if not acceso.cuenta_activa(db, usuario_id):
        raise DatosInvalidos("La cuenta no existe o está inactiva")
    if repo.es_participante(db, proyecto["id"], usuario_id):
        raise Conflicto("La persona ya participa en el proyecto")
    with transaccion(db):
        repo.activar_participante(db, proyecto["id"], usuario_id)


def retirar_participante(db, proyecto: dict, actor_id: int, usuario_id: int) -> None:
    exigir_responsable(proyecto, actor_id)
    if usuario_id == proyecto["responsable_id"]:
        raise DatosInvalidos("No se puede retirar al responsable del proyecto")
    with transaccion(db):
        if not repo.retirar_participante(db, proyecto["id"], usuario_id):
            raise NoEncontrado("La persona no participa en el proyecto")
