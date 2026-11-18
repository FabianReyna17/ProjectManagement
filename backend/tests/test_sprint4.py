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


def test_aviso_sin_acceso_no_revela_detalles(esc4):
    crear_tarea(esc4, responsable_id=esc4.beto_id)
    assert avisos(esc4, esc4.beto)[0]["con_acceso"] is True
    esc4.c.delete(f"/api/proyectos/{esc4.pid}/participantes/{esc4.beto_id}", headers=esc4.ana)
    [aviso] = avisos(esc4, esc4.beto)  # el aviso se conserva, pero sin tarea ni proyecto (HU-06-005)
    assert aviso["con_acceso"] is False and aviso["tipo"] == "asignacion"
    assert all(aviso[k] is None for k in ("proyecto_id", "proyecto_nombre", "tarea_id", "tarea_nombre", "actor_nombre"))


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


# HU-06-005 Consultar y abrir mis avisos
def no_leidos(e, h):
    r = e.c.get("/api/avisos/resumen", headers=h)
    assert r.status_code == 200, r.text
    return r.json()["no_leidos"]


def abrir(e, aviso_id, h):
    return e.c.post(f"/api/avisos/{aviso_id}/abrir", headers=h)


def test_contador_de_no_leidos(esc4):
    assert no_leidos(esc4, esc4.beto) == 0
    crear_tarea(esc4, "Diseño", responsable_id=esc4.beto_id)
    crear_tarea(esc4, "Maquetar", responsable_id=esc4.beto_id)
    assert no_leidos(esc4, esc4.beto) == 2
    assert [a["leido"] for a in avisos(esc4, esc4.beto)] == [False, False]
    assert no_leidos(esc4, esc4.ana) == 0 and no_leidos(esc4, esc4.carla) == 0


def test_abrir_aviso_lleva_a_la_tarea_y_lo_marca_leido(esc4):
    t = crear_tarea(esc4, "Diseño", responsable_id=esc4.beto_id)
    crear_tarea(esc4, "Maquetar", responsable_id=esc4.beto_id)
    reciente, primero = avisos(esc4, esc4.beto)

    r = abrir(esc4, primero["id"], esc4.beto)
    assert r.status_code == 200, r.text
    assert r.json()["destino"] == {"tipo": "tarea", "id": t["id"]} and r.json()["leido"] is True
    assert esc4.c.get(f"/api/tareas/{t['id']}", headers=esc4.beto).status_code == 200  # el destino se puede ver
    assert [(a["id"], a["leido"]) for a in avisos(esc4, esc4.beto)] == [(reciente["id"], False), (primero["id"], True)]
    assert no_leidos(esc4, esc4.beto) == 1

    assert abrir(esc4, primero["id"], esc4.beto).status_code == 200  # abrirlo de nuevo no cambia nada
    assert no_leidos(esc4, esc4.beto) == 1


def test_aviso_de_bloqueo_lleva_a_la_tarea_bloqueada(esc4):
    t = crear_tarea(esc4, responsable_id=esc4.beto_id)
    esc4.c.post(f"/api/tareas/{t['id']}/bloqueos", headers=esc4.beto, json={"motivo": "Falta el logo"})
    [aviso] = avisos(esc4, esc4.ana)
    assert abrir(esc4, aviso["id"], esc4.ana).json()["destino"] == {"tipo": "tarea", "id": t["id"]}
    assert esc4.c.get(f"/api/tareas/{t['id']}", headers=esc4.ana).json()["bloqueo"]["motivo"] == "Falta el logo"


def test_abrir_aviso_sin_acceso_vigente_no_muestra_detalle(esc4):
    crear_tarea(esc4, responsable_id=esc4.beto_id)
    [aviso] = avisos(esc4, esc4.beto)
    esc4.c.delete(f"/api/proyectos/{esc4.pid}/participantes/{esc4.beto_id}", headers=esc4.ana)

    r = abrir(esc4, aviso["id"], esc4.beto)
    assert r.status_code == 200
    datos = r.json()
    assert datos["destino"] is None and datos["con_acceso"] is False
    assert datos["tarea_nombre"] is None and datos["proyecto_nombre"] is None and datos["tarea_id"] is None
    assert no_leidos(esc4, esc4.beto) == 0  # se trata como leído para no dejar el contador atascado


def test_solo_se_abren_los_avisos_propios(esc4):
    crear_tarea(esc4, responsable_id=esc4.beto_id)
    [aviso] = avisos(esc4, esc4.beto)
    assert abrir(esc4, aviso["id"], esc4.carla).status_code == 403
    assert abrir(esc4, 9999, esc4.beto).status_code == 403  # inexistente: misma respuesta
    assert no_leidos(esc4, esc4.beto) == 1


def test_marcar_todos_como_leidos(esc4):
    crear_tarea(esc4, "Diseño", responsable_id=esc4.beto_id)
    crear_tarea(esc4, "Maquetar", responsable_id=esc4.carla_id)
    r = esc4.c.post("/api/avisos/leer-todos", headers=esc4.beto)
    assert r.status_code == 200 and r.json() == {"marcados": 1}
    assert no_leidos(esc4, esc4.beto) == 0 and no_leidos(esc4, esc4.carla) == 1  # solo los propios
    assert esc4.c.post("/api/avisos/leer-todos", headers=esc4.beto).json() == {"marcados": 0}


def test_avisos_nuevos_llegan_sin_leer(esc4):
    crear_tarea(esc4, "Diseño", responsable_id=esc4.beto_id)
    esc4.c.post("/api/avisos/leer-todos", headers=esc4.beto)
    crear_tarea(esc4, "Maquetar", responsable_id=esc4.beto_id)
    assert [a["leido"] for a in avisos(esc4, esc4.beto)] == [False, True]


# HU-05-001 Comentar proyecto o tarea
def comentar(e, url, h, texto, clave=None):
    cab = {**h, "Idempotency-Key": clave} if clave else h
    return e.c.post(f"{url}/comentarios", headers=cab, json={"texto": texto})


def comentarios(e, url, h):
    r = e.c.get(f"{url}/comentarios", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_comentar_tarea_y_proyecto(esc):
    t = crear_tarea(esc)
    tarea, proyecto = f"/api/tareas/{t['id']}", f"/api/proyectos/{esc.pid}"
    r = comentar(esc, tarea, esc.beto, "¿Usamos la paleta nueva?")
    assert r.status_code == 201, r.text
    c = r.json()
    assert (c["texto"], c["autor_nombre"], c["tarea_id"], c["proyecto_id"]) == ("¿Usamos la paleta nueva?", "Beto", t["id"], esc.pid)
    assert c["creado_en"]
    assert comentar(esc, proyecto, esc.ana, "Reunión el lunes").status_code == 201

    assert [x["texto"] for x in comentarios(esc, tarea, esc.ana)] == ["¿Usamos la paleta nueva?"]
    assert [x["texto"] for x in comentarios(esc, proyecto, esc.beto)] == ["Reunión el lunes"]  # no mezcla los de la tarea


def test_comentarios_en_orden_y_autor_tras_reasignar(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    tarea = f"/api/tareas/{t['id']}"
    comentar(esc, tarea, esc.beto, "Primero")
    comentar(esc, tarea, esc.ana, "Segundo")
    comentar(esc, tarea, esc.beto, "Tercero")
    esc.c.put(f"{tarea}/responsable", headers=esc.ana, json={"usuario_id": esc.ana_id})
    assert [(x["texto"], x["autor_nombre"]) for x in comentarios(esc, tarea, esc.ana)] == [
        ("Primero", "Beto"), ("Segundo", "Ana"), ("Tercero", "Beto")]


def test_comentario_vacio_se_rechaza(esc):
    t = crear_tarea(esc)
    for texto in ("", "   "):
        assert comentar(esc, f"/api/tareas/{t['id']}", esc.ana, texto).status_code == 400
        assert comentar(esc, f"/api/proyectos/{esc.pid}", esc.ana, texto).status_code == 400
    assert comentarios(esc, f"/api/tareas/{t['id']}", esc.ana) == []


def test_sin_acceso_no_lee_ni_comenta(esc):
    t = crear_tarea(esc)
    tarea, proyecto = f"/api/tareas/{t['id']}", f"/api/proyectos/{esc.pid}"
    comentar(esc, tarea, esc.ana, "Interno")
    for url in (tarea, proyecto):
        assert esc.c.get(f"{url}/comentarios", headers=esc.carla).status_code == 403
        assert comentar(esc, url, esc.carla, "Hola").status_code == 403
        assert esc.c.get(f"{url}/comentarios", headers=esc.adm).status_code == 403  # la función no da acceso
    assert esc.c.get("/api/tareas/9999/comentarios", headers=esc.ana).status_code == 403

    esc.c.delete(f"/api/proyectos/{esc.pid}/participantes/{esc.beto_id}", headers=esc.ana)
    assert esc.c.get(f"{tarea}/comentarios", headers=esc.beto).status_code == 403  # perdió el acceso
    assert comentar(esc, tarea, esc.beto, "¿Sigo?").status_code == 403
    assert len(comentarios(esc, tarea, esc.ana)) == 1


def test_reintentar_comentario_no_lo_duplica(esc):
    url = f"/api/proyectos/{esc.pid}"
    a = comentar(esc, url, esc.beto, "Listo el acta", clave="com-1").json()
    b = comentar(esc, url, esc.beto, "Listo el acta", clave="com-1").json()
    assert a["id"] == b["id"] and len(comentarios(esc, url, esc.ana)) == 1
