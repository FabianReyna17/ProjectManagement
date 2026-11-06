"""Reglas de negocio probadas directamente en los servicios, sin peticiones HTTP."""
import ast
import pathlib
from datetime import date

import pytest

from app.core.errors import Conflicto, DatosInvalidos, NoAutenticado, Prohibido
from app.db.database import get_conn, init_db
from app.modules.acceso import service as acceso
from app.modules.proyectos import service as proyectos

APP = pathlib.Path(__file__).resolve().parents[1] / "app"


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    init_db()
    conn = get_conn()
    yield conn
    conn.close()


def funcion(db, nombre):
    return next(f["id"] for f in acceso.listar_funciones(db) if f["nombre"] == nombre)


def test_servicios_no_dependen_de_fastapi():
    for archivo in APP.glob("modules/*/service.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                nombres = [nodo.module or ""] if isinstance(nodo, ast.ImportFrom) else [a.name for a in nodo.names]
                assert not any(n.split(".")[0] in ("fastapi", "starlette") for n in nombres), archivo


def test_registro_y_login(db):
    acceso.registrar_usuario(db, "ana", "Ana", "clave123", funcion(db, "Responsable"))
    with pytest.raises(Conflicto):
        acceso.registrar_usuario(db, "ana", "Otra", "clave123", funcion(db, "Integrante"))
    with pytest.raises(DatosInvalidos):
        acceso.registrar_usuario(db, "beto", "Beto", "clave123", 999)
    with pytest.raises(NoAutenticado):
        acceso.iniciar_sesion(db, "ana", "mala")
    sesion = acceso.iniciar_sesion(db, "ana", "clave123")
    assert acceso.usuario_por_token(db, sesion["token"])["usuario"] == "ana"
    acceso.cerrar_sesion(db, sesion["token"])
    assert acceso.usuario_por_token(db, sesion["token"]) is None


def test_crear_proyecto_reglas(db):
    ana = acceso.registrar_usuario(db, "ana", "Ana", "clave123", funcion(db, "Responsable"))["id"]
    beto = acceso.registrar_usuario(db, "beto", "Beto", "clave123", funcion(db, "Integrante"))["id"]
    with pytest.raises(DatosInvalidos):
        proyectos.crear(db, ana, "P", "O", ana, date(2026, 11, 10), date(2026, 11, 1))
    with pytest.raises(DatosInvalidos):  # un Integrante no puede ser responsable
        proyectos.crear(db, ana, "P", "O", beto, date(2026, 11, 1), date(2026, 12, 1))
    p = proyectos.crear(db, ana, "Web", "Sitio", ana, date(2026, 11, 1), date(2026, 12, 1))
    assert p["estado"] == "planificado"
    assert [x["id"] for x in proyectos.mis_proyectos(db, ana)] == [p["id"]]
    assert proyectos.mis_proyectos(db, beto) == []


def test_participantes_reglas(db):
    ana = acceso.registrar_usuario(db, "ana", "Ana", "clave123", funcion(db, "Responsable"))["id"]
    beto = acceso.registrar_usuario(db, "beto", "Beto", "clave123", funcion(db, "Integrante"))["id"]
    pid = proyectos.crear(db, ana, "Web", "Sitio", ana, date(2026, 11, 1), date(2026, 12, 1))["id"]
    with pytest.raises(Prohibido):
        proyectos.obtener_autorizado(db, pid, beto)
    p = proyectos.obtener_autorizado(db, pid, ana)
    with pytest.raises(Prohibido):  # solo el responsable administra participantes
        proyectos.agregar_participante(db, p, beto, beto)
    proyectos.agregar_participante(db, p, ana, beto)
    with pytest.raises(Conflicto):
        proyectos.agregar_participante(db, p, ana, beto)
    assert proyectos.obtener_autorizado(db, pid, beto)["id"] == pid
    with pytest.raises(DatosInvalidos):
        proyectos.retirar_participante(db, p, ana, ana)
    proyectos.retirar_participante(db, p, ana, beto)
    with pytest.raises(Prohibido):
        proyectos.obtener_autorizado(db, pid, beto)
