"""Historial de cambios de los datos del proyecto (HU-02-003).

Cada cambio confirmado de nombre, objetivo, responsable o fechas guarda el campo,
el valor anterior, el nuevo, el actor y la fecha.

Revision ID: 0008
Revises: 0007
"""
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE historial_proyectos (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id     INTEGER NOT NULL REFERENCES proyectos(id),
        campo           TEXT NOT NULL,
        valor_anterior  TEXT,
        valor_nuevo     TEXT,
        actor_id        INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX ix_historial_proyecto ON historial_proyectos (proyecto_id)")


def downgrade() -> None:
    op.execute("DROP TABLE historial_proyectos")
