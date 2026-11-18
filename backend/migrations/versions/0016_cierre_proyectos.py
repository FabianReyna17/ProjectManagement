"""Cierre de proyectos (HU-02-005).

El cierre guarda cuándo y quién lo hizo, cuántas tareas seguían abiertas y, si había,
la justificación de la excepción. El cambio de estado también queda en historial_proyectos.
Nada se borra: tareas, archivos, comentarios e historial se conservan para consulta.

Revision ID: 0016
Revises: 0015
"""
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

COLUMNAS = (("cerrado_en", "TEXT"), ("cerrado_por", "INTEGER REFERENCES usuarios(id)"),
            ("cierre_justificacion", "TEXT"), ("cierre_tareas_abiertas", "INTEGER"))


def upgrade() -> None:
    for nombre, tipo in COLUMNAS:
        op.execute(f"ALTER TABLE proyectos ADD COLUMN {nombre} {tipo}")


def downgrade() -> None:
    for nombre, _ in reversed(COLUMNAS):
        op.execute(f"ALTER TABLE proyectos DROP COLUMN {nombre}")
