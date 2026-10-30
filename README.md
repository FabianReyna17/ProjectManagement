# Gestión de Proyectos — Primera iteración (Sprint 1)

MVP: un usuario entra, crea un proyecto, da acceso a otro y este solo ve lo autorizado.

- **Backend:** Python + FastAPI + SQLite
- **Frontend:** HTML, CSS y JavaScript (sin frameworks), servido por el mismo backend

## Estructura

```
Primer_Iteracion/
├── ci/ci.yml                    # Pipeline: instala dependencias y corre pytest en cada push
├── backend/
│   ├── app/
│   │   ├── main.py              # App FastAPI, manejo de errores, sirve el frontend
│   │   ├── database.py          # Esquema SQLite + datos iniciales (funciones y admin)
│   │   ├── security.py          # Hash de contraseñas (PBKDF2) y tokens
│   │   ├── deps.py              # Sesión actual y autorización (denegar por defecto)
│   │   ├── schemas.py           # Validación de entradas (Pydantic)
│   │   └── routers/
│   │       ├── auth.py          # login, logout, me
│   │       ├── usuarios.py      # funciones, registrar/listar cuentas
│   │       └── proyectos.py     # proyectos, ficha y participantes
│   ├── tests/test_sprint1.py    # Pruebas de los criterios del Sprint 1
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
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir <http://localhost:8000>. Cuenta inicial: **admin / Admin123!**

La BD se crea sola en `backend/data/gestion.db`. Para reiniciar, borrar esa carpeta.

## Pruebas

```bash
cd backend
python -m pytest -v
```

## Cobertura del Sprint 1

| HU | Implementación |
|---|---|
| TEC-01 | Estructura backend/frontend, modelo BD (usuarios, funciones, proyectos, participantes, sesiones), CI en GitHub Actions |
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

> Nota CI: mover `ci/ci.yml` a `.github/workflows/ci.yml` en la raíz del repositorio. Asume que `Primer_Iteracion` es la raíz; si no lo es, ajustar `working-directory`.
