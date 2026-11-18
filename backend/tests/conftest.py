"""Cada prueba usa su propia BD SQLite vacía y sus carpetas de archivos y respaldos en una carpeta temporal."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def bd_limpia(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("ARCHIVOS_DIR", str(tmp_path / "archivos"))
    monkeypatch.setenv("AVISOS_CADA_MIN", "0")  # el proceso programado se llama a mano en las pruebas
    monkeypatch.setenv("RESPALDO_CADA_HORAS", "0")  # el respaldo también
    monkeypatch.setenv("RESPALDOS_DIR", str(tmp_path / "respaldos"))


@pytest.fixture(autouse=True)
def intentos_limpios():
    """El freno de inicio de sesión vive en memoria: cada prueba empieza sin fallos."""
    from app.modules.acceso.service import INTENTOS
    INTENTOS.limpiar()
    yield
    INTENTOS.limpiar()


@pytest.fixture()
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
