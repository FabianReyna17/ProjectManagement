"""Claves de idempotencia para reintentos sin duplicar (HU-08-002, RP-08-02).

Revision ID: 0006
Revises: 0005
"""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE claves_idempotencia (
        usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
        clave       TEXT NOT NULL,
        tipo        TEXT NOT NULL,
        recurso_id  INTEGER NOT NULL,
        creado_en   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (usuario_id, clave)
    )""")


def downgrade() -> None:
    op.execute("DROP TABLE claves_idempotencia")
