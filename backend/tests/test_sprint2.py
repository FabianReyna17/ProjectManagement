"""Pruebas de API del Sprint 2: tareas, estados y bloqueos."""
from types import SimpleNamespace

import pytest

from .helpers import crear_usuario, login


@pytest.fixture()
def esc(client):
    """ana: responsable de un proyecto · beto: integrante del proyecto · carla: integrante sin acceso."""
    adm = login(client, "admin", "Admin123!")
    ana_id = crear_usuario(client, adm, "ana", "Responsable")
    beto_id = crear_usuario(client, adm, "beto", "Integrante")
    carla_id = crear_usuario(client, adm, "carla", "Integrante")
    ana, beto, carla = (login(client, u, "clave123") for u in ("ana", "beto", "carla"))
    r = client.post("/api/proyectos", headers=ana, json={
        "nombre": "Web", "objetivo": "Sitio", "responsable_id": ana_id,
        "fecha_inicio": "2026-11-01", "fecha_fin": "2026-12-01"})
    pid = r.json()["id"]
    assert client.post(f"/api/proyectos/{pid}/participantes", headers=ana,
                       json={"usuario_id": beto_id}).status_code == 201
    return SimpleNamespace(c=client, adm=adm, ana=ana, beto=beto, carla=carla,
                           ana_id=ana_id, beto_id=beto_id, carla_id=carla_id, pid=pid)


def crear_tarea(e, nombre="Diseño", **extra):
    r = e.c.post(f"/api/proyectos/{e.pid}/tareas", headers=e.ana,
                 json={"nombre": nombre, "descripcion": "Maqueta de la portada", **extra})
    assert r.status_code == 201, r.text
    return r.json()


# HU-03-001 Crear tarea
def test_crear_tarea_en_el_proyecto(esc):
    t = crear_tarea(esc, resultado_esperado="Maqueta aprobada")
    assert t["id"] and t["proyecto_id"] == esc.pid and t["estado"] == "pendiente"
    detalle = esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()
    assert detalle["nombre"] == "Diseño" and detalle["resultado_esperado"] == "Maqueta aprobada"
    assert detalle["puedo_planificar"] is False
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()["puedo_planificar"] is True


def test_crear_tarea_sin_permiso_de_planificar(esc):
    c, url, datos = esc.c, f"/api/proyectos/{esc.pid}/tareas", {"nombre": "X", "descripcion": "Y"}
    assert c.post(url, headers=esc.beto, json=datos).status_code == 403   # participa pero no planifica
    assert c.post(url, headers=esc.carla, json=datos).status_code == 403  # sin acceso al proyecto
    assert c.post(url, headers=esc.adm, json=datos).status_code == 403    # la función no da acceso
    assert c.post("/api/proyectos/9999/tareas", headers=esc.ana, json=datos).status_code == 403


def test_crear_tarea_datos_invalidos(esc):
    url = f"/api/proyectos/{esc.pid}/tareas"
    assert esc.c.post(url, headers=esc.ana, json={"nombre": "  ", "descripcion": "Y"}).status_code == 400
    assert esc.c.post(url, headers=esc.ana, json={"nombre": "X"}).status_code == 400


def test_detalle_tarea_sin_acceso(esc):
    t = crear_tarea(esc)
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.carla).status_code == 403
    assert esc.c.get("/api/tareas/9999", headers=esc.ana).status_code == 403


# HU-03-002 Asignar responsable
def test_asignar_responsable_y_registrar_cambio(esc):
    t = crear_tarea(esc)
    url = f"/api/tareas/{t['id']}/responsable"
    r = esc.c.put(url, headers=esc.ana, json={"usuario_id": esc.beto_id})
    assert r.status_code == 200 and r.json()["responsable_nombre"] == "Beto"
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()["soy_asignado"] is True
    assert esc.c.put(url, headers=esc.ana, json={"usuario_id": esc.ana_id}).status_code == 200
    cambios = esc.c.get(f"/api/tareas/{t['id']}/historial", headers=esc.ana).json()
    assert [(h["anterior_nombre"], h["nuevo_nombre"], h["actor_nombre"]) for h in cambios] == [
        (None, "Beto", "Ana"), ("Beto", "Ana", "Ana")]
    assert all(h["tipo"] == "responsable" and h["creado_en"] for h in cambios)


def test_asignar_a_cuenta_ajena_o_inactiva_no_cambia(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    url = f"/api/tareas/{t['id']}/responsable"
    assert esc.c.put(url, headers=esc.ana, json={"usuario_id": esc.carla_id}).status_code == 400  # ajena
    assert esc.c.put(url, headers=esc.ana, json={"usuario_id": 9999}).status_code == 400          # no existe
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()["responsable_id"] == esc.beto_id
    assert len(esc.c.get(f"/api/tareas/{t['id']}/historial", headers=esc.ana).json()) == 1
    # crear con responsable ajeno tampoco se permite
    r = esc.c.post(f"/api/proyectos/{esc.pid}/tareas", headers=esc.ana,
                   json={"nombre": "X", "descripcion": "Y", "responsable_id": esc.carla_id})
    assert r.status_code == 400


def test_solo_el_responsable_del_proyecto_asigna(esc):
    t = crear_tarea(esc)
    url = f"/api/tareas/{t['id']}/responsable"
    assert esc.c.put(url, headers=esc.beto, json={"usuario_id": esc.beto_id}).status_code == 403
    assert esc.c.put(url, headers=esc.carla, json={"usuario_id": esc.carla_id}).status_code == 403


# HU-03-003 Fecha límite y prioridad
def test_fecha_y_prioridad_con_historial(esc):
    t = crear_tarea(esc, fecha_limite="2026-11-20", prioridad="alta")
    assert (t["fecha_limite"], t["prioridad"]) == ("2026-11-20", "alta")
    assert crear_tarea(esc, nombre="Otra")["prioridad"] == "media"  # valor por defecto
    url = f"/api/tareas/{t['id']}/planificacion"
    r = esc.c.put(url, headers=esc.ana, json={"fecha_limite": "2026-11-25", "prioridad": "alta"})
    assert r.status_code == 200 and r.json()["fecha_limite"] == "2026-11-25"
    esc.c.put(url, headers=esc.ana, json={"fecha_limite": "2026-11-25", "prioridad": "baja"})
    cambios = [(h["tipo"], h["valor_anterior"], h["valor_nuevo"], h["actor_nombre"])
               for h in esc.c.get(f"/api/tareas/{t['id']}/historial", headers=esc.ana).json()]
    assert cambios == [("fecha_limite", "2026-11-20", "2026-11-25", "Ana"), ("prioridad", "alta", "baja", "Ana")]


def test_fecha_o_prioridad_invalida_no_guarda(esc):
    t = crear_tarea(esc, fecha_limite="2026-11-20")
    url = f"/api/tareas/{t['id']}/planificacion"
    r = esc.c.put(url, headers=esc.ana, json={"fecha_limite": "2026-02-30", "prioridad": "media"})
    assert r.status_code == 400 and "fecha_limite" in r.json()["detail"]
    r = esc.c.put(url, headers=esc.ana, json={"fecha_limite": "2026-11-21", "prioridad": "urgente"})
    assert r.status_code == 400 and "prioridad" in r.json()["detail"]
    assert esc.c.put(url, headers=esc.beto, json={"fecha_limite": None, "prioridad": "baja"}).status_code == 403
    actual = esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()
    assert (actual["fecha_limite"], actual["prioridad"]) == ("2026-11-20", "media")
    assert esc.c.get(f"/api/tareas/{t['id']}/historial", headers=esc.ana).json() == []


# HU-03-005 Revisar tareas del proyecto
def test_tareas_del_proyecto_sin_mezclar_y_con_permisos(esc):
    asignada = crear_tarea(esc, nombre="A", responsable_id=esc.beto_id)
    libre = crear_tarea(esc, nombre="B")
    otro = esc.c.post("/api/proyectos", headers=esc.ana, json={
        "nombre": "Otro", "objetivo": "O", "responsable_id": esc.ana_id,
        "fecha_inicio": "2026-11-01", "fecha_fin": "2026-12-01"}).json()["id"]
    esc.c.post(f"/api/proyectos/{otro}/tareas", headers=esc.ana, json={"nombre": "C", "descripcion": "D"})

    lista = esc.c.get(f"/api/proyectos/{esc.pid}/tareas", headers=esc.beto).json()
    assert [(t["id"], t["responsable_nombre"]) for t in lista] == [(asignada["id"], "Beto"), (libre["id"], None)]
    assert {"estado", "prioridad", "fecha_limite"} <= lista[0].keys()
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tareas", headers=esc.carla).status_code == 403
    assert esc.c.get(f"/api/proyectos/{otro}/tareas", headers=esc.beto).status_code == 403
