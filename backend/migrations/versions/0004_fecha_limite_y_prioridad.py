"""Fecha límite y prioridad de tareas (HU-03-003).

Revision ID: 0004
Revises: 0003
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE tareas ADD COLUMN fecha_limite TEXT")
    op.execute("""ALTER TABLE tareas ADD COLUMN prioridad TEXT NOT NULL DEFAULT 'media'
                  CHECK (prioridad IN ('alta', 'media', 'baja'))""")


def downgrade() -> None:
    op.execute("ALTER TABLE tareas DROP COLUMN prioridad")
    op.execute("ALTER TABLE tareas DROP COLUMN fecha_limite")
