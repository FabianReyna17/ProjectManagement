"""Pruebas de API del Sprint 3: tablero, vencimientos, replanificación y concurrencia."""
from datetime import date, datetime, timezone

import pytest

from app.core import tiempo

from .helpers import crear_usuario, login
from .test_sprint2 import crear_tarea, esc  # noqa: F401  (esc es el escenario del Sprint 2)

ESTADOS = ["pendiente", "en_curso", "terminada"]


def tablero(e, h):
    r = e.c.get(f"/api/proyectos/{e.pid}/tablero", headers=h)
    assert r.status_code == 200, r.text
    return r.json()["columnas"]


def lista(e, h):
    r = e.c.get(f"/api/proyectos/{e.pid}/tareas", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def cambiar_estado(e, h, tid, estado):
    r = e.c.put(f"/api/tareas/{tid}/estado", headers=h, json={"estado": estado})
    assert r.status_code == 200, r.text


# HU-07-001 Tablero de tareas
def test_tablero_tiene_una_columna_por_estado(esc):
    columnas = tablero(esc, esc.ana)
    assert [(c["estado"], c["nombre"]) for c in columnas] == [
        ("pendiente", "Pendiente"), ("en_curso", "En curso"), ("terminada", "Terminada")]
    assert all(c["tareas"] == [] for c in columnas)


def test_tablero_coincide_con_la_lista(esc):
    a = crear_tarea(esc, "Diseño", responsable_id=esc.beto_id, prioridad="alta", fecha_limite="2026-11-20")
    b = crear_tarea(esc, "Maquetar")
    c = crear_tarea(esc, "Publicar", responsable_id=esc.beto_id)
    cambiar_estado(esc, esc.beto, a["id"], "en_curso")
    cambiar_estado(esc, esc.ana, c["id"], "en_curso")
    cambiar_estado(esc, esc.ana, c["id"], "terminada")
    assert esc.c.post(f"/api/tareas/{b['id']}/bloqueos", headers=esc.ana,
                      json={"motivo": "Falta el logo"}).status_code == 201

    tarjetas = {t["id"]: t for col in tablero(esc, esc.beto) for t in col["tareas"]}
    filas = lista(esc, esc.beto)
    assert sorted(tarjetas) == sorted(t["id"] for t in filas)
    for fila in filas:  # mismos datos: responsable, fecha, prioridad, estado y bloqueo
        tarjeta = {k: v for k, v in tarjetas[fila["id"]].items() if k != "transiciones"}
        assert tarjeta == fila

    columnas = tablero(esc, esc.beto)
    assert {c["estado"]: [t["id"] for t in c["tareas"]] for c in columnas} == {
        "pendiente": [b["id"]], "en_curso": [a["id"]], "terminada": [c["id"]]}
    diseno = columnas[1]["tareas"][0]
    assert (diseno["responsable_nombre"], diseno["fecha_limite"], diseno["prioridad"]) == ("Beto", "2026-11-20", "alta")
    assert columnas[0]["tareas"][0]["bloqueada"] is True and columnas[0]["tareas"][0]["responsable_id"] is None


def test_columna_conserva_el_orden_de_la_lista(esc):
    ids = [crear_tarea(esc, n, **extra)["id"] for n, extra in [
        ("Sin fecha", {}), ("Tarde", {"fecha_limite": "2026-12-01"}),
        ("Pronto baja", {"fecha_limite": "2026-11-20", "prioridad": "baja"}),
        ("Pronto alta", {"fecha_limite": "2026-11-20", "prioridad": "alta"})]]
    pendientes = [t["id"] for t in tablero(esc, esc.ana)[0]["tareas"]]
    assert pendientes == [t["id"] for t in lista(esc, esc.ana)]
    assert pendientes == [ids[3], ids[2], ids[1], ids[0]]


def test_cambio_de_estado_se_refleja_en_ambas_vistas(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    for estado in ["en_curso", "terminada", "en_curso"]:
        cambiar_estado(esc, esc.beto, t["id"], estado)
        assert lista(esc, esc.ana)[0]["estado"] == estado
        columnas = tablero(esc, esc.ana)
        assert [len(c["tareas"]) for c in columnas] == [int(e == estado) for e in ESTADOS]


def test_tarjeta_ofrece_solo_las_transiciones_permitidas(esc):
    mia = crear_tarea(esc, "Mía", responsable_id=esc.beto_id)
    ajena = crear_tarea(esc, "Sin asignar")

    def transiciones(h):
        return {t["id"]: t["transiciones"] for col in tablero(esc, h) for t in col["tareas"]}

    assert transiciones(esc.beto) == {mia["id"]: ["en_curso"], ajena["id"]: []}
    assert transiciones(esc.ana) == {mia["id"]: ["en_curso"], ajena["id"]: ["en_curso"]}

    cambiar_estado(esc, esc.beto, mia["id"], "en_curso")
    assert esc.c.post(f"/api/tareas/{mia['id']}/bloqueos", headers=esc.beto,
                      json={"motivo": "Espera"}).status_code == 201
    assert transiciones(esc.beto)[mia["id"]] == ["pendiente"]  # bloqueada: no se ofrece terminar


def test_tablero_sin_acceso(esc):
    crear_tarea(esc)
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tablero", headers=esc.carla).status_code == 403
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tablero", headers=esc.adm).status_code == 403
    assert esc.c.get("/api/proyectos/9999/tablero", headers=esc.ana).status_code == 403
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tablero").status_code == 401


# HU-04-005 Identificar tareas vencidas
HOY = date(2026, 11, 17)


@pytest.fixture()
def hoy_fijo(monkeypatch):
    monkeypatch.setattr(tiempo, "hoy", lambda: HOY)


def test_dia_de_la_organizacion_es_el_de_guatemala():
    # 03:00 UTC del 18 son las 21:00 del 17 en Guatemala (UTC-6)
    assert tiempo.hoy(datetime(2026, 11, 18, 3, 0, tzinfo=timezone.utc)) == date(2026, 11, 17)
    assert tiempo.hoy(datetime(2026, 11, 18, 6, 0, tzinfo=timezone.utc)) == date(2026, 11, 18)


@pytest.mark.parametrize("fecha, marca, dias", [
    ("2026-11-16", "vencida", -1),     # ayer
    ("2026-11-17", "por_vencer", 0),   # hoy todavía no está vencida
    ("2026-11-18", "por_vencer", 1),   # mañana
    ("2026-11-20", "por_vencer", 3),   # último día del aviso
    ("2026-11-21", None, 4),
    (None, None, None),
])
def test_casos_limite_de_fecha(esc, hoy_fijo, fecha, marca, dias):
    t = crear_tarea(esc, fecha_limite=fecha)
    detalle = esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()
    assert (detalle["vencimiento"], detalle["dias_restantes"]) == (marca, dias)


def test_terminada_no_se_marca_como_vencida(esc, hoy_fijo):
    t = crear_tarea(esc, fecha_limite="2026-11-10", responsable_id=esc.beto_id)
    cambiar_estado(esc, esc.beto, t["id"], "en_curso")
    assert lista(esc, esc.ana)[0]["vencimiento"] == "vencida"
    cambiar_estado(esc, esc.beto, t["id"], "terminada")
    assert lista(esc, esc.ana)[0]["vencimiento"] is None
    cambiar_estado(esc, esc.beto, t["id"], "en_curso")  # reabrirla la vuelve a marcar
    assert lista(esc, esc.ana)[0]["vencimiento"] == "vencida"


def test_indicador_en_lista_tablero_y_mis_tareas(esc, hoy_fijo):
    vencida = crear_tarea(esc, "Vencida", fecha_limite="2026-11-15", responsable_id=esc.beto_id)
    pronto = crear_tarea(esc, "Pronto", fecha_limite="2026-11-19", responsable_id=esc.beto_id)
    marcas = {vencida["id"]: "vencida", pronto["id"]: "por_vencer"}
    assert {t["id"]: t["vencimiento"] for t in lista(esc, esc.beto)} == marcas
    assert {t["id"]: t["vencimiento"] for c in tablero(esc, esc.beto) for t in c["tareas"]} == marcas
    mias = esc.c.get("/api/mis-tareas", headers=esc.beto).json()
    assert {t["id"]: t["vencimiento"] for t in mias} == marcas


# HU-03-006 Replanificar tarea
def replanificar(e, h, tid, **plan):
    return e.c.put(f"/api/tareas/{tid}/plan", headers=h, json=plan)


def historial(e, h, tid):
    r = e.c.get(f"/api/tareas/{tid}/historial", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_replanificar_cambia_todo_y_registra_cada_campo(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id, fecha_limite="2026-11-20", prioridad="media")
    r = replanificar(esc, esc.ana, t["id"], responsable_id=esc.ana_id, fecha_limite="2026-11-27", prioridad="alta")
    assert r.status_code == 200, r.text
    assert (r.json()["responsable_nombre"], r.json()["fecha_limite"], r.json()["prioridad"]) == ("Ana", "2026-11-27", "alta")
    cambios = [(h["tipo"], h["valor_anterior"], h["valor_nuevo"], h["actor_nombre"])
               for h in historial(esc, esc.ana, t["id"])][1:]  # la primera es la asignación al crear
    assert cambios == [("responsable", str(esc.beto_id), str(esc.ana_id), "Ana"),
                       ("fecha_limite", "2026-11-20", "2026-11-27", "Ana"),
                       ("prioridad", "media", "alta", "Ana")]


def test_cambios_visibles_en_todas_las_vistas(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    assert [x["id"] for x in esc.c.get("/api/mis-tareas", headers=esc.beto).json()] == [t["id"]]
    replanificar(esc, esc.ana, t["id"], responsable_id=esc.ana_id, fecha_limite="2026-12-01", prioridad="baja")
    assert esc.c.get("/api/mis-tareas", headers=esc.beto).json() == []
    assert [x["id"] for x in esc.c.get("/api/mis-tareas", headers=esc.ana).json()] == [t["id"]]
    fila = lista(esc, esc.beto)[0]
    assert (fila["responsable_nombre"], fila["fecha_limite"], fila["prioridad"]) == ("Ana", "2026-12-01", "baja")
    detalle = esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()
    assert (detalle["responsable_nombre"], detalle["fecha_limite"], detalle["prioridad"]) == ("Ana", "2026-12-01", "baja")


def test_replanificar_sin_cambios_no_registra_nada(esc):
    t = crear_tarea(esc, fecha_limite="2026-11-20")
    assert replanificar(esc, esc.ana, t["id"], responsable_id=None, fecha_limite="2026-11-20",
                        prioridad="media").status_code == 200
    assert historial(esc, esc.ana, t["id"]) == []


def test_desasignar_y_quitar_fecha(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id, fecha_limite="2026-11-20")
    r = replanificar(esc, esc.ana, t["id"], responsable_id=None, fecha_limite=None, prioridad="media")
    assert (r.json()["responsable_id"], r.json()["fecha_limite"]) == (None, None)


def test_replanificar_invalido_no_cambia_nada(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id, fecha_limite="2026-11-20")
    antes = esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()
    # responsable sin acceso al proyecto: tampoco se guarda la fecha ni la prioridad
    r = replanificar(esc, esc.ana, t["id"], responsable_id=esc.carla_id, fecha_limite="2026-12-01", prioridad="alta")
    assert r.status_code == 400
    assert replanificar(esc, esc.ana, t["id"], responsable_id=esc.beto_id, fecha_limite="mañana",
                        prioridad="alta").status_code == 400
    assert replanificar(esc, esc.ana, t["id"], responsable_id=esc.beto_id, fecha_limite=None,
                        prioridad="urgente").status_code == 400
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json() == antes


def test_solo_el_responsable_del_proyecto_replanifica(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    plan = {"responsable_id": esc.beto_id, "fecha_limite": None, "prioridad": "alta"}
    assert replanificar(esc, esc.beto, t["id"], **plan).status_code == 403   # asignado, pero no planifica
    assert replanificar(esc, esc.carla, t["id"], **plan).status_code == 403  # sin acceso
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()["prioridad"] == "media"


# HU-02-003 Actualizar datos del proyecto
DATOS_PROYECTO = {"nombre": "Web", "objetivo": "Sitio", "fecha_inicio": "2026-11-01", "fecha_fin": "2026-12-01"}


def editar_proyecto(e, h, **cambios):
    return e.c.put(f"/api/proyectos/{e.pid}", headers=h,
                   json={**DATOS_PROYECTO, "responsable_id": e.ana_id, **cambios})


def test_actualizar_proyecto_guarda_valor_anterior_y_actor(esc):
    r = editar_proyecto(esc, esc.ana, objetivo="Sitio nuevo", fecha_fin="2026-12-15")
    assert r.status_code == 200, r.text
    assert (r.json()["objetivo"], r.json()["fecha_fin"]) == ("Sitio nuevo", "2026-12-15")
    ficha = esc.c.get(f"/api/proyectos/{esc.pid}", headers=esc.beto).json()
    assert (ficha["objetivo"], ficha["fecha_fin"]) == ("Sitio nuevo", "2026-12-15")
    cambios = esc.c.get(f"/api/proyectos/{esc.pid}/historial", headers=esc.beto).json()
    assert [(h["campo"], h["valor_anterior"], h["valor_nuevo"], h["actor_nombre"]) for h in cambios] == [
        ("objetivo", "Sitio", "Sitio nuevo", "Ana"), ("fecha_fin", "2026-12-01", "2026-12-15", "Ana")]
    assert all(h["creado_en"] for h in cambios)


def test_cambiar_responsable_del_proyecto(esc):
    dora_id = crear_usuario(esc.c, esc.adm, "dora", "Responsable")
    dora = login(esc.c, "dora", "clave123")
    assert esc.c.get(f"/api/proyectos/{esc.pid}", headers=dora).status_code == 403
    r = editar_proyecto(esc, esc.ana, responsable_id=dora_id)
    assert r.status_code == 200 and r.json()["responsable_nombre"] == "Dora" and r.json()["soy_responsable"] is False
    assert esc.c.get(f"/api/proyectos/{esc.pid}", headers=dora).json()["soy_responsable"] is True  # obtiene acceso
    assert esc.c.get(f"/api/proyectos/{esc.pid}", headers=esc.ana).status_code == 200  # sigue participando
    cambio = esc.c.get(f"/api/proyectos/{esc.pid}/historial", headers=dora).json()[0]
    assert (cambio["anterior_nombre"], cambio["nuevo_nombre"]) == ("Ana", "Dora")
    assert editar_proyecto(esc, esc.ana, objetivo="Otro", responsable_id=dora_id).status_code == 403


def test_actualizar_proyecto_invalido_no_cambia_nada(esc):
    antes = esc.c.get(f"/api/proyectos/{esc.pid}", headers=esc.ana).json()
    assert editar_proyecto(esc, esc.ana, objetivo="X", fecha_fin="2026-10-01").status_code == 400
    assert editar_proyecto(esc, esc.ana, objetivo="X", responsable_id=esc.beto_id).status_code == 400  # Integrante
    assert editar_proyecto(esc, esc.ana, objetivo="").status_code == 400
    assert esc.c.get(f"/api/proyectos/{esc.pid}", headers=esc.ana).json() == antes
    assert esc.c.get(f"/api/proyectos/{esc.pid}/historial", headers=esc.ana).json() == []


def test_actualizar_proyecto_sin_permiso(esc):
    assert editar_proyecto(esc, esc.beto, objetivo="X").status_code == 403   # participa pero no es responsable
    assert editar_proyecto(esc, esc.carla, objetivo="X").status_code == 403  # sin acceso
    assert editar_proyecto(esc, esc.adm, objetivo="X").status_code == 403    # la función no da acceso
    assert esc.c.get(f"/api/proyectos/{esc.pid}/historial", headers=esc.carla).status_code == 403
    assert esc.c.get(f"/api/proyectos/{esc.pid}", headers=esc.ana).json()["objetivo"] == "Sitio"


# HU-04-002 Registrar avance
def avance(e, h, tid, texto, clave=None):
    extra = {"Idempotency-Key": clave} if clave else {}
    return e.c.post(f"/api/tareas/{tid}/avances", headers={**h, **extra}, json={"texto": texto})


def test_avance_queda_con_texto_autor_y_fecha(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    r = avance(esc, esc.beto, t["id"], "Portada lista en borrador")
    assert r.status_code == 201, r.text
    assert (r.json()["texto"], r.json()["autor_nombre"]) == ("Portada lista en borrador", "Beto") and r.json()["creado_en"]
    avance(esc, esc.ana, t["id"], "Revisada con el cliente")
    lista_avances = esc.c.get(f"/api/tareas/{t['id']}/avances", headers=esc.ana).json()
    assert [(a["texto"], a["autor_nombre"]) for a in lista_avances] == [
        ("Portada lista en borrador", "Beto"), ("Revisada con el cliente", "Ana")]


def test_avance_se_distingue_de_los_cambios_de_estado(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    cambiar_estado(esc, esc.beto, t["id"], "en_curso")
    avance(esc, esc.beto, t["id"], "Mitad hecha")
    assert [h["tipo"] for h in historial(esc, esc.ana, t["id"])][1:] == ["estado", "avance"]
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()["estado"] == "en_curso"  # no cambia el estado


def test_avance_sin_permiso_o_invalido(esc):
    t = crear_tarea(esc)  # sin asignar
    assert avance(esc, esc.beto, t["id"], "Hola").status_code == 403    # participa pero no está asignado
    assert avance(esc, esc.carla, t["id"], "Hola").status_code == 403   # sin acceso al proyecto
    assert esc.c.get(f"/api/tareas/{t['id']}/avances", headers=esc.carla).status_code == 403
    assert avance(esc, esc.ana, t["id"], "   ").status_code == 400
    assert esc.c.get(f"/api/tareas/{t['id']}/avances", headers=esc.ana).json() == []
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()["puedo_registrar_avance"] is False


def test_reintentar_avance_no_lo_duplica(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    a = avance(esc, esc.beto, t["id"], "Listo", clave="k-1").json()
    assert avance(esc, esc.beto, t["id"], "Listo", clave="k-1").json()["id"] == a["id"]
    assert len(esc.c.get(f"/api/tareas/{t['id']}/avances", headers=esc.beto).json()) == 1


def test_reasignar_conserva_los_avances_previos(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    avance(esc, esc.beto, t["id"], "Primer avance de Beto")
    replanificar(esc, esc.ana, t["id"], responsable_id=esc.ana_id, fecha_limite=None, prioridad="media")
    lista_avances = esc.c.get(f"/api/tareas/{t['id']}/avances", headers=esc.ana).json()
    assert [(a["texto"], a["autor_nombre"]) for a in lista_avances] == [("Primer avance de Beto", "Beto")]
    assert avance(esc, esc.beto, t["id"], "Otro").status_code == 403  # ya no está asignado
