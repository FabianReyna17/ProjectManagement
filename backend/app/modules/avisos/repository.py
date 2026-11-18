"""Acceso a datos de avisos. Solo SQL: sin reglas ni commits."""
from sqlalchemy import text

from ...db.database import varios


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


def listar_de_usuario(db, usuario_id: int) -> list:
    """Avisos de la persona en proyectos donde aún participa, del más reciente al más antiguo."""
    return varios(db, """SELECT a.id, a.tipo, a.proyecto_id, p.nombre AS proyecto_nombre,
                                 a.tarea_id, t.nombre AS tarea_nombre,
                                 a.actor_id, u.nombre AS actor_nombre, a.creado_en,
                                 a.bloqueo_id, b.motivo AS bloqueo_motivo,
                                 CASE WHEN b.id IS NULL THEN NULL ELSE b.resuelto_en IS NOT NULL END AS bloqueo_resuelto
                          FROM avisos a
                          JOIN proyectos p      ON p.id = a.proyecto_id
                          JOIN participantes pa ON pa.proyecto_id = a.proyecto_id
                                               AND pa.usuario_id = a.usuario_id AND pa.activo = 1
                          JOIN usuarios u       ON u.id = a.actor_id
                          LEFT JOIN tareas t    ON t.id = a.tarea_id
                          LEFT JOIN bloqueos b  ON b.id = a.bloqueo_id
                          WHERE a.usuario_id = :u
                          ORDER BY a.id DESC""", u=usuario_id)
