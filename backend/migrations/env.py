from alembic import context

from app.db.database import crear_engine, database_url


def run_migrations_online() -> None:
    # migrar(url) puede apuntar a otra BD, p. ej. una restaurada desde un respaldo (HU-08-005)
    engine = crear_engine(context.config.attributes.get("url") or database_url())
    with engine.connect() as conn:
        context.configure(connection=conn)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
