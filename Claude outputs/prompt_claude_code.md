# Prompt para Claude Code — Auditoría, corrección y modernización (Gestión de Proyectos)

> Copia todo lo que está debajo de la línea y pégalo en Claude Code abierto en la raíz del repositorio.

---

Eres un ingeniero senior full-stack y diseñador de producto trabajando en este repositorio: un sistema de **gestión de proyectos** hecho por un equipo universitario (3 devs, Scrum, 6 sprints). Ya se terminaron el **Sprint 1** y el **Sprint 2**. Tu trabajo: (1) verificar que no haya errores, (2) corregir lo que encuentres, (3) añadir *quality-of-life features* que faltan y (4) modernizar la interfaz con un diseño propio, que no parezca generado por IA. **No hagas commit, push, ni crees ramas**: yo reviso y commiteo.

## 0. Antes de tocar nada, lee el contexto (obligatorio)

Lee completos, en este orden:

1. `README.md` (stack, estructura, cobertura por HU de los Sprints 1 y 2, lo que queda fuera de alcance).
2. `Planning_Sprints_ProjectManagement.md` (backlog priorizado, sprint backlog, Definición de Terminado).
3. `UserStoryMapping_Gestion_Proyectos.md` (criterios de aceptación de cada HU) y `Epicas_Gestion_Proyectos.md`.
4. `docs/Arquitectura_Gestion_Proyectos.md` (C4 y ADRs).
5. Todo `backend/app/`, `backend/migrations/`, `backend/tests/` y todo `frontend/`.

Luego escribe un resumen de 10–15 líneas con lo que entendiste (módulos, reglas de permisos, convenciones) **antes** de editar.

## 1. Reglas del proyecto (no negociables)

- **Stack fijo:** FastAPI + SQLAlchemy Core (SQL con `text()`) + Alembic + SQLite; frontend en **HTML/CSS/JS vanilla, sin frameworks, sin bundler, sin paso de build y sin dependencias de CDN** (lo sirve el mismo backend con `StaticFiles`). No agregues React, Tailwind, Bootstrap, jQuery, ni librerías de íconos externas. Si de verdad necesitas una dependencia Python nueva, justifícala y agrégala a `requirements.txt`.
- **Capas del backend:** `router → service → repository` por módulo (`acceso`, `proyectos`, `tareas`). Routers solo validan y llaman al servicio; servicios no importan FastAPI, lanzan errores de `core/errors.py` y abren la transacción con `transaccion(db)`; repositorios solo SQL y **nunca** hacen commit. Un módulo usa el *servicio* de otro, nunca su repositorio.
- **Esquema de BD:** cualquier cambio va en una **migración nueva** en `backend/migrations/versions/` (`0007_...`). Nunca edites migraciones existentes.
- **Permisos en el servidor:** denegar por defecto; un 403 uniforme que no revele si el recurso existe. La UI puede ocultar botones, pero la regla vive en el backend.
- **HU-08-001:** la UI solo muestra "guardado" cuando el servidor confirma. **Prohibido el *optimistic UI*** que muestre un cambio antes de la respuesta OK.
- **HU-08-002:** las creaciones usan `Idempotency-Key` (una clave por formulario/acción intencional) y deshabilitan el botón mientras se envía. Mantenlo en todo lo nuevo que cree registros.
- **Accesibilidad de estados:** bloqueos, prioridades y avisos se comunican con **icono + texto**, nunca solo con color.
- **Responsive:** todo debe funcionar en computadora y teléfono (DoD punto 4).
- **Idioma y estilo de código:** identificadores, mensajes y comentarios en **español**, igual que el código actual. Comentarios cortos que citen la HU cuando aplique (`// HU-04-003 ...`). Mismo tono sobrio del código existente: nada de comentarios decorativos ni sobreexplicados.
- **Fin de línea:** el repositorio se usa en Windows y `git status` ya muestra ~50 archivos "modificados" solo por CRLF/LF. **No cambies los finales de línea** de archivos que no editas; en los que editas conserva el que ya tienen. Al final, sugiere (sin aplicarlo) un `.gitattributes` para resolver esto.
- **No te adelantes al backlog sin avisar:** las HU de los Sprints 3–6 (tablero, vencidas, replanificación, filtros, historial visible, avisos, comentarios, etc.) son trabajo planificado del equipo. Ver la sección 4.

## 2. Fase 1 — Auditoría y verificación

1. Crea el entorno y corre las pruebas: `cd backend && python -m venv .venv && (activar) && pip install -r requirements.txt && python -m pytest -v`. Reporta el resultado exacto.
2. Levanta la app (`python -m uvicorn app.main:app --reload`), entra con `admin / Admin123!` y recorre de punta a punta: crear cuentas (Responsable e Integrante) → crear proyecto → dar acceso → crear y asignar tarea → cambiar estado → bloquear → resolver → "Mis tareas" → retirar participante → verificar que pierde acceso. Hazlo también a 375 px de ancho. Si puedes, automatízalo con Playwright en un script fuera de `backend/tests` o como prueba E2E opcional.
3. Revisa contra los criterios de aceptación de cada HU de los Sprints 1 y 2 en `UserStoryMapping_...md`. Crea una tabla `HU | criterio | ¿cumple? | evidencia (archivo:línea o prueba)`.
4. Investiga en particular estos puntos que detecté (confirma o descarta cada uno con evidencia, no asumas):
   - `frontend/js/api.js`: **todo 403 redirige a "Sin acceso"**, incluso los 403 de una acción concreta (p. ej. "Solo la persona asignada o el responsable pueden cambiar el estado"), con lo que el usuario pierde el mensaje y la vista donde estaba. Distingue "no puedes ver este recurso" (GET → pantalla Sin acceso) de "no puedes hacer esta acción" (mutación → toast con el mensaje, quedarse en la vista).
   - Tras un 401 se manda a login y se pierde la ruta original: al volver a entrar debería regresar a donde estaba.
   - `localStorage.usuario` nunca se refresca: si el Admin cambia la función de alguien, la barra y los botones siguen con la función vieja. Existe `GET /api/auth/me` y no se usa.
   - **Las sesiones no expiran nunca** (tabla `sesiones` sin caducidad). Propón e implementa expiración por inactividad con migración, sin romper las pruebas.
   - Login sin ninguna protección contra fuerza bruta. Propón algo proporcionado (p. ej. retraso progresivo o límite por usuario en memoria) sin revelar si la cuenta existe.
   - `acceso/deps.py` lanza `HTTPException` directamente mientras el resto usa `NoAutenticado`/`Prohibido`; unifica si no rompe nada.
   - `GET /api/proyectos/{id}/tareas` ordena por `t.id`; "Mis tareas" sí tiene un orden útil. Evalúa un orden coherente (abiertas primero, bloqueadas visibles, prioridad, fecha).
   - Estados del proyecto (`planificado`) se muestran crudos en la UI; prioridades y estados de tarea sí tienen etiqueta legible.
   - Handlers `onclick="..."` inline en las plantillas: sustitúyelos por delegación de eventos (necesario además si se agrega una CSP).
   - Botón "Retirar" participante sin confirmación.
   - Cualquier XSS: verifica que **todo** texto de usuario pase por `escapar()`, incluidas fechas y valores que hoy se interpolan sin escapar.
   - Condiciones de carrera en el router: si el usuario navega rápido, una vista lenta puede pintar encima de la nueva (`router()` solo protege el caso de error).
   - Validaciones del cliente vs. servidor (longitudes, fechas) coherentes con los esquemas Pydantic.
   - Discrepancia documental: `docs/Arquitectura...md` dice PostgreSQL, Docker Compose y módulos ES "desde el Sprint 2", pero el código usa SQLite y scripts clásicos. **No migres a PostgreSQL, Docker ni módulos ES en esta tarea.** En lugar de eso, déjalo **registrado en el repositorio como pendiente técnico obligatorio para una próxima iteración**, de modo que quien siga lo encuentre sin depender de este chat:
     - Agrega en `README.md` una sección "Pendientes técnicos" (antes de "Fuera de alcance") con una entrada tipo: *"Alinear el código con la arquitectura (ADR-03): migrar de SQLite a PostgreSQL 16, agregar `docker-compose.yml` (api + postgres) y pasar el frontend a módulos ES. **Responsable sugerido: Fabián Reyna** (autor del C4); cualquier integrante puede tomarlo si él no está disponible."*
     - En `docs/Arquitectura_Gestion_Proyectos.md`, junto al stack o a la tabla de ADRs, agrega una nota breve de **estado actual** que diga que esas piezas aún no están implementadas y remita al pendiente del README. **No cambies las decisiones del documento**: siguen siendo el objetivo.
     - En la nota incluye una lista corta de lo que implica el cambio, según lo que veas en el código: SQL específico de SQLite (`PRAGMA`, `lastrowid`, booleanos `activo = 1`, índices parciales), migraciones de Alembic que haya que revisar, `DATABASE_URL` y el fixture de pruebas, el CI con un servicio Postgres y el orden de carga de los `<script>`.
5. Antes de corregir, presenta la lista de hallazgos clasificados (🔴 bug / 🟠 riesgo / 🟡 mejora) y continúa.

## 3. Fase 2 — Correcciones

- Corrige los bugs y riesgos confirmados. Por cada corrección de backend agrega o ajusta una **prueba** en `backend/tests/` (API en `test_sprint*.py`, reglas puras en `test_servicios.py`, usando `helpers.py` y el fixture `client`).
- Al final `python -m pytest -v` debe pasar completo.

## 4. Fase 3 — Quality of life features

Implementa las que aporten valor real, en este orden de prioridad. Todas respetan las reglas de la sección 1.

**A. Sin solaparse con el backlog (impleméntalas):**
1. **Atajos de teclado y paleta de comandos** (`Ctrl/⌘ K`): ir a proyectos, mis tareas, abrir un proyecto o tarea por nombre, crear tarea en el proyecto actual. Atajos estilo `g p`, `g t`, `n` (nueva tarea donde aplique), `?` muestra la ayuda. Que no se disparen escribiendo en inputs.
2. **Estados de carga y vacíos útiles:** *skeletons* en vez de pantalla en blanco; estados vacíos con la acción siguiente ("Este proyecto no tiene tareas — Crear la primera").
3. **Navegación:** `document.title` por vista, migas de pan, foco al `h1` en cada cambio de ruta (accesibilidad), volver a la ruta original tras login.
4. **Formularios:** contador de caracteres en textareas con `maxlength`, `Ctrl+Enter` para enviar, aviso al salir con cambios sin guardar, autofocus en el primer campo, mostrar/ocultar contraseña, mensajes de error junto al campo cuando el backend indica el campo (`Datos inválidos o incompletos: fecha_limite`).
5. **Confirmaciones propias** (diálogo accesible con `<dialog>`, no `window.confirm`) para acciones destructivas como retirar participante.
6. **Toasts mejorados:** apilables, con botón cerrar, errores que duran más y usan `aria-live="assertive"`, éxito con `polite`.
7. **Fechas legibles:** formato local `es-GT` ("12 nov 2026"), relativas en metadatos ("hace 3 h") con la absoluta en `title`.
8. **Ordenar columnas** de las tablas en el cliente y **búsqueda rápida** por texto en la lista de proyectos y de usuarios (solo cliente, sin tocar API).
9. **Copiar enlace** a una tarea/proyecto.
10. **Refresco de sesión** con `/api/auth/me` al cargar y expiración manejada con un mensaje claro ("Tu sesión expiró").
11. **Modo oscuro** automático con `prefers-color-scheme` y selector manual recordado.
12. Iniciales/avatar generado para personas (sin imágenes externas).

**B. Se solapan con HU planificadas (Sprint 3+):** historial visible de la tarea (HU-04-006 — el endpoint `/api/tareas/{id}/historial` ya existe), indicador de vencidas (HU-04-005), filtros por estado/responsable/prioridad (HU-07-002), tablero (HU-07-001), resumen/progreso del proyecto (HU-07-003). **No las implementes.** En el reporte final, deja para cada una una nota breve de cómo encajaría con la base que dejaste (componentes y tokens reutilizables) para que el equipo las haga en su sprint.

## 5. Fase 4 — Rediseño visual y funcional (que no parezca hecho por IA)

Objetivo: que se sienta como una herramienta de trabajo seria y propia (referencia de *espíritu*, no de copia: Linear, Things, Basecamp, un buen ERP bien hecho), no como una plantilla genérica.

**Evita explícitamente los clichés de UI generada por IA:**
- Degradados morado/azul, *glassmorphism*, sombras grandes y difusas en todo, tarjetas `rounded-2xl` flotando sobre fondo gris claro.
- Emojis como iconos (hoy hay `⛔` y `⚠`): reemplázalos por **SVG inline propios** (un `sprite` en `index.html` con `<symbol>`), trazo uniforme, conservando el texto al lado.
- Secciones "hero", textos de marketing, saludos tipo "¡Bienvenido de nuevo! 👋", iconos decorativos que no significan nada.
- Todo centrado con mucho aire y poca información; botones *pill* gigantes; paleta arcoíris de etiquetas.

**Dirección de diseño a seguir:**
- **Sistema de tokens** en `:root` (colores, espaciado en escala 4 px, radios pequeños 4–6 px, tipografía, sombras mínimas, duraciones) y su variante oscura. Nada de valores sueltos repetidos en el CSS.
- **Paleta sobria:** neutros cálidos o fríos bien escalonados + **un** color de acento con identidad (no el azul por defecto `#2b6cb0` ni morado). Colores semánticos (peligro, aviso, éxito) solo donde significan algo. Contraste WCAG AA verificado.
- **Tipografía:** pila del sistema bien ajustada, escala tipográfica clara, `font-variant-numeric: tabular-nums` en fechas y números, pesos con intención.
- **Densidad de información:** layout de aplicación con barra lateral de navegación en escritorio (proyectos recientes, Mis tareas, Usuarios si es Admin) y barra inferior o menú compacto en teléfono. Tablas densas pero legibles, filas de altura cómoda, hover sutil.
- **Estados con forma + texto:** chips de estado con un pequeño indicador de forma distinta por estado (círculo vacío pendiente, medio lleno en curso, check terminada), bloqueo con icono y borde, prioridad con barras tipo señal (1/2/3).
- **Ficha de tarea en dos columnas** en escritorio: contenido (descripción, resultado esperado, bloqueos) a la izquierda; panel de propiedades editable (responsable, prioridad, fecha, estado) a la derecha, como un inspector. En teléfono se apila.
- **Microinteracciones discretas** (100–200 ms), respetando `prefers-reduced-motion`. Focus ring visible y consistente.
- **Pantalla de login** sobria: el nombre del producto, el formulario, y ya.
- Organiza el CSS por secciones (tokens, base, layout, componentes, vistas, utilidades); si crece mucho, divídelo en varios archivos CSS enlazados desde `index.html`.

Organiza también el JS si lo necesitas (p. ej. `js/componentes.js`, `js/atajos.js`), manteniendo scripts clásicos cargados en orden desde `index.html` (sin módulos ES ni build), y actualiza la sección "Estructura" del `README.md`.

## 6. Fase 5 — Verificación final

1. `python -m pytest -v` pasa completo.
2. Repite el recorrido E2E de la Fase 1 en escritorio (1440 px) y teléfono (375 px), en modo claro y oscuro. Toma capturas si puedes y revísalas tú mismo.
3. Consola del navegador sin errores. Navegación completa con solo teclado.
4. Verifica de nuevo cada criterio de aceptación de los Sprints 1 y 2: no puede haber regresiones (especialmente permisos, idempotencia y "solo confirmar si el servidor responde OK").
5. `git status` y `git diff --stat`: confirma que solo cambiaste lo que querías (sin cambios de fin de línea accidentales).

## 7. Entregable final (en el chat, no como archivo)

1. Resultado de pruebas antes y después.
2. Tabla de hallazgos: problema → corrección → archivo(s) → prueba que lo cubre.
3. Lista de QoL implementadas y cómo usarlas (incluye la tabla de atajos).
4. Resumen del sistema de diseño (tokens, componentes) y decisiones visuales.
5. Notas para las HU de la sección 4.B.
6. Cambios para el `README.md` (ya aplicados), incluido el pendiente técnico de alinear el código con la arquitectura (responsable sugerido: Fabián Reyna, no exclusivo), y la sugerencia de `.gitattributes`.
7. Lista de archivos creados/modificados, agrupados por commit lógico sugerido (p. ej. `fix: ...`, `feat(ui): ...`, `style: ...`) con el mensaje propuesto en español, para que yo haga los commits.

Trabaja por fases y no avances a la siguiente con pruebas rotas. Si algo de este pedido choca con un criterio de aceptación o con la arquitectura, gana el criterio/arquitectura: explícalo y sigue.
