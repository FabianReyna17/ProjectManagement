"""Acceso a datos de proyectos y participantes. Solo SQL: sin reglas ni commits."""
from typing import Optional

from sqlalchemy import text

from ...db.database import uno, varios


def listar_de_participante(db, usuario_id: int) -> list:
    return varios(db, """SELECT p.id, p.nombre, p.estado, p.fecha_inicio, p.fecha_fin,
                                 r.nombre AS responsable_nombre
                          FROM proyectos p
                          JOIN participantes pa ON pa.proyecto_id = p.id AND pa.usuario_id = :u AND pa.activo = 1
                          JOIN usuarios r ON r.id = p.responsable_id
                          ORDER BY p.id DESC""", u=usuario_id)


def insertar(db, nombre: str, objetivo: str, responsable_id: int,
             fecha_inicio: str, fecha_fin: str, creado_por: int) -> int:
    return db.execute(
        text("""INSERT INTO proyectos (nombre, objetivo, responsable_id, fecha_inicio, fecha_fin, creado_por)
                VALUES (:nombre, :objetivo, :resp, :ini, :fin, :por)"""),
        {"nombre": nombre, "objetivo": objetivo, "resp": responsable_id,
         "ini": fecha_inicio, "fin": fecha_fin, "por": creado_por},
    ).lastrowid


def obtener(db, proyecto_id: int) -> Optional[dict]:
    return uno(db, "SELECT * FROM proyectos WHERE id = :id", id=proyecto_id)


def obtener_con_responsable(db, proyecto_id: int) -> Optional[dict]:
    return uno(db, """SELECT p.*, r.nombre AS responsable_nombre
                       FROM proyectos p JOIN usuarios r ON r.id = p.responsable_id
                       WHERE p.id = :id""", id=proyecto_id)


def es_participante(db, proyecto_id: int, usuario_id: int) -> bool:
    return uno(db, """SELECT 1 FROM participantes
                       WHERE proyecto_id = :p AND usuario_id = :u AND activo = 1""",
                p=proyecto_id, u=usuario_id) is not None


def activar_participante(db, proyecto_id: int, usuario_id: int) -> None:
    """Agrega o reactiva (la fila se conserva al retirar)."""
    db.execute(
        text("""INSERT INTO participantes (proyecto_id, usuario_id) VALUES (:p, :u)
                ON CONFLICT (proyecto_id, usuario_id)
                DO UPDATE SET activo = 1, retirado_en = NULL, agregado_en = CURRENT_TIMESTAMP"""),
        {"p": proyecto_id, "u": usuario_id},
    )


def retirar_participante(db, proyecto_id: int, usuario_id: int) -> bool:
    cur = db.execute(
        text("""UPDATE participantes SET activo = 0, retirado_en = CURRENT_TIMESTAMP
                WHERE proyecto_id = :p AND usuario_id = :u AND activo = 1"""),
        {"p": proyecto_id, "u": usuario_id},
    )
    return cur.rowcount > 0


def listar_participantes(db, proyecto_id: int) -> list:
    return varios(db, """SELECT u.id, u.usuario, u.nombre, f.nombre AS funcion, pa.agregado_en
                          FROM participantes pa
                          JOIN usuarios u  ON u.id = pa.usuario_id
                          JOIN funciones f ON f.id = u.funcion_id
                          WHERE pa.proyecto_id = :p AND pa.activo = 1 ORDER BY u.nombre""", p=proyecto_id)
