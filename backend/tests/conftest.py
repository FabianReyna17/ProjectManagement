"""Cada prueba usa su propia BD SQLite vacía en una carpeta temporal."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def bd_limpia(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")


@pytest.fixture()
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
