"""Reglas de tareas (HU-03-001 a HU-03-006, HU-04-001 a HU-04-005, HU-07-001, HU-07-002, HU-08-002, HU-08-003).

No importa FastAPI. Para proyectos y cuentas usa sus servicios, nunca sus repositorios.
Planificar (crear, asignar, fechar) es exclusivo del responsable del proyecto.
Todo cambio del plan queda en el historial con valor anterior, nuevo y actor.
"""
from datetime import date
from typing import Optional

from ...core import concurrencia, tiempo
from ...core.errors import Conflicto, DatosInvalidos, NoEncontrado, Prohibido
from ...db.database import transaccion
from ...db.idempotencia import crear_una_vez
from ..acceso import service as acceso
from ..proyectos import service as proyectos
from . import repository as repo

MSG_RESPONSABLE = "El responsable debe ser una cuenta activa con acceso al proyecto"
MSG_ESTADO_PERMISO = "Solo la persona asignada o el responsable del proyecto pueden cambiar el estado"
MSG_AVANCE_PERMISO = "Solo la persona asignada o el responsable del proyecto pueden registrar avances"
MSG_BLOQUEO_PERMISO = "Solo la persona asignada o el responsable del proyecto pueden reportar un bloqueo"

NOMBRE_ESTADO = {"pendiente": "Pendiente", "en_curso": "En curso", "terminada": "Terminada"}
# Transiciones permitidas (HU-04-001). Terminar requiere haber iniciado; una terminada se puede reabrir.
TRANSICIONES = {
    "pendiente": {"en_curso"},
    "en_curso": {"pendiente", "terminada"},
    "terminada": {"en_curso"},
}


def _validar_responsable(db, proyecto_id: int, usuario_id: int) -> None:
    if not acceso.cuenta_activa(db, usuario_id) or not proyectos.es_participante(db, proyecto_id, usuario_id):
        raise DatosInvalidos(MSG_RESPONSABLE)


def _exigir_planificador(tarea: dict, actor_id: int) -> None:
    if tarea["proyecto_responsable_id"] != actor_id:
        raise Prohibido()


def _iso(fecha: Optional[date]) -> Optional[str]:
    return fecha.isoformat() if fecha else None


def crear(db, proyecto: dict, actor_id: int, nombre: str, descripcion: str,
          resultado_esperado: Optional[str], responsable_id: Optional[int] = None,
          fecha_limite: Optional[date] = None, prioridad: str = "media", clave: Optional[str] = None) -> dict:
    proyectos.exigir_responsable(proyecto, actor_id)
    if responsable_id is not None:
        _validar_responsable(db, proyecto["id"], responsable_id)

    def insertar() -> int:
        tid = repo.insertar(db, proyecto["id"], nombre, descripcion, resultado_esperado or None,
                            responsable_id, _iso(fecha_limite), prioridad, actor_id)
        if responsable_id is not None:
            repo.registrar_cambio(db, tid, "responsable", None, responsable_id, actor_id)
        return tid

    return repo.obtener(db, crear_una_vez(db, actor_id, clave, "tarea", insertar))


def obtener_autorizada(db, tarea_id: int, usuario_id: int) -> dict:
    """Tarea si el usuario participa en su proyecto. Si no existe o no participa → Prohibido."""
    tarea = repo.obtener(db, tarea_id)
    if not tarea:
        raise Prohibido()
    proyecto = proyectos.obtener_autorizado(db, tarea["proyecto_id"], usuario_id)
    return {**tarea, "proyecto_responsable_id": proyecto["responsable_id"]}


def _puede_cambiar_estado(tarea: dict, usuario_id: int) -> bool:
    return usuario_id in (tarea["responsable_id"], tarea["proyecto_responsable_id"])


def _transiciones(tarea: dict) -> list:
    """Las que el servidor aceptaría ahora: con un bloqueo abierto no se ofrece terminar."""
    return sorted(e for e in TRANSICIONES[tarea["estado"]] if not (e == "terminada" and tarea["bloqueada"]))


def _con_vencimiento(tarea: dict, dia) -> dict:
    """HU-04-005: marca de vencida / por vencer según el día de la organización."""
    return {**tarea, "bloqueada": bool(tarea["bloqueada"]),
            **tiempo.vencimiento(tarea["fecha_limite"], tarea["estado"] == "terminada", dia)}


def detalle(tarea: dict, usuario_id: int) -> dict:
    puede = _puede_cambiar_estado(tarea, usuario_id)
    return {**_con_vencimiento(tarea, tiempo.hoy()),
            "puedo_bloquear": puede and not tarea["bloqueada"] and tarea["estado"] != "terminada",
            "puedo_planificar": tarea["proyecto_responsable_id"] == usuario_id,
            "puedo_registrar_avance": puede,
            "soy_asignado": tarea["responsable_id"] == usuario_id,
            "transiciones": _transiciones(tarea) if puede else []}


def _lista(tareas: list) -> list:
    dia = tiempo.hoy()
    return [_con_vencimiento(t, dia) for t in tareas]


def _cumple(tarea: dict, filtros: dict) -> bool:
    """HU-07-002: la tarea cumple todos los filtros indicados (los vacíos no filtran)."""
    responsable = filtros.get("responsable")
    return ((not filtros.get("estado") or tarea["estado"] == filtros["estado"])
            and (not filtros.get("prioridad") or tarea["prioridad"] == filtros["prioridad"])
            and (not filtros.get("vencimiento") or tarea["vencimiento"] == filtros["vencimiento"])
            and (not responsable
                 or (responsable == "sin_asignar" and tarea["responsable_id"] is None)
                 or (responsable.isdigit() and tarea["responsable_id"] == int(responsable))))


def listar_de_proyecto(db, proyecto: dict, filtros: Optional[dict] = None) -> list:
    """HU-03-005: tareas del proyecto (ya autorizado); responsable_id null = sin asignar.
    Los filtros solo reducen esta lista: nunca agregan tareas de otros proyectos."""
    return [t for t in _lista(repo.listar_de_proyecto(db, proyecto["id"])) if _cumple(t, filtros or {})]


def tablero(db, proyecto: dict, usuario_id: int, filtros: Optional[dict] = None) -> dict:
    """HU-07-001: las mismas tareas y en el mismo orden que la lista del proyecto, en una
    columna por estado. Cada tarjeta trae las transiciones que este usuario puede hacer."""
    columnas = [{"estado": e, "nombre": n, "tareas": []} for e, n in NOMBRE_ESTADO.items()]
    por_estado = {c["estado"]: c["tareas"] for c in columnas}
    for t in listar_de_proyecto(db, proyecto, filtros):
        puede = usuario_id in (t["responsable_id"], proyecto["responsable_id"])
        por_estado[t["estado"]].append({**t, "transiciones": _transiciones(t) if puede else []})
    return {"columnas": columnas}


def mis_tareas(db, usuario_id: int) -> list:
    """HU-03-004: al reasignar la tarea o perder acceso al proyecto deja de aparecer."""
    return _lista(repo.listar_asignadas(db, usuario_id))


def asignar(db, tarea: dict, actor_id: int, usuario_id: int) -> dict:
    """HU-03-002: si la validación falla no se toca al responsable anterior."""
    _exigir_planificador(tarea, actor_id)
    _validar_responsable(db, tarea["proyecto_id"], usuario_id)
    if tarea["responsable_id"] != usuario_id:
        with transaccion(db):
            repo.actualizar_responsable(db, tarea["id"], usuario_id)
            repo.registrar_cambio(db, tarea["id"], "responsable", tarea["responsable_id"], usuario_id, actor_id)
    return detalle(obtener_autorizada(db, tarea["id"], actor_id), actor_id)


def planificar(db, tarea: dict, actor_id: int, fecha_limite: Optional[date], prioridad: str) -> dict:
    """HU-03-003: fecha límite (puede quedar sin fecha) y prioridad. Cada valor que cambia
    se registra con su valor anterior. La validación de formato y catálogo la hace el esquema."""
    _exigir_planificador(tarea, actor_id)
    nueva_fecha = _iso(fecha_limite)
    cambios = [(campo, tarea[campo], nuevo)
               for campo, nuevo in (("fecha_limite", nueva_fecha), ("prioridad", prioridad))
               if tarea[campo] != nuevo]
    if cambios:
        with transaccion(db):
            repo.actualizar_plan(db, tarea["id"], nueva_fecha, prioridad)
            for campo, anterior, nuevo in cambios:
                repo.registrar_cambio(db, tarea["id"], campo, anterior, nuevo, actor_id)
    return detalle(obtener_autorizada(db, tarea["id"], actor_id), actor_id)


# Tipo con el que cada campo del plan queda en el historial
TIPO_HISTORIAL = {"responsable_id": "responsable", "fecha_limite": "fecha_limite", "prioridad": "prioridad"}
NOMBRE_CAMPO = {"responsable_id": "el responsable", "fecha_limite": "la fecha límite", "prioridad": "la prioridad"}


def _conflicto_plan(actual: dict, campos: list) -> Conflicto:
    """HU-08-003: 409 con los campos en conflicto y el plan vigente."""
    vigente = {k: actual[k] for k in ("responsable_id", "responsable_nombre", "fecha_limite", "prioridad")}
    return Conflicto(concurrencia.mensaje(campos, NOMBRE_CAMPO), {"campos": campos, "vigente": vigente})


def replanificar(db, tarea: dict, actor_id: int, responsable_id: Optional[int],
                 fecha_limite: Optional[date], prioridad: str, leidos: Optional[dict] = None) -> dict:
    """HU-03-006: cambia responsable, fecha y prioridad en una sola confirmación. Cada valor
    que cambia queda en el historial (anterior, nuevo, actor); si algo no es válido no se
    guarda nada. Reasignar no toca el estado, los bloqueos ni el historial previo.
    HU-08-003: con `leidos`, un campo que otra persona cambió mientras tanto da conflicto."""
    _exigir_planificador(tarea, actor_id)
    nuevos = {"responsable_id": responsable_id, "fecha_limite": _iso(fecha_limite), "prioridad": prioridad}
    cambios, en_conflicto = concurrencia.cambios_a_aplicar(tarea, nuevos, leidos)
    if en_conflicto:
        raise _conflicto_plan(tarea, en_conflicto)
    if responsable_id is not None and any(campo == "responsable_id" for campo, _, _ in cambios):
        _validar_responsable(db, tarea["proyecto_id"], responsable_id)
    if cambios:
        with transaccion(db):
            for campo, leido, nuevo in cambios:
                if not repo.actualizar_si_vigente(db, tarea["id"], campo, leido, nuevo):
                    raise _conflicto_plan(repo.obtener(db, tarea["id"]), [campo])
                repo.registrar_cambio(db, tarea["id"], TIPO_HISTORIAL[campo], leido, nuevo, actor_id)
    return detalle(obtener_autorizada(db, tarea["id"], actor_id), actor_id)


def _conflicto_estado(actual: str) -> Conflicto:
    return Conflicto(f"Otra persona cambió el estado a «{NOMBRE_ESTADO[actual]}» mientras lo revisabas. "
                     "Tu cambio no se guardó: revisa el estado vigente y vuelve a intentarlo",
                     {"campos": ["estado"], "vigente": {"estado": actual}})


def cambiar_estado(db, tarea: dict, actor_id: int, estado: str, leido: Optional[str] = None) -> dict:
    """HU-04-001: solo transiciones permitidas, por la persona asignada o el responsable del proyecto.
    Repetir el mismo estado no hace nada (un reintento no duplica el historial).
    HU-08-003: si el estado ya no es el que se veía (`leido`), conflicto en lugar de pisarlo."""
    if not _puede_cambiar_estado(tarea, actor_id):
        raise Prohibido(MSG_ESTADO_PERMISO)
    actual = tarea["estado"]
    if estado != actual:
        if leido is not None and leido != actual:
            raise _conflicto_estado(actual)
        if estado not in TRANSICIONES[actual]:
            raise DatosInvalidos(f"No se puede pasar de «{NOMBRE_ESTADO[actual]}» a «{NOMBRE_ESTADO[estado]}»")
        if estado == "terminada" and tarea["bloqueada"]:
            raise DatosInvalidos("La tarea tiene un bloqueo abierto: resuélvelo antes de terminarla")
        with transaccion(db):
            if not repo.actualizar_estado(db, tarea["id"], actual, estado):
                raise _conflicto_estado(repo.obtener(db, tarea["id"])["estado"])
            repo.registrar_cambio(db, tarea["id"], "estado", actual, estado, actor_id)
    return detalle(obtener_autorizada(db, tarea["id"], actor_id), actor_id)


def con_bloqueo(db, tarea: dict, usuario_id: int) -> dict:
    """Detalle de la tarea con su bloqueo abierto (o None)."""
    return {**detalle(tarea, usuario_id), "bloqueo": repo.bloqueo_abierto(db, tarea["id"])}


def registrar_avance(db, tarea: dict, actor_id: int, texto: str, clave: Optional[str] = None) -> dict:
    """HU-04-002: nota breve con autor y fecha; también queda en el historial de la tarea.
    No cambia el estado ni se borra al reasignar."""
    if not _puede_cambiar_estado(tarea, actor_id):
        raise Prohibido(MSG_AVANCE_PERMISO)

    def insertar() -> int:
        aid = repo.insertar_avance(db, tarea["id"], texto, actor_id)
        repo.registrar_cambio(db, tarea["id"], "avance", None, texto, actor_id)
        return aid

    return repo.obtener_avance(db, crear_una_vez(db, actor_id, clave, "avance", insertar))


def avances(db, tarea: dict) -> list:
    return repo.listar_avances(db, tarea["id"])


def registrar_bloqueo(db, tarea: dict, actor_id: int, motivo: str, clave: Optional[str] = None) -> dict:
    """HU-04-003: abre un bloqueo con motivo, autor y fecha sin cambiar el estado de trabajo."""
    if not _puede_cambiar_estado(tarea, actor_id):
        raise Prohibido(MSG_BLOQUEO_PERMISO)
    if tarea["estado"] == "terminada":
        raise DatosInvalidos("No se puede bloquear una tarea terminada")

    def insertar() -> int:
        bid = repo.insertar_bloqueo(db, tarea["id"], motivo, actor_id)
        repo.registrar_cambio(db, tarea["id"], "bloqueo", None, motivo, actor_id)
        return bid

    try:
        bid = crear_una_vez(db, actor_id, clave, "bloqueo", insertar)
    except repo.BloqueoYaAbierto:
        raise Conflicto("La tarea ya tiene un bloqueo abierto")
    return repo.obtener_bloqueo(db, bid)


def bloqueos(db, tarea: dict) -> list:
    return repo.listar_bloqueos(db, tarea["id"])


def resolver_bloqueo(db, tarea: dict, actor_id: int, bloqueo_id: int, resolucion: str) -> dict:
    """HU-04-004: solo el responsable del proyecto; exige explicación. El bloqueo se conserva
    con motivo y resolución; la tarea sigue en su estado de trabajo. Uno ya resuelto → Conflicto."""
    _exigir_planificador(tarea, actor_id)
    bloqueo = repo.obtener_bloqueo(db, bloqueo_id)
    if not bloqueo or bloqueo["tarea_id"] != tarea["id"]:
        raise NoEncontrado("El bloqueo no existe en esta tarea")
    with transaccion(db):
        if not repo.resolver_bloqueo(db, bloqueo_id, resolucion, actor_id):
            raise Conflicto("El bloqueo ya estaba resuelto")
        repo.registrar_cambio(db, tarea["id"], "resolucion_bloqueo", bloqueo["motivo"], resolucion, actor_id)
    return repo.obtener_bloqueo(db, bloqueo_id)


def historial(db, tarea: dict) -> list:
    return repo.listar_historial(db, tarea["id"])
