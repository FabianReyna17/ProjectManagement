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


# HU-03-004 Consultar mis tareas
def test_mis_tareas_solo_propias_y_accesibles(esc):
    t1 = crear_tarea(esc, nombre="Tarde", responsable_id=esc.beto_id, fecha_limite="2026-11-30")
    t2 = crear_tarea(esc, nombre="Pronto", responsable_id=esc.beto_id, fecha_limite="2026-11-10", prioridad="alta")
    crear_tarea(esc, nombre="De Ana", responsable_id=esc.ana_id)
    mias = esc.c.get("/api/mis-tareas", headers=esc.beto).json()
    assert [t["id"] for t in mias] == [t2["id"], t1["id"]]  # ordenadas por fecha límite
    assert mias[0]["proyecto_nombre"] == "Web" and mias[0]["prioridad"] == "alta"

    # reasignada → ya no aparece
    esc.c.put(f"/api/tareas/{t2['id']}/responsable", headers=esc.ana, json={"usuario_id": esc.ana_id})
    assert [t["id"] for t in esc.c.get("/api/mis-tareas", headers=esc.beto).json()] == [t1["id"]]
    # sin acceso al proyecto → ya no aparece ni se abre
    esc.c.delete(f"/api/proyectos/{esc.pid}/participantes/{esc.beto_id}", headers=esc.ana)
    assert esc.c.get("/api/mis-tareas", headers=esc.beto).json() == []
    assert esc.c.get(f"/api/tareas/{t1['id']}", headers=esc.beto).status_code == 403
    assert esc.c.get("/api/mis-tareas").status_code == 401


# HU-04-001 Cambiar estado de tarea
def test_transiciones_validas_se_reflejan_y_registran(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    url = f"/api/tareas/{t['id']}/estado"
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()["transiciones"] == ["en_curso"]
    r = esc.c.put(url, headers=esc.beto, json={"estado": "en_curso"})
    assert r.status_code == 200 and r.json()["estado"] == "en_curso"
    assert esc.c.get("/api/mis-tareas", headers=esc.beto).json()[0]["estado"] == "en_curso"
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tareas", headers=esc.ana).json()[0]["estado"] == "en_curso"
    assert esc.c.put(url, headers=esc.ana, json={"estado": "terminada"}).status_code == 200  # responsable del proyecto
    estados = [(h["valor_anterior"], h["valor_nuevo"], h["actor_nombre"])
               for h in esc.c.get(f"/api/tareas/{t['id']}/historial", headers=esc.ana).json() if h["tipo"] == "estado"]
    assert estados == [("pendiente", "en_curso", "Beto"), ("en_curso", "terminada", "Ana")]


def test_transicion_invalida_o_sin_permiso_no_cambia(esc):
    t = crear_tarea(esc)  # sin asignar
    url = f"/api/tareas/{t['id']}/estado"
    r = esc.c.put(url, headers=esc.ana, json={"estado": "terminada"})
    assert r.status_code == 400 and "Pendiente" in r.json()["detail"]
    assert esc.c.put(url, headers=esc.ana, json={"estado": "archivada"}).status_code == 400
    r = esc.c.put(url, headers=esc.beto, json={"estado": "en_curso"})  # participa pero no está asignado
    assert r.status_code == 403 and "asignada" in r.json()["detail"]
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()["transiciones"] == []
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()["estado"] == "pendiente"


# HU-04-003 Registrar bloqueo
def test_registrar_bloqueo_visible_sin_cambiar_estado(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    esc.c.put(f"/api/tareas/{t['id']}/estado", headers=esc.beto, json={"estado": "en_curso"})
    r = esc.c.post(f"/api/tareas/{t['id']}/bloqueos", headers=esc.beto, json={"motivo": "Falta acceso al servidor"})
    assert r.status_code == 201
    b = r.json()
    assert b["abierto_por_nombre"] == "Beto" and b["abierto_en"] and b["resuelto_en"] is None

    detalle = esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()
    assert detalle["estado"] == "en_curso" and detalle["bloqueada"] is True  # no reemplaza el estado
    assert detalle["bloqueo"]["motivo"] == "Falta acceso al servidor"
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tareas", headers=esc.ana).json()[0]["bloqueada"]
    assert esc.c.get("/api/mis-tareas", headers=esc.beto).json()[0]["bloqueada"]
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()["transiciones"] == ["pendiente"]
    # no se termina con un bloqueo abierto
    assert esc.c.put(f"/api/tareas/{t['id']}/estado", headers=esc.beto, json={"estado": "terminada"}).status_code == 400


def test_bloqueo_sin_motivo_duplicado_o_sin_permiso(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    url = f"/api/tareas/{t['id']}/bloqueos"
    assert esc.c.post(url, headers=esc.beto, json={"motivo": "   "}).status_code == 400
    assert esc.c.post(url, headers=esc.carla, json={"motivo": "X"}).status_code == 403
    assert esc.c.post(url, headers=esc.beto, json={"motivo": "Esperando datos"}).status_code == 201
    r = esc.c.post(url, headers=esc.beto, json={"motivo": "Esperando datos"})
    assert r.status_code == 409  # no abre dos bloqueos a la vez
    bloqueos = [h for h in esc.c.get(f"/api/tareas/{t['id']}/historial", headers=esc.ana).json() if h["tipo"] == "bloqueo"]
    assert len(bloqueos) == 1


# HU-04-004 Resolver bloqueo
def bloquear(e, t, motivo="Falta acceso"):
    r = e.c.post(f"/api/tareas/{t['id']}/bloqueos", headers=e.beto, json={"motivo": motivo})
    assert r.status_code == 201, r.text
    return r.json()


def test_resolver_bloqueo_conserva_historia(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    esc.c.put(f"/api/tareas/{t['id']}/estado", headers=esc.beto, json={"estado": "en_curso"})
    b = bloquear(esc, t)
    url = f"/api/tareas/{t['id']}/bloqueos/{b['id']}/resolver"
    r = esc.c.post(url, headers=esc.ana, json={"resolucion": "Se dio acceso"})
    assert r.status_code == 200
    assert (r.json()["resuelto_por_nombre"], r.json()["resolucion"]) == ("Ana", "Se dio acceso")
    assert r.json()["resuelto_en"]

    detalle = esc.c.get(f"/api/tareas/{t['id']}", headers=esc.beto).json()
    assert detalle["bloqueada"] is False and detalle["bloqueo"] is None and detalle["estado"] == "en_curso"
    assert not esc.c.get("/api/mis-tareas", headers=esc.beto).json()[0]["bloqueada"]
    [guardado] = esc.c.get(f"/api/tareas/{t['id']}/bloqueos", headers=esc.beto).json()
    assert (guardado["motivo"], guardado["resolucion"]) == ("Falta acceso", "Se dio acceso")
    # ya se puede terminar y volver a bloquear si surge otro impedimento
    assert esc.c.put(f"/api/tareas/{t['id']}/estado", headers=esc.beto, json={"estado": "terminada"}).status_code == 200


def test_resolver_bloqueo_cerrado_sin_explicacion_o_sin_permiso(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    b = bloquear(esc, t)
    url = f"/api/tareas/{t['id']}/bloqueos/{b['id']}/resolver"
    assert esc.c.post(url, headers=esc.ana, json={"resolucion": ""}).status_code == 400
    assert esc.c.post(url, headers=esc.beto, json={"resolucion": "Listo"}).status_code == 403
    assert esc.c.post(f"/api/tareas/{t['id']}/bloqueos/999/resolver", headers=esc.ana,
                      json={"resolucion": "X"}).status_code == 404
    assert esc.c.post(url, headers=esc.ana, json={"resolucion": "Listo"}).status_code == 200
    r = esc.c.post(url, headers=esc.ana, json={"resolucion": "Otra vez"})
    assert r.status_code == 409
    [guardado] = esc.c.get(f"/api/tareas/{t['id']}/bloqueos", headers=esc.ana).json()
    assert guardado["resolucion"] == "Listo"  # no cambia su historia


# HU-08-002 Reintentar sin duplicar
def test_reintento_con_la_misma_clave_no_duplica(esc):
    url, datos = f"/api/proyectos/{esc.pid}/tareas", {"nombre": "Doble clic", "descripcion": "D"}
    clave = {**esc.ana, "Idempotency-Key": "tarea-123"}
    r1 = esc.c.post(url, headers=clave, json=datos)
    r2 = esc.c.post(url, headers=clave, json=datos)  # reintento tras perder la respuesta
    assert r1.status_code == r2.status_code == 201 and r1.json()["id"] == r2.json()["id"]
    assert len(esc.c.get(url, headers=esc.ana).json()) == 1

    # dos acciones intencionales con contenido igual pero claves distintas → dos tareas
    esc.c.post(url, headers={**esc.ana, "Idempotency-Key": "tarea-456"}, json=datos)
    esc.c.post(url, headers=esc.ana, json=datos)  # sin clave: siempre crea
    assert len(esc.c.get(url, headers=esc.ana).json()) == 3


def test_reintento_de_proyecto_y_bloqueo(esc):
    clave = {**esc.ana, "Idempotency-Key": "proy-1"}
    datos = {"nombre": "Nuevo", "objetivo": "O", "responsable_id": esc.ana_id,
             "fecha_inicio": "2026-11-01", "fecha_fin": "2026-12-01"}
    ids = {esc.c.post("/api/proyectos", headers=clave, json=datos).json()["id"] for _ in range(2)}
    assert len(ids) == 1 and len(esc.c.get("/api/proyectos", headers=esc.ana).json()) == 2

    t = crear_tarea(esc, responsable_id=esc.beto_id)
    url, clave = f"/api/tareas/{t['id']}/bloqueos", {**esc.beto, "Idempotency-Key": "bloq-1"}
    r1 = esc.c.post(url, headers=clave, json={"motivo": "Sin datos"})
    r2 = esc.c.post(url, headers=clave, json={"motivo": "Sin datos"})
    assert r1.status_code == r2.status_code == 201 and r1.json()["id"] == r2.json()["id"]  # muestra el existente


def test_primer_envio_fallido_se_registra_una_vez_en_el_reintento(esc):
    url, clave = f"/api/proyectos/{esc.pid}/tareas", {**esc.ana, "Idempotency-Key": "k-1"}
    malo = esc.c.post(url, headers=clave, json={"nombre": "T", "descripcion": "D", "responsable_id": esc.carla_id})
    assert malo.status_code == 400  # no se guardó: la clave tampoco
    ok = [esc.c.post(url, headers=clave, json={"nombre": "T", "descripcion": "D"}) for _ in range(2)]
    assert [r.status_code for r in ok] == [201, 201] and ok[0].json()["id"] == ok[1].json()["id"]
    assert len(esc.c.get(url, headers=esc.ana).json()) == 1


# Orden coherente de la lista del proyecto (igual que "Mis tareas")
def test_orden_de_tareas_del_proyecto(esc):
    terminada = crear_tarea(esc, nombre="Terminada", responsable_id=esc.beto_id, prioridad="alta")
    for estado in ("en_curso", "terminada"):
        esc.c.put(f"/api/tareas/{terminada['id']}/estado", headers=esc.ana, json={"estado": estado})
    sin_fecha = crear_tarea(esc, nombre="Sin fecha", prioridad="alta")
    baja = crear_tarea(esc, nombre="Baja", fecha_limite="2026-11-15", prioridad="baja")
    alta = crear_tarea(esc, nombre="Alta", fecha_limite="2026-11-15", prioridad="alta")
    pronto = crear_tarea(esc, nombre="Pronto", fecha_limite="2026-11-10", prioridad="baja")
    bloqueada = crear_tarea(esc, nombre="Bloqueada", responsable_id=esc.beto_id, fecha_limite="2026-11-30")
    bloquear(esc, bloqueada)
    orden = [t["id"] for t in esc.c.get(f"/api/proyectos/{esc.pid}/tareas", headers=esc.ana).json()]
    assert orden == [bloqueada["id"], pronto["id"], alta["id"], baja["id"], sin_fecha["id"], terminada["id"]]
