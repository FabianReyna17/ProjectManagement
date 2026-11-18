"""Endpoints de comentarios y archivos de proyectos y tareas. Solo validan la entrada y llaman al servicio."""
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from ...core.cabeceras import clave_idempotencia
from ...db.database import get_db
from ..acceso.deps import usuario_actual
from ..proyectos.deps import proyecto_autorizado
from ...core.errors import DatosInvalidos
from ..tareas.deps import tarea_autorizada
from . import service
from .schemas import ComentarioIn

router = APIRouter(prefix="/api", tags=["colaboración"])


@router.post("/proyectos/{proyecto_id}/comentarios", status_code=201)
def comentar_proyecto(data: ComentarioIn, proyecto: dict = Depends(proyecto_autorizado),
                      u: dict = Depends(usuario_actual), clave=Depends(clave_idempotencia), db=Depends(get_db)):
    return service.comentar(db, proyecto["id"], None, u["id"], data.texto, clave)


@router.get("/proyectos/{proyecto_id}/comentarios")
def comentarios_proyecto(proyecto: dict = Depends(proyecto_autorizado), db=Depends(get_db)):
    return service.comentarios(db, proyecto["id"])


@router.post("/tareas/{tarea_id}/comentarios", status_code=201)
def comentar_tarea(data: ComentarioIn, tarea: dict = Depends(tarea_autorizada),
                   u: dict = Depends(usuario_actual), clave=Depends(clave_idempotencia), db=Depends(get_db)):
    return service.comentar(db, tarea["proyecto_id"], tarea["id"], u["id"], data.texto, clave)


@router.get("/tareas/{tarea_id}/comentarios")
def comentarios_tarea(tarea: dict = Depends(tarea_autorizada), db=Depends(get_db)):
    return service.comentarios(db, tarea["proyecto_id"], tarea["id"])


# --- Archivos (HU-05-002) ---
# El archivo se envía como cuerpo crudo (no multipart) con su nombre en ?nombre=.

async def cuerpo_archivo(request: Request) -> bytes:
    """Lee el cuerpo y corta en cuanto supera el máximo, sin cargar archivos enormes en memoria."""
    largo = request.headers.get("content-length")
    if largo and largo.isdigit() and int(largo) > service.MAX_BYTES:
        raise DatosInvalidos(service.MSG_TAMANO)
    datos = bytearray()
    async for trozo in request.stream():
        datos += trozo
        if len(datos) > service.MAX_BYTES:
            raise DatosInvalidos(service.MSG_TAMANO)
    return bytes(datos)


NombreArchivo = Query(min_length=1, max_length=255)


@router.get("/archivos/reglas")
def reglas_archivos(u: dict = Depends(usuario_actual)):
    return service.reglas()


@router.post("/proyectos/{proyecto_id}/archivos", status_code=201)
def adjuntar_a_proyecto(nombre: str = NombreArchivo, proyecto: dict = Depends(proyecto_autorizado),
                        u: dict = Depends(usuario_actual), contenido: bytes = Depends(cuerpo_archivo),
                        clave=Depends(clave_idempotencia), db=Depends(get_db)):
    return service.adjuntar(db, proyecto["id"], None, u["id"], nombre, contenido, clave)


@router.get("/proyectos/{proyecto_id}/archivos")
def archivos_proyecto(proyecto: dict = Depends(proyecto_autorizado), db=Depends(get_db)):
    return service.archivos(db, proyecto["id"])


@router.post("/tareas/{tarea_id}/archivos", status_code=201)
def adjuntar_a_tarea(nombre: str = NombreArchivo, tarea: dict = Depends(tarea_autorizada),
                     u: dict = Depends(usuario_actual), contenido: bytes = Depends(cuerpo_archivo),
                     clave=Depends(clave_idempotencia), db=Depends(get_db)):
    return service.adjuntar(db, tarea["proyecto_id"], tarea["id"], u["id"], nombre, contenido, clave)


@router.get("/tareas/{tarea_id}/archivos")
def archivos_tarea(tarea: dict = Depends(tarea_autorizada), db=Depends(get_db)):
    return service.archivos(db, tarea["proyecto_id"], tarea["id"])


@router.get("/archivos/{archivo_id}/descarga")
def descargar_archivo(archivo_id: int, u: dict = Depends(usuario_actual), db=Depends(get_db)):
    archivo, contenido = service.descargar(db, archivo_id, u["id"])
    return Response(contenido, media_type=archivo["tipo"], headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(archivo['nombre'])}",
        "Cache-Control": "private, no-store",
    })


# --- Comentarios y archivos juntos (HU-05-003) ---

@router.get("/proyectos/{proyecto_id}/actividad")
def actividad_proyecto(proyecto: dict = Depends(proyecto_autorizado), db=Depends(get_db)):
    return service.actividad(db, proyecto["id"])


@router.get("/tareas/{tarea_id}/actividad")
def actividad_tarea(tarea: dict = Depends(tarea_autorizada), db=Depends(get_db)):
    return service.actividad(db, tarea["proyecto_id"], tarea["id"])
