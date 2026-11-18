"""Avisos dentro de la aplicación (HU-06-001).

Cada aviso es para una persona (usuario_id), tiene un tipo y apunta al proyecto y, si
aplica, a la tarea. evento_id es la entrada de historial_tareas que lo originó: el
índice único impide dos avisos del mismo tipo a la misma persona por un mismo evento.

Revision ID: 0010
Revises: 0009
"""
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE avisos (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id   INTEGER NOT NULL REFERENCES usuarios(id),
        tipo         TEXT NOT NULL,
        proyecto_id  INTEGER NOT NULL REFERENCES proyectos(id),
        tarea_id     INTEGER REFERENCES tareas(id),
        evento_id    INTEGER REFERENCES historial_tareas(id),
        actor_id     INTEGER NOT NULL REFERENCES usuarios(id),
        creado_en    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    op.execute("CREATE UNIQUE INDEX ux_avisos_evento ON avisos (usuario_id, tipo, evento_id)")
    op.execute("CREATE INDEX ix_avisos_usuario ON avisos (usuario_id, id)")


def downgrade() -> None:
    op.execute("DROP TABLE avisos")
