"""Acceso a datos de avisos. Solo SQL: sin reglas ni commits."""
from typing import Optional

from sqlalchemy import text

from ...db.database import uno, varios


def insertar(db, usuario_id: int, tipo: str, proyecto_id: int, tarea_id, evento_id, actor_id: int,
             bloqueo_id=None) -> None:
    """Un mismo evento no genera dos avisos iguales para la misma persona (índice único)."""
    db.execute(
        text("""INSERT INTO avisos (usuario_id, tipo, proyecto_id, tarea_id, evento_id, actor_id, bloqueo_id)
                VALUES (:u, :tipo, :p, :t, :e, :a, :b)
                ON CONFLICT (usuario_id, tipo, evento_id) DO NOTHING"""),
        {"u": usuario_id, "tipo": tipo, "p": proyecto_id, "t": tarea_id, "e": evento_id, "a": actor_id,
         "b": bloqueo_id},
    )


def insertar_vencimiento(db, usuario_id: int, proyecto_id: int, tarea_id: int, fecha_limite: str) -> bool:
    """HU-06-002: lo genera el sistema; actor_id es la propia persona avisada. False si ese
    vencimiento ya se le había avisado (índice único por persona, tarea y fecha)."""
    cur = db.execute(
        text("""INSERT OR IGNORE INTO avisos (usuario_id, tipo, proyecto_id, tarea_id, actor_id, fecha_limite)
                VALUES (:u, 'vencimiento', :p, :t, :u, :f)"""),
        {"u": usuario_id, "p": proyecto_id, "t": tarea_id, "f": fecha_limite},
    )
    return cur.rowcount > 0


# con_acceso: la persona aún participa en el proyecto del aviso (acceso vigente, no el de entonces)
SELECT_AVISO = """SELECT a.id, a.usuario_id, a.tipo, a.creado_en, a.leido_en,
                         pa.usuario_id IS NOT NULL AS con_acceso,
                         a.proyecto_id, p.nombre AS proyecto_nombre,
                         a.tarea_id, t.nombre AS tarea_nombre,
                         a.actor_id, u.nombre AS actor_nombre,
                         a.bloqueo_id, b.motivo AS bloqueo_motivo, a.fecha_limite,
                         CASE WHEN b.id IS NULL THEN NULL ELSE b.resuelto_en IS NOT NULL END AS bloqueo_resuelto
                  FROM avisos a
                  JOIN proyectos p           ON p.id = a.proyecto_id
                  JOIN usuarios u            ON u.id = a.actor_id
                  LEFT JOIN participantes pa ON pa.proyecto_id = a.proyecto_id
                                            AND pa.usuario_id = a.usuario_id AND pa.activo = 1
                  LEFT JOIN tareas t         ON t.id = a.tarea_id
                  LEFT JOIN bloqueos b       ON b.id = a.bloqueo_id"""


def listar_de_usuario(db, usuario_id: int) -> list:
    """Avisos de la persona, del más reciente al más antiguo."""
    return varios(db, f"{SELECT_AVISO} WHERE a.usuario_id = :u ORDER BY a.id DESC", u=usuario_id)


def obtener(db, aviso_id: int) -> Optional[dict]:
    return uno(db, f"{SELECT_AVISO} WHERE a.id = :id", id=aviso_id)


def contar_no_leidos(db, usuario_id: int) -> int:
    return db.execute(text("SELECT COUNT(*) FROM avisos WHERE usuario_id = :u AND leido_en IS NULL"),
                      {"u": usuario_id}).scalar()


def marcar_leido(db, aviso_id: int) -> None:
    """Solo la primera apertura fija la fecha de lectura."""
    db.execute(text("UPDATE avisos SET leido_en = CURRENT_TIMESTAMP WHERE id = :id AND leido_en IS NULL"),
               {"id": aviso_id})


def marcar_todos_leidos(db, usuario_id: int) -> int:
    return db.execute(text("""UPDATE avisos SET leido_en = CURRENT_TIMESTAMP
                              WHERE usuario_id = :u AND leido_en IS NULL"""), {"u": usuario_id}).rowcount
