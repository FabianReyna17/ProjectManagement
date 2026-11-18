"""Pruebas E2E (TEC-02): la aplicación real en un servidor local y un navegador Chromium.

Se saltan si Playwright o su navegador no están instalados, así `python -m pytest` sigue
funcionando sin ellos. Para correrlas:

    pip install -r requirements-e2e.txt
    python -m playwright install chromium
    python -m pytest tests/e2e -v

E2E_CHROME permite usar un Chrome ya instalado (ruta al ejecutable) y E2E_VISIBLE=1 abre la ventana.
"""
import os
import socket
import threading
import time

import pytest

sync_api = pytest.importorskip("playwright.sync_api")


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def servidor(monkeypatch):
    """Servidor uvicorn en un hilo, con la BD y las carpetas temporales de la prueba (conftest raíz).
    El admin inicial debe cambiar su contraseña, como en una instalación nueva."""
    import uvicorn
    monkeypatch.setenv("ADMIN_CAMBIO_OBLIGATORIO", "1")
    from app.main import app
    puerto = _puerto_libre()
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=puerto, log_level="warning"))
    hilo = threading.Thread(target=srv.run, daemon=True)
    hilo.start()
    limite = time.time() + 20
    while not srv.started:
        if time.time() > limite:
            pytest.fail("El servidor no arrancó")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{puerto}"
    srv.should_exit = True
    hilo.join(timeout=10)


@pytest.fixture(scope="session")
def navegador():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=os.getenv("E2E_CHROME") or None,
                                  headless=os.getenv("E2E_VISIBLE") != "1")
        except Exception as e:  # noqa: BLE001 — sin navegador instalado
            pytest.skip(f"No hay navegador para las pruebas E2E: {str(e).splitlines()[0]}")
        yield b
        b.close()


class Persona:
    """Una pestaña con su propia sesión (contexto aislado), con las acciones comunes."""

    def __init__(self, navegador, base, telefono=False):
        tam = {"width": 390, "height": 844} if telefono else {"width": 1280, "height": 860}
        self.ctx = navegador.new_context(viewport=tam, locale="es-GT", timezone_id="America/Guatemala")
        self.pagina = self.ctx.new_page()
        self.base = base
        self.errores = []
        self.pagina.on("pageerror", lambda e: self.errores.append(str(e)))
        self.pagina.set_default_timeout(8000)

    def ir(self, ruta):
        self.pagina.goto(f"{self.base}/{ruta}")

    def entrar(self, usuario, password):
        p = self.pagina
        self.ir("#/login")
        p.fill("#f-login [name=usuario]", usuario)
        p.fill("#f-login [name=password]", password)
        p.click("#f-login button.boton")

    def salir(self):
        p = self.pagina
        p.locator("details.menu-cuenta:visible summary").click()
        p.get_by_role("button", name="Cerrar sesión").click()
        p.wait_for_url("**/#/login")

    def confirmar(self):
        self.pagina.locator("#dlg-confirmar [data-aceptar]").click()

    def aviso_ok(self, texto):
        self.pagina.locator("#avisos").get_by_text(texto).first.wait_for()

    def cerrar(self):
        assert not self.errores, self.errores
        self.ctx.close()


@pytest.fixture()
def persona(navegador, servidor):
    creadas = []

    def nueva(telefono=False):
        p = Persona(navegador, servidor, telefono)
        creadas.append(p)
        return p
    yield nueva
    for p in creadas:
        p.cerrar()
