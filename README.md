# Gestión de Proyectos

Sistema web para planificar proyectos, asignar tareas y dar seguimiento a su avance. Se instala para un solo cliente (single-tenant).

- **Backend:** Python · FastAPI · SQLAlchemy Core · Alembic · SQLite
- **Frontend:** HTML, CSS y JavaScript sin frameworks ni paso de build, servido por el mismo backend
- **Arquitectura:** [docs/Arquitectura_Gestion_Proyectos.md](docs/Arquitectura_Gestion_Proyectos.md) (monolito modular)

## Ejecutar (Windows)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Abrir <http://localhost:8000>. Cuenta inicial: **admin / Admin123!**

- La BD se crea en `backend/data/gestion.db` y las migraciones pendientes se aplican al arrancar. Para reiniciar, borrar esa carpeta.
- El esquema se cambia siempre con una migración nueva (`alembic revision -m "descripcion"`), nunca editando tablas a mano.
- Las tareas vencidas se calculan con el día de Guatemala (`ZONA_HORARIA`) y se avisa desde 3 días antes (`DIAS_POR_VENCER`).
- El aviso de vencimiento cercano lo genera un proceso programado que el servidor corre al arrancar y cada hora (`AVISOS_CADA_MIN`, 0 lo desactiva). También se puede correr aparte, por ejemplo desde el Programador de tareas: `python -m app.programado`. Correrlo de más no repite avisos.
- Los archivos adjuntos se guardan en `backend/data/archivos` (`ARCHIVOS_DIR`), con un máximo de 10 MB por archivo (`ARCHIVO_MAX_MB`). Un respaldo debe incluir la BD y esa carpeta.
- La sesión expira tras 8 horas sin actividad (`SESION_INACTIVIDAD_MIN`). Tras 5 intentos fallidos de inicio de sesión con el mismo usuario, cada intento espera 2 s, 4 s, 8 s… hasta 5 min.

## Pruebas

```bash
cd backend
python -m pytest -v
```

Cada prueba usa su propia BD temporal. GitHub Actions las corre en cada push.

## Estructura

```
backend/
├── app/
│   ├── main.py        # crea la app, traduce errores a HTTP y sirve el frontend
│   ├── core/          # errores, seguridad, freno de intentos, cabeceras
│   ├── db/            # conexión, transacciones, migraciones e idempotencia
│   └── modules/       # acceso, proyectos, tareas, avisos y colaboración: router → service → repository
├── migrations/        # Alembic
└── tests/
frontend/
├── index.html
├── css/               # tokens, base, layout, componentes y vistas
└── js/                # tema, api, ui, componentes, atajos, colaboración, tareas, avisos y app (scripts clásicos, en ese orden)
```

En las plantillas no hay `onclick`: los botones usan `data-accion` (delegación de eventos), lo que permite la CSP estricta del backend.

## Historias implementadas

| Sprint | HU | Implementación |
|---|---|---|
| 1 | TEC-01 | Estructura, modelo de datos y CI en GitHub Actions |
| 1 | TEC-02 | Backend por módulos (router → service → repository) y migraciones con Alembic |
| 1 | HU-01-001 | Registrar cuenta (solo Admin) — `POST /api/usuarios` |
| 1 | HU-01-002 | Funciones Admin, Responsable, Integrante y Supervisor |
| 1 | HU-01-003 | Iniciar sesión con mensaje genérico ante error o cuenta inactiva — `POST /api/auth/login` |
| 1 | HU-01-004 | Cerrar sesión elimina la sesión en el servidor — `POST /api/auth/logout` |
| 1 | HU-01-005 | Dar y retirar acceso (solo el responsable; retiro lógico) — `POST/DELETE /api/proyectos/{id}/participantes` |
| 1 | HU-01-006 | Mis proyectos, solo con participación activa — `GET /api/proyectos` |
| 1 | HU-01-007 | 403 uniforme que no revela si el recurso existe y pantalla "Sin acceso" |
| 1 | HU-02-001 | Crear proyecto (Admin o Responsable) con validación de fechas — `POST /api/proyectos` |
| 1 | HU-02-002 | Ficha del proyecto — `GET /api/proyectos/{id}` |
| 1 | HU-08-001 | La interfaz confirma "guardado" solo cuando el servidor responde OK |
| 2 | HU-03-001 | Crear tarea (solo el responsable del proyecto) — `POST /api/proyectos/{id}/tareas` |
| 2 | HU-03-002 | Asignar responsable (cuenta activa y participante), con historial — `PUT /api/tareas/{id}/responsable` |
| 2 | HU-03-003 | Fecha límite y prioridad, con historial — `PUT /api/tareas/{id}/planificacion` |
| 2 | HU-03-004 | Mis tareas en todos mis proyectos — `GET /api/mis-tareas` |
| 2 | HU-03-005 | Tareas del proyecto, marcando las sin asignar — `GET /api/proyectos/{id}/tareas` |
| 2 | HU-04-001 | Estados pendiente → en curso → terminada, por la persona asignada o el responsable — `PUT /api/tareas/{id}/estado` |
| 2 | HU-04-003 | Registrar bloqueo con motivo; una tarea bloqueada no se puede terminar — `POST /api/tareas/{id}/bloqueos` |
| 2 | HU-04-004 | Resolver bloqueo (solo el responsable) con explicación — `POST /api/tareas/{id}/bloqueos/{bid}/resolver` |
| 2 | HU-08-002 | `Idempotency-Key` en las creaciones: un reintento no duplica el registro |
| 3 | HU-07-001 | Tablero con una columna por estado (mismas tareas y orden que la lista), cambio de estado desde la tarjeta; selector Lista/Tablero que se recuerda — `GET /api/proyectos/{id}/tablero` |
| 3 | HU-04-005 | Marca "Vencida" o "Vence hoy / mañana / en N días" (hasta 3 días antes) en lista, tablero, "Mis tareas" y detalle; se calcula con el día de Guatemala y no aplica a tareas terminadas |
| 3 | HU-03-006 | Replanificar responsable, prioridad y fecha en una sola confirmación; cada valor que cambia queda en el historial y si algo es inválido no se guarda nada — `PUT /api/tareas/{id}/plan` |
| 3 | HU-02-003 | Editar nombre, objetivo, responsable y fechas del proyecto (solo su responsable); cada cambio guarda valor anterior, actor y fecha y se ve en "Cambios del plan"; el nuevo responsable obtiene acceso — `PUT /api/proyectos/{id}`, `GET /api/proyectos/{id}/historial` |
| 3 | HU-04-002 | Avances de la tarea con texto, autor y fecha (la persona asignada o el responsable), en orden y separados de los cambios de estado; reasignar no los borra — `POST/GET /api/tareas/{id}/avances` |
| 3 | HU-07-002 | Filtros por estado, responsable (o sin asignar), prioridad y vencimiento en la lista y el tablero; se combinan, se indican los activos y se quitan con un botón; los aplica el servidor dentro del proyecto autorizado — `?estado=&responsable=&prioridad=&vencimiento=` |
| 3 | HU-08-003 | El plan de la tarea, su estado y los datos del proyecto se guardan campo por campo solo si nadie cambió ese dato desde que se leyó (UPDATE condicional). Si hubo cambio: 409 con el valor vigente, se avisa, lo escrito se conserva y se puede volver a confirmar; cambios en datos distintos no chocan |
| 3 | HU-04-006 | Sección "Historial" en el detalle: responsable, fecha, prioridad, estado, avances, bloqueos y resoluciones en orden, con actor y fecha; sin acceso al proyecto no se puede consultar — `GET /api/tareas/{id}/historial` |
| 4 | HU-06-001 | Al asignar una tarea (al crearla, asignarla o replanificarla) la nueva persona responsable recibe un aviso con tarea, proyecto, quién la asignó y fecha, en la misma transacción que la asignación: si esta falla no queda aviso y un reintento no lo duplica (un aviso por evento del historial). Quien se asigna a sí mismo no recibe aviso. Vista "Avisos" (`g a`) — `GET /api/avisos` |
| 4 | HU-06-003 | Al registrar un bloqueo, el responsable del proyecto recibe un aviso con la tarea y el motivo, en la misma transacción; un reintento no lo repite y quien reporta su propio bloqueo no se avisa a sí mismo. Al resolverse, el aviso se conserva marcado "Resuelto" |
| 4 | HU-06-005 | Bandeja "Avisos" en orden, con los no leídos resaltados y un contador en la navegación; abrir un aviso lo marca como leído y lleva a su tarea; "Marcar todos como leídos". Si se retiró el acceso al proyecto, el aviso se conserva sin datos de la tarea ni del proyecto y abrirlo muestra "Sin acceso" — `GET /api/avisos`, `GET /api/avisos/resumen`, `POST /api/avisos/{id}/abrir`, `POST /api/avisos/leer-todos` |
| 4 | HU-05-001 | Comentarios en el proyecto y en cada tarea, con autor y fecha, en orden de publicación; cualquier participante comenta, un comentario vacío se rechaza y reasignar la tarea no cambia su autoría. Sin acceso vigente no se leen ni se publican, ni con enlace directo — `POST/GET /api/proyectos/{id}/comentarios`, `POST/GET /api/tareas/{id}/comentarios` |
| 4 | HU-05-002 | Adjuntar archivos al proyecto o a una tarea (cualquier participante), con nombre, tamaño, autor y fecha. Máximo 10 MB y solo tipos permitidos por extensión (PDF, imágenes, texto, Office/OpenDocument, ZIP); lo demás se rechaza con un mensaje claro y no queda adjunto. Un reintento con la misma `Idempotency-Key` no duplica y una carga que no se confirma no deja archivo en disco. La descarga comprueba el acceso vigente: una URL guardada no sirve a quien perdió el acceso — `POST/GET /api/proyectos/{id}/archivos`, `POST/GET /api/tareas/{id}/archivos` (cuerpo crudo, `?nombre=`), `GET /api/archivos/{id}/descarga`, `GET /api/archivos/reglas` |
| 4 | HU-05-003 | Sección "Comentarios y archivos" en el proyecto y en la tarea: ambos en una sola lista en orden de publicación, con autor y fecha, filtro Todo / Comentarios / Archivos y los formularios para comentar y adjuntar. Solo muestra lo de ese destino (ni sus tareas ni otros proyectos); reasignar la tarea conserva conversación y archivos — `GET /api/proyectos/{id}/actividad`, `GET /api/tareas/{id}/actividad` |
| 4 | HU-02-004 | El responsable inicia la ejecución del proyecto (Planificado → En curso) con confirmación; la ficha muestra desde cuándo y quién lo cambió, y el cambio queda en "Cambios del plan". Una transición no permitida o un estado inexistente se rechaza sin tocar el estado; el cierre queda para su propio procedimiento (HU-02-005). Si otra persona cambió el estado mientras tanto → 409 — `PUT /api/proyectos/{id}/estado` |
| 4 | HU-07-003 | Resumen en la ficha del proyecto: pendientes, en curso, terminadas, vencidas, por vencer y bloqueadas, más las próximas fechas límite. Se calcula sobre la misma lista que el tablero (solo datos confirmados) y cada cifra abre la lista con su filtro; nuevo filtro "Bloqueo" — `GET /api/proyectos/{id}/resumen`, `?bloqueo=bloqueada|sin_bloqueo` |
| 5 | HU-07-005 | Vista "Estado general" (`g e`, solo Admin, Responsable y Supervisor): cada proyecto en el que la persona participa, con responsable, estado, fecha prevista de término, tareas vencidas y bloqueadas y abiertas. Los que tienen al menos una tarea vencida o bloqueada se marcan "Requiere atención" (propuesta de RP-07-03) y van primero. Las cifras son las del resumen de cada proyecto y cada una abre su lista filtrada; los cerrados se incluyen o excluyen con una casilla y los proyectos sin acceso ni aparecen ni se cuentan — `GET /api/estado-proyectos?incluir_cerrados=` |
| 5 | HU-06-002 | Aviso de vencimiento cercano: cada tarea abierta con responsable que vence hoy o en los próximos 3 días (día de Guatemala) avisa a esa persona con la fecha límite vigente. Un mismo vencimiento (tarea + fecha) se avisa una sola vez aunque el proceso corra muchas veces; si la tarea se reprograma o se reasigna, el vencimiento nuevo sí se avisa. Las terminadas, las de proyectos cerrados y las de personas sin acceso no generan avisos |
| 5 | HU-02-005 | Cerrar proyecto (solo su responsable) en "Cerrar proyecto": antes de confirmar se muestran las tareas que siguen abiertas; para cerrar con alguna abierta hay que terminarla o justificar la excepción (las tareas quedan tal como están). El cierre guarda fecha, quién, cuántas tareas seguían abiertas y la justificación, y el cambio de estado queda en "Cambios del plan". Repetir el cierre no duplica nada; si las tareas abiertas cambiaron mientras se revisaba → 409. Un proyecto cerrado solo se consulta: no admite tareas, cambios de plan o estado, avances, bloqueos, comentarios ni archivos (sí gestionar quién tiene acceso), y sus tareas salen de "Mis tareas" y de la atención del estado general — `GET/POST /api/proyectos/{id}/cierre` |
| 5 | HU-07-004 | Vista "Carga por responsable" (`g c`, Admin, Responsable y Supervisor; también desde el estado general y el resumen del proyecto): por persona, sus tareas abiertas, vencidas y bloqueadas en los proyectos activos a los que quien consulta tiene acceso, de la más cargada a la menos, con una barra para comparar; al abrir a una persona se ven sus tareas y su proyecto. Las tareas sin responsable van aparte. Se puede limitar a un proyecto autorizado (otro → 403). Se calcula sobre la misma lista que el proyecto, así que las cifras coinciden con sus filtros — `GET /api/carga?proyecto_id=` |

Cada cambio de responsable, fecha, prioridad, estado o bloqueo queda en el historial de la tarea (`GET /api/tareas/{id}/historial`).

## Mejoras posteriores al Sprint 2

- **Sesión:** expira por inactividad; al volver a entrar regresa a la ruta original; `/api/auth/me` refresca nombre y función.
- **Login:** freno progresivo a intentos fallidos sin revelar si la cuenta existe.
- **Permisos en la interfaz:** un 403 al consultar muestra "Sin acceso"; al actuar muestra el motivo sin salir de la vista.
- **Seguridad web:** CSP estricta y cabeceras `nosniff`, `Referrer-Policy` y `X-Frame-Options`.
- **Listas de tareas:** mismo orden en el proyecto y en "Mis tareas": abiertas, bloqueadas arriba, fecha límite y prioridad.
- **Interfaz:** rediseño con tema oscuro, paleta de comandos (Ctrl/⌘ K) y atajos de teclado.

## Pendientes técnicos

Según la propuesta de [arquitectura](docs/Arquitectura_Gestion_Proyectos.md), antes de usar datos reales:

- Aprovisionar el primer administrador de forma segura; hoy se crea `admin / Admin123!` al arrancar.
- Sesión en cookie HttpOnly/Secure/SameSite con protección CSRF y hash del token en BD; hoy el token vive en `localStorage`.
- Política de hash de contraseñas que guarde algoritmo y costo, con rehash al iniciar sesión.
- Respaldo y restauración probados.
- `str_strip_whitespace` también recorta contraseñas; corregirlo sin romper las ya guardadas.

Al llegar la historia que lo necesite:

- Frontend dividido en módulos ES (`core/`, `components/`, `features/`); hoy son scripts clásicos que comparten globales.
- Paginación en los listados.
- PostgreSQL solo si el piloto confirma escritura concurrente o varios procesos; mientras tanto se sigue con SQLite. En ese caso, el freno de intentos (en memoria) debe pasar a un almacén compartido.

## Siguientes sprints

Avisos de cambios del plan, proyectos cerrados e historial, corregir comentarios, desactivar cuentas y respaldos.
