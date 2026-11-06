from alembic import context

from app.db.database import crear_engine, database_url


def run_migrations_online() -> None:
    engine = crear_engine(database_url())
    with engine.connect() as conn:
        context.configure(connection=conn)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
