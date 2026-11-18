"""Registro de respaldos (HU-08-004).

Cada ejecución del respaldo (programada o pedida por un Admin) deja su fecha, resultado,
archivo y tamaño. Un respaldo fallido queda registrado con el motivo y nunca cuenta como
disponible.

Revision ID: 0020
Revises: 0019
"""
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE respaldos (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        iniciado_en   TEXT NOT NULL,
        terminado_en  TEXT NOT NULL,
        resultado     TEXT NOT NULL CHECK (resultado IN ('ok', 'fallido')),
        origen        TEXT NOT NULL CHECK (origen IN ('programado', 'manual')),
        actor_id      INTEGER REFERENCES usuarios(id),
        archivo       TEXT,
        tamano        INTEGER,
        detalle       TEXT
    )""")
    op.execute("CREATE INDEX ix_respaldos_resultado ON respaldos (resultado, id)")


def downgrade() -> None:
    op.execute("DROP TABLE respaldos")
