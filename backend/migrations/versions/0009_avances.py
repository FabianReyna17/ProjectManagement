"""Avances de una tarea (HU-04-002).

Texto breve con autor y fecha. Cada avance también queda en historial_tareas (tipo
'avance') para verlo junto con los demás cambios de la tarea.

Revision ID: 0009
Revises: 0008
"""
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE avances (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        tarea_id    INTEGER NOT NULL REFERENCES tareas(id),
        texto       TEXT NOT NULL,
        autor_id    INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX ix_avances_tarea ON avances (tarea_id)")


def downgrade() -> None:
    op.execute("DROP TABLE avances")
