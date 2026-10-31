# Épicas del sistema de gestión de proyectos

**Estado:** propuesta inicial para validar con el cliente.  
**Base:** descripción general del proyecto y guía de preguntas para la entrevista. Las necesidades descritas son supuestos de trabajo, no decisiones ya confirmadas.

## 1. Propósito y alcance

El sistema permitirá planificar proyectos, distribuir tareas, registrar el avance y consultar el estado del trabajo en un lugar común. Se plantea para una organización que coordina varios proyectos a la vez y cuyos integrantes necesitan conocer sus responsabilidades, fechas y bloqueos. La primera versión se usará desde un navegador en computadora o teléfono, con conexión a internet.

Una **épica** reúne una necesidad amplia con valor para quienes usarán el sistema. Más adelante se dividirá en historias de usuario y criterios de aceptación detallados. Las ocho épicas siguientes forman una propuesta de alcance esencial; su contenido y orden deben confirmarse con el cliente antes de comprometer una entrega.

## 2. Catálogo de épicas

| ID | Épica | Resultado principal |
| --- | --- | --- |
| EP-01 | Usuarios y acceso según función | Cada persona entra con su cuenta y realiza solo las acciones autorizadas. |
| EP-02 | Creación y administración de proyectos | Los proyectos tienen responsables, objetivos, fechas y un ciclo de vida claro. |
| EP-03 | Planificación y asignación de tareas | El trabajo se descompone, prioriza y asigna con fechas visibles. |
| EP-04 | Actualización del trabajo y gestión de bloqueos | El avance, los retrasos y los impedimentos se registran sin perder su historia. |
| EP-05 | Colaboración y archivos del proyecto | La conversación y los documentos relevantes quedan vinculados al trabajo. |
| EP-06 | Avisos sobre eventos importantes | Las personas indicadas conocen a tiempo los cambios que requieren atención. |
| EP-07 | Consulta del avance e informes | Responsables y dirección identifican pendientes, retrasos y estado de los proyectos. |
| EP-08 | Conservación y recuperación de la información | El trabajo guardado se mantiene íntegro y puede recuperarse ante fallos. |

## 3. Descripción de las épicas

### EP-01. Usuarios y acceso según función

**Objetivo:** permitir que cada participante trabaje con la información y las acciones que le correspondan, sin exponer proyectos a personas no autorizadas.

**Descripción:** la organización podrá dar acceso a responsables de proyecto, integrantes del equipo y personal de supervisión. Cada persona ingresará con una cuenta propia. Los permisos determinarán quién puede crear proyectos, asignar tareas, modificar información y consultar los resúmenes generales.

**Alcance:** alta, desactivación e ingreso de usuarios; funciones y permisos básicos; acceso a proyectos según participación o responsabilidad. El acceso de clientes o colaboradores externos queda sujeto a confirmación.

**Resultados verificables:**

- Una persona autorizada puede ingresar y consultar los proyectos que le corresponden.
- Una persona sin permiso no puede ver ni modificar un proyecto restringido, aunque intente abrirlo directamente.
- Al desactivar una cuenta se impiden nuevos accesos y se conserva la atribución de sus acciones anteriores.

**Límites y dependencias:** es una capacidad transversal. No presupone inicio de sesión mediante cuentas de otras aplicaciones ni un portal para clientes externos.

### EP-02. Creación y administración de proyectos

**Objetivo:** mantener una ficha única y actualizada de cada proyecto, desde su inicio hasta su cierre.

**Descripción:** el responsable podrá registrar el propósito del proyecto, sus fechas, participantes y etapas; consultar su estado; y cerrarlo cuando se cumplan las condiciones acordadas. Los cambios relevantes quedarán identificados para evitar versiones contradictorias del plan.

**Alcance:** creación, consulta, actualización y cierre de proyectos; responsable principal, objetivo, fechas previstas, participantes y estado. Las etapas concretas se definirán con el cliente.

**Resultados verificables:**

- Un proyecto creado muestra su objetivo, responsable, fechas y estado vigente en un solo lugar.
- Los integrantes autorizados ven los cambios confirmados sin depender de una hoja o mensaje separado.
- Un proyecto cerrado conserva sus tareas, archivos e historial para consulta; el cierre no borra el trabajo realizado.

**Límites y dependencias:** utiliza los permisos de EP-01. No incluye presupuestos, facturación ni carteras complejas de programas y subproyectos en la primera versión.

### EP-03. Planificación y asignación de tareas

**Objetivo:** convertir el plan de cada proyecto en trabajo concreto, con responsables y fechas claras.

**Descripción:** los responsables podrán crear tareas, describir el resultado esperado, asignarlas a personas, establecer fechas límite y prioridades, y revisar la distribución del trabajo. Los integrantes podrán identificar sus pendientes sin buscar en varias herramientas.

**Alcance:** creación y edición de tareas; descripción, responsable, prioridad, fecha límite y estado inicial; consulta por proyecto y por persona. Las dependencias entre tareas se incorporarán si el cliente las considera necesarias para planificar.

**Resultados verificables:**

- Cada tarea pertenece a un proyecto y muestra quién es responsable y cuándo debe atenderla.
- La persona asignada puede encontrar sus tareas pendientes y distinguir las vencidas o próximas a vencer.
- Al cambiar responsable, prioridad o fecha, se muestra el valor vigente y se conserva quién realizó el cambio.

**Límites y dependencias:** depende de EP-01 y EP-02. No contempla asignación automática de personal ni cálculo automático de cronogramas.

### EP-04. Actualización del trabajo y gestión de bloqueos

**Objetivo:** mostrar el avance real de las tareas y permitir intervenir cuando el trabajo se detenga o cambie.

**Descripción:** los integrantes actualizarán el estado de sus tareas y podrán indicar avances o impedimentos. Los responsables revisarán bloqueos y retrasos, registrarán la resolución y confirmarán cuándo una tarea o un proyecto se considera terminado.

**Alcance:** estados de tarea, avances, registro y resolución de bloqueos, identificación de vencimientos e historial de cambios relevantes. Las reglas de aprobación formal de entregas se definirán si el cliente las necesita.

**Resultados verificables:**

- Un cambio de estado confirmado aparece en las consultas del proyecto y de la persona asignada.
- Una tarea bloqueada muestra el impedimento y puede identificarse entre los asuntos que requieren atención.
- La resolución de un bloqueo y los cambios de estado importantes conservan fecha y responsable.

**Límites y dependencias:** depende de EP-03 y alimenta las consultas de EP-07. No sustituye procesos especializados de control de calidad o aprobación contractual.

### EP-05. Colaboración y archivos del proyecto

**Objetivo:** mantener el contexto del trabajo junto a los proyectos y tareas, para que las decisiones y los documentos no se dispersen.

**Descripción:** las personas autorizadas podrán comentar avances o dudas y adjuntar archivos pertinentes. La información quedará vinculada a la tarea o al proyecto correspondiente y podrá consultarse después.

**Alcance:** comentarios y archivos vinculados a proyectos o tareas; identificación de autor y fecha; consulta según permisos. Se deberán acordar los tipos y tamaños de archivo permitidos.

**Resultados verificables:**

- Un comentario o archivo agregado a una tarea puede encontrarse desde esa misma tarea.
- Solo las personas con acceso al proyecto pueden consultar sus comentarios y archivos.
- La conversación conserva su orden y autoría, incluso cuando una tarea cambie de responsable.

**Límites y dependencias:** depende de EP-01 a EP-03. No pretende reemplazar una aplicación de mensajería instantánea ni incluir edición simultánea de documentos.

### EP-06. Avisos sobre eventos importantes

**Objetivo:** alertar a las personas adecuadas cuando haya cambios o pendientes que requieran actuar.

**Descripción:** el sistema mostrará avisos sobre nuevas asignaciones, vencimientos cercanos, bloqueos y cambios relevantes. Cada aviso deberá conducir al proyecto o tarea que lo originó, para que el usuario pueda entenderlo y actuar.

**Alcance:** avisos dentro de la aplicación; destinatarios y eventos esenciales; consulta de avisos pendientes. La frecuencia y anticipación de los recordatorios se definirán con el cliente.

**Resultados verificables:**

- La persona asignada recibe un aviso visible al obtener una tarea nueva.
- Un vencimiento o bloqueo genera un aviso para quienes deban atenderlo, sin enviar el mismo aviso repetidamente por una sola acción.
- Cada aviso identifica el motivo y abre el proyecto o tarea relacionado, siempre que el destinatario tenga permiso.

**Límites y dependencias:** depende de EP-01, EP-03 y EP-04. Correo electrónico, mensajes externos y avisos en el teléfono fuera de la aplicación requieren confirmación adicional.

### EP-07. Consulta del avance e informes

**Objetivo:** ofrecer una visión confiable del trabajo para detectar retrasos y tomar decisiones oportunas.

**Descripción:** responsables y supervisores podrán consultar proyectos activos, tareas por estado, próximas fechas y bloqueos. Las vistas resumidas permitirán pasar del dato general a las tareas que lo explican.

**Alcance:** lista o tablero de tareas, resumen por proyecto y por responsable, filtros básicos, indicadores de pendientes, vencimientos y bloqueos. Las métricas específicas se validarán con el cliente.

**Resultados verificables:**

- Un responsable puede identificar qué tareas están pendientes, vencidas o bloqueadas en cada proyecto.
- La dirección puede consultar el estado general de los proyectos a los que tiene acceso y abrir el detalle que sustenta cada resumen.
- Los resúmenes reflejan los cambios confirmados y no muestran información de proyectos sin autorización.

**Límites y dependencias:** depende de EP-01 a EP-04. No equivale a un sistema de análisis financiero, predicción de fechas o reportes a medida ilimitados.

### EP-08. Conservación y recuperación de la información

**Objetivo:** evitar la pérdida o duplicación del trabajo registrado y permitir que la organización retome sus actividades después de una interrupción.

**Descripción:** las personas deben saber si una acción se guardó correctamente. El sistema conservará la información confirmada y dispondrá de un procedimiento de recuperación ante fallos. Esta épica convierte la confiabilidad esperada por el cliente en resultados que puedan comprobarse.

**Alcance:** confirmación clara de guardado o error; protección frente a envíos repetidos y cambios simultáneos; copias de respaldo y prueba de restauración; conservación de datos e historial relevante.

**Resultados verificables:**

- Si una acción falla, la aplicación lo informa y no presenta un cambio inexistente como guardado.
- Repetir una acción tras una interrupción no crea proyectos, tareas o comentarios duplicados por accidente.
- Una prueba de restauración permite recuperar los proyectos y tareas confirmados dentro de los límites de pérdida y tiempo acordados con el cliente.

**Límites y dependencias:** atraviesa todas las épicas. El tiempo máximo de recuperación y la cantidad de información que podría perderse deben acordarse antes de cerrar los criterios de aceptación. No presupone funcionamiento sin conexión.

## 4. Condiciones compartidas de calidad

Estas condiciones aplican a las épicas y deberán concretarse en historias de usuario y pruebas:

- **Claridad de uso:** las acciones principales deben poder realizarse sin formación técnica y ser comprensibles en computadora y teléfono.
- **Consistencia:** una tarea no debe aparecer con estados, responsables o fechas contradictorios en distintas vistas.
- **Accesibilidad y legibilidad:** la información y las acciones deben poder localizarse y comprenderse sin depender exclusivamente del color.
- **Protección de la información:** se recogerán solo los datos necesarios; comentarios y archivos respetarán los permisos del proyecto.
- **Respuesta y continuidad:** se acordarán tiempos de respuesta y recuperación según el uso real esperado, y se verificarán antes de la entrega.

## 5. Secuencia sugerida para la primera versión

1. Establecer usuarios, permisos y estructura de proyectos: EP-01 y EP-02.
2. Completar el recorrido de una tarea desde su asignación hasta su cierre: EP-03 y EP-04.
3. Incorporar comentarios, archivos y avisos ligados a ese recorrido: EP-05 y EP-06.
4. Mostrar el avance conjunto y comprobar la recuperación de la información: EP-07 y EP-08.

Esta secuencia organiza el trabajo; no convierte cada épica en una entrega aislada. La primera versión debe permitir un recorrido completo y confiable de un proyecto real.

## 6. Decisiones pendientes con el cliente

- ¿Cuáles son las tres necesidades prioritarias y qué tipo de proyecto se usará para validar la primera versión?
- ¿Qué etapas, estados y reglas de cierre corresponden a proyectos y tareas?
- ¿Qué permisos tendrán responsables, integrantes, supervisores y posibles usuarios externos?
- ¿Se necesitan dependencias entre tareas o aprobaciones formales desde el inicio?
- ¿Qué avisos son indispensables y con cuánta anticipación deben aparecer?
- ¿Qué información existente debe trasladarse y qué otras herramientas deben seguir utilizándose?
- ¿Qué volumen de usuarios y proyectos se espera, y qué tiempos de respuesta y recuperación son aceptables?

Estas respuestas permitirán ajustar el alcance y dividir las épicas en historias de usuario comprobables.
