"""Cada prueba usa su propia BD SQLite vacía en una carpeta temporal."""
import pytest


@pytest.fixture(autouse=True)
def bd_limpia(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
