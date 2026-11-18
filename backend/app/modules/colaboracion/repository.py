"""Acceso a datos de comentarios y archivos. Solo SQL: sin reglas ni commits."""
from typing import Optional

from sqlalchemy import text

from ...db.database import uno, varios


def insertar_comentario(db, proyecto_id: int, tarea_id: Optional[int], texto: str, autor_id: int) -> int:
    return db.execute(
        text("INSERT INTO comentarios (proyecto_id, tarea_id, texto, autor_id) VALUES (:p, :t, :x, :a)"),
        {"p": proyecto_id, "t": tarea_id, "x": texto, "a": autor_id},
    ).lastrowid


SELECT_COMENTARIO = """SELECT c.id, c.proyecto_id, c.tarea_id, c.texto, c.autor_id, a.nombre AS autor_nombre, c.creado_en
                       FROM comentarios c JOIN usuarios a ON a.id = c.autor_id"""


def obtener_comentario(db, comentario_id: int) -> Optional[dict]:
    return uno(db, f"{SELECT_COMENTARIO} WHERE c.id = :id", id=comentario_id)


def listar_comentarios(db, proyecto_id: int, tarea_id: Optional[int]) -> list:
    """Del destino exacto: los del proyecto no incluyen los de sus tareas. En orden de publicación."""
    return varios(db, f"""{SELECT_COMENTARIO}
                           WHERE c.proyecto_id = :p AND c.tarea_id IS :t ORDER BY c.id""", p=proyecto_id, t=tarea_id)


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
                           f.autor_id, a.nombre AS autor_nombre, f.creado_en
                    FROM archivos f JOIN usuarios a ON a.id = f.autor_id"""


def obtener_archivo(db, archivo_id: int) -> Optional[dict]:
    return uno(db, f"{SELECT_ARCHIVO} WHERE f.id = :id", id=archivo_id)


def listar_archivos(db, proyecto_id: int, tarea_id: Optional[int]) -> list:
    return varios(db, f"""{SELECT_ARCHIVO}
                           WHERE f.proyecto_id = :p AND f.tarea_id IS :t ORDER BY f.id""", p=proyecto_id, t=tarea_id)
