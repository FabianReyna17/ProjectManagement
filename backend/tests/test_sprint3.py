"""Pruebas de API del Sprint 3: tablero, vencimientos, replanificación y concurrencia."""
from .test_sprint2 import crear_tarea, esc  # noqa: F401  (esc es el escenario del Sprint 2)

ESTADOS = ["pendiente", "en_curso", "terminada"]


def tablero(e, h):
    r = e.c.get(f"/api/proyectos/{e.pid}/tablero", headers=h)
    assert r.status_code == 200, r.text
    return r.json()["columnas"]


def lista(e, h):
    r = e.c.get(f"/api/proyectos/{e.pid}/tareas", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def cambiar_estado(e, h, tid, estado):
    r = e.c.put(f"/api/tareas/{tid}/estado", headers=h, json={"estado": estado})
    assert r.status_code == 200, r.text


# HU-07-001 Tablero de tareas
def test_tablero_tiene_una_columna_por_estado(esc):
    columnas = tablero(esc, esc.ana)
    assert [(c["estado"], c["nombre"]) for c in columnas] == [
        ("pendiente", "Pendiente"), ("en_curso", "En curso"), ("terminada", "Terminada")]
    assert all(c["tareas"] == [] for c in columnas)


def test_tablero_coincide_con_la_lista(esc):
    a = crear_tarea(esc, "Diseño", responsable_id=esc.beto_id, prioridad="alta", fecha_limite="2026-11-20")
    b = crear_tarea(esc, "Maquetar")
    c = crear_tarea(esc, "Publicar", responsable_id=esc.beto_id)
    cambiar_estado(esc, esc.beto, a["id"], "en_curso")
    cambiar_estado(esc, esc.ana, c["id"], "en_curso")
    cambiar_estado(esc, esc.ana, c["id"], "terminada")
    assert esc.c.post(f"/api/tareas/{b['id']}/bloqueos", headers=esc.ana,
                      json={"motivo": "Falta el logo"}).status_code == 201

    tarjetas = {t["id"]: t for col in tablero(esc, esc.beto) for t in col["tareas"]}
    filas = lista(esc, esc.beto)
    assert sorted(tarjetas) == sorted(t["id"] for t in filas)
    for fila in filas:  # mismos datos: responsable, fecha, prioridad, estado y bloqueo
        tarjeta = {k: v for k, v in tarjetas[fila["id"]].items() if k != "transiciones"}
        assert tarjeta == fila

    columnas = tablero(esc, esc.beto)
    assert {c["estado"]: [t["id"] for t in c["tareas"]] for c in columnas} == {
        "pendiente": [b["id"]], "en_curso": [a["id"]], "terminada": [c["id"]]}
    diseno = columnas[1]["tareas"][0]
    assert (diseno["responsable_nombre"], diseno["fecha_limite"], diseno["prioridad"]) == ("Beto", "2026-11-20", "alta")
    assert columnas[0]["tareas"][0]["bloqueada"] is True and columnas[0]["tareas"][0]["responsable_id"] is None


def test_columna_conserva_el_orden_de_la_lista(esc):
    ids = [crear_tarea(esc, n, **extra)["id"] for n, extra in [
        ("Sin fecha", {}), ("Tarde", {"fecha_limite": "2026-12-01"}),
        ("Pronto baja", {"fecha_limite": "2026-11-20", "prioridad": "baja"}),
        ("Pronto alta", {"fecha_limite": "2026-11-20", "prioridad": "alta"})]]
    pendientes = [t["id"] for t in tablero(esc, esc.ana)[0]["tareas"]]
    assert pendientes == [t["id"] for t in lista(esc, esc.ana)]
    assert pendientes == [ids[3], ids[2], ids[1], ids[0]]


def test_cambio_de_estado_se_refleja_en_ambas_vistas(esc):
    t = crear_tarea(esc, responsable_id=esc.beto_id)
    for estado in ["en_curso", "terminada", "en_curso"]:
        cambiar_estado(esc, esc.beto, t["id"], estado)
        assert lista(esc, esc.ana)[0]["estado"] == estado
        columnas = tablero(esc, esc.ana)
        assert [len(c["tareas"]) for c in columnas] == [int(e == estado) for e in ESTADOS]


def test_tarjeta_ofrece_solo_las_transiciones_permitidas(esc):
    mia = crear_tarea(esc, "Mía", responsable_id=esc.beto_id)
    ajena = crear_tarea(esc, "Sin asignar")

    def transiciones(h):
        return {t["id"]: t["transiciones"] for col in tablero(esc, h) for t in col["tareas"]}

    assert transiciones(esc.beto) == {mia["id"]: ["en_curso"], ajena["id"]: []}
    assert transiciones(esc.ana) == {mia["id"]: ["en_curso"], ajena["id"]: ["en_curso"]}

    cambiar_estado(esc, esc.beto, mia["id"], "en_curso")
    assert esc.c.post(f"/api/tareas/{mia['id']}/bloqueos", headers=esc.beto,
                      json={"motivo": "Espera"}).status_code == 201
    assert transiciones(esc.beto)[mia["id"]] == ["pendiente"]  # bloqueada: no se ofrece terminar


def test_tablero_sin_acceso(esc):
    crear_tarea(esc)
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tablero", headers=esc.carla).status_code == 403
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tablero", headers=esc.adm).status_code == 403
    assert esc.c.get("/api/proyectos/9999/tablero", headers=esc.ana).status_code == 403
    assert esc.c.get(f"/api/proyectos/{esc.pid}/tablero").status_code == 401
