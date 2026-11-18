"""Historial de cambios de acceso (HU-01-010).

eventos_cuenta pasa a ser el historial de accesos: además de los cambios de una cuenta
(alta, función, desactivación, restablecimiento) guarda cada alta y retiro de acceso a un
proyecto (proyecto_id). Los eventos solo se agregan; nunca se modifican ni se borran.

La tabla se recrea para que actor_id admita NULL: los accesos y cuentas anteriores a este
historial se cargan desde participantes y usuarios con actor "no registrado". Los ciclos de
retirar y volver a dar acceso anteriores a esta versión no se conocían (participantes solo
guardaba el último), así que se carga el último estado conocido.

Revision ID: 0021
Revises: 0020
"""
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE eventos_cuenta RENAME TO eventos_cuenta_0018")
    op.execute("DROP INDEX ix_eventos_cuenta")
    op.execute("""CREATE TABLE eventos_cuenta (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id      INTEGER NOT NULL REFERENCES usuarios(id),
        proyecto_id     INTEGER REFERENCES proyectos(id),
        tipo            TEXT NOT NULL,
        valor_anterior  TEXT,
        valor_nuevo     TEXT,
        actor_id        INTEGER REFERENCES usuarios(id),
        creado_en       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    # Lo anterior a este historial, en orden cronológico; actor NULL = no registrado
    op.execute("""INSERT INTO eventos_cuenta (usuario_id, tipo, valor_anterior, valor_nuevo, actor_id, creado_en)
        SELECT u.id, 'cuenta_alta', NULL,
               COALESCE((SELECT e.valor_anterior FROM eventos_cuenta_0018 e
                         WHERE e.usuario_id = u.id AND e.tipo = 'funcion' ORDER BY e.id LIMIT 1), f.nombre),
               NULL, u.creado_en
        FROM usuarios u JOIN funciones f ON f.id = u.funcion_id ORDER BY u.creado_en, u.id""")
    op.execute("""INSERT INTO eventos_cuenta (usuario_id, proyecto_id, tipo, valor_anterior, valor_nuevo, actor_id, creado_en)
        SELECT usuario_id, proyecto_id, tipo, valor_anterior, valor_nuevo, NULL, creado_en FROM (
            SELECT usuario_id, proyecto_id, 'acceso_alta' AS tipo, 'sin acceso' AS valor_anterior,
                   'con acceso' AS valor_nuevo, agregado_en AS creado_en FROM participantes
            UNION ALL
            SELECT usuario_id, proyecto_id, 'acceso_retiro', 'con acceso', 'sin acceso', retirado_en
            FROM participantes WHERE activo = 0 AND retirado_en IS NOT NULL
        ) ORDER BY creado_en""")
    op.execute("""INSERT INTO eventos_cuenta (usuario_id, tipo, valor_anterior, valor_nuevo, actor_id, creado_en)
        SELECT usuario_id, tipo, valor_anterior, valor_nuevo, actor_id, creado_en
        FROM eventos_cuenta_0018 ORDER BY id""")
    op.execute("DROP TABLE eventos_cuenta_0018")
    op.execute("CREATE INDEX ix_eventos_cuenta ON eventos_cuenta (usuario_id, id)")
    op.execute("CREATE INDEX ix_eventos_cuenta_proyecto ON eventos_cuenta (proyecto_id, id)")


def downgrade() -> None:
    op.execute("DROP INDEX ix_eventos_cuenta_proyecto")
    op.execute("DELETE FROM eventos_cuenta WHERE proyecto_id IS NOT NULL OR tipo = 'cuenta_alta' OR actor_id IS NULL")
    op.execute("ALTER TABLE eventos_cuenta DROP COLUMN proyecto_id")
