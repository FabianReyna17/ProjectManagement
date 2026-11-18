"""Pruebas de API del Sprint 5: supervisión y cierre de proyectos."""
import pytest

from .helpers import crear_usuario, login
from .test_sprint2 import esc  # noqa: F401  (esc es el escenario del Sprint 2)
from .test_sprint4 import en_dias, escenario_resumen


def cerrar_en_bd(pid):
    """El cierre llega con HU-02-005; aquí solo se deja el proyecto en ese estado."""
    from sqlalchemy import text

    from app.db.database import get_engine
    with get_engine().begin() as conn:
        conn.execute(text("UPDATE proyectos SET estado = 'cerrado' WHERE id = :id"), {"id": pid})


# HU-07-005 Estado general de los proyectos
@pytest.fixture()
def sup(esc):
    """sofia (Supervisor) participa en Web (con una tarea vencida y una bloqueada) y en App (al día).
    Interno también tiene una tarea vencida, pero sofia no participa en él."""
    c = esc.c
    esc.sofia_id = crear_usuario(c, esc.adm, "sofia", "Supervisor")
    esc.sofia = login(c, "sofia", "clave123")
    esc.ids = escenario_resumen(esc)
    esc.proyectos = {"Web": esc.pid}
    for nombre, fin in (("App", "2026-11-20"), ("Interno", "2026-11-10")):
        r = c.post("/api/proyectos", headers=esc.ana, json={
            "nombre": nombre, "objetivo": "Objetivo", "responsable_id": esc.ana_id,
            "fecha_inicio": "2026-11-01", "fecha_fin": fin})
        esc.proyectos[nombre] = r.json()["id"]
    for nombre in ("Web", "App"):
        assert c.post(f"/api/proyectos/{esc.proyectos[nombre]}/participantes", headers=esc.ana,
                      json={"usuario_id": esc.sofia_id}).status_code == 201
    c.post(f"/api/proyectos/{esc.proyectos['App']}/tareas", headers=esc.ana,
           json={"nombre": "Al día", "descripcion": "D", "fecha_limite": en_dias(10)})
    c.post(f"/api/proyectos/{esc.proyectos['Interno']}/tareas", headers=esc.ana,
           json={"nombre": "Atrasada", "descripcion": "D", "fecha_limite": en_dias(-1)})
    return esc


def estado_general(e, h, **params):
    r = e.c.get("/api/estado-proyectos", headers=h, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_supervisor_ve_solo_sus_proyectos_autorizados(sup):
    r = estado_general(sup, sup.sofia)
    assert [p["nombre"] for p in r["proyectos"]] == ["Web", "App"]  # Interno ni aparece
    assert r["totales"] == {"proyectos": 2, "requieren_atencion": 1, "vencidas": 1, "bloqueadas": 1}
    web = r["proyectos"][0]
    assert (web["responsable_nombre"], web["estado"], web["fecha_fin"]) == ("Ana", "planificado", "2026-12-01")
    # quien participa en los tres ve también Interno y sus cifras
    r = estado_general(sup, sup.ana)
    assert {p["nombre"] for p in r["proyectos"]} == {"Web", "App", "Interno"}
    assert r["totales"]["vencidas"] == 2


def test_cifras_coinciden_con_el_resumen_y_la_lista_de_cada_proyecto(sup):
    for p in estado_general(sup, sup.sofia)["proyectos"]:
        r = sup.c.get(f"/api/proyectos/{p['id']}/resumen", headers=sup.sofia).json()
        assert (p["total"], p["abiertas"]) == (r["total"], r["abiertas"])
        for clave, ind in p["indicadores"].items():
            assert ind == r["indicadores"][clave]
            lista = sup.c.get(f"/api/proyectos/{p['id']}/tareas", headers=sup.sofia, params=ind["filtro"]).json()
            assert len(lista) == ind["total"]  # cada cifra abre las tareas que la explican


def test_requiere_atencion_con_tareas_vencidas_o_bloqueadas(sup):
    web, app = estado_general(sup, sup.sofia)["proyectos"]
    assert (web["requiere_atencion"], app["requiere_atencion"]) == (True, False)
    # se resuelve el bloqueo y la tarea vencida se termina: Web deja de requerir atención
    tid = sup.ids["bloqueada"]
    [bloqueo] = sup.c.get(f"/api/tareas/{tid}/bloqueos", headers=sup.ana).json()
    assert sup.c.post(f"/api/tareas/{tid}/bloqueos/{bloqueo['id']}/resolver", headers=sup.ana,
                      json={"resolucion": "Acceso concedido"}).status_code == 200
    for est in ("en_curso", "terminada"):
        sup.c.put(f"/api/tareas/{sup.ids['vencida']}/estado", headers=sup.ana, json={"estado": est})
    r = estado_general(sup, sup.sofia)
    assert [p["nombre"] for p in r["proyectos"]] == ["App", "Web"]  # sin atención: por fecha de término
    assert not any(p["requiere_atencion"] for p in r["proyectos"])
    assert r["totales"] == {"proyectos": 2, "requieren_atencion": 0, "vencidas": 0, "bloqueadas": 0}


def test_cerrados_se_incluyen_o_excluyen(sup):
    cerrar_en_bd(sup.pid)
    r = estado_general(sup, sup.sofia)
    assert [p["nombre"] for p in r["proyectos"]] == ["App"]
    assert r["totales"] == {"proyectos": 1, "requieren_atencion": 0, "vencidas": 0, "bloqueadas": 0}
    r = estado_general(sup, sup.sofia, incluir_cerrados="true")
    assert [(p["nombre"], p["estado"]) for p in r["proyectos"]] == [("Web", "cerrado"), ("App", "planificado")]


def test_estado_general_sin_permiso_o_sin_proyectos(sup):
    assert sup.c.get("/api/estado-proyectos", headers=sup.beto).status_code == 403  # integrante
    assert sup.c.get("/api/estado-proyectos").status_code == 401
    assert sup.c.get("/api/estado-proyectos", headers=sup.sofia, params={"incluir_cerrados": "quizas"}).status_code == 400
    crear_usuario(sup.c, sup.adm, "dora", "Supervisor")
    r = estado_general(sup, login(sup.c, "dora", "clave123"))
    assert r == {"proyectos": [], "totales": {"proyectos": 0, "requieren_atencion": 0, "vencidas": 0, "bloqueadas": 0}}
