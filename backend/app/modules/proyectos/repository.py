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


CAMPOS_EDITABLES = ("nombre", "objetivo", "responsable_id", "fecha_inicio", "fecha_fin")


def actualizar(db, proyecto_id: int, valores: dict) -> None:
    """Actualiza solo los campos recibidos (nombres validados contra CAMPOS_EDITABLES)."""
    campos = [c for c in valores if c in CAMPOS_EDITABLES]
    db.execute(text(f"UPDATE proyectos SET {', '.join(f'{c} = :{c}' for c in campos)} WHERE id = :id"),
               {**{c: valores[c] for c in campos}, "id": proyecto_id})


def registrar_cambio(db, proyecto_id: int, campo: str, anterior, nuevo, actor_id: int) -> None:
    db.execute(
        text("""INSERT INTO historial_proyectos (proyecto_id, campo, valor_anterior, valor_nuevo, actor_id)
                VALUES (:p, :campo, :ant, :nuevo, :actor)"""),
        {"p": proyecto_id, "campo": campo, "actor": actor_id,
         "ant": None if anterior is None else str(anterior), "nuevo": None if nuevo is None else str(nuevo)},
    )


def listar_historial(db, proyecto_id: int) -> list:
    """Cambios en orden cronológico; para el responsable se devuelven también los nombres."""
    return varios(db, """SELECT h.id, h.campo, h.valor_anterior, h.valor_nuevo, h.creado_en,
                                 a.nombre AS actor_nombre,
                                 CASE WHEN h.campo = 'responsable_id' THEN ua.nombre END AS anterior_nombre,
                                 CASE WHEN h.campo = 'responsable_id' THEN un.nombre END AS nuevo_nombre
                          FROM historial_proyectos h
                          JOIN usuarios a       ON a.id = h.actor_id
                          LEFT JOIN usuarios ua ON ua.id = h.valor_anterior
                          LEFT JOIN usuarios un ON un.id = h.valor_nuevo
                          WHERE h.proyecto_id = :p ORDER BY h.id""", p=proyecto_id)


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
