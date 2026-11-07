import pytest
from sqlalchemy import text

from app.db.database import get_engine

from .helpers import crear_usuario, login


@pytest.fixture()
def escenario(client):
    """admin + responsable (con un proyecto) + integrante sin acceso."""
    adm = login(client, "admin", "Admin123!")
    resp_id = crear_usuario(client, adm, "ana", "Responsable")
    int_id = crear_usuario(client, adm, "beto", "Integrante")
    ana = login(client, "ana", "clave123")
    beto = login(client, "beto", "clave123")
    r = client.post("/api/proyectos", headers=ana, json={
        "nombre": "Web", "objetivo": "Sitio", "responsable_id": resp_id,
        "fecha_inicio": "2026-11-01", "fecha_fin": "2026-12-01"})
    assert r.status_code == 201
    return {"c": client, "adm": adm, "ana": ana, "beto": beto, "beto_id": int_id, "pid": r.json()["id"]}


# HU-01-001 Registrar cuenta
def test_registro_valido_duplicado_y_vacio(client):
    adm = login(client, "admin", "Admin123!")
    crear_usuario(client, adm, "carla", "Integrante")
    dup = client.post("/api/usuarios", headers=adm, json={
        "usuario": "carla", "nombre": "X", "password": "clave123", "funcion_id": 3})
    assert dup.status_code == 409
    vacio = client.post("/api/usuarios", headers=adm, json={"usuario": "", "nombre": "", "password": "", "funcion_id": 3})
    assert vacio.status_code == 400
    carla = login(client, "carla", "clave123")
    assert client.get("/api/proyectos", headers=carla).json() == []


def test_solo_admin_registra(escenario):
    c = escenario["c"]
    r = c.post("/api/usuarios", headers=escenario["ana"], json={
        "usuario": "zz", "nombre": "Z", "password": "clave123", "funcion_id": 3})
    assert r.status_code == 403


# HU-01-002 Función inicial
def test_funcion_inexistente(client):
    adm = login(client, "admin", "Admin123!")
    r = client.post("/api/usuarios", headers=adm, json={
        "usuario": "dani", "nombre": "D", "password": "clave123", "funcion_id": 999})
    assert r.status_code == 400


# HU-01-003 Iniciar sesión
def test_login_invalido_mensaje_generico(client):
    r1 = client.post("/api/auth/login", json={"usuario": "admin", "password": "mala"})
    r2 = client.post("/api/auth/login", json={"usuario": "noexiste", "password": "mala"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"]


# HU-02-001 Crear proyecto
def test_crear_proyecto_validaciones(escenario):
    c, ana = escenario["c"], escenario["ana"]
    base = {"nombre": "P", "objetivo": "O", "responsable_id": 2,
            "fecha_inicio": "2026-11-10", "fecha_fin": "2026-11-01"}
    assert c.post("/api/proyectos", headers=ana, json=base).status_code == 400
    assert c.post("/api/proyectos", headers=ana, json={"nombre": "P"}).status_code == 400
    assert c.post("/api/proyectos", headers=escenario["beto"], json={**base, "fecha_fin": "2026-12-01"}).status_code == 403


# HU-01-005 / HU-01-006 Participantes y proyectos autorizados
def test_dar_y_retirar_acceso(escenario):
    c, ana, beto, pid, bid = escenario["c"], escenario["ana"], escenario["beto"], escenario["pid"], escenario["beto_id"]
    assert c.get("/api/proyectos", headers=beto).json() == []
    assert c.post(f"/api/proyectos/{pid}/participantes", headers=ana, json={"usuario_id": bid}).status_code == 201
    assert [p["id"] for p in c.get("/api/proyectos", headers=beto).json()] == [pid]
    # beto no es responsable: no puede administrar participantes
    assert c.delete(f"/api/proyectos/{pid}/participantes/{bid}", headers=beto).status_code == 403
    assert c.delete(f"/api/proyectos/{pid}/participantes/{bid}", headers=ana).status_code == 200
    assert c.get("/api/proyectos", headers=beto).json() == []


# HU-01-007 / HU-02-002 Acciones no autorizadas y ficha
def test_ficha_sin_acceso_y_sin_token(escenario):
    c, pid = escenario["c"], escenario["pid"]
    assert c.get(f"/api/proyectos/{pid}", headers=escenario["ana"]).json()["nombre"] == "Web"
    assert c.get(f"/api/proyectos/{pid}", headers=escenario["beto"]).status_code == 403
    assert c.get(f"/api/proyectos/{pid}", headers=escenario["adm"]).status_code == 403  # la función no da acceso
    assert c.get(f"/api/proyectos/{pid}").status_code == 401
    assert c.get("/api/proyectos/9999", headers=escenario["ana"]).status_code == 403


# HU-01-004 Cerrar sesión
def test_logout_invalida_token(escenario):
    c, ana = escenario["c"], escenario["ana"]
    assert c.post("/api/auth/logout", headers=ana).status_code == 200
    assert c.get(f"/api/proyectos/{escenario['pid']}", headers=ana).status_code == 401


def sql(consulta, **params):
    with get_engine().connect() as conn:
        conn.execute(text(consulta), params)
        conn.commit()


# HU-01-003 Freno a la fuerza bruta: igual para cuentas que existen y que no
def test_freno_a_intentos_fallidos(client):
    from app.modules.acceso.service import INTENTOS
    for usuario in ("admin", "fantasma"):
        respuestas = [client.post("/api/auth/login", json={"usuario": usuario, "password": "mala"}) for _ in range(5)]
        assert {r.status_code for r in respuestas} == {401}
        r = client.post("/api/auth/login", json={"usuario": usuario, "password": "Admin123!"})
        assert r.status_code == 429 and "Demasiados intentos" in r.json()["detail"]  # ni con la correcta
    reloj = INTENTOS.reloj
    INTENTOS.reloj = lambda: reloj() + 10  # pasa la espera
    try:
        assert client.post("/api/auth/login", json={"usuario": "admin", "password": "Admin123!"}).status_code == 200
        assert client.post("/api/auth/login", json={"usuario": "admin", "password": "mala"}).status_code == 401
    finally:
        INTENTOS.reloj = reloj


# Sesión con expiración por inactividad
def test_sesion_expira_por_inactividad(escenario):
    c, ana = escenario["c"], escenario["ana"]
    assert c.get("/api/auth/me", headers=ana).status_code == 200
    sql("UPDATE sesiones SET ultimo_uso = '2000-01-01 00:00:00' WHERE token = :t", t=ana["Authorization"][7:])
    r = c.get("/api/auth/me", headers=ana)
    assert r.status_code == 401 and "expiró" in r.json()["detail"]
    r = c.get("/api/auth/me", headers=ana)  # la sesión vencida ya se borró
    assert r.status_code == 401 and "no es válida" in r.json()["detail"]
    assert c.get("/api/proyectos", headers={"Authorization": "Bearer x"}).status_code == 401


# HU-01-007 / RP-04: /auth/me refleja la función vigente aunque la sesión siga abierta
def test_me_refleja_cambio_de_funcion(escenario):
    c, beto = escenario["c"], escenario["beto"]
    assert c.get("/api/auth/me", headers=beto).json()["funcion"] == "Integrante"
    sql("UPDATE usuarios SET funcion_id = (SELECT id FROM funciones WHERE nombre = 'Responsable') WHERE id = :id",
        id=escenario["beto_id"])
    assert c.get("/api/auth/me", headers=beto).json()["funcion"] == "Responsable"


# HU-08-002 en el registro de cuentas
def test_registro_reintento_con_la_misma_clave(client):
    adm = login(client, "admin", "Admin123!")
    datos = {"usuario": "dora", "nombre": "Dora", "password": "clave123", "funcion_id": 3}
    con_clave = {**adm, "Idempotency-Key": "cuenta-1"}
    r1, r2 = (client.post("/api/usuarios", headers=con_clave, json=datos) for _ in range(2))
    assert r1.status_code == r2.status_code == 201 and r1.json() == r2.json()
    assert r1.json()["activo"] is True
    assert client.post("/api/usuarios", headers={**adm, "Idempotency-Key": "cuenta-2"}, json=datos).status_code == 409


def test_cabeceras_de_seguridad(client):
    r = client.get("/")
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    api = client.get("/api/proyectos")
    assert api.headers["x-content-type-options"] == "nosniff" and "content-security-policy" not in api.headers
