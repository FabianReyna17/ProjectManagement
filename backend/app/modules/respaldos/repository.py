"""Registro de ejecuciones del respaldo. Solo SQL: sin reglas ni commits."""
from typing import Optional

from sqlalchemy import text

from ...db.database import uno, varios

SELECT = """SELECT r.id, r.iniciado_en, r.terminado_en, r.resultado, r.origen, r.archivo, r.tamano, r.detalle,
                   a.nombre AS actor_nombre
            FROM respaldos r LEFT JOIN usuarios a ON a.id = r.actor_id"""


def registrar(db, datos: dict) -> int:
    return db.execute(
        text("""INSERT INTO respaldos (iniciado_en, terminado_en, resultado, origen, actor_id, archivo, tamano, detalle)
                VALUES (:iniciado_en, :terminado_en, :resultado, :origen, :actor_id, :archivo, :tamano, :detalle)"""),
        datos,
    ).lastrowid


def obtener(db, respaldo_id: int) -> Optional[dict]:
    return uno(db, f"{SELECT} WHERE r.id = :id", id=respaldo_id)


def listar(db, limite: int = 50) -> list:
    return varios(db, f"{SELECT} ORDER BY r.id DESC LIMIT :n", n=limite)


def validos(db) -> list:
    """Respaldos correctos, del más reciente al más antiguo."""
    return varios(db, f"{SELECT} WHERE r.resultado = 'ok' ORDER BY r.id DESC")
