"""TEC-02: regresión de permisos sobre todas las rutas de la API.

Recorre las rutas que publica la aplicación (una ruta nueva entra sola en estas pruebas):
- sin sesión, con una sesión de una cuenta desactivada o con la contraseña temporal pendiente
  de cambiar, ninguna ruta responde datos;
- las rutas de administración solo las usa el Admin;
- quien no participa en un proyecto recibe 403 en todo lo del proyecto y sus tareas, comentarios,
  archivos y avisos, sin que cambie nada.
"""
import re

import pytest
from fastapi.routing import APIRoute

from .helpers import crear_usuario, login
from .test_sprint2 import bloquear, crear_tarea, esc  # noqa: F401
from .test_sprint4 import PDF, adjuntar

PUBLICAS = {("POST", "/api/auth/login")}
# Con la contraseña temporal pendiente solo se permite esto (HU-01-011)
SIN_CAMBIO_PENDIENTE = {("GET", "/api/auth/me"), ("POST", "/api/auth/logout"), ("POST", "/api/auth/password")}
SOLO_ADMIN = {
    ("GET", "/api/funciones"), ("POST", "/api/usuarios"), ("POST", "/api/usuarios/{usuario_id}/desactivacion"),
    ("PUT", "/api/usuarios/{usuario_id}/funcion"), ("POST", "/api/usuarios/{usuario_id}/restablecimiento"),
    ("GET", "/api/cambios-acceso"), ("GET", "/api/respaldos"), ("POST", "/api/respaldos"),
}
# Rutas de un proyecto o de algo que pertenece a uno: exigen participar en él
DE_PROYECTO = re.compile(r"\{(proyecto_id|tarea_id|comentario_id|archivo_id|aviso_id)\}")


def rutas_api():
    from app.main import app
    return sorted((m, r.path) for r in app.routes if isinstance(r, APIRoute) and r.path.startswith("/api")
                  for m in r.methods)


def url(ruta, ids):
    return re.sub(r"\{(\w+)\}", lambda m: str(ids.get(m.group(1), 1)), ruta)


# Un cuerpo válido para cualquier ruta de escritura: así la respuesta depende del permiso y no
# de un dato faltante (los campos que una ruta no usa se ignoran)
CUERPO = {"texto": "Cambio ajeno", "estado": "en_curso", "motivo": "Motivo", "resolucion": "Resuelto",
          "nombre": "Otro nombre", "objetivo": "Otro objetivo", "descripcion": "Descripción",
          "fecha_inicio": "2026-11-01", "fecha_fin": "2026-12-31", "fecha_limite": "2026-12-15",
          "prioridad": "alta", "justificacion": "Justificación", "usuario_id": 1, "responsable_id": 1,
          "funcion_id": 1, "usuario": "nueva", "password": "clave123", "actual": "clave123", "nueva": "otra123"}


def pedir(c, metodo, ruta, h=None):
    return c.request(metodo, ruta, headers=h or {}, json=CUERPO if metodo in ("POST", "PUT") else None)


@pytest.fixture()
def mundo(esc):
    """Proyecto Web con tarea bloqueada, comentario, archivo y aviso para beto. dani no participa."""
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    bid = bloquear(esc, t)["id"]
    cid = esc.c.post(f"/api/proyectos/{esc.pid}/comentarios", headers=esc.beto, json={"texto": "Hola"}).json()["id"]
    aid = adjuntar(esc, f"/api/proyectos/{esc.pid}", esc.beto).json()["id"]
    avid = esc.c.get("/api/avisos", headers=esc.beto).json()[0]["id"]
    esc.dani_id = crear_usuario(esc.c, esc.adm, "dani", "Responsable")
    esc.dani = login(esc.c, "dani", "clave123")
    esc.ids = {"proyecto_id": esc.pid, "tarea_id": t["id"], "comentario_id": cid, "archivo_id": aid,
               "aviso_id": avid, "bloqueo_id": bid, "usuario_id": esc.beto_id}
    return esc


def test_ninguna_ruta_responde_sin_sesion_valida(mundo):
    c = mundo.c
    caducada = {"Authorization": "Bearer token-que-no-existe"}
    rutas = [r for r in rutas_api() if r not in PUBLICAS]
    assert len(rutas) > 50
    for metodo, ruta in rutas:
        for h in (None, caducada):
            r = pedir(c, metodo, url(ruta, mundo.ids), h)
            assert r.status_code == 401, (metodo, ruta, r.status_code)


def test_una_cuenta_desactivada_no_usa_ninguna_ruta(mundo):
    c = mundo.c
    assert c.post(f"/api/usuarios/{mundo.beto_id}/desactivacion", headers=mundo.adm).status_code == 200
    for metodo, ruta in rutas_api():
        if (metodo, ruta) in PUBLICAS:
            continue
        r = pedir(c, metodo, url(ruta, mundo.ids), mundo.beto)
        assert r.status_code == 401, (metodo, ruta, r.status_code)


def test_con_la_contrasena_temporal_solo_puede_cambiarla(mundo):
    c = mundo.c
    temporal = c.post(f"/api/usuarios/{mundo.dani_id}/restablecimiento", headers=mundo.adm).json()["password_temporal"]
    h = login(c, "dani", temporal)
    for metodo, ruta in rutas_api():
        if (metodo, ruta) in PUBLICAS | SIN_CAMBIO_PENDIENTE:
            continue
        r = pedir(c, metodo, url(ruta, mundo.ids), h)
        assert (r.status_code, r.json().get("cambiar_password")) == (403, True), (metodo, ruta, r.status_code)
    assert c.get("/api/auth/me", headers=h).status_code == 200


def test_las_rutas_de_administracion_son_solo_del_admin(mundo):
    c = mundo.c
    assert SOLO_ADMIN <= set(rutas_api())
    supervisor = crear_usuario(c, mundo.adm, "sofia", "Supervisor")
    assert supervisor
    for h in (mundo.ana, mundo.beto, mundo.dani, login(c, "sofia", "clave123")):
        for metodo, ruta in SOLO_ADMIN:
            r = pedir(c, metodo, url(ruta, mundo.ids), h)
            assert r.status_code == 403, (metodo, ruta, r.status_code)
        assert c.get("/api/usuarios", headers=h, params={"todas": 1}).status_code == 403
    assert len(c.get("/api/usuarios", headers=mundo.adm, params={"todas": 1}).json()) == 6  # nada cambió


def test_quien_no_participa_no_ve_ni_cambia_nada_del_proyecto(mundo):
    c = mundo.c
    antes = {r: c.get(url(r, mundo.ids), headers=mundo.ana).json()
             for r in ("/api/proyectos/{proyecto_id}", "/api/tareas/{tarea_id}", "/api/proyectos/{proyecto_id}/actividad",
                       "/api/proyectos/{proyecto_id}/participantes")}
    rutas = [(m, r) for m, r in rutas_api() if DE_PROYECTO.search(r)]
    assert len(rutas) > 35
    for h in (mundo.dani, mundo.carla, mundo.adm):  # Responsable, Integrante y Admin sin participar
        for metodo, ruta in rutas:
            r = pedir(c, metodo, url(ruta, mundo.ids), h)
            assert r.status_code == 403, (metodo, ruta, r.status_code)
            assert "Web" not in r.text and "Hola" not in r.text  # no revela nombres ni contenido
        r = c.post(f"/api/proyectos/{mundo.pid}/archivos", params={"nombre": "x.pdf"}, content=PDF,
                   headers={**h, "Content-Type": "application/octet-stream"})
        assert r.status_code == 403
    for r, valor in antes.items():
        assert c.get(url(r, mundo.ids), headers=mundo.ana).json() == valor, r
