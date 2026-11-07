# Gestión de Proyectos

MVP: un usuario entra, crea un proyecto, da acceso a otro y este solo ve lo autorizado.

- **Backend:** Python + FastAPI + SQLite (SQLAlchemy + Alembic)
- **Frontend:** HTML, CSS y JavaScript (sin frameworks), servido por el mismo backend

## Arquitectura

Ver [docs/Arquitectura_Gestion_Proyectos.md](docs/Arquitectura_Gestion_Proyectos.md) (modelo C4).

## Estructura

```
├── .github/workflows/ci.yml     # Corre las pruebas en cada push
├── backend/
│   ├── app/
│   │   ├── main.py              # App FastAPI, traduce errores a HTTP, sirve el frontend
│   │   ├── core/                # Errores, seguridad (hash y tokens), freno de intentos, esquema base, cabeceras
│   │   ├── db/                  # Conexión, transacciones, migraciones, admin inicial e idempotencia
│   │   └── modules/
│   │       ├── acceso/          # login, logout, cuentas y funciones
│   │       ├── proyectos/       # proyectos, ficha y participantes
│   │       └── tareas/          # tareas de un proyecto
│   │           # cada módulo: router → service → repository (+ schemas, deps)
│   ├── migrations/              # Cambios de esquema (Alembic)
│   ├── tests/                   # API (test_sprint1, test_sprint2) y reglas sin HTTP (test_servicios)
│   └── requirements.txt
└── frontend/                    # Sin build ni dependencias externas; scripts clásicos cargados en orden
    ├── index.html               # Marco (barra lateral / navegación inferior), sprite de iconos SVG y diálogos
    ├── img/favicon.svg
    ├── css/
    │   ├── tokens.css           # Colores, espaciado (4 px), radios, tipografía, tiempos; tema claro y oscuro
    │   ├── base.css             # Reinicio, tipografía, controles, foco visible y utilidades
    │   ├── layout.css           # Barra lateral en escritorio; barra superior y navegación inferior en teléfono
    │   ├── componentes.css      # Botones, chips de estado, prioridad, tablas, formularios, avisos, diálogos
    │   └── vistas.css           # Login, ficha de tarea con inspector, proyecto, usuarios y ajustes de teléfono
    └── js/
        ├── tema.js              # Aplica el tema elegido antes de pintar (se carga en <head>)
        ├── api.js               # Cliente HTTP: token, 401 → login recordando la ruta, errores con campos
        ├── ui.js                # escapar(), iconos, avisos apilables, guardar() (HU-08-001) y fechas es-GT
        ├── componentes.js       # Etiquetas, personas, diálogo de confirmación, tablas, formularios, tema
        ├── atajos.js            # Atajos de teclado y paleta de comandos (Ctrl/⌘ K)
        ├── tareas.js            # Vistas de tareas
        └── app.js               # Router, marco, delegación de eventos y vistas del Sprint 1
```

Cada vista devuelve `{ titulo, html, montar, ... }` y el router la pinta solo si sigue siendo la última navegación. Los botones usan `data-accion` (delegación de eventos): no hay `onclick` en las plantillas, lo que permite la cabecera CSP estricta que envía el backend.

## Ejecutar (Windows)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Abrir <http://localhost:8000>. Cuenta inicial: **admin / Admin123!**

La sesión expira tras 8 horas sin actividad (`SESION_INACTIVIDAD_MIN` para cambiarlo). Tras 5 intentos fallidos de inicio de sesión con el mismo usuario, cada intento nuevo exige esperar un tiempo creciente (2 s, 4 s, 8 s… hasta 5 min), exista o no la cuenta.

La BD se crea sola en `backend/data/gestion.db` y al arrancar se aplican las migraciones pendientes. Para reiniciar, borrar esa carpeta.

**Cambiar el esquema:** no editar tablas a mano. Crear una migración con `alembic revision -m "descripcion"`, escribir el cambio en el archivo nuevo de `migrations/versions/` y reiniciar la app. Así nadie pierde sus datos.

## Pruebas

```bash
cd backend
python -m pytest -v
```

Cada prueba usa su propia BD temporal.

## Cobertura del Sprint 1

| HU | Implementación |
|---|---|
| TEC-01 | Estructura backend/frontend, modelo BD (usuarios, funciones, proyectos, participantes, sesiones), CI en GitHub Actions |
| TEC-02 | Backend en módulos (router → service → repository); migraciones con Alembic |
| HU-01-001 | `POST /api/usuarios` (solo Admin), pantalla "Usuarios" |
| HU-01-002 | Catálogo Admin/Responsable/Integrante/Supervisor y selector en el registro |
| HU-01-003 | `POST /api/auth/login`, mensaje genérico ante error o cuenta inactiva |
| HU-01-004 | `POST /api/auth/logout` elimina la sesión en servidor; botón "Salir" |
| HU-01-005 | `POST/DELETE /api/proyectos/{id}/participantes` (solo responsable); retiro lógico, conserva historial |
| HU-01-006 | `GET /api/proyectos` filtrado por participación activa |
| HU-01-007 | Dependencias `usuario_actual` / `requiere_funcion` / `proyecto_autorizado`; 403 uniforme y pantalla "Sin acceso" |
| HU-02-001 | `POST /api/proyectos` (Admin/Responsable), valida fechas, estado inicial "planificado" |
| HU-02-002 | `GET /api/proyectos/{id}` y vista de ficha |
| HU-08-001 | `guardar()` en `ui.js`: confirma solo si el servidor responde OK; si falla muestra error y no actualiza la vista |

## Cobertura del Sprint 2

| HU | Implementación |
|---|---|
| HU-03-001 | `POST /api/proyectos/{id}/tareas` (solo responsable del proyecto), estado inicial "pendiente"; `GET /api/tareas/{id}`; formulario "Nueva tarea" y detalle |
| HU-03-002 | `PUT /api/tareas/{id}/responsable` (solo responsable del proyecto) valida cuenta activa y participante; cada cambio queda en `historial_tareas` (anterior, nuevo, actor, fecha) — `GET /api/tareas/{id}/historial`; selector en la tarea y al crearla |
| HU-03-003 | `PUT /api/tareas/{id}/planificacion` (fecha límite opcional y prioridad alta/media/baja); fecha o prioridad inválida → 400 indicando el campo; cada cambio guarda valor anterior y actor |
| HU-03-005 | `GET /api/proyectos/{id}/tareas` (participantes del proyecto); lista en la ficha con responsable, prioridad, fecha y estado; las no asignadas se marcan "Sin asignar" (icono + texto) |
| HU-03-004 | `GET /api/mis-tareas`: tareas asignadas en proyectos donde aún participo (abiertas primero, por fecha y prioridad); vista "Mis tareas" con proyecto, prioridad, fecha y estado, abre el detalle |
| HU-04-001 | Estados pendiente → en curso → terminada (volver a pendiente y reabrir permitidos); `PUT /api/tareas/{id}/estado` solo para la persona asignada o el responsable; transición inválida → 400 con el motivo; queda en el historial; botones en el detalle y en "Mis tareas" |
| HU-04-003 | Tabla `bloqueos` aparte del estado (una tarea puede estar en curso y bloqueada); `POST /api/tareas/{id}/bloqueos` exige motivo, guarda autor y fecha; índice único impide dos bloqueos abiertos (409); marca "Bloqueada" (icono SVG + texto) en detalle y listas; no se puede terminar una tarea bloqueada |
| HU-04-004 | `POST /api/tareas/{id}/bloqueos/{bid}/resolver` (solo responsable del proyecto) exige explicación y guarda quién y cuándo; la tarea sigue en su estado de trabajo; resolver uno ya cerrado → 409 sin cambiar su historia; `GET /api/tareas/{id}/bloqueos` y sección "Bloqueos resueltos" |
| HU-08-002 | Cabecera `Idempotency-Key` en las creaciones (proyectos, tareas, bloqueos): la clave se guarda en la misma transacción que el registro (`claves_idempotencia`), un reintento devuelve el existente y uno fallido se registra una sola vez; el frontend genera una clave por formulario y deshabilita el botón durante el envío |

## Mejoras transversales (después del Sprint 2)

| Tema | Implementación |
|---|---|
| Sesión | Expiración por inactividad (`sesiones.ultimo_uso`, migración 0007); mensaje "Tu sesión expiró" y regreso a la ruta original al volver a entrar; `/api/auth/me` refresca nombre y función al cargar y al volver a la pestaña |
| Login | Freno progresivo a intentos fallidos por identificador, sin revelar si la cuenta existe (`core/intentos.py`, 429); verificación de contraseña con tiempo similar exista o no la cuenta |
| Permisos en la UI | Un 403 al consultar muestra "Sin acceso" sin cambiar la URL; un 403 al actuar muestra el motivo y recarga la vista con los permisos vigentes |
| HU-08-002 | También el registro de cuentas acepta `Idempotency-Key` |
| Seguridad web | CSP estricta, `nosniff`, `Referrer-Policy` y `X-Frame-Options`; `escapar()` también escapa comillas y se aplica a fechas y atributos |
| Listas | Tareas del proyecto y "Mis tareas" con el mismo orden: abiertas, bloqueadas arriba, fecha límite, prioridad |
| Interfaz | Rediseño con tokens y tema oscuro, paleta de comandos y atajos, esqueletos de carga, estados vacíos con acción, migas, foco al título, confirmaciones propias, avisos apilables, fechas legibles, orden y búsqueda en tablas, copiar enlace |

## Pendientes técnicos

- **Alinear el código con la arquitectura (ADR-03, ADR-04, ADR-10).** Migrar de SQLite a PostgreSQL 16, agregar `docker-compose.yml` (api + postgres) y pasar el frontend a módulos ES. **Responsable sugerido:** Fabián Reyna (autor del C4); cualquier integrante puede tomarlo si él no está disponible. Implica revisar:
  - SQL específico de SQLite: `PRAGMA foreign_keys` en `db/database.py`, `.lastrowid` en los repositorios (en PostgreSQL usar `RETURNING id`), booleanos como `activo = 1` / `activo = 0`, `INSERT OR IGNORE` de la migración 0001 y `INTEGER PRIMARY KEY AUTOINCREMENT`.
  - Migraciones de Alembic 0001–0007: tipos `TEXT` para fechas, `CURRENT_TIMESTAMP` como texto, índice único parcial `ux_bloqueo_abierto` (0005, compatible con PostgreSQL) y `ALTER TABLE ... DROP COLUMN` de los `downgrade`.
  - `DATABASE_URL` (driver `psycopg` en `requirements.txt`) y el fixture `bd_limpia` de `tests/conftest.py`, que hoy crea un archivo SQLite por prueba (usar una BD o esquema por prueba).
  - CI (`.github/workflows/ci.yml`) con un servicio `postgres:16`.
  - Frontend: hoy son scripts clásicos que dependen del orden de carga en `index.html` (`api.js` → `ui.js` → `componentes.js` → `atajos.js` → `tareas.js` → `app.js`) y comparten globales; pasar a `import`/`export` con `<script type="module">`.
- Sesión en cookie HttpOnly con hash del token en BD (ADR-05); hoy el token vive en `localStorage`.
- `str_strip_whitespace` también recorta contraseñas (Arquitectura §7, prioridad B). Cambiarlo exige cuidar las contraseñas ya guardadas.
- El freno de intentos vive en memoria del proceso: con varios procesos de la API, cada uno lleva su cuenta.

## Fuera de alcance (siguientes sprints)

Tablero, vencimientos, replanificación con control de versión, historial visible de la tarea, avisos, comentarios, edición de proyectos, desactivar cuentas, respaldos.
