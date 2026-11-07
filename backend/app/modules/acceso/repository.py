"""Acceso a datos de cuentas, funciones y sesiones. Solo SQL: sin reglas ni commits."""
from typing import Optional

from sqlalchemy import bindparam, text
from sqlalchemy.exc import IntegrityError

from ...db.database import uno, varios


class UsuarioDuplicado(Exception):
    pass


def buscar_por_token(db, token: str) -> Optional[dict]:
    return uno(db, """SELECT u.id, u.usuario, u.nombre, u.activo, f.nombre AS funcion,
                              COALESCE(s.ultimo_uso, s.creado_en) AS ultimo_uso
                       FROM sesiones s
                       JOIN usuarios u  ON u.id = s.usuario_id
                       JOIN funciones f ON f.id = u.funcion_id
                       WHERE s.token = :token""", token=token)


def buscar_por_usuario(db, usuario: str) -> Optional[dict]:
    return uno(db, """SELECT u.id, u.usuario, u.nombre, u.password_hash, u.activo, f.nombre AS funcion
                       FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
                       WHERE u.usuario = :usuario""", usuario=usuario)


def crear_sesion(db, token: str, usuario_id: int, ahora: str) -> None:
    db.execute(text("INSERT INTO sesiones (token, usuario_id, ultimo_uso) VALUES (:t, :u, :ahora)"),
               {"t": token, "u": usuario_id, "ahora": ahora})


def tocar_sesion(db, token: str, ahora: str) -> None:
    db.execute(text("UPDATE sesiones SET ultimo_uso = :ahora WHERE token = :t"), {"t": token, "ahora": ahora})


def borrar_sesion(db, token: str) -> None:
    db.execute(text("DELETE FROM sesiones WHERE token = :t"), {"t": token})


def borrar_sesiones_inactivas(db, limite: str) -> None:
    db.execute(text("DELETE FROM sesiones WHERE COALESCE(ultimo_uso, creado_en) < :limite"), {"limite": limite})


def listar_funciones(db) -> list:
    return varios(db, "SELECT id, nombre FROM funciones ORDER BY id")


def existe_funcion(db, funcion_id: int) -> bool:
    return uno(db, "SELECT 1 FROM funciones WHERE id = :id", id=funcion_id) is not None


def listar_usuarios_activos(db) -> list:
    return varios(db, """SELECT u.id, u.usuario, u.nombre, f.nombre AS funcion
                          FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
                          WHERE u.activo = 1 ORDER BY u.nombre""")


def insertar_usuario(db, usuario: str, nombre: str, password_hash: str, funcion_id: int) -> int:
    try:
        return db.execute(
            text("""INSERT INTO usuarios (usuario, nombre, password_hash, funcion_id)
                    VALUES (:usuario, :nombre, :h, :f)"""),
            {"usuario": usuario, "nombre": nombre, "h": password_hash, "f": funcion_id},
        ).lastrowid
    except IntegrityError as e:
        raise UsuarioDuplicado() from e


def obtener_usuario(db, usuario_id: int) -> Optional[dict]:
    return uno(db, "SELECT id, usuario, nombre, activo FROM usuarios WHERE id = :id", id=usuario_id)


def es_cuenta_activa(db, usuario_id: int) -> bool:
    return uno(db, "SELECT 1 FROM usuarios WHERE id = :id AND activo = 1", id=usuario_id) is not None


def tiene_funcion_activa(db, usuario_id: int, funciones: tuple) -> bool:
    sql = text("""SELECT 1 FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
                  WHERE u.id = :id AND u.activo = 1 AND f.nombre IN :funciones""")
    sql = sql.bindparams(bindparam("funciones", expanding=True))
    return db.execute(sql, {"id": usuario_id, "funciones": list(funciones)}).first() is not None
