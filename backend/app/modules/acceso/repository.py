"""Acceso a datos de cuentas, funciones y sesiones. Solo SQL: sin reglas ni commits."""
import sqlite3
from typing import Optional


class UsuarioDuplicado(Exception):
    pass


def buscar_por_token(db, token: str) -> Optional[sqlite3.Row]:
    return db.execute(
        """SELECT u.id, u.usuario, u.nombre, u.activo, f.nombre AS funcion
           FROM sesiones s
           JOIN usuarios u  ON u.id = s.usuario_id
           JOIN funciones f ON f.id = u.funcion_id
           WHERE s.token = ?""",
        (token,),
    ).fetchone()


def buscar_por_usuario(db, usuario: str) -> Optional[sqlite3.Row]:
    return db.execute(
        """SELECT u.id, u.usuario, u.nombre, u.password_hash, u.activo, f.nombre AS funcion
           FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
           WHERE u.usuario = ?""",
        (usuario,),
    ).fetchone()


def crear_sesion(db, token: str, usuario_id: int) -> None:
    db.execute("INSERT INTO sesiones (token, usuario_id) VALUES (?, ?)", (token, usuario_id))


def borrar_sesion(db, token: str) -> None:
    db.execute("DELETE FROM sesiones WHERE token = ?", (token,))


def listar_funciones(db) -> list:
    return [dict(r) for r in db.execute("SELECT id, nombre FROM funciones ORDER BY id")]


def existe_funcion(db, funcion_id: int) -> bool:
    return db.execute("SELECT 1 FROM funciones WHERE id = ?", (funcion_id,)).fetchone() is not None


def listar_usuarios_activos(db) -> list:
    rows = db.execute(
        """SELECT u.id, u.usuario, u.nombre, f.nombre AS funcion
           FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
           WHERE u.activo = 1 ORDER BY u.nombre"""
    )
    return [dict(r) for r in rows]


def insertar_usuario(db, usuario: str, nombre: str, password_hash: str, funcion_id: int) -> int:
    try:
        cur = db.execute(
            "INSERT INTO usuarios (usuario, nombre, password_hash, funcion_id) VALUES (?,?,?,?)",
            (usuario, nombre, password_hash, funcion_id),
        )
    except sqlite3.IntegrityError as e:
        raise UsuarioDuplicado() from e
    return cur.lastrowid


def es_cuenta_activa(db, usuario_id: int) -> bool:
    return db.execute(
        "SELECT 1 FROM usuarios WHERE id = ? AND activo = 1", (usuario_id,)
    ).fetchone() is not None


def tiene_funcion_activa(db, usuario_id: int, funciones: tuple) -> bool:
    marcas = ",".join("?" * len(funciones))
    return db.execute(
        f"""SELECT 1 FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
            WHERE u.id = ? AND u.activo = 1 AND f.nombre IN ({marcas})""",
        (usuario_id, *funciones),
    ).fetchone() is not None
