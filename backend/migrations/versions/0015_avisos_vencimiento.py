"""Avisos de vencimiento cercano (HU-06-002).

No nacen de un evento del historial sino del proceso programado, así que se identifican
por la tarea y la fecha límite avisada: el índice único impide repetir el aviso del mismo
vencimiento a la misma persona. Si la tarea se reprograma, la fecha nueva es otro vencimiento.

Revision ID: 0015
Revises: 0014
"""
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE avisos ADD COLUMN fecha_limite TEXT")
    op.execute("""CREATE UNIQUE INDEX ux_avisos_vencimiento ON avisos (usuario_id, tarea_id, fecha_limite)
                  WHERE tipo = 'vencimiento'""")


def downgrade() -> None:
    op.execute("DROP INDEX ux_avisos_vencimiento")
    op.execute("ALTER TABLE avisos DROP COLUMN fecha_limite")
