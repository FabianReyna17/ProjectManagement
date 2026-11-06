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
│   │   ├── core/                # Errores, seguridad (hash y tokens), esquema base
│   │   ├── db/database.py       # Conexión, transacciones, migraciones y admin inicial
│   │   └── modules/
│   │       ├── acceso/          # login, logout, cuentas y funciones
│   │       └── proyectos/       # proyectos, ficha y participantes
│   │           # cada módulo: router → service → repository (+ schemas, deps)
│   ├── migrations/              # Cambios de esquema (Alembic)
│   ├── tests/                   # API (test_sprint1) y reglas sin HTTP (test_servicios)
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── css/styles.css
    └── js/
        ├── api.js               # Cliente HTTP (token, 401 → login, 403 → sin acceso)
        ├── ui.js                # Aviso de guardado/error común (HU-08-001)
        └── app.js               # Router y vistas
```

## Ejecutar (Windows)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Abrir <http://localhost:8000>. Cuenta inicial: **admin / Admin123!**

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

## Fuera de alcance (siguientes sprints)

Tareas, estados, bloqueos, tablero, avisos, comentarios, edición de proyectos, desactivar cuentas, respaldos.
