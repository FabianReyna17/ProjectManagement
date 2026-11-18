"""Avisos leídos (HU-06-005).

leido_en queda en NULL mientras el aviso está pendiente; se fija al abrirlo o al
marcar todos como leídos. El índice sirve al contador de no leídos.

Revision ID: 0012
Revises: 0011
"""
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE avisos ADD COLUMN leido_en TEXT")
    op.execute("CREATE INDEX ix_avisos_no_leidos ON avisos (usuario_id, leido_en)")


def downgrade() -> None:
    op.execute("DROP INDEX ix_avisos_no_leidos")
    op.execute("ALTER TABLE avisos DROP COLUMN leido_en")
