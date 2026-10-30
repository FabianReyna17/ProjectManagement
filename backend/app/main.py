import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import auth, proyectos, usuarios

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Gestión de Proyectos - Sprint 1", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def error_validacion(request: Request, exc: RequestValidationError):
    campos = sorted({str(e["loc"][-1]) for e in exc.errors()})
    return JSONResponse(
        status_code=400,
        content={"detail": f"Datos inválidos o incompletos: {', '.join(campos)}"},
    )


app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(proyectos.router)

# Frontend estático (se monta al final para no tapar /api)
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
