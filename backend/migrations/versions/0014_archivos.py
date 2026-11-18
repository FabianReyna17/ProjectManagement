"""Archivos adjuntos de proyectos y tareas (HU-05-002).

Como los comentarios: siempre de un proyecto y, si tarea_id no es NULL, de esa tarea.
El contenido vive en disco (ARCHIVOS_DIR) con un nombre interno aleatorio
(almacen); aquí se guardan el nombre original, el tipo, el tamaño y la huella SHA-256.

Revision ID: 0014
Revises: 0013
"""
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE archivos (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id  INTEGER NOT NULL REFERENCES proyectos(id),
        tarea_id     INTEGER REFERENCES tareas(id),
        nombre       TEXT NOT NULL,
        tipo         TEXT NOT NULL,
        tamano       INTEGER NOT NULL,
        sha256       TEXT NOT NULL,
        almacen      TEXT NOT NULL UNIQUE,
        autor_id     INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX ix_archivos_destino ON archivos (proyecto_id, tarea_id)")


def downgrade() -> None:
    op.execute("DROP TABLE archivos")
