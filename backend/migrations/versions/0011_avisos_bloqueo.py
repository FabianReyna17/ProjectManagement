"""Avisos de bloqueo (HU-06-003).

bloqueo_id liga el aviso al bloqueo que lo originó: así el aviso muestra el motivo y
deja de figurar como pendiente de atención cuando el bloqueo se resuelve, sin borrarse.

Revision ID: 0011
Revises: 0010
"""
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE avisos ADD COLUMN bloqueo_id INTEGER REFERENCES bloqueos(id)")


def downgrade() -> None:
    op.execute("ALTER TABLE avisos DROP COLUMN bloqueo_id")
