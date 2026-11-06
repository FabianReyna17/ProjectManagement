"""Esquema inicial del Sprint 1: funciones, usuarios, sesiones, proyectos y participantes.

Usa IF NOT EXISTS para que una BD creada antes de Alembic (Sprint 1) se adopte sin perder datos.

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLAS = [
    """CREATE TABLE IF NOT EXISTS funciones (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre  TEXT UNIQUE NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS usuarios (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario        TEXT UNIQUE NOT NULL,
        nombre         TEXT NOT NULL,
        password_hash  TEXT NOT NULL,
        funcion_id     INTEGER NOT NULL REFERENCES funciones(id),
        activo         INTEGER NOT NULL DEFAULT 1,
        creado_en      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS sesiones (
        token       TEXT PRIMARY KEY,
        usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS proyectos (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre          TEXT NOT NULL,
        objetivo        TEXT NOT NULL,
        responsable_id  INTEGER NOT NULL REFERENCES usuarios(id),
        fecha_inicio    TEXT NOT NULL,
        fecha_fin       TEXT NOT NULL,
        estado          TEXT NOT NULL DEFAULT 'planificado',
        creado_por      INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    # Retirar un participante no borra la fila (se conserva historial)
    """CREATE TABLE IF NOT EXISTS participantes (
        proyecto_id  INTEGER NOT NULL REFERENCES proyectos(id),
        usuario_id   INTEGER NOT NULL REFERENCES usuarios(id),
        activo       INTEGER NOT NULL DEFAULT 1,
        agregado_en  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        retirado_en  TEXT,
        PRIMARY KEY (proyecto_id, usuario_id)
    )""",
]


def upgrade() -> None:
    for sql in TABLAS:
        op.execute(sql)
    for nombre in ("Admin", "Responsable", "Integrante", "Supervisor"):
        op.execute(f"INSERT OR IGNORE INTO funciones (nombre) VALUES ('{nombre}')")


def downgrade() -> None:
    for tabla in ("participantes", "proyectos", "sesiones", "usuarios", "funciones"):
        op.execute(f"DROP TABLE {tabla}")
