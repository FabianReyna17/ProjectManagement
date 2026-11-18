# Cambios

## 1.0.0 — 2026-11-17

Primera versión para el cliente: los seis sprints del planning.

- **Acceso (EP-01):** cuentas y funciones (Admin, Responsable, Integrante, Supervisor), inicio y cierre de sesión con expiración por inactividad y freno de intentos, acceso por proyecto, pantalla "Sin acceso". Administración de cuentas: desactivar, cambiar función, restablecer acceso con contraseña temporal, cambio de contraseña e historial de cambios de acceso.
- **Proyectos (EP-02):** crear, editar con historial, iniciar ejecución, cerrar revisando tareas abiertas y consultar proyectos cerrados.
- **Tareas (EP-03, EP-04):** crear, asignar, planificar y replanificar; estados, avances, bloqueos y su resolución, vencimientos con el día de Guatemala e historial de cada tarea.
- **Colaboración (EP-05):** comentarios y archivos adjuntos en proyectos y tareas, con edición y retiro del contenido propio.
- **Avisos (EP-06):** asignación, bloqueo, vencimiento cercano y cambios relevantes del plan, con bandeja y contador.
- **Supervisión (EP-07):** tablero, filtros, resumen del proyecto, estado general y carga por responsable.
- **Confiabilidad (EP-08):** confirmación de guardado, operaciones que no se duplican al reintentar, sin sobrescritura silenciosa entre personas, respaldo periódico verificado y restauración ensayada.
- **Release:** el admin inicial debe cambiar su contraseña; las contraseñas ya no se recortan; regresión de permisos sobre todas las rutas y pruebas E2E en navegador; `/api/salud`; versiones exactas en `requirements-lock.txt`; guía de [despliegue](docs/Despliegue.md).

Esquema de base de datos: migración `0021`. Al actualizar desde una base anterior, las migraciones se aplican al arrancar; el historial de accesos se carga con lo conocido hasta entonces (actor "No registrado").
