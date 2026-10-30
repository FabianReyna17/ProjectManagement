from fastapi import APIRouter, Depends, HTTPException

from ..deps import es_participante, get_db, prohibido, proyecto_autorizado, requiere_funcion, usuario_actual
from ..schemas import ParticipanteIn, ProyectoIn

router = APIRouter(prefix="/api/proyectos", tags=["proyectos"])


def _agregar_participante(db, proyecto_id: int, usuario_id: int):
    db.execute(
        """INSERT INTO participantes (proyecto_id, usuario_id) VALUES (?, ?)
           ON CONFLICT(proyecto_id, usuario_id)
           DO UPDATE SET activo = 1, retirado_en = NULL, agregado_en = CURRENT_TIMESTAMP""",
        (proyecto_id, usuario_id),
    )


def _solo_responsable(proyecto: dict, u: dict):
    if proyecto["responsable_id"] != u["id"]:
        raise prohibido()


@router.get("")
def mis_proyectos(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    rows = db.execute(
        """SELECT p.id, p.nombre, p.estado, p.fecha_inicio, p.fecha_fin, r.nombre AS responsable_nombre
           FROM proyectos p
           JOIN participantes pa ON pa.proyecto_id = p.id AND pa.usuario_id = ? AND pa.activo = 1
           JOIN usuarios r ON r.id = p.responsable_id
           ORDER BY p.id DESC""",
        (u["id"],),
    )
    return [dict(r) for r in rows]


@router.post("", status_code=201)
def crear_proyecto(data: ProyectoIn, u: dict = Depends(requiere_funcion("Admin", "Responsable")), db=Depends(get_db)):
    if data.fecha_fin < data.fecha_inicio:
        raise HTTPException(status_code=400, detail="La fecha de fin no puede ser anterior a la de inicio")
    resp = db.execute(
        """SELECT u.id FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
           WHERE u.id = ? AND u.activo = 1 AND f.nombre IN ('Admin', 'Responsable')""",
        (data.responsable_id,),
    ).fetchone()
    if not resp:
        raise HTTPException(status_code=400, detail="El responsable debe ser una cuenta activa con función Responsable o Admin")

    cur = db.execute(
        """INSERT INTO proyectos (nombre, objetivo, responsable_id, fecha_inicio, fecha_fin, creado_por)
           VALUES (?,?,?,?,?,?)""",
        (data.nombre, data.objetivo, data.responsable_id, data.fecha_inicio.isoformat(), data.fecha_fin.isoformat(), u["id"]),
    )
    pid = cur.lastrowid
    _agregar_participante(db, pid, data.responsable_id)
    if u["id"] != data.responsable_id:
        _agregar_participante(db, pid, u["id"])
    db.commit()
    return dict(db.execute("SELECT * FROM proyectos WHERE id = ?", (pid,)).fetchone())


@router.get("/{proyecto_id}")
def ficha_proyecto(proyecto: dict = Depends(proyecto_autorizado), u: dict = Depends(usuario_actual)):
    return {**proyecto, "soy_responsable": proyecto["responsable_id"] == u["id"]}


@router.get("/{proyecto_id}/participantes")
def listar_participantes(proyecto: dict = Depends(proyecto_autorizado), db=Depends(get_db)):
    rows = db.execute(
        """SELECT u.id, u.usuario, u.nombre, f.nombre AS funcion, pa.agregado_en
           FROM participantes pa
           JOIN usuarios u  ON u.id = pa.usuario_id
           JOIN funciones f ON f.id = u.funcion_id
           WHERE pa.proyecto_id = ? AND pa.activo = 1 ORDER BY u.nombre""",
        (proyecto["id"],),
    )
    return [dict(r) for r in rows]


@router.post("/{proyecto_id}/participantes", status_code=201)
def agregar_participante(
    data: ParticipanteIn,
    proyecto: dict = Depends(proyecto_autorizado),
    u: dict = Depends(usuario_actual),
    db=Depends(get_db),
):
    _solo_responsable(proyecto, u)
    if not db.execute("SELECT 1 FROM usuarios WHERE id = ? AND activo = 1", (data.usuario_id,)).fetchone():
        raise HTTPException(status_code=400, detail="La cuenta no existe o está inactiva")
    if es_participante(db, proyecto["id"], data.usuario_id):
        raise HTTPException(status_code=409, detail="La persona ya participa en el proyecto")
    _agregar_participante(db, proyecto["id"], data.usuario_id)
    db.commit()
    return {"mensaje": "Participante agregado"}


@router.delete("/{proyecto_id}/participantes/{usuario_id}")
def retirar_participante(
    usuario_id: int,
    proyecto: dict = Depends(proyecto_autorizado),
    u: dict = Depends(usuario_actual),
    db=Depends(get_db),
):
    _solo_responsable(proyecto, u)
    if usuario_id == proyecto["responsable_id"]:
        raise HTTPException(status_code=400, detail="No se puede retirar al responsable del proyecto")
    cur = db.execute(
        """UPDATE participantes SET activo = 0, retirado_en = CURRENT_TIMESTAMP
           WHERE proyecto_id = ? AND usuario_id = ? AND activo = 1""",
        (proyecto["id"], usuario_id),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="La persona no participa en el proyecto")
    db.commit()
    return {"mensaje": "Participante retirado"}
