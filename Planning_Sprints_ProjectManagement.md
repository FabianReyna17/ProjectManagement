# Planning — Sistema de Gestión de Proyectos

**Fuente:** `UserStoryMapping_Gestion_Proyectos.md` (48 historias, EP-01 a EP-08)
**Sprints:** 6 de 2 semanas (12 semanas) · **Equipo:** 3 desarrolladores · **Velocidad estimada:** 25–30 pts/sprint
**Estimación:** puntos de historia (Fibonacci 1, 2, 3, 5, 8)

**Criterio de prioridad:** primero lo que permite usar el sistema de punta a punta (acceso → proyecto → tareas → seguimiento); luego lo que mejora la coordinación (avisos, colaboración, reportes); al final la administración y continuidad. Las dependencias del story mapping se respetan.

**Tipos de tarea:**
- **Dev:** desarrollo (BD, API, interfaz).
- **Test:** Dev Testing (pruebas unitarias/integración del desarrollador y verificación de los criterios de aceptación).

---

## 1. Product Backlog (ordenado por valor)

| Prio | HU | Historia | MoSCoW | Pts | Sprint |
|---|---|---|---|---|---|
| 1 | TEC-01 | Entorno, arquitectura base y BD | Must | 5 | 1 |
| 2 | HU-01-001 | Registrar cuenta | Must | 3 | 1 |
| 3 | HU-01-003 | Iniciar sesión | Must | 3 | 1 |
| 4 | HU-01-002 | Asignar función inicial | Must | 2 | 1 |
| 5 | HU-02-001 | Crear proyecto | Must | 3 | 1 |
| 6 | HU-01-005 | Dar acceso a participantes | Must | 3 | 1 |
| 7 | HU-01-006 | Consultar proyectos autorizados | Must | 2 | 1 |
| 8 | HU-01-007 | Impedir acciones no autorizadas | Must | 5 | 1 |
| 9 | HU-02-002 | Consultar ficha del proyecto | Must | 2 | 1 |
| 10 | HU-08-001 | Saber si una acción se guardó | Must | 2 | 1 |
| 11 | HU-01-004 | Cerrar sesión | Must | 1 | 1 |
| 12 | HU-03-001 | Crear tarea | Must | 3 | 2 |
| 13 | HU-03-002 | Asignar responsable | Must | 3 | 2 |
| 14 | HU-03-004 | Consultar mis tareas | Must | 3 | 2 |
| 15 | HU-04-001 | Cambiar estado de tarea | Must | 3 | 2 |
| 16 | HU-03-003 | Definir fecha límite y prioridad | Must | 2 | 2 |
| 17 | HU-03-005 | Revisar tareas del proyecto | Must | 3 | 2 |
| 18 | HU-04-003 | Registrar bloqueo | Must | 3 | 2 |
| 19 | HU-04-004 | Resolver bloqueo | Must | 3 | 2 |
| 20 | HU-08-002 | Reintentar sin duplicar | Must | 5 | 2 |
| 21 | HU-07-001 | Tablero de tareas del proyecto | Must | 5 | 3 |
| 22 | HU-04-005 | Identificar tareas vencidas | Must | 2 | 3 |
| 23 | HU-03-006 | Replanificar tarea | Must | 3 | 3 |
| 24 | HU-02-003 | Actualizar datos del proyecto | Must | 3 | 3 |
| 25 | HU-04-002 | Registrar avance | Should | 2 | 3 |
| 26 | HU-07-002 | Filtrar tareas | Should | 3 | 3 |
| 27 | HU-08-003 | Evitar sobrescribir cambios ajenos | Must | 5 | 3 |
| 28 | HU-04-006 | Historial de una tarea | Should | 3 | 3 |
| 29 | HU-06-001 | Aviso de nueva asignación | Must | 3 | 4 |
| 30 | HU-06-003 | Aviso de bloqueo al responsable | Must | 2 | 4 |
| 31 | HU-06-005 | Consultar y abrir mis avisos | Must | 3 | 4 |
| 32 | HU-05-001 | Comentar proyecto o tarea | Should | 3 | 4 |
| 33 | HU-05-002 | Adjuntar archivo | Should | 5 | 4 |
| 34 | HU-05-003 | Consultar comentarios y archivos | Should | 2 | 4 |
| 35 | HU-02-004 | Cambiar estado del proyecto | Must | 2 | 4 |
| 36 | HU-07-003 | Resumen del proyecto | Should | 3 | 4 |
| 37 | HU-07-005 | Estado general de los proyectos | Should | 5 | 5 |
| 38 | HU-06-002 | Aviso de vencimiento cercano | Should | 3 | 5 |
| 39 | HU-02-005 | Cerrar proyecto | Must | 3 | 5 |
| 40 | HU-07-004 | Carga por responsable | Should | 3 | 5 |
| 41 | HU-06-004 | Aviso de cambio relevante | Could | 3 | 5 |
| 42 | HU-02-006 | Proyecto cerrado e historial | Should | 3 | 5 |
| 43 | HU-05-004 | Corregir contenido propio | Could | 2 | 5 |
| 44 | HU-01-009 | Desactivar cuenta | Must | 2 | 6 |
| 45 | HU-01-008 | Cambiar función de cuenta | Should | 2 | 6 |
| 46 | HU-01-011 | Restablecer acceso | Should | 3 | 6 |
| 47 | HU-08-004 | Respaldo periódico | Must | 3 | 6 |
| 48 | HU-08-005 | Restaurar y verificar recuperación | Must | 5 | 6 |
| 49 | HU-01-010 | Historial de cambios de acceso | Could | 3 | 6 |
| 50 | TEC-02 | Regresión, pruebas E2E y release | Must | 5 | 6 |

| Sprint | Objetivo | Pts |
|---|---|---|
| 1 | Acceso controlado y primer proyecto | 31 |
| 2 | Tareas asignadas y seguimiento básico | 28 |
| 3 | Tablero, replanificación y consistencia | 26 |
| 4 | Avisos y colaboración | 23 |
| 5 | Supervisión y cierre de proyectos | 22 |
| 6 | Administración, respaldo y release | 23 |

---

## 2. Sprint Backlog

### Sprint 1 — Semanas 1–2 · Acceso controlado y primer proyecto (31 pts)

**Resultado:** un usuario entra, crea un proyecto, da acceso a otro y este solo ve lo autorizado.

**TEC-01 Entorno y arquitectura base (5)**
- Dev: crear repositorio, ramas y estructura del proyecto (frontend/backend).
- Dev: modelo de BD inicial: usuarios, funciones, proyectos, participantes.
- Dev: pipeline de integración (build + ejecución de pruebas en cada push).
- Test: verificar que el pipeline falla con una prueba rota y pasa con todo correcto.

**HU-01-001 Registrar cuenta (3)**
- Dev: endpoint de alta con validación de campos obligatorios e identificador único.
- Dev: formulario de registro (solo administrador) con mensajes de error.
- Test: alta válida crea 1 cuenta activa; duplicado/campos vacíos → rechazo sin crear; cuenta nueva no ve proyectos.

**HU-01-003 Iniciar sesión (3)**
- Dev: autenticación con contraseña cifrada y manejo de sesión/token.
- Dev: pantalla de login y redirección a "Mis proyectos".
- Test: credenciales válidas → sesión; inválidas o cuenta inactiva → mensaje genérico sin revelar datos.

**HU-01-002 Asignar función inicial (2)**
- Dev: catálogo de funciones (Admin, Responsable, Integrante, Supervisor) y asignación a cuenta.
- Dev: selector de función en el formulario de cuenta.
- Test: función válida se guarda; inexistente → rechazo; la función no da acceso a proyectos ajenos.

**HU-02-001 Crear proyecto (3)**
- Dev: endpoint de creación (nombre, objetivo, responsable, fechas, estado "planificado").
- Dev: formulario de nuevo proyecto con validación de fechas.
- Test: creación válida; fecha fin < inicio → error; campos faltantes → no crea.

**HU-01-005 Dar acceso a participantes (3)**
- Dev: endpoints para agregar/retirar participantes (solo responsable del proyecto).
- Dev: sección "Participantes" en el proyecto.
- Test: agregado ve el proyecto; retirado deja de verlo sin borrar su historial; responsable ajeno → rechazo.

**HU-01-006 Consultar proyectos autorizados (2)**
- Dev: endpoint "mis proyectos" filtrado por participación.
- Dev: vista de lista de proyectos.
- Test: solo aparecen proyectos con acceso; al perder acceso desaparece en la siguiente consulta.

**HU-01-007 Impedir acciones no autorizadas (5)**
- Dev: middleware de autorización por función + proyecto en todos los endpoints (denegar por defecto).
- Dev: respuesta 403 uniforme y pantalla de "sin acceso".
- Test: acceso por enlace directo y peticiones manuales sin permiso → rechazadas; permisos cambiados en sesión abierta se aplican.

**HU-02-002 Consultar ficha del proyecto (2)**
- Dev: endpoint y vista de ficha (nombre, objetivo, responsable, fechas, estado).
- Test: datos correctos; usuario sin acceso no abre la ficha por URL.

**HU-08-001 Saber si una acción se guardó (2)**
- Dev: componente común de confirmación/error para todas las acciones de guardado.
- Test: forzar error del servidor → la UI muestra error y no muestra el cambio como guardado.

**HU-01-004 Cerrar sesión (1)**
- Dev: invalidar sesión en servidor y botón "Salir".
- Test: tras salir, abrir un proyecto exige login.

---

### Sprint 2 — Semanas 3–4 · Tareas asignadas y seguimiento básico (28 pts)

**Resultado:** el responsable crea y asigna tareas; cada integrante ve las suyas, cambia su estado y reporta bloqueos.

**HU-03-001 Crear tarea (3)**
- Dev: tabla y endpoint de tareas ligadas a un proyecto (estado inicial "pendiente").
- Dev: formulario de nueva tarea dentro del proyecto.
- Test: tarea creada en el proyecto correcto; usuario sin permiso de planificar → rechazo.

**HU-03-002 Asignar responsable (3)**
- Dev: asignación validando cuenta activa y participante del proyecto; registro del cambio.
- Dev: selector de responsable en la tarea.
- Test: asignación válida aparece en pendientes; cuenta inactiva/ajena → rechazo; cambio conserva anterior y actor.

**HU-03-004 Consultar mis tareas (3)**
- Dev: endpoint "mis tareas" de todos mis proyectos con acceso.
- Dev: vista con proyecto, estado, prioridad y fecha; acceso al detalle.
- Test: solo tareas propias y accesibles; reasignada o sin acceso → ya no aparece.

**HU-04-001 Cambiar estado de tarea (3)**
- Dev: estados (pendiente, en curso, bloqueada, terminada) y transiciones permitidas.
- Dev: control de cambio de estado en detalle y lista.
- Test: transición válida se refleja en vista personal y del proyecto; transición inválida → rechazo.

**HU-03-003 Fecha límite y prioridad (2)**
- Dev: campos fecha y prioridad (alta/media/baja) con validación e historial.
- Test: fecha inválida o prioridad fuera de catálogo → no guarda; cambio registra valor anterior.

**HU-03-005 Revisar tareas del proyecto (3)**
- Dev: endpoint y lista de tareas del proyecto; marcar las no asignadas.
- Test: no se mezclan tareas de otros proyectos; respeta permisos.

**HU-04-003 Registrar bloqueo (3)**
- Dev: registrar motivo del bloqueo, pasar tarea a "bloqueada" con fecha y autor.
- Dev: botón "Reportar bloqueo" y marca visual (icono + texto, no solo color).
- Test: bloqueo visible en tarea y lista; sin motivo → no guarda.

**HU-04-004 Resolver bloqueo (3)**
- Dev: registrar resolución y devolver tarea a su estado de trabajo.
- Test: resolución guarda fecha y responsable; tarea deja de figurar como bloqueada.

**HU-08-002 Reintentar sin duplicar (5)**
- Dev: clave de idempotencia en creaciones (proyectos, tareas, comentarios).
- Dev: deshabilitar botón durante el envío.
- Test: doble clic y reenvío tras corte de red → se crea un solo registro.

---

### Sprint 3 — Semanas 5–6 · Tablero, replanificación y consistencia (26 pts)

**Resultado:** el equipo sigue el trabajo en un tablero, detecta vencidas y los cambios no se pisan entre sí.

**HU-07-001 Tablero de tareas (5)**
- Dev: vista tablero por columnas de estado con datos de responsable, fecha y prioridad.
- Dev: diseño responsive (computadora y teléfono).
- Test: tablero coincide con la lista; un cambio de estado se refleja en ambas vistas.

**HU-04-005 Identificar tareas vencidas (2)**
- Dev: cálculo de vencida/próxima a vencer según zona horaria de la organización.
- Dev: indicador en lista, tablero y "mis tareas".
- Test: casos límite de fecha (hoy, ayer, mañana) y tareas terminadas no marcadas como vencidas.

**HU-03-006 Replanificar tarea (3)**
- Dev: edición de responsable, fecha y prioridad con registro de historial.
- Test: cambios visibles en todas las vistas; avances previos se conservan al reasignar.

**HU-02-003 Actualizar datos del proyecto (3)**
- Dev: edición de objetivo, responsable y fechas con historial.
- Test: cambio válido guarda valor anterior y actor; sin permiso o inválido → rechazo.

**HU-04-002 Registrar avance (2)**
- Dev: nota de avance en la tarea con autor y fecha.
- Test: avance visible en el detalle; usuario sin acceso no puede registrarlo.

**HU-07-002 Filtrar tareas (3)**
- Dev: filtros por estado, responsable, prioridad y vencimiento en lista/tablero.
- Test: combinaciones de filtros devuelven resultados correctos y solo de proyectos autorizados.

**HU-08-003 Evitar sobrescribir cambios ajenos (5)**
- Dev: control de versión por registro (bloqueo optimista) en proyectos y tareas.
- Dev: mensaje de conflicto con opción de recargar.
- Test: dos usuarios editan el mismo dato → el segundo recibe conflicto y no sobrescribe.

**HU-04-006 Historial de una tarea (3)**
- Dev: vista cronológica de cambios (estado, responsable, fecha, bloqueos).
- Test: cada cambio de sprints anteriores aparece con actor, fecha y valores.

---

### Sprint 4 — Semanas 7–8 · Avisos y colaboración (23 pts)

**Resultado:** las personas se enteran a tiempo de asignaciones y bloqueos, y el contexto queda en la tarea.

**HU-06-001 Aviso de nueva asignación (3)**
- Dev: tabla de avisos y generación al asignar una tarea.
- Test: el asignado recibe 1 aviso por asignación; reasignar avisa al nuevo responsable.

**HU-06-003 Aviso de bloqueo al responsable (2)**
- Dev: generar aviso al responsable del proyecto al registrar bloqueo.
- Test: aviso llega al destinatario correcto y no se repite por la misma acción.

**HU-06-005 Consultar y abrir mis avisos (3)**
- Dev: bandeja de avisos con contador de no leídos y enlace a la tarea/proyecto.
- Test: abrir aviso lleva al recurso; sin permiso actual → no muestra detalle.

**HU-05-001 Comentar proyecto o tarea (3)**
- Dev: comentarios con autor y fecha ligados a tarea o proyecto.
- Test: comentario visible en orden; usuario sin acceso no lo ve ni crea.

**HU-05-002 Adjuntar archivo (5)**
- Dev: carga de archivos con límite de tamaño y tipos permitidos; almacenamiento ligado a la tarea.
- Dev: descarga protegida por permisos.
- Test: tipo/tamaño inválido → rechazo; descarga por URL directa sin acceso → bloqueada.

**HU-05-003 Consultar comentarios y archivos (2)**
- Dev: sección unificada de comentarios y archivos en el detalle.
- Test: se conservan autoría y orden tras cambiar responsable de la tarea.

**HU-02-004 Cambiar estado del proyecto (2)**
- Dev: transiciones planificado → en curso (cierre queda para HU-02-005).
- Test: transición válida registra actor y fecha; inválida → rechazo.

**HU-07-003 Resumen del proyecto (3)**
- Dev: indicadores del proyecto: pendientes, vencidas, bloqueadas, terminadas.
- Test: los números coinciden con las tareas reales; cada indicador abre su lista.

---

### Sprint 5 — Semanas 9–10 · Supervisión y cierre de proyectos (22 pts)

**Resultado:** dirección ve el estado general y los proyectos pueden cerrarse sin perder información.

**HU-07-005 Estado general de los proyectos (5)**
- Dev: vista de todos los proyectos autorizados con estado e indicadores clave.
- Dev: acceso al detalle desde cada resumen.
- Test: supervisor solo ve proyectos autorizados; cifras coinciden con cada proyecto.

**HU-06-002 Aviso de vencimiento cercano (3)**
- Dev: proceso programado que genera avisos con la anticipación acordada.
- Test: se genera 1 aviso por tarea y no se repite en cada ejecución.

**HU-02-005 Cerrar proyecto (3)**
- Dev: cierre que muestra tareas abiertas y exige resolverlas o justificar excepción.
- Test: cierre registra fecha y actor; tareas y archivos se conservan; repetir cierre no duplica.

**HU-07-004 Carga por responsable (3)**
- Dev: vista de tareas abiertas/vencidas por persona.
- Test: totales correctos y solo de proyectos autorizados.

**HU-06-004 Aviso de cambio relevante (3)**
- Dev: avisos por cambio de fecha, prioridad o responsable de tareas propias.
- Test: aviso llega a los afectados; quien hizo el cambio no se avisa a sí mismo.

**HU-02-006 Proyecto cerrado e historial (3)**
- Dev: lista de proyectos cerrados y vista de historial de cambios.
- Test: proyecto cerrado se consulta completo; historial no se altera; sin acceso → bloqueado.

**HU-05-004 Corregir contenido propio (2)**
- Dev: editar/ocultar comentario propio dejando marca de edición.
- Test: solo el autor puede corregir; queda constancia del cambio.

---

### Sprint 6 — Semanas 11–12 · Administración, respaldo y release (23 pts)

**Resultado:** la organización administra cuentas de forma segura, la información se respalda y se entrega la versión 1.

**HU-01-009 Desactivar cuenta (2)**
- Dev: desactivación que invalida sesiones activas.
- Test: cuenta desactivada no entra ni actúa; su historial conserva autoría; desactivar dos veces no rompe estado.

**HU-01-008 Cambiar función de cuenta (2)**
- Dev: cambio de función con registro (anterior, nueva, actor, fecha).
- Test: permisos nuevos aplican de inmediato; no-admin no puede cambiar funciones (ni la propia).

**HU-01-011 Restablecer acceso (3)**
- Dev: restablecimiento iniciado por admin con credencial temporal y cambio obligatorio.
- Test: credencial anterior deja de servir; se conservan permisos y se registra quién lo inició.

**HU-08-004 Respaldo periódico (3)**
- Dev: script programado de respaldo de BD y archivos con registro de ejecución.
- Test: respaldo se genera según la frecuencia y es legible.

**HU-08-005 Restaurar y verificar recuperación (5)**
- Dev: procedimiento documentado de restauración.
- Test: restaurar en entorno de prueba y comparar proyectos/tareas con el origen; medir tiempo de recuperación.

**HU-01-010 Historial de cambios de acceso (3)**
- Dev: registro y consulta de altas, retiros y cambios de función por persona/proyecto.
- Test: cada cambio muestra actor, fecha y valores; usuarios no admin no lo ven.

**TEC-02 Regresión, E2E y release (5)**
- Dev: corregir defectos pendientes y preparar despliegue.
- Test: pruebas E2E del recorrido completo (login → proyecto → tareas → bloqueo → aviso → cierre) y regresión de permisos.

---

## 3. Definición de Terminado (DoD)

Una historia está terminada cuando:
1. Cumple todos sus criterios de aceptación del story mapping.
2. Sus tareas Dev y Test están completas y las pruebas pasan en el pipeline.
3. Los permisos se validan en el servidor, no solo en la interfaz.
4. Funciona en computadora y teléfono.
5. Fue revisada por otro integrante (code review) y está integrada en la rama principal.
