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
│   └── modules/       # acceso, proyectos y tareas: router → service → repository
├── migrations/        # Alembic
└── tests/
frontend/
├── index.html
├── css/               # tokens, base, layout, componentes y vistas
└── js/                # tema, api, ui, componentes, atajos, tareas y app (scripts clásicos, en ese orden)
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

Vencimientos, filtros, replanificación, control de versión, historial visible de la tarea, avisos, comentarios, edición de proyectos, desactivar cuentas y respaldos.
