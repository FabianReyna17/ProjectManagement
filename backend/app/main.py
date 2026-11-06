import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .core.errors import ErrorNegocio, codigo_http
from .db.database import init_db
from .modules.acceso.router import router as acceso_router
from .modules.proyectos.router import router as proyectos_router
from .modules.tareas.router import router as tareas_router

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Gestión de Proyectos", lifespan=lifespan)


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
    return JSONResponse(status_code=codigo_http(exc), content={"detail": exc.mensaje})


@app.middleware("http")
async def sin_cache_frontend(request: Request, call_next):
    """El navegador revalida HTML/JS/CSS en cada carga (ETag): tras actualizar el código
    nunca se mezcla un index.html nuevo con un app.js viejo."""
    respuesta = await call_next(request)
    if not request.url.path.startswith("/api"):
        respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


app.include_router(acceso_router)
app.include_router(proyectos_router)
app.include_router(tareas_router)

# Frontend estático (se monta al final para no tapar /api)
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
