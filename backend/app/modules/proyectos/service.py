"""Reglas de proyectos y participantes (HU-01-005, HU-01-006, HU-02-001 a HU-02-004, HU-08-002, HU-08-003).

No importa FastAPI. Para datos de cuentas usa el servicio de acceso, nunca su repositorio.
"""
from datetime import date
from typing import Optional

from ...core import concurrencia
from ...core.errors import Conflicto, DatosInvalidos, NoEncontrado, Prohibido
from ...db.database import transaccion
from ...db.idempotencia import crear_una_vez
from ..acceso import service as acceso
from . import repository as repo


def mis_proyectos(db, usuario_id: int) -> list:
    return repo.listar_de_participante(db, usuario_id)


MSG_FECHAS = "La fecha de fin no puede ser anterior a la de inicio"
MSG_RESPONSABLE = "El responsable debe ser una cuenta activa con función Responsable o Admin"


def crear(db, actor_id: int, nombre: str, objetivo: str, responsable_id: int,
          fecha_inicio: date, fecha_fin: date, clave: Optional[str] = None) -> dict:
    if fecha_fin < fecha_inicio:
        raise DatosInvalidos(MSG_FECHAS)
    if not acceso.puede_ser_responsable(db, responsable_id):
        raise DatosInvalidos(MSG_RESPONSABLE)

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


NOMBRE_CAMPO = {"nombre": "el nombre", "objetivo": "el objetivo", "responsable_id": "el responsable",
                "fecha_inicio": "la fecha de inicio", "fecha_fin": "la fecha de fin"}


def _conflicto(actual: dict, campos: list) -> Conflicto:
    """HU-08-003: 409 con los campos en conflicto y los datos vigentes."""
    vigente = {k: actual[k] for k in (*repo.CAMPOS_EDITABLES, "responsable_nombre")}
    return Conflicto(concurrencia.mensaje(campos, NOMBRE_CAMPO), {"campos": campos, "vigente": vigente})


def actualizar(db, proyecto: dict, actor_id: int, nombre: str, objetivo: str, responsable_id: int,
               fecha_inicio: date, fecha_fin: date, leidos: Optional[dict] = None) -> dict:
    """HU-02-003: solo el responsable del proyecto. Cada dato que cambia queda en el historial
    con valor anterior, actor y fecha; si algo no es válido no se guarda nada. El nuevo
    responsable obtiene acceso si no lo tenía; el anterior sigue como participante.
    HU-08-003: con `leidos`, un dato que otra persona cambió mientras tanto da conflicto;
    los cambios ajenos en otros datos se conservan."""
    exigir_responsable(proyecto, actor_id)
    nuevos = {"nombre": nombre, "objetivo": objetivo, "responsable_id": responsable_id,
              "fecha_inicio": fecha_inicio.isoformat(), "fecha_fin": fecha_fin.isoformat()}
    cambios, en_conflicto = concurrencia.cambios_a_aplicar(proyecto, nuevos, leidos)
    if en_conflicto:
        raise _conflicto(proyecto, en_conflicto)
    final = {**proyecto, **{campo: valor for campo, _, valor in cambios}}
    if final["fecha_fin"] < final["fecha_inicio"]:
        raise DatosInvalidos(MSG_FECHAS)
    if final["responsable_id"] != proyecto["responsable_id"] and not acceso.puede_ser_responsable(db, responsable_id):
        raise DatosInvalidos(MSG_RESPONSABLE)
    if cambios:
        with transaccion(db):
            for campo, leido, nuevo in cambios:
                if not repo.actualizar_si_vigente(db, proyecto["id"], campo, leido, nuevo):
                    raise _conflicto(repo.obtener_con_responsable(db, proyecto["id"]), [campo])
                repo.registrar_cambio(db, proyecto["id"], campo, leido, nuevo, actor_id)
            if not repo.es_participante(db, proyecto["id"], responsable_id):
                repo.activar_participante(db, proyecto["id"], responsable_id)
    return ficha(repo.obtener_con_responsable(db, proyecto["id"]), actor_id)


NOMBRE_ESTADO = {"planificado": "Planificado", "en_curso": "En curso", "cerrado": "Cerrado"}
# HU-02-004: por ahora solo se inicia la ejecución. El cierre tiene su propio procedimiento
# (HU-02-005: revisar tareas abiertas), así que no se acepta como un cambio de estado simple.
TRANSICIONES = {"planificado": {"en_curso"}, "en_curso": set(), "cerrado": set()}
MSG_CIERRE = "El proyecto se cierra con su propio procedimiento, que revisa las tareas abiertas"


def _transiciones(proyecto: dict) -> list:
    return sorted(TRANSICIONES[proyecto["estado"]])


def _conflicto_estado(actual: str) -> Conflicto:
    return Conflicto(f"Otra persona cambió el estado del proyecto a «{NOMBRE_ESTADO[actual]}» mientras lo "
                     "revisabas. Tu cambio no se guardó", {"campos": ["estado"], "vigente": {"estado": actual}})


def cambiar_estado(db, proyecto: dict, actor_id: int, estado: str, leido: Optional[str] = None) -> dict:
    """HU-02-004: solo el responsable y solo transiciones permitidas. El cambio queda en el
    historial (anterior, nuevo, actor y fecha). Repetir el estado actual no hace nada; si algo
    no es válido el estado anterior se conserva. HU-08-003: si el estado ya no es el leído → 409."""
    exigir_responsable(proyecto, actor_id)
    actual = proyecto["estado"]
    if estado != actual:
        if leido is not None and leido != actual:
            raise _conflicto_estado(actual)
        if estado == "cerrado":
            raise DatosInvalidos(MSG_CIERRE)
        if estado not in TRANSICIONES[actual]:
            raise DatosInvalidos(f"No se puede pasar el proyecto de «{NOMBRE_ESTADO[actual]}» a «{NOMBRE_ESTADO[estado]}»")
        with transaccion(db):
            if not repo.actualizar_estado(db, proyecto["id"], actual, estado):
                raise _conflicto_estado(repo.obtener(db, proyecto["id"])["estado"])
            repo.registrar_cambio(db, proyecto["id"], "estado", actual, estado, actor_id)
    return ficha(repo.obtener_con_responsable(db, proyecto["id"]), actor_id)


def historial(db, proyecto: dict) -> list:
    return repo.listar_historial(db, proyecto["id"])


def es_participante(db, proyecto_id: int, usuario_id: int) -> bool:
    return repo.es_participante(db, proyecto_id, usuario_id)


def ficha(proyecto: dict, usuario_id: int) -> dict:
    soy_responsable = proyecto["responsable_id"] == usuario_id
    return {**proyecto, "soy_responsable": soy_responsable,
            "transiciones": _transiciones(proyecto) if soy_responsable else []}


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
