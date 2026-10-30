import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    from app.main import app
    with TestClient(app) as c:
        yield c


def login(c, usuario, password):
    r = c.post("/api/auth/login", json={"usuario": usuario, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def funcion_id(c, h, nombre):
    return next(f["id"] for f in c.get("/api/funciones", headers=h).json() if f["nombre"] == nombre)


def crear_usuario(c, h, usuario, funcion):
    r = c.post("/api/usuarios", headers=h, json={
        "usuario": usuario, "nombre": usuario.title(), "password": "clave123",
        "funcion_id": funcion_id(c, h, funcion)})
    assert r.status_code == 201, r.text
    return r.json()["id"]


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
