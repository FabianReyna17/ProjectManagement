"""Acceso a datos de tareas y su historial. Solo SQL: sin reglas ni commits."""
from typing import Optional

from sqlalchemy import text

from ...db.database import uno, varios


def insertar(db, proyecto_id: int, nombre: str, descripcion: str,
             resultado_esperado: Optional[str], responsable_id: Optional[int], creado_por: int) -> int:
    return db.execute(
        text("""INSERT INTO tareas (proyecto_id, nombre, descripcion, resultado_esperado, responsable_id, creado_por)
                VALUES (:p, :nombre, :descripcion, :resultado, :resp, :por)"""),
        {"p": proyecto_id, "nombre": nombre, "descripcion": descripcion,
         "resultado": resultado_esperado, "resp": responsable_id, "por": creado_por},
    ).lastrowid


def obtener(db, tarea_id: int) -> Optional[dict]:
    return uno(db, """SELECT t.*, p.nombre AS proyecto_nombre, c.nombre AS creado_por_nombre,
                              r.nombre AS responsable_nombre
                       FROM tareas t
                       JOIN proyectos p     ON p.id = t.proyecto_id
                       JOIN usuarios c      ON c.id = t.creado_por
                       LEFT JOIN usuarios r ON r.id = t.responsable_id
                       WHERE t.id = :id""", id=tarea_id)


def actualizar_responsable(db, tarea_id: int, responsable_id: int) -> None:
    db.execute(text("UPDATE tareas SET responsable_id = :r WHERE id = :id"), {"r": responsable_id, "id": tarea_id})


# --- Historial ---

def registrar_cambio(db, tarea_id: int, tipo: str, anterior, nuevo, actor_id: int) -> None:
    db.execute(
        text("""INSERT INTO historial_tareas (tarea_id, tipo, valor_anterior, valor_nuevo, actor_id)
                VALUES (:t, :tipo, :ant, :nuevo, :actor)"""),
        {"t": tarea_id, "tipo": tipo, "actor": actor_id,
         "ant": None if anterior is None else str(anterior),
         "nuevo": None if nuevo is None else str(nuevo)},
    )


def listar_historial(db, tarea_id: int) -> list:
    """Cambios en orden cronológico. Para 'responsable' los valores son ids de cuenta
    y se devuelven también los nombres."""
    return varios(db, """SELECT h.id, h.tipo, h.valor_anterior, h.valor_nuevo, h.creado_en,
                                 a.nombre AS actor_nombre,
                                 CASE WHEN h.tipo = 'responsable' THEN ua.nombre END AS anterior_nombre,
                                 CASE WHEN h.tipo = 'responsable' THEN un.nombre END AS nuevo_nombre
                          FROM historial_tareas h
                          JOIN usuarios a       ON a.id = h.actor_id
                          LEFT JOIN usuarios ua ON ua.id = h.valor_anterior
                          LEFT JOIN usuarios un ON un.id = h.valor_nuevo
                          WHERE h.tarea_id = :t ORDER BY h.id""", t=tarea_id)
