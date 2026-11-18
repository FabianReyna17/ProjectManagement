import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from fastapi.staticfiles import StaticFiles

from . import __version__, programado
from .core.errors import ErrorNegocio, codigo_http
from .db.database import get_engine, init_db
from .modules.acceso.router import router as acceso_router
from .modules.avisos.router import router as avisos_router
from .modules.colaboracion.router import router as colaboracion_router
from .modules.proyectos.router import router as proyectos_router
from .modules.respaldos import service as respaldos
from .modules.respaldos.router import router as respaldos_router
from .modules.tareas.router import router as tareas_router

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    minutos = programado.intervalo_minutos()
    ciclos = []
    if minutos > 0:
        ciclos.append(asyncio.create_task(programado.ciclo(minutos)))  # HU-06-002
    if respaldos.frecuencia_horas() > 0:
        ciclos.append(asyncio.create_task(programado.ciclo_respaldos(respaldos.frecuencia_horas())))  # HU-08-004
    yield
    for ciclo in ciclos:
        ciclo.cancel()


app = FastAPI(title="Gestión de Proyectos", version=__version__, lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def error_validacion(request: Request, exc: RequestValidationError):
    campos = sorted({str(e["loc"][-1]) for e in exc.errors()})
    return JSONResponse(
        status_code=400,
        content={"detail": f"Datos inválidos o incompletos: {', '.join(campos)}"},
    )


@app.exception_handler(ErrorNegocio)
async def error_negocio(request: Request, exc: ErrorNegocio):
    """Traduce los errores de los servicios a HTTP con el mismo formato de siempre."""
    return JSONResponse(status_code=codigo_http(exc), content={"detail": exc.mensaje, **exc.datos})


# La interfaz no usa scripts ni estilos en línea, por eso la política puede ser estricta.
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
DOCS = ("/docs", "/redoc", "/openapi.json")  # Swagger carga recursos externos


@app.middleware("http")
async def cabeceras_http(request: Request, call_next):
    """El navegador revalida HTML/JS/CSS en cada carga (ETag): tras actualizar el código
    nunca se mezcla un index.html nuevo con un app.js viejo. Además, cabeceras de seguridad."""
    respuesta = await call_next(request)
    ruta = request.url.path
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["Referrer-Policy"] = "same-origin"
    if not ruta.startswith("/api"):
        respuesta.headers["Cache-Control"] = "no-cache"
        if not ruta.startswith(DOCS):
            respuesta.headers["Content-Security-Policy"] = CSP
            respuesta.headers["X-Frame-Options"] = "DENY"
    return respuesta


@app.get("/api/salud", tags=["operación"])
def salud():
    """Para el monitoreo del despliegue: el proceso responde y la BD está disponible.
    No requiere sesión y no expone datos (el estado de los respaldos lo ve el Admin en Respaldos)."""
    try:
        with get_engine().connect() as db:
            esquema = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"estado": "sin base de datos", "version": __version__})
    return {"estado": "ok", "version": __version__, "esquema": esquema}


app.include_router(acceso_router)
app.include_router(proyectos_router)
app.include_router(tareas_router)
app.include_router(avisos_router)
app.include_router(colaboracion_router)
app.include_router(respaldos_router)

# Frontend estático (se monta al final para no tapar /api)
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
