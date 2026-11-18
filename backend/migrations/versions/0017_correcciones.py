"""Corregir contenido propio (HU-05-004).

Un comentario editado guarda cuándo se editó y cada texto anterior (con quién y cuándo)
en ediciones_comentario. Un comentario o archivo retirado no se borra: guarda cuándo y
quién lo retiró, y deja de mostrarse su contenido. Política propuesta en RP-05-03.

Revision ID: 0017
Revises: 0016
"""
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE comentarios ADD COLUMN editado_en TEXT")
    op.execute("ALTER TABLE comentarios ADD COLUMN retirado_en TEXT")
    op.execute("ALTER TABLE comentarios ADD COLUMN retirado_por INTEGER REFERENCES usuarios(id)")
    op.execute("""CREATE TABLE ediciones_comentario (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        comentario_id   INTEGER NOT NULL REFERENCES comentarios(id),
        texto_anterior  TEXT NOT NULL,
        editado_por     INTEGER NOT NULL REFERENCES usuarios(id),
        editado_en      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX ix_ediciones_comentario ON ediciones_comentario (comentario_id, id)")
    op.execute("ALTER TABLE archivos ADD COLUMN retirado_en TEXT")
    op.execute("ALTER TABLE archivos ADD COLUMN retirado_por INTEGER REFERENCES usuarios(id)")


def downgrade() -> None:
    op.execute("ALTER TABLE archivos DROP COLUMN retirado_por")
    op.execute("ALTER TABLE archivos DROP COLUMN retirado_en")
    op.execute("DROP TABLE ediciones_comentario")
    op.execute("ALTER TABLE comentarios DROP COLUMN retirado_por")
    op.execute("ALTER TABLE comentarios DROP COLUMN retirado_en")
    op.execute("ALTER TABLE comentarios DROP COLUMN editado_en")
