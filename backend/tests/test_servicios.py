"""Reglas de negocio probadas directamente en los servicios, sin peticiones HTTP."""
import ast
import pathlib
from datetime import date

import pytest
from sqlalchemy import text

from app.core.errors import Conflicto, DatosInvalidos, NoAutenticado, Prohibido
from app.db.database import get_engine, init_db
from app.modules.acceso import service as acceso
from app.modules.proyectos import service as proyectos
from app.modules.tareas import service as tareas

APP = pathlib.Path(__file__).resolve().parents[1] / "app"


@pytest.fixture()
def db():
    init_db()
    with get_engine().connect() as conn:
        yield conn


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


def test_no_se_asigna_tarea_a_cuenta_inactiva(db):
    ana = acceso.registrar_usuario(db, "ana", "Ana", "clave123", funcion(db, "Responsable"))["id"]
    beto = acceso.registrar_usuario(db, "beto", "Beto", "clave123", funcion(db, "Integrante"))["id"]
    p = proyectos.crear(db, ana, "Web", "Sitio", ana, date(2026, 11, 1), date(2026, 12, 1))
    proyectos.agregar_participante(db, p, ana, beto)
    t = tareas.obtener_autorizada(db, tareas.crear(db, p, ana, "T", "D", None)["id"], ana)
    db.execute(text("UPDATE usuarios SET activo = 0 WHERE id = :id"), {"id": beto})
    db.commit()
    with pytest.raises(DatosInvalidos):
        tareas.asignar(db, t, ana, beto)
    assert tareas.obtener_autorizada(db, t["id"], ana)["responsable_id"] is None


def test_crear_una_vez_si_falla_no_guarda_la_clave(db):
    from app.db.idempotencia import crear_una_vez
    ana = acceso.registrar_usuario(db, "ana", "Ana", "clave123", funcion(db, "Responsable"))["id"]

    def falla():
        db.execute(text("INSERT INTO funciones (nombre) VALUES ('Temporal')"))
        raise RuntimeError("corte de conexión")

    with pytest.raises(RuntimeError):
        crear_una_vez(db, ana, "k", "prueba", falla)
    assert db.execute(text("SELECT COUNT(*) FROM funciones WHERE nombre = 'Temporal'")).scalar() == 0
    assert crear_una_vez(db, ana, "k", "prueba", lambda: 7) == 7
    assert crear_una_vez(db, ana, "k", "prueba", lambda: 8) == 7   # reintento: devuelve el primero
    with pytest.raises(Conflicto):
        crear_una_vez(db, ana, "k", "otra", lambda: 9)            # misma clave, otra acción


def test_freno_de_intentos_crece_y_se_olvida():
    from app.core.intentos import LIBRES, OLVIDO, Intentos
    ahora = [1000.0]
    frenos = Intentos(reloj=lambda: ahora[0])
    for _ in range(LIBRES - 1):
        frenos.fallo("ana")
    assert frenos.espera("ana") == 0
    frenos.fallo("ana")
    assert frenos.espera("ana") == 2
    frenos.fallo("ana")
    assert frenos.espera("ana") == 4            # se duplica
    assert frenos.espera("otra") == 0           # cada identificador lleva su cuenta
    ahora[0] += 4
    assert frenos.espera("ana") == 0
    frenos.exito("ana")
    frenos.fallo("ana")
    assert frenos.espera("ana") == 0            # un inicio correcto limpia el contador
    for _ in range(LIBRES):
        frenos.fallo("beto")
    ahora[0] += OLVIDO + 1
    assert frenos.espera("beto") == 0           # sin fallos recientes se olvida


def test_sesion_vencida_se_borra(db):
    acceso.registrar_usuario(db, "ana", "Ana", "clave123", funcion(db, "Responsable"))
    token = acceso.iniciar_sesion(db, "ana", "clave123")["token"]
    assert acceso.sesion_vigente(db, token)["usuario"] == "ana"
    db.execute(text("UPDATE sesiones SET ultimo_uso = '2000-01-01 00:00:00'"))
    db.commit()
    with pytest.raises(NoAutenticado, match="expiró"):
        acceso.sesion_vigente(db, token)
    assert db.execute(text("SELECT COUNT(*) FROM sesiones")).scalar() == 0
