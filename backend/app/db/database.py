"""Conexión a la BD (SQLite), transacciones y datos iniciales.

El esquema lo crean las migraciones de Alembic (carpeta migrations/).
"""
import os
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, create_engine, event, text

from ..core.security import hash_password

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_URL = f"sqlite:///{(BACKEND_DIR / 'data' / 'gestion.db').as_posix()}"

_engine: Engine | None = None


def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_URL)


def get_engine() -> Engine:
    """Un solo engine (pool de conexiones). Se recrea si cambia la URL (pruebas)."""
    global _engine
    if _engine is None or _engine.url.render_as_string(hide_password=False) != database_url():
        if _engine is not None:
            _engine.dispose()
        _engine = crear_engine(database_url())
    return _engine


def crear_engine(url: str) -> Engine:
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _claves_foraneas(conn, _):
            conn.execute("PRAGMA foreign_keys = ON")
    return engine


def migrar() -> None:
    """Aplica las migraciones pendientes (equivale a `alembic upgrade head`)."""
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(cfg, "head")


def init_db() -> None:
    migrar()
    with get_engine().connect() as conn:
        # Administrador inicial (solo si no hay cuentas)
        if conn.execute(text("SELECT COUNT(*) FROM usuarios")).scalar() == 0:
            conn.execute(
                text("""INSERT INTO usuarios (usuario, nombre, password_hash, funcion_id)
                        SELECT 'admin', 'Administrador', :h, id FROM funciones WHERE nombre = 'Admin'"""),
                {"h": hash_password("Admin123!")},
            )
        conn.commit()


def get_db():
    """Una conexión por petición."""
    with get_engine().connect() as conn:
        yield conn


@contextmanager
def transaccion(conn: Connection):
    """Confirma todo lo hecho dentro del bloque o nada.

    Solo los servicios abren transacciones; los repositorios nunca hacen commit.
    """
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# --- Ayudas para los repositorios ---

def uno(db: Connection, sql: str, **params) -> dict | None:
    """Primera fila como dict, o None."""
    row = db.execute(text(sql), params).mappings().first()
    return dict(row) if row else None


def varios(db: Connection, sql: str, **params) -> list[dict]:
    """Todas las filas como lista de dicts."""
    return [dict(r) for r in db.execute(text(sql), params).mappings()]
