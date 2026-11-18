"""Pruebas de API del Sprint 4: avisos y colaboración."""
import pytest

from app.modules.tareas import repository as repo_tareas

from .test_sprint2 import crear_tarea, esc  # noqa: F401  (esc es el escenario del Sprint 2)


@pytest.fixture()
def esc4(esc):
    """El escenario del Sprint 2 con carla también como integrante del proyecto."""
    assert esc.c.post(f"/api/proyectos/{esc.pid}/participantes", headers=esc.ana,
                      json={"usuario_id": esc.carla_id}).status_code == 201
    return esc


def avisos(e, h):
    r = e.c.get("/api/avisos", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def asignar(e, tid, usuario_id, h=None):
    return e.c.put(f"/api/tareas/{tid}/responsable", headers=h or e.ana, json={"usuario_id": usuario_id})


def replanificar(e, tid, **plan):
    datos = {"responsable_id": None, "fecha_limite": None, "prioridad": "media", **plan}
    return e.c.put(f"/api/tareas/{tid}/plan", headers=e.ana, json=datos)


# HU-06-001 Aviso de nueva asignación
def test_asignar_avisa_al_nuevo_responsable(esc4):
    t = crear_tarea(esc4)
    assert avisos(esc4, esc4.beto) == []
    assert asignar(esc4, t["id"], esc4.beto_id).status_code == 200

    [aviso] = avisos(esc4, esc4.beto)
    assert aviso["tipo"] == "asignacion"
    assert (aviso["tarea_id"], aviso["tarea_nombre"]) == (t["id"], "Diseño")
    assert (aviso["proyecto_id"], aviso["proyecto_nombre"]) == (esc4.pid, "Web")
    assert aviso["actor_nombre"] == "Ana" and aviso["creado_en"]
    assert avisos(esc4, esc4.carla) == [] and avisos(esc4, esc4.ana) == []


def test_crear_tarea_con_responsable_avisa(esc4):
    t = crear_tarea(esc4, responsable_id=esc4.beto_id)
    assert [a["tarea_id"] for a in avisos(esc4, esc4.beto)] == [t["id"]]
    crear_tarea(esc4, "Sin asignar")
    assert len(avisos(esc4, esc4.beto)) == 1


def test_un_aviso_por_asignacion(esc4):
    a = crear_tarea(esc4, "Diseño")
    b = crear_tarea(esc4, "Maquetar")
    asignar(esc4, a["id"], esc4.beto_id)
    asignar(esc4, b["id"], esc4.beto_id)
    assert [x["tarea_id"] for x in avisos(esc4, esc4.beto)] == [b["id"], a["id"]]  # el más reciente primero


def test_reintentar_la_asignacion_no_duplica_el_aviso(esc4):
    t = crear_tarea(esc4)
    for _ in range(3):
        assert asignar(esc4, t["id"], esc4.beto_id).status_code == 200
    assert len(avisos(esc4, esc4.beto)) == 1

    datos = {"nombre": "Logo", "descripcion": "Versión final", "responsable_id": esc4.beto_id}
    cabecera = {**esc4.ana, "Idempotency-Key": "crear-logo-1"}
    for _ in range(2):
        assert esc4.c.post(f"/api/proyectos/{esc4.pid}/tareas", headers=cabecera, json=datos).status_code == 201
    assert len(avisos(esc4, esc4.beto)) == 2


def test_reasignar_avisa_al_nuevo_responsable(esc4):
    t = crear_tarea(esc4, responsable_id=esc4.beto_id)
    assert asignar(esc4, t["id"], esc4.carla_id).status_code == 200
    assert [a["tarea_id"] for a in avisos(esc4, esc4.carla)] == [t["id"]]
    assert len(avisos(esc4, esc4.beto)) == 1  # el aviso anterior se conserva y no llega otro

    assert replanificar(esc4, t["id"], responsable_id=esc4.beto_id).status_code == 200
    assert len(avisos(esc4, esc4.beto)) == 2  # vuelve a recibirla: es otra asignación
    assert replanificar(esc4, t["id"], responsable_id=esc4.beto_id, prioridad="alta").status_code == 200
    assert len(avisos(esc4, esc4.beto)) == 2  # cambiar solo la prioridad no es una asignación


def test_asignarse_a_si_mismo_no_genera_aviso(esc4):
    t = crear_tarea(esc4, responsable_id=esc4.ana_id)
    asignar(esc4, crear_tarea(esc4, "Otra")["id"], esc4.ana_id)
    assert t["responsable_id"] == esc4.ana_id
    assert avisos(esc4, esc4.ana) == []


def test_asignacion_fallida_no_deja_aviso(esc, monkeypatch):
    t = crear_tarea(esc)
    assert asignar(esc, t["id"], esc.carla_id).status_code == 400            # carla no participa
    assert asignar(esc, t["id"], esc.beto_id, h=esc.beto).status_code == 403  # beto no planifica
    r = esc.c.post(f"/api/proyectos/{esc.pid}/tareas", headers=esc.ana,
                   json={"nombre": "X", "descripcion": "Y", "responsable_id": esc.carla_id})
    assert r.status_code == 400
    assert avisos(esc, esc.beto) == [] and avisos(esc, esc.carla) == []

    # El responsable ya se guardó cuando otro campo choca: la transacción se deshace con su aviso
    real = repo_tareas.actualizar_si_vigente
    monkeypatch.setattr(repo_tareas, "actualizar_si_vigente",
                        lambda db, tid, campo, leido, nuevo: campo != "prioridad" and real(db, tid, campo, leido, nuevo))
    assert replanificar(esc, t["id"], responsable_id=esc.beto_id, prioridad="alta").status_code == 409
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()["responsable_id"] is None
    assert avisos(esc, esc.beto) == []


def test_avisos_solo_de_proyectos_con_acceso(esc4):
    crear_tarea(esc4, responsable_id=esc4.beto_id)
    assert len(avisos(esc4, esc4.beto)) == 1
    esc4.c.delete(f"/api/proyectos/{esc4.pid}/participantes/{esc4.beto_id}", headers=esc4.ana)
    assert avisos(esc4, esc4.beto) == []  # sin acceso no se revela la tarea ni el proyecto


def test_avisos_requieren_sesion(esc):
    assert esc.c.get("/api/avisos").status_code == 401


# HU-06-003 Aviso de bloqueo al responsable
def bloquear(e, tid, h, motivo="Falta el logo", clave=None):
    cab = {**h, "Idempotency-Key": clave} if clave else h
    return e.c.post(f"/api/tareas/{tid}/bloqueos", headers=cab, json={"motivo": motivo})


def test_bloqueo_avisa_al_responsable_del_proyecto(esc4):
    t = crear_tarea(esc4, responsable_id=esc4.beto_id)
    assert bloquear(esc4, t["id"], esc4.beto).status_code == 201

    [aviso] = avisos(esc4, esc4.ana)
    assert aviso["tipo"] == "bloqueo" and aviso["tarea_id"] == t["id"] and aviso["proyecto_id"] == esc4.pid
    assert (aviso["actor_nombre"], aviso["bloqueo_motivo"], aviso["bloqueo_resuelto"]) == ("Beto", "Falta el logo", False)
    assert [a["tipo"] for a in avisos(esc4, esc4.beto)] == ["asignacion"]  # quien reporta no recibe este aviso
    assert avisos(esc4, esc4.carla) == []


def test_bloqueo_no_repite_el_aviso(esc4):
    t = crear_tarea(esc4, responsable_id=esc4.beto_id)
    for _ in range(2):  # reintento con la misma clave
        assert bloquear(esc4, t["id"], esc4.beto, clave="bloq-1").status_code == 201
    assert bloquear(esc4, t["id"], esc4.beto, clave="bloq-2").status_code == 409  # ya hay uno abierto
    assert len(avisos(esc4, esc4.ana)) == 1


def test_bloqueo_reportado_por_el_responsable_no_le_avisa(esc4):
    t = crear_tarea(esc4)
    assert bloquear(esc4, t["id"], esc4.ana).status_code == 201
    assert avisos(esc4, esc4.ana) == []


def test_resolver_bloqueo_conserva_el_aviso(esc4):
    t = crear_tarea(esc4, responsable_id=esc4.beto_id)
    b = bloquear(esc4, t["id"], esc4.beto).json()
    assert esc4.c.post(f"/api/tareas/{t['id']}/bloqueos/{b['id']}/resolver", headers=esc4.ana,
                       json={"resolucion": "Llegó el logo"}).status_code == 200
    [aviso] = avisos(esc4, esc4.ana)
    assert aviso["bloqueo_resuelto"] is True and aviso["bloqueo_motivo"] == "Falta el logo"

    assert bloquear(esc4, t["id"], esc4.beto, motivo="Falta el texto").status_code == 201
    nuevo, anterior = avisos(esc4, esc4.ana)  # un bloqueo nuevo es otro aviso
    assert (nuevo["bloqueo_motivo"], nuevo["bloqueo_resuelto"]) == ("Falta el texto", False)
    assert anterior["bloqueo_resuelto"] is True


def test_bloqueo_rechazado_no_deja_aviso(esc4):
    t = crear_tarea(esc4, responsable_id=esc4.beto_id)
    assert bloquear(esc4, t["id"], esc4.carla).status_code == 403  # participa pero no es la asignada
    esc4.c.put(f"/api/tareas/{t['id']}/estado", headers=esc4.beto, json={"estado": "en_curso"})
    esc4.c.put(f"/api/tareas/{t['id']}/estado", headers=esc4.beto, json={"estado": "terminada"})
    assert bloquear(esc4, t["id"], esc4.beto).status_code == 400   # terminada
    assert avisos(esc4, esc4.ana) == []
