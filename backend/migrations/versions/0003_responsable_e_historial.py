"""Responsable de tarea e historial de cambios de tareas (HU-03-002).

historial_tareas guarda cada cambio confirmado (tipo, valor anterior, valor nuevo,
actor y fecha). Lo reutilizan fecha/prioridad, estados y bloqueos.

Revision ID: 0003
Revises: 0002
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE tareas ADD COLUMN responsable_id INTEGER REFERENCES usuarios(id)")
    op.execute("CREATE INDEX ix_tareas_responsable ON tareas (responsable_id)")
    op.execute("""CREATE TABLE historial_tareas (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        tarea_id        INTEGER NOT NULL REFERENCES tareas(id),
        tipo            TEXT NOT NULL,
        valor_anterior  TEXT,
        valor_nuevo     TEXT,
        actor_id        INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX ix_historial_tarea ON historial_tareas (tarea_id)")


def downgrade() -> None:
    op.execute("DROP TABLE historial_tareas")
    op.execute("DROP INDEX ix_tareas_responsable")
    op.execute("ALTER TABLE tareas DROP COLUMN responsable_id")
