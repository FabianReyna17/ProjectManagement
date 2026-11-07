"""Expiración de sesiones por inactividad.

ultimo_uso guarda la última petición atendida con la sesión (UTC, mismo formato que
CURRENT_TIMESTAMP). Las sesiones que ya existían toman su fecha de creación.

Revision ID: 0007
Revises: 0006
"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE sesiones ADD COLUMN ultimo_uso TEXT")
    op.execute("UPDATE sesiones SET ultimo_uso = creado_en")
    op.execute("CREATE INDEX ix_sesiones_ultimo_uso ON sesiones (ultimo_uso)")


def downgrade() -> None:
    op.execute("DROP INDEX ix_sesiones_ultimo_uso")
    op.execute("ALTER TABLE sesiones DROP COLUMN ultimo_uso")
