"""Bloqueos de tareas (HU-04-003, HU-04-004).

El bloqueo se registra aparte del estado (RP-04-01): una tarea puede estar en curso y
bloqueada a la vez. El índice único parcial impide dos bloqueos abiertos en la misma tarea.

Revision ID: 0005
Revises: 0004
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE bloqueos (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        tarea_id     INTEGER NOT NULL REFERENCES tareas(id),
        motivo       TEXT NOT NULL,
        abierto_por  INTEGER NOT NULL REFERENCES usuarios(id),
        abierto_en   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        resolucion   TEXT,
        resuelto_por INTEGER REFERENCES usuarios(id),
        resuelto_en  TEXT
    )""")
    op.execute("CREATE INDEX ix_bloqueos_tarea ON bloqueos (tarea_id)")
    op.execute("CREATE UNIQUE INDEX ux_bloqueo_abierto ON bloqueos (tarea_id) WHERE resuelto_en IS NULL")


def downgrade() -> None:
    op.execute("DROP TABLE bloqueos")
