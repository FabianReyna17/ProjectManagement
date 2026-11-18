"""Reglas de tareas (HU-02-005, HU-03-001 a HU-03-006, HU-04-001 a HU-04-005, HU-06-001 a HU-06-003, HU-07-001 a HU-07-005, HU-08-002, HU-08-003).

No importa FastAPI. Para proyectos y cuentas usa sus servicios, nunca sus repositorios.
Planificar (crear, asignar, fechar) es exclusivo del responsable del proyecto.
Las tareas de un proyecto cerrado solo se consultan: ningún cambio se acepta.
Todo cambio del plan queda en el historial con valor anterior, nuevo y actor.
Cada asignación avisa a la nueva persona responsable y cada bloqueo al responsable del
proyecto, en la misma transacción que el cambio.
"""
from datetime import date, timedelta
from typing import Optional

from ...core import concurrencia, tiempo
from ...core.errors import Conflicto, DatosInvalidos, NoEncontrado, Prohibido
from ...db.database import transaccion
from ...db.idempotencia import crear_una_vez
from ..acceso import service as acceso
from ..avisos import service as avisos
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


def _exigir_abierta(tarea: dict) -> None:
    """HU-02-005: en un proyecto cerrado las tareas solo se consultan."""
    if tarea["proyecto_estado"] == "cerrado":
        raise DatosInvalidos(proyectos.MSG_CERRADO)


def _iso(fecha: Optional[date]) -> Optional[str]:
    return fecha.isoformat() if fecha else None


def crear(db, proyecto: dict, actor_id: int, nombre: str, descripcion: str,
          resultado_esperado: Optional[str], responsable_id: Optional[int] = None,
          fecha_limite: Optional[date] = None, prioridad: str = "media", clave: Optional[str] = None) -> dict:
    proyectos.exigir_responsable(proyecto, actor_id)
    proyectos.exigir_abierto(proyecto)
    if responsable_id is not None:
        _validar_responsable(db, proyecto["id"], responsable_id)

    def insertar() -> int:
        tid = repo.insertar(db, proyecto["id"], nombre, descripcion, resultado_esperado or None,
                            responsable_id, _iso(fecha_limite), prioridad, actor_id)
        if responsable_id is not None:
            _registrar_asignacion(db, tid, proyecto["id"], None, responsable_id, actor_id)
        return tid

    return repo.obtener(db, crear_una_vez(db, actor_id, clave, "tarea", insertar))


def _registrar_asignacion(db, tarea_id: int, proyecto_id: int, anterior: Optional[int],
                          nuevo: Optional[int], actor_id: int) -> None:
    """Historial del cambio de responsable y aviso a quien recibe la tarea (HU-06-001)."""
    evento = repo.registrar_cambio(db, tarea_id, "responsable", anterior, nuevo, actor_id)
    avisos.avisar_asignacion(db, proyecto_id, tarea_id, nuevo, actor_id, evento)


def obtener_autorizada(db, tarea_id: int, usuario_id: int) -> dict:
    """Tarea si el usuario participa en su proyecto. Si no existe o no participa → Prohibido."""
    tarea = repo.obtener(db, tarea_id)
    if not tarea:
        raise Prohibido()
    proyecto = proyectos.obtener_autorizado(db, tarea["proyecto_id"], usuario_id)
    return {**tarea, "proyecto_responsable_id": proyecto["responsable_id"], "proyecto_estado": proyecto["estado"]}


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
    abierta = tarea["proyecto_estado"] != "cerrado"  # HU-02-005: proyecto cerrado → solo consulta
    puede = abierta and _puede_cambiar_estado(tarea, usuario_id)
    return {**_con_vencimiento(tarea, tiempo.hoy()),
            "puedo_bloquear": puede and not tarea["bloqueada"] and tarea["estado"] != "terminada",
            "puedo_planificar": abierta and tarea["proyecto_responsable_id"] == usuario_id,
            "editable": abierta,
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
            and (not filtros.get("bloqueo") or tarea["bloqueada"] == (filtros["bloqueo"] == "bloqueada"))
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
        puede = proyecto["estado"] != "cerrado" and usuario_id in (t["responsable_id"], proyecto["responsable_id"])
        por_estado[t["estado"]].append({**t, "transiciones": _transiciones(t) if puede else []})
    return {"columnas": columnas}


PROXIMAS = 5


def resumen(db, proyecto: dict) -> dict:
    """HU-07-003: cifras del proyecto calculadas sobre la misma lista que muestran la lista y el
    tablero (datos confirmados). Cada cifra trae el filtro que abre las tareas que la componen.
    Próximas fechas: tareas abiertas que aún no vencen, de la más cercana a la más lejana."""
    tareas = listar_de_proyecto(db, proyecto)
    abiertas = [t for t in tareas if t["estado"] != "terminada"]
    filtros = {
        **{e: {"estado": e} for e in NOMBRE_ESTADO},
        "vencidas": {"vencimiento": "vencida"},
        "por_vencer": {"vencimiento": "por_vencer"},
        "bloqueadas": {"bloqueo": "bloqueada"},
    }
    indicadores = {clave: {"total": sum(_cumple(t, f) for t in tareas), "filtro": f} for clave, f in filtros.items()}
    proximas = sorted((t for t in abiertas if t["fecha_limite"] and t["dias_restantes"] >= 0),
                      key=lambda t: (t["fecha_limite"], t["id"]))[:PROXIMAS]
    return {"total": len(tareas), "abiertas": len(abiertas), "indicadores": indicadores, "proximas": proximas}


def generar_avisos_vencimiento(db, dia: Optional[date] = None) -> int:
    """HU-06-002 (lo llama el proceso programado): cada tarea abierta que vence dentro del plazo
    de anticipación (hoy y los DIAS_POR_VENCER días siguientes, con el día de la organización)
    avisa a su responsable con la fecha vigente. Correr el proceso de nuevo no repite avisos;
    si la tarea se reprograma o reasigna, el vencimiento nuevo sí se avisa. Devuelve cuántos generó."""
    dia = dia or tiempo.hoy()
    hasta = dia + timedelta(days=tiempo.DIAS_POR_VENCER)
    with transaccion(db):
        return sum(avisos.avisar_vencimiento(db, t["proyecto_id"], t["id"], t["responsable_id"], t["fecha_limite"])
                   for t in repo.listar_por_vencer(db, dia.isoformat(), hasta.isoformat()))


# ---------- HU-02-005 Cerrar proyecto ----------

MSG_JUSTIFICACION = "Quedan tareas abiertas: termínalas o justifica la excepción para cerrar el proyecto"
MSG_ABIERTAS_CAMBIARON = ("Las tareas abiertas del proyecto cambiaron mientras revisabas el cierre. "
                          "Revisa la lista actualizada; el proyecto no se cerró")


def _abiertas(db, proyecto: dict) -> list:
    return [t for t in listar_de_proyecto(db, proyecto) if t["estado"] != "terminada"]


def revision_cierre(db, proyecto: dict, usuario_id: int) -> dict:
    """Lo que se revisa antes de cerrar: las tareas que siguen abiertas (no se ocultan, RP-02-03)."""
    ficha = proyectos.ficha(proyecto, usuario_id)
    return {"abiertas": _abiertas(db, proyecto), "puedo_cerrar": ficha["puedo_cerrar"]}


def cerrar_proyecto(db, proyecto: dict, actor_id: int, justificacion: Optional[str],
                    revisadas: Optional[list] = None) -> dict:
    """HU-02-005: solo el responsable. Si quedan tareas abiertas exige justificar la excepción
    (política propuesta en RP-02-03); las tareas no se tocan. Repetir el cierre no hace nada."""
    proyectos.exigir_responsable(proyecto, actor_id)
    if proyecto["estado"] == "cerrado":
        return proyectos.ficha(proyecto, actor_id)
    abiertas = _abiertas(db, proyecto)
    if revisadas is not None and sorted(revisadas) != sorted(t["id"] for t in abiertas):
        raise Conflicto(MSG_ABIERTAS_CAMBIARON, {"abiertas": abiertas})
    if abiertas and not justificacion:
        raise DatosInvalidos(MSG_JUSTIFICACION, {"abiertas": abiertas})
    return proyectos.cerrar(db, proyecto, actor_id, justificacion or None, len(abiertas))


# HU-07-005: funciones que consultan el estado general (los integrantes ven sus tareas y proyectos)
FUNCIONES_SUPERVISAN = ("Admin", "Responsable", "Supervisor")
INDICADORES_ATENCION = ("vencidas", "bloqueadas")


def estado_general(db, usuario_id: int, incluir_cerrados: bool = False) -> dict:
    """HU-07-005: los proyectos en los que participa la persona (los demás ni aparecen ni se
    cuentan), con las cifras de su resumen (HU-07-003), así que coinciden con la ficha de cada uno.
    RP-07-03 (propuesta): requiere atención si tiene al menos una tarea vencida o bloqueada.
    Un proyecto cerrado ya no requiere atención (HU-02-005) y va al final.
    Primero los que requieren atención; después por fecha prevista de término."""
    filas = []
    for p in proyectos.mis_proyectos(db, usuario_id):
        if p["estado"] == "cerrado" and not incluir_cerrados:
            continue
        r = resumen(db, p)
        indicadores = {k: r["indicadores"][k] for k in INDICADORES_ATENCION}
        filas.append({**p, "total": r["total"], "abiertas": r["abiertas"], "indicadores": indicadores,
                      "requiere_atencion": p["estado"] != "cerrado" and any(i["total"] for i in indicadores.values())})
    filas.sort(key=lambda f: (f["estado"] == "cerrado", not f["requiere_atencion"], f["fecha_fin"], f["id"]))
    totales = {"proyectos": len(filas), "requieren_atencion": sum(f["requiere_atencion"] for f in filas),
               **{k: sum(f["indicadores"][k]["total"] for f in filas) for k in INDICADORES_ATENCION}}
    return {"proyectos": filas, "totales": totales}


def _cifras(grupo: dict) -> dict:
    tareas = grupo["tareas"]
    return {**grupo, "abiertas": len(tareas), "vencidas": sum(t["vencimiento"] == "vencida" for t in tareas),
            "bloqueadas": sum(t["bloqueada"] for t in tareas)}


def carga(db, usuario_id: int, proyecto_id: Optional[int] = None) -> dict:
    """HU-07-004: tareas abiertas, vencidas y bloqueadas por persona en los proyectos activos en
    los que participa quien consulta (o solo en `proyecto_id`, si lo tiene autorizado). Se calcula
    sobre la misma lista que ven el proyecto y el tablero; otras tareas ni se cuentan ni se ven.
    Las tareas sin responsable van aparte para que no queden ocultas."""
    activos = [p for p in proyectos.mis_proyectos(db, usuario_id) if p["estado"] != "cerrado"]
    consultados = [proyectos.obtener_autorizado(db, proyecto_id, usuario_id)] if proyecto_id else activos
    grupos = {None: {"usuario_id": None, "nombre": None, "tareas": []}}
    for p in consultados:
        for t in listar_de_proyecto(db, p):
            if t["estado"] == "terminada":
                continue
            grupo = grupos.setdefault(t["responsable_id"], {"usuario_id": t["responsable_id"],
                                                            "nombre": t["responsable_nombre"], "tareas": []})
            grupo["tareas"].append({**t, "proyecto_nombre": p["nombre"]})
    sin_asignar = _cifras(grupos.pop(None))
    personas = sorted((_cifras(g) for g in grupos.values()),
                      key=lambda g: (-g["abiertas"], -g["vencidas"], -g["bloqueadas"], g["nombre"]))
    return {"personas": personas, "sin_asignar": sin_asignar,
            "proyectos": [{"id": p["id"], "nombre": p["nombre"]} for p in activos]}


def mis_tareas(db, usuario_id: int) -> list:
    """HU-03-004: al reasignar la tarea o perder acceso al proyecto deja de aparecer."""
    return _lista(repo.listar_asignadas(db, usuario_id))


def asignar(db, tarea: dict, actor_id: int, usuario_id: int) -> dict:
    """HU-03-002: si la validación falla no se toca al responsable anterior."""
    _exigir_planificador(tarea, actor_id)
    _exigir_abierta(tarea)
    _validar_responsable(db, tarea["proyecto_id"], usuario_id)
    if tarea["responsable_id"] != usuario_id:
        with transaccion(db):
            repo.actualizar_responsable(db, tarea["id"], usuario_id)
            _registrar_asignacion(db, tarea["id"], tarea["proyecto_id"], tarea["responsable_id"], usuario_id, actor_id)
    return detalle(obtener_autorizada(db, tarea["id"], actor_id), actor_id)


def planificar(db, tarea: dict, actor_id: int, fecha_limite: Optional[date], prioridad: str) -> dict:
    """HU-03-003: fecha límite (puede quedar sin fecha) y prioridad. Cada valor que cambia
    se registra con su valor anterior. La validación de formato y catálogo la hace el esquema."""
    _exigir_planificador(tarea, actor_id)
    _exigir_abierta(tarea)
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
    _exigir_abierta(tarea)
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
                if campo == "responsable_id":
                    _registrar_asignacion(db, tarea["id"], tarea["proyecto_id"], leido, nuevo, actor_id)
                else:
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
    _exigir_abierta(tarea)
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
    _exigir_abierta(tarea)

    def insertar() -> int:
        aid = repo.insertar_avance(db, tarea["id"], texto, actor_id)
        repo.registrar_cambio(db, tarea["id"], "avance", None, texto, actor_id)
        return aid

    return repo.obtener_avance(db, crear_una_vez(db, actor_id, clave, "avance", insertar))


def avances(db, tarea: dict) -> list:
    return repo.listar_avances(db, tarea["id"])


def registrar_bloqueo(db, tarea: dict, actor_id: int, motivo: str, clave: Optional[str] = None) -> dict:
    """HU-04-003: abre un bloqueo con motivo, autor y fecha sin cambiar el estado de trabajo.
    HU-06-003: avisa al responsable del proyecto; un reintento no repite el aviso."""
    if not _puede_cambiar_estado(tarea, actor_id):
        raise Prohibido(MSG_BLOQUEO_PERMISO)
    _exigir_abierta(tarea)
    if tarea["estado"] == "terminada":
        raise DatosInvalidos("No se puede bloquear una tarea terminada")

    def insertar() -> int:
        bid = repo.insertar_bloqueo(db, tarea["id"], motivo, actor_id)
        evento = repo.registrar_cambio(db, tarea["id"], "bloqueo", None, motivo, actor_id)
        avisos.avisar_bloqueo(db, tarea["proyecto_id"], tarea["id"], tarea["proyecto_responsable_id"],
                              actor_id, evento, bid)
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
    _exigir_abierta(tarea)
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
