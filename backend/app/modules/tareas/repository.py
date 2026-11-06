"""Acceso a datos de tareas. Solo SQL: sin reglas ni commits."""
from typing import Optional

from sqlalchemy import text

from ...db.database import uno


def insertar(db, proyecto_id: int, nombre: str, descripcion: str,
             resultado_esperado: Optional[str], creado_por: int) -> int:
    return db.execute(
        text("""INSERT INTO tareas (proyecto_id, nombre, descripcion, resultado_esperado, creado_por)
                VALUES (:p, :nombre, :descripcion, :resultado, :por)"""),
        {"p": proyecto_id, "nombre": nombre, "descripcion": descripcion,
         "resultado": resultado_esperado, "por": creado_por},
    ).lastrowid


def obtener(db, tarea_id: int) -> Optional[dict]:
    return uno(db, """SELECT t.*, p.nombre AS proyecto_nombre, c.nombre AS creado_por_nombre
                       FROM tareas t
                       JOIN proyectos p ON p.id = t.proyecto_id
                       JOIN usuarios c  ON c.id = t.creado_por
                       WHERE t.id = :id""", id=tarea_id)
