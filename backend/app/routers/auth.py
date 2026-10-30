from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_db, usuario_actual
from ..schemas import LoginIn
from ..security import nuevo_token, verificar_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

MSG_LOGIN = "Usuario o contraseña incorrectos"


@router.post("/login")
def login(data: LoginIn, db=Depends(get_db)):
    row = db.execute(
        """SELECT u.id, u.usuario, u.nombre, u.password_hash, u.activo, f.nombre AS funcion
           FROM usuarios u JOIN funciones f ON f.id = u.funcion_id
           WHERE u.usuario = ?""",
        (data.usuario,),
    ).fetchone()
    # Mensaje genérico: no revela si el usuario existe o está inactivo
    if not row or not row["activo"] or not verificar_password(data.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail=MSG_LOGIN)
    token = nuevo_token()
    db.execute("INSERT INTO sesiones (token, usuario_id) VALUES (?, ?)", (token, row["id"]))
    db.commit()
    return {
        "token": token,
        "usuario": {"id": row["id"], "usuario": row["usuario"], "nombre": row["nombre"], "funcion": row["funcion"]},
    }


@router.post("/logout")
def logout(u: dict = Depends(usuario_actual), db=Depends(get_db)):
    db.execute("DELETE FROM sesiones WHERE token = ?", (u["token"],))
    db.commit()
    return {"mensaje": "Sesión cerrada"}


@router.get("/me")
def me(u: dict = Depends(usuario_actual)):
    return {k: u[k] for k in ("id", "usuario", "nombre", "funcion")}
