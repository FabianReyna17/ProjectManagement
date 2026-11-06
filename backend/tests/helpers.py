"""Ayudas comunes para las pruebas de API."""


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
