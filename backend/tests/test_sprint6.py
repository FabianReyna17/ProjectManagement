"""Pruebas de API del Sprint 6: administración de cuentas, respaldo y release."""
import os
import sqlite3
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from .helpers import funcion_id, login
from .test_sprint2 import bloquear, crear_tarea, esc  # noqa: F401  (esc es el escenario del Sprint 2)
from .test_sprint4 import PDF, adjuntar


def desactivar(e, uid, h=None):
    return e.c.post(f"/api/usuarios/{uid}/desactivacion", headers=h or e.adm)


def eventos_cuenta(uid):
    """Cambios sobre la cuenta (sin su alta ni los accesos a proyectos, que se prueban en HU-01-010)."""
    from app.db.database import get_engine, varios
    with get_engine().connect() as db:
        return varios(db, """SELECT tipo, valor_anterior, valor_nuevo, actor_id FROM eventos_cuenta
                             WHERE usuario_id = :u AND tipo IN ('desactivacion', 'funcion', 'restablecimiento')""",
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


# HU-01-011 Restablecer acceso
def restablecer(e, uid, h=None):
    return e.c.post(f"/api/usuarios/{uid}/restablecimiento", headers=h or e.adm)


def entrar(e, usuario, password):
    return e.c.post("/api/auth/login", json={"usuario": usuario, "password": password})


def test_restablecer_invalida_la_credencial_anterior_y_obliga_a_cambiarla(esc):
    r = restablecer(esc, esc.beto_id)
    assert r.status_code == 200, r.text
    temporal = r.json()["password_temporal"]
    assert len(temporal) == 12 and r.json()["activo"] is True
    assert esc.c.get("/api/proyectos", headers=esc.beto).status_code == 401  # su sesión abierta ya no sirve
    assert entrar(esc, "beto", "clave123").status_code == 401                 # ni la contraseña anterior
    r = entrar(esc, "beto", temporal)
    assert r.status_code == 200 and r.json()["usuario"]["debe_cambiar_password"] is True
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    # con la temporal solo puede ver su cuenta, cambiarla o salir
    r = esc.c.get("/api/proyectos", headers=h)
    assert (r.status_code, r.json()["cambiar_password"]) == (403, True)
    assert esc.c.get("/api/auth/me", headers=h).json()["debe_cambiar_password"] is True
    cambio = {"actual": temporal, "nueva": "nueva123"}
    assert esc.c.post("/api/auth/password", headers=h, json={**cambio, "nueva": temporal}).status_code == 400
    assert esc.c.post("/api/auth/password", headers=h, json={**cambio, "actual": "otra"}).status_code == 400
    assert esc.c.post("/api/auth/password", headers=h, json=cambio).status_code == 200
    assert esc.c.get("/api/proyectos", headers=h).status_code == 200  # la misma sesión sigue
    assert entrar(esc, "beto", temporal).status_code == 401           # la temporal ya no sirve
    assert entrar(esc, "beto", "nueva123").json()["usuario"]["debe_cambiar_password"] is False


def test_conserva_permisos_y_autoria_y_registra_quien_lo_inicio(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    esc.c.post(f"/api/proyectos/{esc.pid}/comentarios", headers=esc.beto, json={"texto": "Listo"})
    temporal = restablecer(esc, esc.beto_id).json()["password_temporal"]
    h = {"Authorization": f"Bearer {entrar(esc, 'beto', temporal).json()['token']}"}
    esc.c.post("/api/auth/password", headers=h, json={"actual": temporal, "nueva": "nueva123"})
    assert esc.c.get("/api/auth/me", headers=h).json()["funcion"] == "Integrante"
    assert [p["id"] for p in esc.c.get("/api/proyectos", headers=h).json()] == [esc.pid]
    assert esc.c.put(f"/api/tareas/{t['id']}/estado", headers=h, json={"estado": "en_curso"}).status_code == 200
    [com] = esc.c.get(f"/api/proyectos/{esc.pid}/comentarios", headers=h).json()
    assert (com["autor_nombre"], com["autor_id"]) == ("Beto", esc.beto_id)
    assert eventos_cuenta(esc.beto_id) == [
        {"tipo": "restablecimiento", "valor_anterior": None, "valor_nuevo": None, "actor_id": 1}]


def test_solo_un_admin_restablece_una_cuenta_existente_y_activa(esc):
    for h in (esc.ana, esc.beto):
        assert restablecer(esc, esc.carla_id, h).status_code == 403
    assert restablecer(esc, 1).status_code == 400      # la propia se cambia con su contraseña actual
    assert restablecer(esc, 9999).status_code == 404
    desactivar(esc, esc.carla_id)
    assert restablecer(esc, esc.carla_id).status_code == 409
    assert login(esc.c, "beto", "clave123")  # nada cambió
    assert eventos_cuenta(esc.beto_id) == []


def test_restablecer_quita_el_freno_de_intentos_fallidos(esc):
    for _ in range(5):
        entrar(esc, "beto", "mala")
    assert entrar(esc, "beto", "clave123").status_code == 429
    temporal = restablecer(esc, esc.beto_id).json()["password_temporal"]
    assert entrar(esc, "beto", temporal).status_code == 200


# HU-08-004 Respaldo periódico
def respaldar(e, h=None):
    r = e.c.post("/api/respaldos", headers=h or e.adm)
    assert r.status_code == 201, r.text
    return r.json()


def carpeta_respaldos():
    return Path(os.environ["RESPALDOS_DIR"])


def con_bd(fn):
    from app.db.database import get_engine
    with get_engine().connect() as db:
        return fn(db)


@pytest.fixture()
def datos(esc):
    """Proyecto con tarea asignada, avance, bloqueo, comentario, adjunto, aviso e historial."""
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    url = f"/api/tareas/{t['id']}"
    esc.c.put(f"{url}/estado", headers=esc.beto, json={"estado": "en_curso"})
    esc.c.post(f"{url}/avances", headers=esc.beto, json={"texto": "Portada lista"})
    bloquear(esc, t)
    esc.c.post(f"/api/proyectos/{esc.pid}/comentarios", headers=esc.beto, json={"texto": "Revisen"})
    adjuntar(esc, f"/api/proyectos/{esc.pid}", esc.beto)
    assert esc.c.put(f"/api/proyectos/{esc.pid}/estado", headers=esc.ana,
                     json={"estado": "en_curso"}).status_code == 200
    desactivar(esc, esc.carla_id)
    esc.tarea = t
    return esc


def test_el_respaldo_incluye_toda_la_informacion_y_es_legible(datos):
    r = respaldar(datos)
    assert (r["resultado"], r["origen"], r["actor_nombre"]) == ("ok", "manual", "Administrador")
    assert r["detalle"] == "1 proyectos, 1 tareas, 1 adjuntos" and r["tamano"] > 0
    ruta = carpeta_respaldos() / r["archivo"]
    assert "/" not in r["archivo"] and ruta.is_file()  # al Admin no se le muestra la ruta del servidor
    with zipfile.ZipFile(ruta) as z:
        assert z.testzip() is None
        z.extractall(carpeta_respaldos() / "leido")
    from app.modules.respaldos.service import leer_manifiesto
    filas = leer_manifiesto(ruta)["filas"]
    for tabla in ("usuarios", "funciones", "participantes", "eventos_cuenta", "proyectos", "historial_proyectos",
                  "tareas", "historial_tareas", "avances", "bloqueos", "comentarios", "archivos", "avisos"):
        assert filas[tabla] > 0, tabla
    bd = sqlite3.connect(carpeta_respaldos() / "leido" / "gestion.db")
    assert bd.execute("SELECT nombre FROM proyectos").fetchall() == [("Web",)]
    assert bd.execute("SELECT activo FROM usuarios WHERE usuario = 'carla'").fetchone() == (0,)
    [(interno,)] = bd.execute("SELECT almacen FROM archivos").fetchall()
    bd.close()
    assert (carpeta_respaldos() / "leido" / "archivos" / interno).read_bytes() == PDF
    if os.name == "posix":  # solo el usuario del servicio puede leerlos
        assert ruta.stat().st_mode & 0o077 == 0 and carpeta_respaldos().stat().st_mode & 0o077 == 0


def test_se_respalda_segun_la_frecuencia(datos, monkeypatch):
    from app.modules.respaldos import service
    monkeypatch.setenv("RESPALDO_CADA_HORAS", "24")
    assert con_bd(service.toca_respaldo)  # sin ningún respaldo válido
    primero = con_bd(service.respaldar_si_toca)
    assert (primero["resultado"], primero["origen"]) == ("ok", "programado")
    assert con_bd(service.respaldar_si_toca) is None  # aún no toca
    hecho = datetime.fromisoformat(primero["terminado_en"])
    assert not con_bd(lambda db: service.toca_respaldo(db, hecho + timedelta(hours=23)))
    assert con_bd(lambda db: service.toca_respaldo(db, hecho + timedelta(hours=24)))
    estado = datos.c.get("/api/respaldos", headers=datos.adm).json()
    assert (estado["frecuencia_horas"], estado["atrasado"], estado["ultimo_valido"]["id"]) == (24, False, primero["id"])
    # si el archivo del último desaparece, deja de contar y vuelve a tocar
    (carpeta_respaldos() / primero["archivo"]).unlink()
    assert con_bd(service.toca_respaldo)


def test_un_respaldo_fallido_queda_senalado_y_no_cuenta(datos, monkeypatch):
    from app.modules.respaldos import service
    bueno = respaldar(datos)

    def falla(_):
        raise ValueError("La BD del respaldo no pasa la revisión de integridad")
    monkeypatch.setattr(service, "verificar", falla)
    r = respaldar(datos)
    assert (r["resultado"], r["archivo"]) == ("fallido", None)
    assert "integridad" in r["detalle"]
    assert sorted(p.name for p in carpeta_respaldos().iterdir()) == [bueno["archivo"]]  # ni .parcial
    estado = datos.c.get("/api/respaldos", headers=datos.adm).json()
    assert estado["ultimo_fallido"] is True and estado["ultimo_valido"]["id"] == bueno["id"]
    assert [x["resultado"] for x in estado["respaldos"]] == ["fallido", "ok"]
    # tampoco si la carpeta de respaldos no se puede usar
    monkeypatch.setenv("RESPALDOS_DIR", str(carpeta_respaldos() / bueno["archivo"]))
    assert respaldar(datos)["resultado"] == "fallido"


def test_conserva_solo_los_mas_recientes(datos, monkeypatch):
    monkeypatch.setenv("RESPALDOS_CONSERVAR", "2")
    hechos = [respaldar(datos)["archivo"] for _ in range(3)]
    assert sorted(p.name for p in carpeta_respaldos().iterdir()) == sorted(hechos[1:])
    estado = datos.c.get("/api/respaldos", headers=datos.adm).json()
    assert len(estado["respaldos"]) == 3  # el registro de ejecuciones se conserva


def test_solo_admin_consulta_o_pide_respaldos(datos):
    archivo = respaldar(datos)["archivo"]
    for h in (datos.ana, datos.beto):
        assert datos.c.get("/api/respaldos", headers=h).status_code == 403
        assert datos.c.post("/api/respaldos", headers=h).status_code == 403
    assert datos.c.get("/api/respaldos").status_code == 401
    for ruta in (f"/{archivo}", f"/data/respaldos/{archivo}", f"/respaldos/{archivo}"):
        assert datos.c.get(ruta).status_code == 404  # nunca se sirven por HTTP


# HU-08-005 Restaurar y verificar recuperación
def bd_en_uso() -> Path:
    return Path(os.environ["DATABASE_URL"].removeprefix("sqlite:///"))


def test_restaurar_recupera_lo_respaldado_y_documenta_lo_posterior(datos, tmp_path):
    from app.modules.respaldos.restauracion import comparar, informe, restaurar
    zip_ = carpeta_respaldos() / respaldar(datos)["archivo"]
    # trabajo registrado después del respaldo: un proyecto nuevo y un cambio en la tarea existente
    posterior = nuevo_proyecto(datos, datos.ana, datos.ana_id).json()["id"]
    assert datos.c.put(f"/api/tareas/{datos.tarea['id']}/estado", headers=datos.beto,
                       json={"estado": "pendiente"}).status_code == 200

    destino = tmp_path / "prueba-restauracion"
    r = restaurar(zip_, destino / "gestion.db", destino / "archivos")
    assert r["segundos"] < 60  # tiempo de recuperación medido (límite propuesto: 1 hora)
    assert r["version_restaurada"] == r["version_respaldo"] and r["filas"]["proyectos"] == 1

    dif = comparar(bd_en_uso(), destino / "gestion.db")
    assert dif["proyectos"]["posteriores"] == [posterior] and dif["proyectos"]["iguales"] == 1
    assert dif["tareas"]["cambiadas"] == [datos.tarea["id"]]
    assert dif["historial_tareas"]["posteriores"]  # el cambio de estado posterior no está en el respaldo
    for tabla in ("usuarios", "participantes", "avances", "bloqueos", "comentarios", "archivos", "avisos", "eventos_cuenta"):
        d = dif[tabla]
        assert d["iguales"] > 0 and not (d["cambiadas"] or d["solo_restaurada"]), tabla
    texto = informe(r, dif, limite_seg=3600)
    assert "cumple" in texto and "| proyectos | 1 | " + str(posterior) in texto


def test_la_informacion_restaurada_conserva_relaciones_autoria_y_permisos(datos, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.modules.respaldos.restauracion import restaurar
    zip_ = carpeta_respaldos() / respaldar(datos)["archivo"]
    destino = tmp_path / "prueba-restauracion"
    restaurar(zip_, destino / "gestion.db", destino / "archivos")
    pid, tid = datos.pid, datos.tarea["id"]

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(destino / 'gestion.db').as_posix()}")
    monkeypatch.setenv("ARCHIVOS_DIR", str(destino / "archivos"))
    from app.main import app
    with TestClient(app) as c:
        ana, beto, adm = (login(c, u, p) for u, p in (("ana", "clave123"), ("beto", "clave123"), ("admin", "Admin123!")))
        assert [p["nombre"] for p in c.get("/api/proyectos", headers=beto).json()] == ["Web"]
        tarea = c.get(f"/api/tareas/{tid}", headers=ana).json()
        assert (tarea["proyecto_id"], tarea["responsable_nombre"], tarea["estado"]) == (pid, "Beto", "en_curso")
        assert [h["actor_nombre"] for h in c.get(f"/api/tareas/{tid}/historial", headers=ana).json()][-1] == "Beto"
        [com] = c.get(f"/api/proyectos/{pid}/comentarios", headers=ana).json()
        assert com["autor_nombre"] == "Beto"
        [arch] = c.get(f"/api/proyectos/{pid}/archivos", headers=ana).json()
        assert c.get(f"/api/archivos/{arch['id']}/descarga", headers=beto).content == PDF
        # nadie gana acceso: la función de Admin no da acceso al proyecto y la cuenta desactivada sigue así
        assert c.get(f"/api/proyectos/{pid}", headers=adm).status_code == 403
        assert c.post("/api/auth/login", json={"usuario": "carla", "password": "clave123"}).status_code == 401
        # y se puede seguir trabajando sobre lo restaurado
        assert c.put(f"/api/tareas/{tid}/estado", headers=beto, json={"estado": "pendiente"}).status_code == 200


def test_no_restaura_encima_ni_desde_un_respaldo_danado(datos, tmp_path):
    from app.modules.respaldos.restauracion import main
    zip_ = carpeta_respaldos() / respaldar(datos)["archivo"]
    destino = tmp_path / "prueba"
    args = [str(zip_), "--bd", str(destino / "gestion.db"), "--archivos", str(destino / "archivos")]
    assert main(args + ["--comparar-con", str(bd_en_uso()), "--informe", str(destino / "informe.md")]) == 0
    assert "Comparación con la BD de origen" in (destino / "informe.md").read_text(encoding="utf-8")
    antes = (destino / "gestion.db").stat().st_mtime_ns
    assert main(args) == 1  # ya existe: no la pisa sin --forzar
    assert (destino / "gestion.db").stat().st_mtime_ns == antes
    assert main(args + ["--forzar"]) == 0

    danado = tmp_path / "danado.zip"
    danado.write_bytes(zip_.read_bytes()[:-200])
    otro = tmp_path / "otro"
    assert main([str(danado), "--bd", str(otro / "gestion.db"), "--archivos", str(otro / "archivos")]) == 1
    assert not (otro / "gestion.db").exists()


# HU-01-010 Historial de cambios de acceso
def historial(e, h=None, **filtro):
    r = e.c.get("/api/cambios-acceso", headers=h or e.adm, params=filtro)
    assert r.status_code == 200, r.text
    return [(x["tipo"], x["persona_nombre"], x["proyecto_nombre"], x["actor_nombre"], x["valor_anterior"],
             x["valor_nuevo"]) for x in r.json()["eventos"]]


def test_cada_cambio_muestra_persona_actor_fecha_y_valores(esc):
    assert esc.c.delete(f"/api/proyectos/{esc.pid}/participantes/{esc.beto_id}", headers=esc.ana).status_code == 200
    cambiar_funcion(esc, esc.beto_id, "Supervisor")
    desactivar(esc, esc.beto_id)
    assert historial(esc, usuario_id=esc.beto_id) == [
        ("desactivacion", "Beto", None, "Administrador", "activa", "desactivada"),
        ("funcion", "Beto", None, "Administrador", "Integrante", "Supervisor"),
        ("acceso_retiro", "Beto", "Web", "Ana", "con acceso", "sin acceso"),
        ("acceso_alta", "Beto", "Web", "Ana", "sin acceso", "con acceso"),
        ("cuenta_alta", "Beto", None, "Administrador", None, "Integrante"),
    ]
    assert historial(esc, proyecto_id=esc.pid) == [
        ("acceso_retiro", "Beto", "Web", "Ana", "con acceso", "sin acceso"),
        ("acceso_alta", "Beto", "Web", "Ana", "sin acceso", "con acceso"),
        ("acceso_alta", "Ana", "Web", "Ana", "sin acceso", "con acceso (responsable del proyecto)"),
    ]
    r = esc.c.get("/api/cambios-acceso", headers=esc.adm).json()
    assert all(x["creado_en"] for x in r["eventos"]) and r["proyectos"] == [{"id": esc.pid, "nombre": "Web"}]
    # el nuevo responsable que obtiene acceso al editar el proyecto también queda registrado
    dani = crear_usuario_resp(esc, "dani")
    p = esc.c.get(f"/api/proyectos/{esc.pid}", headers=esc.ana).json()
    r = esc.c.put(f"/api/proyectos/{esc.pid}", headers=esc.ana, json={
        **{k: p[k] for k in ("nombre", "objetivo", "fecha_inicio", "fecha_fin")}, "responsable_id": dani})
    assert r.status_code == 200, r.text
    assert historial(esc, usuario_id=dani)[0] == (
        "acceso_alta", "Dani", "Web", "Ana", "sin acceso", "con acceso (nuevo responsable del proyecto)")


def crear_usuario_resp(e, usuario):
    from .helpers import crear_usuario
    return crear_usuario(e.c, e.adm, usuario, "Responsable")


def test_solo_admin_consulta_el_historial(esc):
    for h in (esc.ana, esc.beto):  # ni siquiera el responsable del proyecto
        assert esc.c.get("/api/cambios-acceso", headers=h, params={"proyecto_id": esc.pid}).status_code == 403
        assert esc.c.get("/api/cambios-acceso", headers=h, params={"usuario_id": esc.beto_id}).status_code == 403
    assert esc.c.get("/api/cambios-acceso").status_code == 401


def test_cambiar_o_desactivar_no_altera_eventos_anteriores(esc):
    antes = esc.c.get("/api/cambios-acceso", headers=esc.adm).json()["eventos"]
    cambiar_funcion(esc, esc.beto_id, "Responsable")
    restablecer(esc, esc.beto_id)
    desactivar(esc, esc.beto_id)
    desactivar(esc, esc.beto_id)  # repetir no agrega ni cambia nada
    despues = esc.c.get("/api/cambios-acceso", headers=esc.adm).json()["eventos"]
    assert len(despues) == len(antes) + 3 and despues[3:] == antes
    assert [x["tipo"] for x in despues[:3]] == ["desactivacion", "restablecimiento", "funcion"]


def test_la_migracion_carga_los_accesos_anteriores(tmp_path, monkeypatch):
    """Una BD de antes del historial (0020) obtiene altas de cuenta y de acceso con actor no registrado."""
    from alembic import command
    from alembic.config import Config

    from app.db.database import BACKEND_DIR
    url = f"sqlite:///{(tmp_path / 'vieja.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(cfg, "0020")
    bd = sqlite3.connect(tmp_path / "vieja.db")
    bd.executescript("""
        INSERT INTO usuarios (id, usuario, nombre, password_hash, funcion_id, creado_en)
            VALUES (1, 'admin', 'Administrador', 'x', 1, '2026-10-01 10:00:00'),
                   (2, 'ana', 'Ana', 'x', 3, '2026-10-02 10:00:00');
        INSERT INTO eventos_cuenta (usuario_id, tipo, valor_anterior, valor_nuevo, actor_id, creado_en)
            VALUES (2, 'funcion', 'Responsable', 'Integrante', 1, '2026-11-01 10:00:00');
        UPDATE usuarios SET funcion_id = 3 WHERE id = 2;
        INSERT INTO proyectos (id, nombre, objetivo, responsable_id, fecha_inicio, fecha_fin, creado_por)
            VALUES (1, 'Web', 'Sitio', 1, '2026-10-01', '2026-12-01', 1);
        INSERT INTO participantes (proyecto_id, usuario_id, activo, agregado_en, retirado_en)
            VALUES (1, 1, 1, '2026-10-03 10:00:00', NULL), (1, 2, 0, '2026-10-04 10:00:00', '2026-10-05 10:00:00');
    """)
    bd.commit()
    command.upgrade(cfg, "head")
    filas = bd.execute("""SELECT usuario_id, proyecto_id, tipo, valor_anterior, valor_nuevo, actor_id, creado_en
                          FROM eventos_cuenta ORDER BY creado_en, id""").fetchall()
    bd.close()
    assert filas == [
        (1, None, "cuenta_alta", None, "Admin", None, "2026-10-01 10:00:00"),
        (2, None, "cuenta_alta", None, "Responsable", None, "2026-10-02 10:00:00"),  # su función inicial
        (1, 1, "acceso_alta", "sin acceso", "con acceso", None, "2026-10-03 10:00:00"),
        (2, 1, "acceso_alta", "sin acceso", "con acceso", None, "2026-10-04 10:00:00"),
        (2, 1, "acceso_retiro", "con acceso", "sin acceso", None, "2026-10-05 10:00:00"),
        (2, None, "funcion", "Responsable", "Integrante", 1, "2026-11-01 10:00:00"),
    ]
