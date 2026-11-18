"""Restablecer acceso (HU-01-011).

debe_cambiar_password marca una cuenta que entró con una contraseña temporal entregada por
un Admin: hasta que la cambie, solo puede consultar su cuenta, cambiar la contraseña o salir.

Revision ID: 0019
Revises: 0018
"""
from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE usuarios ADD COLUMN debe_cambiar_password INTEGER NOT NULL DEFAULT 0")


def downgrade() -> None:
    op.execute("ALTER TABLE usuarios DROP COLUMN debe_cambiar_password")
