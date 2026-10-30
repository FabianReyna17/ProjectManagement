import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_db, requiere_funcion
from ..schemas import UsuarioIn
from ..security import hash_password

router = APIRouter(prefix="/api", tags=["usuarios"])


@router.get("/funciones")
def listar_funciones(_=Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    return [dict(r) for r in db.execute("SELECT id, nombre FROM funciones ORDER BY id")]


@router.get("/usuarios")
def listar_usuarios(_=Depends(requiere_funcion("Admin", "Responsable")), db=Depends(get_db)):
    rows = db.execute(
        """SELECT u.id, u.usuario, u.nombre, f.nombre AS funcion
           FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
           WHERE u.activo = 1 ORDER BY u.nombre"""
    )
    return [dict(r) for r in rows]


@router.post("/usuarios", status_code=201)
def registrar_usuario(data: UsuarioIn, _=Depends(requiere_funcion("Admin")), db=Depends(get_db)):
    if not db.execute("SELECT 1 FROM funciones WHERE id = ?", (data.funcion_id,)).fetchone():
        raise HTTPException(status_code=400, detail="La función seleccionada no existe")
    try:
        cur = db.execute(
            "INSERT INTO usuarios (usuario, nombre, password_hash, funcion_id) VALUES (?,?,?,?)",
            (data.usuario, data.nombre, hash_password(data.password), data.funcion_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="El identificador de usuario ya existe")
    return {"id": cur.lastrowid, "usuario": data.usuario, "nombre": data.nombre, "activo": True}
