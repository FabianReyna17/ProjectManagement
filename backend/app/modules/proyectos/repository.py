"""Acceso a datos de proyectos y participantes. Solo SQL: sin reglas ni commits."""
from typing import Optional


def listar_de_participante(db, usuario_id: int) -> list:
    rows = db.execute(
        """SELECT p.id, p.nombre, p.estado, p.fecha_inicio, p.fecha_fin, r.nombre AS responsable_nombre
           FROM proyectos p
           JOIN participantes pa ON pa.proyecto_id = p.id AND pa.usuario_id = ? AND pa.activo = 1
           JOIN usuarios r ON r.id = p.responsable_id
           ORDER BY p.id DESC""",
        (usuario_id,),
    )
    return [dict(r) for r in rows]


def insertar(db, nombre: str, objetivo: str, responsable_id: int,
             fecha_inicio: str, fecha_fin: str, creado_por: int) -> int:
    cur = db.execute(
        """INSERT INTO proyectos (nombre, objetivo, responsable_id, fecha_inicio, fecha_fin, creado_por)
           VALUES (?,?,?,?,?,?)""",
        (nombre, objetivo, responsable_id, fecha_inicio, fecha_fin, creado_por),
    )
    return cur.lastrowid


def obtener(db, proyecto_id: int) -> Optional[dict]:
    row = db.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
    return dict(row) if row else None


def obtener_con_responsable(db, proyecto_id: int) -> Optional[dict]:
    row = db.execute(
        """SELECT p.*, r.nombre AS responsable_nombre
           FROM proyectos p JOIN usuarios r ON r.id = p.responsable_id
           WHERE p.id = ?""",
        (proyecto_id,),
    ).fetchone()
    return dict(row) if row else None


def es_participante(db, proyecto_id: int, usuario_id: int) -> bool:
    return db.execute(
        "SELECT 1 FROM participantes WHERE proyecto_id=? AND usuario_id=? AND activo=1",
        (proyecto_id, usuario_id),
    ).fetchone() is not None


def activar_participante(db, proyecto_id: int, usuario_id: int) -> None:
    """Agrega o reactiva (la fila se conserva al retirar)."""
    db.execute(
        """INSERT INTO participantes (proyecto_id, usuario_id) VALUES (?, ?)
           ON CONFLICT(proyecto_id, usuario_id)
           DO UPDATE SET activo = 1, retirado_en = NULL, agregado_en = CURRENT_TIMESTAMP""",
        (proyecto_id, usuario_id),
    )


def retirar_participante(db, proyecto_id: int, usuario_id: int) -> bool:
    cur = db.execute(
        """UPDATE participantes SET activo = 0, retirado_en = CURRENT_TIMESTAMP
           WHERE proyecto_id = ? AND usuario_id = ? AND activo = 1""",
        (proyecto_id, usuario_id),
    )
    return cur.rowcount > 0


def listar_participantes(db, proyecto_id: int) -> list:
    rows = db.execute(
        """SELECT u.id, u.usuario, u.nombre, f.nombre AS funcion, pa.agregado_en
           FROM participantes pa
           JOIN usuarios u  ON u.id = pa.usuario_id
           JOIN funciones f ON f.id = u.funcion_id
           WHERE pa.proyecto_id = ? AND pa.activo = 1 ORDER BY u.nombre""",
        (proyecto_id,),
    )
    return [dict(r) for r in rows]
