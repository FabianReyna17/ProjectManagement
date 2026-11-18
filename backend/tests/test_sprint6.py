"""Pruebas de API del Sprint 6: administración de cuentas, respaldo y release."""
from .helpers import funcion_id, login
from .test_sprint2 import crear_tarea, esc  # noqa: F401  (esc es el escenario del Sprint 2)


def desactivar(e, uid, h=None):
    return e.c.post(f"/api/usuarios/{uid}/desactivacion", headers=h or e.adm)


def eventos_cuenta(uid):
    from app.db.database import get_engine, varios
    with get_engine().connect() as db:
        return varios(db, "SELECT tipo, valor_anterior, valor_nuevo, actor_id FROM eventos_cuenta WHERE usuario_id = :u",
                      u=uid)


# HU-01-009 Desactivar cuenta
def test_cuenta_desactivada_no_entra_ni_actua_con_la_sesion_abierta(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    r = desactivar(esc, esc.beto_id)
    assert r.status_code == 200, r.text
    assert (r.json()["activo"], r.json()["desactivado_por_nombre"]) == (False, "Administrador")
    # la sesión que ya tenía abierta deja de servir para consultar y para actuar
    assert esc.c.get("/api/proyectos", headers=esc.beto).status_code == 401
    r = esc.c.put(f"/api/tareas/{t['id']}/estado", headers=esc.beto, json={"estado": "en_curso"})
    assert r.status_code == 401
    assert esc.c.get(f"/api/tareas/{t['id']}", headers=esc.ana).json()["estado"] == "pendiente"
    # no puede volver a entrar; el mensaje es el genérico (no revela que la cuenta existe)
    r = esc.c.post("/api/auth/login", json={"usuario": "beto", "password": "clave123"})
    assert (r.status_code, r.json()["detail"]) == (401, "Usuario o contraseña incorrectos")
    # ya no se le puede asignar trabajo ni aparece entre las personas para elegir
    assert esc.c.put(f"/api/tareas/{crear_tarea(esc, 'Otra')['id']}/responsable", headers=esc.ana,
                     json={"responsable_id": esc.beto_id}).status_code == 400
    assert esc.beto_id not in [x["id"] for x in esc.c.get("/api/usuarios", headers=esc.ana).json()]


def test_su_historial_conserva_la_autoria(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    url = f"/api/tareas/{t['id']}"
    assert esc.c.put(f"{url}/estado", headers=esc.beto, json={"estado": "en_curso"}).status_code == 200
    assert esc.c.post(f"{url}/avances", headers=esc.beto, json={"texto": "Portada lista"}).status_code == 201
    assert esc.c.post(f"/api/proyectos/{esc.pid}/comentarios", headers=esc.beto,
                      json={"texto": "Revisen la portada"}).status_code == 201
    assert desactivar(esc, esc.beto_id).status_code == 200

    assert esc.c.get(f"{url}/historial", headers=esc.ana).json()[-1]["actor_nombre"] == "Beto"
    assert esc.c.get(f"{url}/avances", headers=esc.ana).json()[0]["autor_nombre"] == "Beto"
    [com] = esc.c.get(f"/api/proyectos/{esc.pid}/comentarios", headers=esc.ana).json()
    assert (com["autor_nombre"], com["texto"]) == ("Beto", "Revisen la portada")
    detalle = esc.c.get(url, headers=esc.ana).json()
    assert (detalle["responsable_id"], detalle["estado"]) == (esc.beto_id, "en_curso")
    # sigue en la lista de participantes, marcado como cuenta desactivada
    beto = next(x for x in esc.c.get(f"/api/proyectos/{esc.pid}/participantes", headers=esc.ana).json()
                if x["id"] == esc.beto_id)
    assert (beto["nombre"], beto["cuenta_activa"]) == ("Beto", False)


def test_desactivar_dos_veces_no_cambia_el_estado(esc):
    primera = desactivar(esc, esc.beto_id).json()
    otro_admin = esc.c.post("/api/usuarios", headers=esc.adm, json={
        "usuario": "root2", "nombre": "Otra Admin", "password": "clave123", "funcion_id": 1}).json()
    r = desactivar(esc, esc.beto_id, login(esc.c, "root2", "clave123"))
    assert r.status_code == 200 and otro_admin["id"]
    assert r.json() == primera  # misma fecha y mismo actor: no se reescribe
    assert eventos_cuenta(esc.beto_id) == [
        {"tipo": "desactivacion", "valor_anterior": "activa", "valor_nuevo": "desactivada", "actor_id": 1}]
    cuentas = esc.c.get("/api/usuarios", headers=esc.adm, params={"todas": 1}).json()
    assert [x["usuario"] for x in cuentas if not x["activo"]] == ["beto"]


def test_solo_admin_desactiva_y_no_su_propia_cuenta(esc):
    for h in (esc.ana, esc.beto):
        assert desactivar(esc, esc.carla_id, h).status_code == 403
    assert desactivar(esc, 1).status_code == 400  # la propia: el admin no se deja sin acceso
    assert desactivar(esc, 9999).status_code == 404
    assert esc.c.get("/api/usuarios", headers=esc.ana, params={"todas": 1}).status_code == 403
    assert all(x["activo"] for x in esc.c.get("/api/usuarios", headers=esc.adm, params={"todas": 1}).json())
    assert login(esc.c, "carla", "clave123")  # nada cambió


# HU-01-008 Cambiar función de cuenta
def cambiar_funcion(e, uid, funcion, h=None):
    return e.c.put(f"/api/usuarios/{uid}/funcion", headers=h or e.adm, json={"funcion_id": funcion_id(e.c, e.adm, funcion)})


def nuevo_proyecto(e, h, responsable_id):
    return e.c.post("/api/proyectos", headers=h, json={
        "nombre": "Nuevo", "objetivo": "Objetivo", "responsable_id": responsable_id,
        "fecha_inicio": "2026-11-01", "fecha_fin": "2026-12-01"})


def test_la_nueva_funcion_aplica_de_inmediato_con_la_sesion_abierta(esc):
    assert nuevo_proyecto(esc, esc.beto, esc.beto_id).status_code == 403  # Integrante
    r = cambiar_funcion(esc, esc.beto_id, "Responsable")
    assert r.status_code == 200, r.text
    assert (r.json()["funcion"], r.json()["activo"]) == ("Responsable", True)
    assert esc.c.get("/api/auth/me", headers=esc.beto).json()["funcion"] == "Responsable"
    assert nuevo_proyecto(esc, esc.beto, esc.beto_id).status_code == 201  # mismo token
    # y al quitarla también: ana deja de poder crear proyectos, pero sigue a cargo del suyo
    assert cambiar_funcion(esc, esc.ana_id, "Integrante").status_code == 200
    assert nuevo_proyecto(esc, esc.ana, esc.ana_id).status_code == 403
    assert esc.c.get(f"/api/proyectos/{esc.pid}", headers=esc.ana).json()["responsable_id"] == esc.ana_id
    assert esc.c.get("/api/funciones", headers=esc.carla).status_code == 403
    assert cambiar_funcion(esc, esc.carla_id, "Admin").status_code == 200
    assert esc.c.get("/api/funciones", headers=esc.carla).status_code == 200


def test_el_cambio_queda_registrado(esc):
    cambiar_funcion(esc, esc.beto_id, "Supervisor")
    assert cambiar_funcion(esc, esc.beto_id, "Supervisor").status_code == 200  # misma función: no registra
    assert eventos_cuenta(esc.beto_id) == [
        {"tipo": "funcion", "valor_anterior": "Integrante", "valor_nuevo": "Supervisor", "actor_id": 1}]


def test_solo_admin_cambia_funciones_y_nadie_la_propia(esc):
    assert cambiar_funcion(esc, esc.beto_id, "Admin", esc.ana).status_code == 403   # Responsable
    assert cambiar_funcion(esc, esc.beto_id, "Admin", esc.beto).status_code == 403  # ni la propia
    assert cambiar_funcion(esc, 1, "Integrante").status_code == 400                 # el Admin tampoco
    assert cambiar_funcion(esc, 9999, "Integrante").status_code == 404
    r = esc.c.put(f"/api/usuarios/{esc.beto_id}/funcion", headers=esc.adm, json={"funcion_id": 999})
    assert r.status_code == 400
    desactivar(esc, esc.carla_id)
    assert cambiar_funcion(esc, esc.carla_id, "Admin").status_code == 409  # cuenta desactivada
    assert eventos_cuenta(esc.beto_id) == []
    assert esc.c.get("/api/auth/me", headers=esc.beto).json()["funcion"] == "Integrante"
