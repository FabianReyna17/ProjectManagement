"""Acceso a datos de comentarios y archivos. Solo SQL: sin reglas ni commits."""
from typing import Optional

from sqlalchemy import text

from ...db.database import uno, varios


def insertar_comentario(db, proyecto_id: int, tarea_id: Optional[int], texto: str, autor_id: int) -> int:
    return db.execute(
        text("INSERT INTO comentarios (proyecto_id, tarea_id, texto, autor_id) VALUES (:p, :t, :x, :a)"),
        {"p": proyecto_id, "t": tarea_id, "x": texto, "a": autor_id},
    ).lastrowid


SELECT_COMENTARIO = """SELECT c.id, c.proyecto_id, c.tarea_id, c.texto, c.autor_id, a.nombre AS autor_nombre, c.creado_en,
                              c.editado_en, c.retirado_en, rp.nombre AS retirado_por_nombre,
                              (SELECT COUNT(*) FROM ediciones_comentario e WHERE e.comentario_id = c.id) AS ediciones
                       FROM comentarios c JOIN usuarios a ON a.id = c.autor_id
                       LEFT JOIN usuarios rp ON rp.id = c.retirado_por"""


def obtener_comentario(db, comentario_id: int) -> Optional[dict]:
    return uno(db, f"{SELECT_COMENTARIO} WHERE c.id = :id", id=comentario_id)


def listar_comentarios(db, proyecto_id: int, tarea_id: Optional[int]) -> list:
    """Del destino exacto: los del proyecto no incluyen los de sus tareas. En orden de publicación."""
    return varios(db, f"""{SELECT_COMENTARIO}
                           WHERE c.proyecto_id = :p AND c.tarea_id IS :t ORDER BY c.id""", p=proyecto_id, t=tarea_id)


def editar_comentario(db, comentario_id: int, leido: str, nuevo: str, actor_id: int) -> bool:
    """HU-05-004: cambia el texto solo si sigue siendo el leído y no está retirado, y guarda el
    texto anterior. False si otra edición o un retiro llegó antes."""
    cur = db.execute(text("""UPDATE comentarios SET texto = :nuevo, editado_en = CURRENT_TIMESTAMP
                             WHERE id = :id AND texto = :leido AND retirado_en IS NULL"""),
                     {"nuevo": nuevo, "leido": leido, "id": comentario_id})
    if cur.rowcount:
        db.execute(text("""INSERT INTO ediciones_comentario (comentario_id, texto_anterior, editado_por)
                           VALUES (:c, :t, :a)"""), {"c": comentario_id, "t": leido, "a": actor_id})
    return cur.rowcount > 0


def listar_ediciones(db, comentario_id: int) -> list:
    """Textos anteriores, del más antiguo al más reciente."""
    return varios(db, """SELECT e.id, e.texto_anterior, e.editado_en, a.nombre AS editado_por_nombre
                         FROM ediciones_comentario e JOIN usuarios a ON a.id = e.editado_por
                         WHERE e.comentario_id = :c ORDER BY e.id""", c=comentario_id)


def retirar(db, tabla: str, elemento_id: int, actor_id: int) -> None:
    """HU-05-004: marca el comentario o archivo como retirado (solo la primera vez). No se borra."""
    assert tabla in ("comentarios", "archivos")
    db.execute(text(f"""UPDATE {tabla} SET retirado_en = CURRENT_TIMESTAMP, retirado_por = :a
                        WHERE id = :id AND retirado_en IS NULL"""), {"a": actor_id, "id": elemento_id})


# --- Archivos ---

def insertar_archivo(db, proyecto_id: int, tarea_id: Optional[int], nombre: str, tipo: str, tamano: int,
                     sha256: str, almacen: str, autor_id: int) -> int:
    return db.execute(
        text("""INSERT INTO archivos (proyecto_id, tarea_id, nombre, tipo, tamano, sha256, almacen, autor_id)
                VALUES (:p, :t, :n, :tipo, :tam, :sha, :alm, :a)"""),
        {"p": proyecto_id, "t": tarea_id, "n": nombre, "tipo": tipo, "tam": tamano, "sha": sha256,
         "alm": almacen, "a": autor_id},
    ).lastrowid


SELECT_ARCHIVO = """SELECT f.id, f.proyecto_id, f.tarea_id, f.nombre, f.tipo, f.tamano, f.almacen,
                           f.autor_id, a.nombre AS autor_nombre, f.creado_en,
                           f.retirado_en, rp.nombre AS retirado_por_nombre
                    FROM archivos f JOIN usuarios a ON a.id = f.autor_id
                    LEFT JOIN usuarios rp ON rp.id = f.retirado_por"""


def obtener_archivo(db, archivo_id: int) -> Optional[dict]:
    return uno(db, f"{SELECT_ARCHIVO} WHERE f.id = :id", id=archivo_id)


def listar_archivos(db, proyecto_id: int, tarea_id: Optional[int]) -> list:
    return varios(db, f"""{SELECT_ARCHIVO}
                           WHERE f.proyecto_id = :p AND f.tarea_id IS :t ORDER BY f.id""", p=proyecto_id, t=tarea_id)
