"""Tareas ligadas a un proyecto (HU-03-001).

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE tareas (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id         INTEGER NOT NULL REFERENCES proyectos(id),
        nombre              TEXT NOT NULL,
        descripcion         TEXT NOT NULL,
        resultado_esperado  TEXT,
        estado              TEXT NOT NULL DEFAULT 'pendiente',
        creado_por          INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX ix_tareas_proyecto ON tareas (proyecto_id)")


def downgrade() -> None:
    op.execute("DROP TABLE tareas")
