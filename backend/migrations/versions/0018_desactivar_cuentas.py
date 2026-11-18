"""Desactivar cuentas (HU-01-009).

Una cuenta desactivada no se borra: guarda cuándo y quién la desactivó, y todo lo que hizo
conserva su autoría. eventos_cuenta registra cada cambio de acceso de una cuenta con el actor,
la fecha y el valor anterior y nuevo; lo consulta el historial de cambios de acceso (HU-01-010).

Revision ID: 0018
Revises: 0017
"""
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE usuarios ADD COLUMN desactivado_en TEXT")
    op.execute("ALTER TABLE usuarios ADD COLUMN desactivado_por INTEGER REFERENCES usuarios(id)")
    op.execute("""CREATE TABLE eventos_cuenta (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id      INTEGER NOT NULL REFERENCES usuarios(id),
        tipo            TEXT NOT NULL,
        valor_anterior  TEXT,
        valor_nuevo     TEXT,
        actor_id        INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX ix_eventos_cuenta ON eventos_cuenta (usuario_id, id)")


def downgrade() -> None:
    op.execute("DROP TABLE eventos_cuenta")
    op.execute("ALTER TABLE usuarios DROP COLUMN desactivado_por")
    op.execute("ALTER TABLE usuarios DROP COLUMN desactivado_en")
