"""Comentarios de proyectos y tareas (HU-05-001).

Un comentario pertenece siempre a un proyecto; si tarea_id es NULL es del proyecto,
si no, de esa tarea. Guarda autor y fecha; no se edita ni se borra.

Revision ID: 0013
Revises: 0012
"""
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE comentarios (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id  INTEGER NOT NULL REFERENCES proyectos(id),
        tarea_id     INTEGER REFERENCES tareas(id),
        texto        TEXT NOT NULL,
        autor_id     INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE INDEX ix_comentarios_destino ON comentarios (proyecto_id, tarea_id)")


def downgrade() -> None:
    op.execute("DROP TABLE comentarios")
