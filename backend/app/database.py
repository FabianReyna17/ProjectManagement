import os
import sqlite3

from .security import hash_password

DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "data", "gestion.db")

FUNCIONES = ["Admin", "Responsable", "Integrante", "Supervisor"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS funciones (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario        TEXT UNIQUE NOT NULL,
    nombre         TEXT NOT NULL,
    password_hash  TEXT NOT NULL,
    funcion_id     INTEGER NOT NULL REFERENCES funciones(id),
    activo         INTEGER NOT NULL DEFAULT 1,
    creado_en      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sesiones (
    token       TEXT PRIMARY KEY,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    creado_en   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proyectos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    objetivo        TEXT NOT NULL,
    responsable_id  INTEGER NOT NULL REFERENCES usuarios(id),
    fecha_inicio    TEXT NOT NULL,
    fecha_fin       TEXT NOT NULL,
    estado          TEXT NOT NULL DEFAULT 'planificado',
    creado_por      INTEGER NOT NULL REFERENCES usuarios(id),
    creado_en       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Retirar un participante no borra la fila (se conserva historial)
CREATE TABLE IF NOT EXISTS participantes (
    proyecto_id  INTEGER NOT NULL REFERENCES proyectos(id),
    usuario_id   INTEGER NOT NULL REFERENCES usuarios(id),
    activo       INTEGER NOT NULL DEFAULT 1,
    agregado_en  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    retirado_en  TEXT,
    PRIMARY KEY (proyecto_id, usuario_id)
);
"""


def db_path() -> str:
    return os.getenv("DB_PATH", DEFAULT_DB)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    os.makedirs(os.path.dirname(os.path.abspath(db_path())), exist_ok=True)
    conn = get_conn()
    conn.executescript(SCHEMA)
    for f in FUNCIONES:
        conn.execute("INSERT OR IGNORE INTO funciones (nombre) VALUES (?)", (f,))
    # Administrador inicial (solo si no hay cuentas)
    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        admin_id = conn.execute("SELECT id FROM funciones WHERE nombre='Admin'").fetchone()[0]
        conn.execute(
            "INSERT INTO usuarios (usuario, nombre, password_hash, funcion_id) VALUES (?,?,?,?)",
            ("admin", "Administrador", hash_password("Admin123!"), admin_id),
        )
    conn.commit()
    conn.close()
