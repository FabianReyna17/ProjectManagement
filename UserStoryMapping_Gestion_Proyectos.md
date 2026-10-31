# User Story Mapping del sistema de gestión de proyectos

**Estado:** propuesta para revisión; historias aún no aprobadas ni implementadas.  
**Fuente:** `Epicas_Gestion_Proyectos.md`.  
**Alcance desarrollado en esta versión:** mapa general del producto e historias de EP-01 a EP-08.

## 1. Propósito y organización

Este documento reunirá los mapas y las historias de usuario del sistema. Cada épica tendrá su recorrido de actividades, entregas propuestas, historias, criterios de aceptación y decisiones pendientes. Las actividades describen lo que hace una persona para lograr un resultado; no representan pantallas ni componentes técnicos.

Los identificadores `HU-01-001` indican épica 01 e historia 001. Permanecerán estables aunque cambie el orden de las entregas. Las historias futuras de otra épica usarán su propio prefijo, por ejemplo `HU-02-001`.

| Épica | Estado de las historias |
| --- | --- |
| EP-01 — Usuarios y acceso según función | Mapa y 11 historias propuestas en este documento |
| EP-02 — Creación y administración de proyectos | Mapa y 6 historias propuestas |
| EP-03 — Planificación y asignación de tareas | Mapa y 6 historias propuestas |
| EP-04 — Actualización del trabajo y gestión de bloqueos | Mapa y 6 historias propuestas |
| EP-05 — Colaboración y archivos del proyecto | Mapa y 4 historias propuestas |
| EP-06 — Avisos sobre eventos importantes | Mapa y 5 historias propuestas |
| EP-07 — Consulta del avance e informes | Mapa y 5 historias propuestas |
| EP-08 — Conservación y recuperación de la información | Mapa y 5 historias propuestas; también aporta criterios compartidos |

### 1.1. Recorrido general del producto

| Actividad del usuario | Resultado esperado | Épicas relacionadas |
| --- | --- | --- |
| A1. Acceder al trabajo autorizado | Cada persona ingresa y encuentra lo que le corresponde. | EP-01 |
| A2. Organizar un proyecto | El proyecto tiene objetivo, responsable, fechas, participantes y estado. | EP-02, EP-01 |
| A3. Planificar las tareas | El trabajo se describe, asigna y prioriza con fechas claras. | EP-03 |
| A4. Ejecutar y colaborar | El equipo actualiza avances, resuelve bloqueos y conserva comentarios y archivos. | EP-04, EP-05 |
| A5. Atender cambios importantes | Las personas indicadas conocen asignaciones, vencimientos y bloqueos. | EP-06 |
| A6. Revisar y cerrar | Responsables y dirección consultan el avance y se conserva el historial del proyecto. | EP-07, EP-02 |

EP-08 acompaña todas las actividades: una acción debe informar si se guardó, no duplicarse por un reintento y poder recuperarse dentro de los límites acordados. El mapa general orienta el recorrido completo; los mapas detallados de cada épica precisan las historias y sus entregas propuestas.

## 2. EP-01 — Usuarios y acceso según función

### 2.1. Objetivo y participantes

**Objetivo:** que cada persona entre con una cuenta propia y trabaje únicamente con la información y las acciones autorizadas, sin perder la atribución de los cambios de acceso.

**Recorrido principal:** habilitar una cuenta y asignarle una función → ingresar → recibir acceso a un proyecto → encontrar los proyectos autorizados → realizar acciones permitidas → mantener y revisar los accesos. La administración de cuentas ocurre también mientras los proyectos están en marcha.

| Participante | Necesidad |
| --- | --- |
| Administrador de la organización | Habilitar y desactivar cuentas, asignar funciones y revisar cambios de acceso. |
| Responsable de proyecto | Dar acceso a participantes de su proyecto y consultar quién puede verlo. |
| Integrante del equipo | Ingresar y consultar únicamente los proyectos y tareas que le corresponden. |
| Supervisor o dirección | Consultar la información autorizada sin adquirir por ello permisos de edición. |

Estas funciones son una propuesta. Una persona podría asumir más de una; la combinación exacta de permisos debe validarse antes de implementar las historias.

### 2.2. Alcance y límites

Incluye creación y desactivación de cuentas, funciones básicas, ingreso y cierre de sesión, acceso por proyecto, verificación de permisos en consultas y acciones, recuperación administrada de acceso y consulta del historial de cambios de permisos. La creación y el cierre de proyectos pertenecen a EP-02; la edición de tareas pertenece a EP-03 y EP-04. EP-01 decide si una persona puede efectuar esas acciones, pero no define sus reglas de negocio.

Para la primera versión se propone acceso mediante una cuenta propia en la aplicación. El ingreso con cuentas de otras plataformas y el acceso de clientes externos quedan pendientes de validación. Ninguna historia supone que una cuenta pueda ver todos los proyectos por defecto.

### 2.3. Mapa de actividades e historias

| Entrega / actividad → | A1. Habilitar cuenta | A2. Entrar y salir | A3. Obtener y encontrar acceso | A4. Actuar con permisos | A5. Mantener y revisar |
| --- | --- | --- | --- | --- | --- |
| **E1. Acceso controlado al primer proyecto** | 001 Registrar cuenta; 002 Asignar función | 003 Iniciar sesión; 004 Cerrar sesión | 005 Dar acceso a un proyecto; 006 Consultar proyectos autorizados | 007 Impedir acciones no autorizadas | — |
| **E2. Administración segura para uso continuo** | — | 011 Restablecer acceso | Se reutilizan 005 y 006 después de cambios | Se reutiliza 007 con permisos actualizados | 008 Cambiar función; 009 Desactivar cuenta; 010 Consultar historial de accesos |

Los números de las tarjetas corresponden al sufijo de `HU-01-xxx`. Cuando una historia se reutiliza en otra actividad, conserva un solo identificador y una sola definición.

**Resultado de E1:** un administrador puede habilitar personas y funciones; un responsable puede conceder acceso al primer proyecto; cada persona ingresa, encuentra sus proyectos y no puede operar fuera de sus permisos. E1 requiere al menos un proyecto creado mediante EP-02 para verificar el recorrido completo.

**Resultado de E2:** la organización puede corregir funciones, desactivar cuentas, restablecer accesos y explicar quién modificó los permisos. E1 y E2 forman el alcance propuesto de EP-01 antes de usar el sistema de manera continua.

### 2.4. Reglas propuestas para redactar los criterios

Estas reglas concretan los ejemplos de aceptación y deben confirmarse con el cliente:

- **RP-01. Permisos por función y proyecto:** una función define acciones posibles; la participación en un proyecto limita dónde pueden realizarse. Tener una función no concede acceso automático a todos los proyectos.
- **RP-02. Acceso denegado por defecto:** si una persona no tiene permiso explícito para ver o modificar un recurso, la acción se rechaza. Esto aplica también al abrir un enlace directo y a los archivos vinculados.
- **RP-03. Cuentas personales:** cada acción se atribuye a una cuenta individual. Cambiar la función o desactivar la cuenta no modifica la autoría de acciones anteriores.
- **RP-04. Cambios de acceso:** una modificación de función o participación debe tener efecto en nuevas consultas y acciones, incluidas las de una sesión que siga abierta. Los cambios anteriores permanecen consultables por personas autorizadas.
- **RP-05. Cuentas inactivas:** una cuenta desactivada no puede iniciar sesión ni ejecutar nuevas acciones. Su historial se conserva.

### 2.5. Historias de usuario — E1: acceso controlado al primer proyecto

#### HU-01-001 — Registrar una cuenta de usuario

**Actividad:** A1. Habilitar cuenta.  
**Historia:** Como administrador, quiero registrar una cuenta para cada integrante que utilizará la aplicación, para darle acceso individual y poder atribuir sus acciones.  
**Dependencias:** ninguna historia funcional previa; requiere definir cómo se entrega el acceso inicial.

**Criterios de aceptación:**

1. Al registrar nombre e identificador de acceso únicos y válidos, se crea una sola cuenta activa y se muestra su estado.
2. Si falta información obligatoria o el identificador ya pertenece a otra cuenta, se informa el problema y no se crea una cuenta duplicada o incompleta.
3. Crear una cuenta no le permite consultar proyectos hasta que reciba la participación correspondiente.

#### HU-01-002 — Asignar una función inicial

**Actividad:** A1. Habilitar cuenta.  
**Historia:** Como administrador, quiero asignar una función inicial a cada cuenta para que sus permisos correspondan al trabajo que realizará.  
**Dependencias:** HU-01-001; catálogo de funciones por confirmar.

**Criterios de aceptación:**

1. Al seleccionar una función válida para una cuenta activa, la cuenta muestra la función asignada.
2. Una función inexistente o no autorizada se rechaza sin alterar los permisos de la cuenta.
3. La función asignada no concede acceso a proyectos en los que la persona no participa, según RP-01.

#### HU-01-003 — Iniciar sesión

**Actividad:** A2. Entrar y salir.  
**Historia:** Como usuario con cuenta activa, quiero ingresar a la aplicación para consultar y realizar mi trabajo autorizado.  
**Dependencias:** HU-01-001 y HU-01-002.

**Criterios de aceptación:**

1. Con datos de acceso válidos de una cuenta activa, se inicia una sesión asociada a esa persona.
2. Con datos incorrectos o una cuenta inactiva, no se concede acceso y se muestra un mensaje que no revela información de otros usuarios.
3. Tras ingresar, las consultas y acciones siguen sujetas a los permisos vigentes; iniciar sesión por sí solo no da acceso a todos los proyectos.

#### HU-01-004 — Cerrar sesión

**Actividad:** A2. Entrar y salir.  
**Historia:** Como usuario, quiero cerrar mi sesión al terminar para impedir que otra persona utilice mi acceso desde ese dispositivo.  
**Dependencias:** HU-01-003.

**Criterios de aceptación:**

1. Al cerrar sesión, la aplicación confirma la salida y deja de permitir operaciones con esa sesión.
2. Intentar abrir después un proyecto protegido exige volver a ingresar.

#### HU-01-005 — Dar acceso a participantes de un proyecto

**Actividad:** A3. Obtener y encontrar acceso.  
**Historia:** Como responsable de proyecto, quiero incorporar o retirar participantes de mi proyecto para que solo las personas indicadas puedan colaborar en él.  
**Dependencias:** HU-01-001, HU-01-002 y creación de proyectos de EP-02.

**Criterios de aceptación:**

1. Al agregar una cuenta activa al proyecto que gestiono, la persona puede encontrarlo y actuar según su función.
2. Al retirar a un participante, este deja de ver el proyecto y de realizar nuevas acciones en él, sin borrar lo que hizo antes.
3. Un responsable no puede modificar los participantes de un proyecto ajeno; la operación se rechaza sin cambios.

#### HU-01-006 — Consultar mis proyectos autorizados

**Actividad:** A3. Obtener y encontrar acceso.  
**Historia:** Como integrante del equipo, quiero ver los proyectos a los que tengo acceso para encontrar mi trabajo sin exponer proyectos de otras personas.  
**Dependencias:** HU-01-003 y HU-01-005.

**Criterios de aceptación:**

1. La consulta muestra los proyectos en los que la persona participa o sobre los que tiene un permiso explícito.
2. Un proyecto sin acceso no aparece en la lista ni en los resultados de búsqueda de esa persona.
3. Si pierde el acceso mientras su sesión sigue abierta, una nueva consulta deja de mostrar el proyecto.

#### HU-01-007 — Impedir acciones no autorizadas

**Actividad:** A4. Actuar con permisos.  
**Historia:** Como responsable de la organización, quiero que el sistema impida consultas y cambios fuera de los permisos asignados para proteger la información y evitar modificaciones indebidas.  
**Dependencias:** HU-01-002, HU-01-005 y acciones de EP-02 a EP-07.

**Criterios de aceptación:**

1. Una persona sin permiso de edición puede consultar lo permitido, pero no guardar cambios en un proyecto o tarea restringidos.
2. Abrir un enlace directo o repetir una solicitud no permite consultar, descargar archivos ni modificar recursos sin permiso.
3. Si el acceso cambia durante una sesión, las acciones posteriores respetan el permiso actualizado, según RP-04.

### 2.6. Historias de usuario — E2: administración segura para uso continuo

#### HU-01-008 — Cambiar la función de una cuenta

**Actividad:** A5. Mantener y revisar.  
**Historia:** Como administrador, quiero cambiar la función de una persona cuando cambien sus responsabilidades para que conserve solo los permisos que necesita.  
**Dependencias:** HU-01-002 y HU-01-007.

**Criterios de aceptación:**

1. Al confirmar una función válida diferente, las nuevas consultas y acciones de esa persona se evalúan con la función actualizada.
2. El cambio conserva quién lo realizó, cuándo y cuál era la función anterior y la nueva.
3. Una persona sin permiso de administración no puede cambiar funciones, ni siquiera la propia.

#### HU-01-009 — Desactivar una cuenta

**Actividad:** A5. Mantener y revisar.  
**Historia:** Como administrador, quiero desactivar una cuenta que ya no debe usar la aplicación para impedir nuevos accesos sin borrar el historial de su trabajo.  
**Dependencias:** HU-01-001 y HU-01-007.

**Criterios de aceptación:**

1. Una cuenta desactivada no puede iniciar sesión ni ejecutar nuevas acciones, aunque hubiera iniciado sesión antes.
2. Sus proyectos, comentarios y cambios anteriores conservan la atribución a esa persona.
3. Desactivar por segunda vez la misma cuenta no produce un estado contradictorio ni elimina información histórica.

#### HU-01-010 — Consultar cambios de acceso

**Actividad:** A5. Mantener y revisar.  
**Historia:** Como administrador, quiero consultar quién cambió las funciones o el acceso a proyectos para aclarar decisiones y detectar modificaciones indebidas.  
**Dependencias:** HU-01-005, HU-01-008 y HU-01-009.

**Criterios de aceptación:**

1. Cada alta, retiro o cambio de acceso muestra la persona afectada, el actor, la fecha y el valor anterior y posterior cuando corresponda.
2. El historial puede consultarse por persona o proyecto, según el tipo de cambio, sin permitir que usuarios no autorizados lo vean.
3. Cambiar o desactivar una cuenta no modifica ni elimina eventos anteriores del historial.

#### HU-01-011 — Restablecer el acceso de una cuenta

**Actividad:** A2. Entrar y salir.  
**Historia:** Como administrador, quiero ayudar a una persona que perdió su acceso para que pueda volver a trabajar sin utilizar la cuenta de otra persona.  
**Dependencias:** HU-01-001 y HU-01-003; procedimiento de verificación de identidad por confirmar.

**Criterios de aceptación:**

1. Solo una persona autorizada puede iniciar el restablecimiento de una cuenta existente y activa.
2. La persona afectada puede ingresar con el acceso renovado; las credenciales anteriores dejan de servir.
3. El restablecimiento conserva los proyectos, permisos y autoría previa de la cuenta, y registra quién lo inició.

### 2.7. Criterios comunes de aceptación

- Los permisos se comprueban al consultar y al modificar información; ocultar un botón no sustituye la restricción de acceso.
- Los mensajes de error explican qué puede hacer el usuario sin revelar nombres, archivos o detalles de proyectos ajenos.
- Los cambios de cuenta o permisos confirmados no se duplican por un reintento; un fallo informa claramente que la acción no se guardó, de acuerdo con EP-08.
- Las tareas principales de esta épica deben poder realizarse y leerse desde computadora y teléfono, sin depender exclusivamente del color para distinguir el acceso.

### 2.8. Trazabilidad con los resultados de EP-01

| Resultado de la épica | Historias que lo cubren |
| --- | --- |
| Una persona autorizada ingresa y encuentra sus proyectos. | HU-01-001 a HU-01-006; HU-01-011 para recuperar acceso. |
| Una persona sin permiso no ve ni modifica proyectos restringidos, incluso por enlace directo. | HU-01-005 a HU-01-008; RP-01 y RP-02. |
| Desactivar una cuenta impide nuevas acciones y conserva la atribución histórica. | HU-01-009 y HU-01-010; RP-03 y RP-05. |

### 2.9. Decisiones pendientes antes de implementar

- ¿Quién será administrador y cómo se habilitará la primera cuenta sin conceder acceso general por accidente?
- ¿Cuáles serán las funciones iniciales y qué acciones podrá realizar cada una?
- ¿Quién podrá dar acceso a un proyecto: solo su responsable, un administrador o ambos?
- ¿La dirección verá todos los proyectos o únicamente los que se le asignen?
- ¿Cómo se entregará el acceso inicial y cómo se verificará la identidad al restablecerlo?
- ¿Qué datos de las cuentas son indispensables y cuánto tiempo se conservará el historial de cambios de acceso?
- ¿Se permitirán clientes o colaboradores externos en la primera versión? Si es así, habrá que ampliar el mapa y las historias de permisos.

## 3. EP-02 — Creación y administración de proyectos

### 3.1. Objetivo, participantes y alcance

**Objetivo:** mantener una ficha única y actualizada de cada proyecto desde su creación hasta su cierre, sin perder los cambios importantes.

**Recorrido principal:** crear el proyecto → consultar su ficha → actualizar el plan y su estado → cerrarlo → recuperar su información histórica.

| Participante | Necesidad |
| --- | --- |
| Responsable de proyecto | Crear y mantener los datos y el estado de sus proyectos. |
| Integrante autorizado | Consultar el objetivo, las fechas y el estado vigentes. |
| Supervisor | Revisar proyectos activos y cerrados según sus permisos. |

Incluye nombre, objetivo, responsable, fechas previstas, participantes visibles, estado, cambios y cierre. La concesión de acceso a participantes pertenece a HU-01-005. La planificación de tareas pertenece a EP-03. No incluye presupuestos, facturación ni subproyectos complejos.

### 3.2. Mapa de actividades e historias

| Entrega / actividad → | A1. Iniciar | A2. Consultar | A3. Mantener el plan | A4. Cerrar | A5. Recuperar |
| --- | --- | --- | --- | --- | --- |
| **E1. Ciclo completo de un proyecto** | 001 Crear proyecto | 002 Consultar ficha | 003 Actualizar datos; 004 Cambiar estado | 005 Cerrar proyecto | 006 Consultar proyecto cerrado e historial |

**Resultado de E1:** un proyecto real puede registrarse, mantenerse actualizado, cerrarse y consultarse después. Su primera operación requiere las cuentas y permisos de EP-01.

### 3.3. Reglas propuestas

- **RP-02-01. Estados:** se propone empezar con *planificado*, *en curso* y *cerrado*. Las etapas y transiciones definitivas las confirmará el cliente.
- **RP-02-02. Cambios históricos:** los cambios de responsable, fechas, objetivo y estado conservan actor, fecha y valores anterior y nuevo.
- **RP-02-03. Cierre:** no se ocultan tareas pendientes al cerrar. Se propone exigir su resolución o una excepción documentada; la política final se confirmará con el cliente.

### 3.4. Historias de usuario

#### HU-02-001 — Crear un proyecto

**Actividad:** A1. Iniciar.  
**Historia:** Como responsable de proyecto, quiero registrar un proyecto con su objetivo, fechas y responsable para reunir su planificación en un lugar identificable.  
**Dependencias:** HU-01-003 y permisos de HU-01-007.

**Criterios de aceptación:**

1. Al confirmar nombre, objetivo, responsable autorizado y fechas válidas, se crea un proyecto con identificador y estado inicial, visible para quien tenga acceso.
2. Si falta un dato obligatorio o la fecha de término precede a la de inicio, se explica el error y no se crea un proyecto incompleto.
3. Reintentar la misma confirmación después de una interrupción no crea otro proyecto por accidente, conforme a EP-08.

#### HU-02-002 — Consultar la ficha de un proyecto

**Actividad:** A2. Consultar.  
**Historia:** Como participante autorizado, quiero consultar la ficha de un proyecto para conocer su propósito, responsable, fechas y estado vigentes.  
**Dependencias:** HU-02-001 y HU-01-006.

**Criterios de aceptación:**

1. La ficha muestra nombre, objetivo, responsable, fechas y estado actuales del proyecto.
2. Una persona sin acceso no puede abrir la ficha mediante la lista, búsqueda o enlace directo.

#### HU-02-003 — Actualizar los datos del proyecto

**Actividad:** A3. Mantener el plan.  
**Historia:** Como responsable de proyecto, quiero modificar los datos del plan cuando cambien las condiciones para que el equipo consulte la versión vigente.  
**Dependencias:** HU-02-001 y HU-01-007.

**Criterios de aceptación:**

1. Un cambio autorizado de objetivo, responsable o fechas válidas se refleja en la ficha y conserva el valor anterior, la fecha y el actor.
2. Un cambio inválido o hecho por una persona sin permiso se rechaza sin alterar el proyecto.
3. Si otra persona modificó el mismo dato antes de guardar, se informa el conflicto y no se sobrescribe silenciosamente su cambio.

#### HU-02-004 — Cambiar el estado del proyecto

**Actividad:** A3. Mantener el plan.  
**Historia:** Como responsable de proyecto, quiero indicar la etapa actual del proyecto para que los participantes sepan si aún se planifica, está en ejecución o ha terminado.  
**Dependencias:** HU-02-001; estados finales por confirmar.

**Criterios de aceptación:**

1. Al confirmar una transición permitida, la ficha y las consultas muestran el nuevo estado con actor y fecha.
2. Un estado inexistente o una transición no permitida se rechaza sin cambiar el estado anterior.
3. La transición a cerrado sigue el procedimiento de HU-02-005 y no omite su revisión de pendientes.

#### HU-02-005 — Cerrar un proyecto

**Actividad:** A4. Cerrar.  
**Historia:** Como responsable de proyecto, quiero cerrar un proyecto cuando el trabajo concluya para distinguirlo de los proyectos en curso sin perder su información.  
**Dependencias:** HU-02-004 y tareas de EP-03/EP-04 cuando existan.

**Criterios de aceptación:**

1. Antes de cerrar, se muestran las tareas que continúan abiertas y se aplica la política acordada para resolverlas o documentar una excepción.
2. Al confirmar el cierre se registra fecha y responsable; el proyecto deja de aparecer como activo, pero mantiene tareas, archivos e historial.
3. Repetir la solicitud de cierre no duplica el evento ni elimina información.

#### HU-02-006 — Consultar un proyecto cerrado y sus cambios

**Actividad:** A5. Recuperar.  
**Historia:** Como supervisor autorizado, quiero consultar los proyectos cerrados y sus cambios relevantes para explicar qué se acordó y cómo terminaron.  
**Dependencias:** HU-02-003 a HU-02-005 y permisos de EP-01.

**Criterios de aceptación:**

1. Una consulta de proyectos cerrados permite abrir la ficha, las tareas y los archivos conservados, según permisos.
2. El historial muestra cambios de responsable, fechas, objetivo y estado con actor, fecha y valores anterior y nuevo.
3. Cerrar el proyecto no modifica silenciosamente el historial ni concede acceso a personas ajenas.

### 3.5. Trazabilidad y decisiones pendientes

| Resultado de EP-02 | Historias |
| --- | --- |
| El proyecto tiene objetivo, responsable, fechas y estado en un lugar. | HU-02-001, HU-02-002 y HU-02-004. |
| Los cambios confirmados son visibles y explicables. | HU-02-003, HU-02-004 y HU-02-006. |
| El cierre conserva trabajo e historial. | HU-02-005 y HU-02-006. |

**Por confirmar:** estados y etapas reales; campos obligatorios; quién puede cambiar responsable o fechas; tratamiento de tareas abiertas al cierre; si se permitirá reabrir un proyecto cerrado.

## 4. EP-03 — Planificación y asignación de tareas

### 4.1. Objetivo, participantes y alcance

**Objetivo:** convertir cada proyecto en tareas concretas con responsables, prioridades y fechas que el equipo pueda consultar.

**Recorrido principal:** descomponer el trabajo → asignar responsables → ordenar por prioridad y fecha → consultar pendientes → ajustar el plan.

| Participante | Necesidad |
| --- | --- |
| Responsable de proyecto | Crear, asignar y replanificar tareas de su proyecto. |
| Integrante del equipo | Encontrar sus tareas y comprender el resultado esperado. |

Incluye descripción y resultado esperado, responsable, prioridad, fecha límite, listado por persona y proyecto, y cambios del plan. El avance y los bloqueos pertenecen a EP-04; los tableros y resúmenes generales, a EP-07. La relación de dependencia entre tareas se añadirá si se confirma como indispensable.

### 4.2. Mapa de actividades e historias

| Entrega / actividad → | A1. Descomponer | A2. Asignar y ordenar | A3. Consultar | A4. Ajustar |
| --- | --- | --- | --- | --- |
| **E1. Plan de tareas utilizable** | 001 Crear tarea | 002 Asignar responsable; 003 Definir fecha y prioridad | 004 Consultar mis tareas; 005 Revisar tareas del proyecto | 006 Replanificar tarea |

**Resultado de E1:** el responsable distribuye tareas y cada integrante sabe qué debe hacer y cuándo. El proyecto y sus participantes deben existir mediante EP-01 y EP-02.

### 4.3. Reglas propuestas

- **RP-03-01. Pertenencia:** cada tarea pertenece a un solo proyecto y solo puede asignarse a una persona con acceso a él. La posibilidad de varios responsables queda pendiente.
- **RP-03-02. Plan vigente e historial:** cambios de responsable, fecha y prioridad conservan el valor anterior y quién los confirmó.
- **RP-03-03. Vencimiento:** la fecha límite se interpreta en la zona horaria acordada para la organización; la política sobre tareas sin fecha debe confirmarse.

### 4.4. Historias de usuario

#### HU-03-001 — Crear una tarea

**Actividad:** A1. Descomponer.  
**Historia:** Como responsable de proyecto, quiero crear tareas con una descripción y un resultado esperado para convertir el objetivo del proyecto en trabajo realizable.  
**Dependencias:** proyecto de HU-02-001 y permisos de EP-01.

**Criterios de aceptación:**

1. Al confirmar nombre y descripción válidos, la tarea se crea dentro del proyecto seleccionado con un identificador y estado inicial.
2. Una persona sin permiso para planificar ese proyecto no puede crear tareas en él.
3. Un reintento de la misma creación no duplica la tarea.

#### HU-03-002 — Asignar responsable a una tarea

**Actividad:** A2. Asignar y ordenar.  
**Historia:** Como responsable de proyecto, quiero asignar cada tarea a una persona para que quede claro quién debe atenderla.  
**Dependencias:** HU-03-001 y participación de HU-01-005.

**Criterios de aceptación:**

1. Al asignar una cuenta activa con acceso al proyecto, la tarea muestra a esa persona como responsable y aparece entre sus pendientes.
2. Se rechaza la asignación a una cuenta inactiva o ajena al proyecto, sin alterar al responsable anterior.
3. Cambiar el responsable conserva el anterior, el nuevo, la fecha y quien realizó la acción.

#### HU-03-003 — Definir fecha límite y prioridad

**Actividad:** A2. Asignar y ordenar.  
**Historia:** Como responsable de proyecto, quiero señalar la fecha límite y la prioridad de una tarea para ayudar al equipo a ordenar el trabajo.  
**Dependencias:** HU-03-001; escala de prioridades por confirmar.

**Criterios de aceptación:**

1. La tarea muestra la fecha y la prioridad confirmadas junto a su descripción y responsable.
2. Una fecha inválida o una prioridad ajena a las opciones acordadas impide guardar el cambio y explica qué corregir.
3. Al modificar estos valores, se conserva el registro del valor anterior y el actor.

#### HU-03-004 — Consultar mis tareas

**Actividad:** A3. Consultar.  
**Historia:** Como integrante del equipo, quiero consultar las tareas que me asignaron para organizar mi jornada sin revisar proyecto por proyecto.  
**Dependencias:** HU-03-002 y acceso de EP-01.

**Criterios de aceptación:**

1. La consulta reúne mis tareas de los proyectos a los que aún tengo acceso y muestra proyecto, estado, prioridad y fecha límite.
2. Una tarea que deja de estar asignada a mi cuenta o cuyo proyecto deja de ser accesible ya no aparece en una nueva consulta.
3. Puedo abrir el detalle de una tarea mostrada sin volver a buscarla en el proyecto.

#### HU-03-005 — Revisar las tareas de un proyecto

**Actividad:** A3. Consultar.  
**Historia:** Como responsable de proyecto, quiero ver las tareas de mi proyecto para comprobar que el trabajo previsto está distribuido.  
**Dependencias:** HU-03-001 y HU-01-006.

**Criterios de aceptación:**

1. La lista muestra tareas del proyecto con responsable, prioridad, fecha y estado; las no asignadas se distinguen claramente.
2. Las tareas de otros proyectos no se mezclan en esta lista y siguen sujetas a permisos de acceso.

#### HU-03-006 — Replanificar una tarea

**Actividad:** A4. Ajustar.  
**Historia:** Como responsable de proyecto, quiero cambiar la asignación, fecha o prioridad de una tarea cuando el plan cambie para que el equipo trabaje con información vigente.  
**Dependencias:** HU-03-002 y HU-03-003.

**Criterios de aceptación:**

1. Los cambios confirmados aparecen en el detalle y en las consultas por persona y proyecto.
2. El historial conserva qué cambió, quién lo cambió y cuándo; el cambio de responsable no borra avances previos.
3. Si otra persona modificó el mismo dato antes de confirmar, se informa el conflicto y no se sobrescribe silenciosamente.

### 4.5. Trazabilidad y decisiones pendientes

| Resultado de EP-03 | Historias |
| --- | --- |
| Cada tarea pertenece a un proyecto y tiene trabajo identificable. | HU-03-001 y HU-03-005. |
| Responsable, prioridad y fecha son claros y consultables. | HU-03-002 a HU-03-005. |
| Los cambios del plan muestran el valor vigente y conservan autoría. | HU-03-002, HU-03-003 y HU-03-006. |

**Por confirmar:** campos obligatorios; si se admiten tareas sin responsable o sin fecha; escala de prioridad; zona horaria; varios responsables; dependencias entre tareas y reglas para tareas de proyectos cerrados.

## 5. EP-04 — Actualización del trabajo y gestión de bloqueos

### 5.1. Objetivo, participantes y alcance

**Objetivo:** reflejar el avance real, los impedimentos y los retrasos de las tareas para que el equipo pueda actuar con información actualizada.

**Recorrido principal:** comenzar el trabajo → informar avances → señalar un bloqueo → resolverlo → revisar vencimientos e historial → terminar la tarea.

| Participante | Necesidad |
| --- | --- |
| Integrante asignado | Actualizar el estado, explicar avances y señalar impedimentos. |
| Responsable de proyecto | Detectar retrasos, atender bloqueos y comprobar cómo evolucionó el trabajo. |

Incluye cambios de estado, notas de avance, bloqueos, resolución, tareas vencidas e historial de la tarea. Las fechas previstas se definen en EP-03; los avisos se gestionan en EP-06. La aprobación formal de entregables queda condicionada a la entrevista.

### 5.2. Mapa de actividades e historias

| Entrega / actividad → | A1. Actualizar | A2. Explicar | A3. Señalar impedimento | A4. Resolver | A5. Revisar |
| --- | --- | --- | --- | --- | --- |
| **E1. Seguimiento completo de tareas** | 001 Cambiar estado | 002 Registrar avance | 003 Registrar bloqueo | 004 Resolver bloqueo | 005 Identificar vencidas; 006 Consultar historial |

**Resultado de E1:** el responsable distingue tareas pendientes, en curso, terminadas, bloqueadas y vencidas, y puede explicar los cambios. Requiere tareas de EP-03.

### 5.3. Reglas propuestas

- **RP-04-01. Estado y bloqueo:** el estado de trabajo y la existencia de un bloqueo se registran por separado; una tarea puede estar en curso y bloqueada al mismo tiempo.
- **RP-04-02. Vencimiento:** una tarea no terminada queda vencida después de su fecha límite. El vencimiento no cambia por sí mismo el estado ni altera la fecha original.
- **RP-04-03. Historial:** los cambios confirmados de estado y bloqueo conservan actor, fecha y motivo cuando corresponda. No se borran al reasignar una tarea.

### 5.4. Historias de usuario

#### HU-04-001 — Cambiar el estado de una tarea

**Actividad:** A1. Actualizar.  
**Historia:** Como integrante asignado, quiero actualizar el estado de mi tarea para que el equipo conozca si está pendiente, en curso o terminada.  
**Dependencias:** tarea asignada de EP-03 y permisos de EP-01.

**Criterios de aceptación:**

1. Una transición permitida cambia el estado visible en el detalle y las consultas, y registra quién y cuándo la confirmó.
2. Una persona no autorizada o una transición no permitida no modifica el estado; la aplicación explica el motivo.
3. Marcar la tarea como terminada no cierra automáticamente el proyecto ni elimina un bloqueo sin resolver.

#### HU-04-002 — Registrar un avance

**Actividad:** A2. Explicar.  
**Historia:** Como integrante asignado, quiero dejar una actualización breve de mi avance para que el responsable entienda qué se ha hecho y qué falta.  
**Dependencias:** HU-04-001.

**Criterios de aceptación:**

1. Una actualización confirmada queda vinculada a la tarea con texto, autor y fecha.
2. El responsable del proyecto puede leer las actualizaciones en orden y distinguirlas de los cambios de estado.
3. Una actualización fallida no aparece como guardada, conforme a EP-08.

#### HU-04-003 — Registrar un bloqueo

**Actividad:** A3. Señalar impedimento.  
**Historia:** Como integrante asignado, quiero informar que una tarea está bloqueada y explicar por qué para que el responsable pueda ayudar a resolverla.  
**Dependencias:** HU-03-001 y permisos de EP-01.

**Criterios de aceptación:**

1. Al confirmar un motivo no vacío, la tarea muestra un bloqueo abierto con autor y fecha.
2. El bloqueo aparece en las consultas de tareas que requieren atención, sin reemplazar el estado de trabajo.
3. Repetir el envío de la misma operación no abre dos bloqueos idénticos por accidente.

#### HU-04-004 — Resolver un bloqueo

**Actividad:** A4. Resolver.  
**Historia:** Como responsable de proyecto, quiero registrar que un bloqueo se resolvió y cómo se resolvió para que el equipo pueda continuar con claridad.  
**Dependencias:** HU-04-003.

**Criterios de aceptación:**

1. Resolver un bloqueo abierto exige una explicación y conserva quién lo resolvió y cuándo.
2. El bloqueo deja de aparecer como pendiente, pero su motivo y resolución siguen en el historial.
3. Intentar resolver un bloqueo ya cerrado no crea una segunda resolución ni cambia su historia.

#### HU-04-005 — Identificar tareas vencidas

**Actividad:** A5. Revisar.  
**Historia:** Como responsable de proyecto, quiero identificar las tareas cuyo plazo terminó y siguen abiertas para decidir qué atender primero.  
**Dependencias:** fecha límite de HU-03-003 y estado de HU-04-001.

**Criterios de aceptación:**

1. Una tarea no terminada cuya fecha límite ya pasó se distingue como vencida en las consultas autorizadas.
2. Una tarea terminada antes del plazo no aparece como vencida; reprogramar una tarea actualiza la evaluación sin borrar la fecha anterior del historial.
3. La marca de vencimiento no cambia por sí sola el estado ni el responsable.

#### HU-04-006 — Consultar el historial de una tarea

**Actividad:** A5. Revisar.  
**Historia:** Como responsable de proyecto, quiero revisar los cambios y avances de una tarea para comprender por qué está en su situación actual.  
**Dependencias:** HU-03-006 y las historias que registran avances o bloqueos.

**Criterios de aceptación:**

1. El historial muestra cambios de responsable, fecha, prioridad y estado, así como avances, bloqueos y resoluciones, con actor y fecha.
2. Las entradas se presentan en orden y una reasignación no elimina las anteriores.
3. Una persona sin acceso al proyecto no puede consultar el historial mediante un enlace directo.

### 5.5. Trazabilidad y decisiones pendientes

| Resultado de EP-04 | Historias |
| --- | --- |
| El avance confirmado aparece en las consultas. | HU-04-001 y HU-04-002. |
| Los bloqueos y vencimientos requieren atención visible. | HU-04-003 a HU-04-005. |
| Los cambios importantes conservan responsable y fecha. | HU-04-001, HU-04-004 y HU-04-006. |

**Por confirmar:** estados y transiciones exactas; quién puede marcar una tarea como terminada; si se requieren aprobaciones de entregables; cómo tratar varios bloqueos simultáneos; si se registrará porcentaje de avance.

## 6. EP-05 — Colaboración y archivos del proyecto

### 6.1. Objetivo, participantes y alcance

**Objetivo:** conservar comentarios y documentos junto al proyecto o tarea que les da contexto, con acceso limitado a las personas autorizadas.

**Recorrido principal:** conversar sobre el trabajo → adjuntar un archivo → consultar el contexto → corregir contenido equivocado sin ocultar lo sucedido.

| Participante | Necesidad |
| --- | --- |
| Integrante del equipo | Plantear dudas, compartir decisiones o entregar archivos de sus tareas. |
| Responsable de proyecto | Consultar y responder el contexto de proyectos y tareas. |

Incluye comentarios y archivos vinculados a un proyecto o una tarea, identificación de autor y fecha, consulta y corrección controlada. No incluye chat independiente, edición simultánea de documentos ni intercambio con personas sin acceso al proyecto.

### 6.2. Mapa de actividades e historias

| Entrega / actividad → | A1. Conversar | A2. Adjuntar | A3. Consultar | A4. Corregir |
| --- | --- | --- | --- | --- |
| **E1. Contexto compartido del trabajo** | 001 Comentar proyecto o tarea | 002 Adjuntar archivo | 003 Consultar comentarios y archivos | 004 Corregir contenido propio |

**Resultado de E1:** una persona autorizada puede dejar y encontrar contexto en el lugar correcto; cambiar de responsable no borra la conversación ni los documentos.

### 6.3. Reglas propuestas

- **RP-05-01. Contexto:** cada comentario o archivo pertenece a un proyecto o a una tarea de ese proyecto; no queda como elemento suelto.
- **RP-05-02. Acceso:** el acceso a comentarios y archivos sigue los permisos del proyecto de EP-01, también al abrir un enlace o descargar.
- **RP-05-03. Corrección:** se propone conservar constancia de una edición o retiro de contenido, especialmente si otras personas ya lo consultaron. La política de conservación se confirmará con el cliente.

### 6.4. Historias de usuario

#### HU-05-001 — Comentar un proyecto o una tarea

**Actividad:** A1. Conversar.  
**Historia:** Como participante autorizado, quiero comentar en el proyecto o la tarea correspondiente para que las dudas y decisiones permanezcan junto al trabajo.  
**Dependencias:** proyecto de EP-02, tarea de EP-03 cuando corresponda y acceso de EP-01.

**Criterios de aceptación:**

1. Un comentario no vacío se guarda en el proyecto o tarea elegido con autor y fecha.
2. Los comentarios se muestran en orden y no cambian de autor si la tarea se reasigna.
3. Una persona sin acceso no puede publicar ni leer comentarios en ese proyecto, incluso mediante enlace directo.

#### HU-05-002 — Adjuntar un archivo

**Actividad:** A2. Adjuntar.  
**Historia:** Como participante autorizado, quiero adjuntar un archivo a un proyecto o tarea para que el equipo encuentre el material relevante en su contexto.  
**Dependencias:** EP-01, EP-02 y EP-03 cuando el destino sea una tarea.

**Criterios de aceptación:**

1. Un archivo permitido queda vinculado al destino elegido y muestra nombre, autor y fecha.
2. Un archivo que excede los límites acordados o no puede guardarse produce un error claro y no aparece como adjunto disponible.
3. Reintentar una carga interrumpida no crea dos adjuntos por accidente.

#### HU-05-003 — Consultar comentarios y archivos

**Actividad:** A3. Consultar.  
**Historia:** Como integrante autorizado, quiero encontrar y abrir los comentarios y archivos de una tarea o proyecto para conocer el contexto antes de continuar.  
**Dependencias:** HU-05-001 y HU-05-002.

**Criterios de aceptación:**

1. Desde el proyecto o tarea se muestran sus comentarios y archivos, sin mezclar contenido de otro proyecto.
2. Un archivo autorizado puede abrirse o descargarse; una persona que perdió el acceso no puede hacerlo desde un enlace anterior.
3. La reasignación de una tarea conserva su conversación y archivos para los participantes que sigan autorizados.

#### HU-05-004 — Corregir contenido publicado por error

**Actividad:** A4. Corregir.  
**Historia:** Como autor autorizado, quiero corregir un comentario o retirar un archivo publicado por error para evitar confusiones sin ocultar que hubo un cambio.  
**Dependencias:** HU-05-001 a HU-05-003; política de conservación por confirmar.

**Criterios de aceptación:**

1. Solo el autor o una persona con permiso de administración acordado puede corregir o retirar contenido.
2. La consulta distingue el contenido vigente de un elemento retirado o editado y conserva actor y fecha del cambio.
3. Un intento no autorizado se rechaza y no altera el contenido visible.

### 6.5. Trazabilidad y decisiones pendientes

| Resultado de EP-05 | Historias |
| --- | --- |
| Comentarios y archivos se encuentran desde su proyecto o tarea. | HU-05-001 a HU-05-003. |
| Solo personas autorizadas pueden acceder al contenido. | HU-05-001 a HU-05-004; RP-05-02. |
| La conversación conserva orden y autoría al cambiar responsables. | HU-05-001, HU-05-003 y HU-05-004. |

**Por confirmar:** tipos y tamaños permitidos; límite total de almacenamiento; quién puede editar o retirar contenido; cuánto tiempo se conserva el contenido retirado; necesidad de archivos en proyectos cerrados.

## 7. EP-06 — Avisos sobre eventos importantes

### 7.1. Objetivo, participantes y alcance

**Objetivo:** hacer visibles a tiempo los cambios y pendientes que requieren una acción, sin saturar al equipo con avisos repetidos.

**Recorrido principal:** ocurre un evento relevante → se identifica a quien debe atenderlo → la persona recibe el aviso → abre el proyecto o tarea y actúa.

| Participante | Necesidad |
| --- | --- |
| Integrante asignado | Enterarse de nuevas tareas, cambios importantes y plazos próximos. |
| Responsable de proyecto | Conocer bloqueos y vencimientos que requieren intervención. |

Incluye avisos dentro de la aplicación por asignación, vencimiento, bloqueo y cambio relevante, así como su consulta y acceso al origen. No incluye correo, SMS ni notificaciones externas al navegador en esta propuesta.

### 7.2. Mapa de actividades e historias

| Entrega / actividad → | A1. Asignar | A2. Vigilar plazos | A3. Señalar bloqueo | A4. Cambiar el plan | A5. Consultar y actuar |
| --- | --- | --- | --- | --- | --- |
| **E1. Avisos ligados al trabajo inmediato** | 001 Avisar nueva asignación | — | 003 Avisar bloqueo | — | 005 Consultar y abrir avisos |
| **E2. Seguimiento preventivo** | Se reutiliza 001 | 002 Avisar vencimiento | Se reutiliza 003 | 004 Avisar cambio relevante | Se reutiliza 005 |

**Resultado de E1:** una persona encuentra sus nuevas tareas y el responsable conoce los bloqueos desde un aviso visible. **Resultado de E2:** se añaden plazos y cambios del plan; E1 y E2 forman el alcance propuesto de la primera versión.

### 7.3. Reglas propuestas

- **RP-06-01. Destinatario:** cada tipo de evento tiene destinatarios definidos; el aviso no concede acceso al proyecto por sí mismo.
- **RP-06-02. No duplicación:** un mismo evento confirmado produce como máximo un aviso de ese tipo para cada destinatario. La frecuencia de recordatorios posteriores se acordará con el cliente.
- **RP-06-03. Permisos vigentes:** si una persona pierde acceso antes de abrir un aviso, no podrá ver el contenido protegido ni entrar al proyecto desde él.

### 7.4. Historias de usuario

#### HU-06-001 — Recibir un aviso de nueva asignación

**Actividad:** A1. Asignar.  
**Historia:** Como integrante del equipo, quiero enterarme cuando me asignen una tarea para incorporarla a mi trabajo pendiente.  
**Dependencias:** asignación de HU-03-002 y acceso de EP-01.

**Criterios de aceptación:**

1. Una asignación confirmada produce un aviso visible para la nueva persona responsable con tarea, proyecto y fecha.
2. Un reintento de la asignación no crea avisos duplicados por el mismo evento.
3. Si la asignación falla, no se muestra un aviso de una tarea que no quedó asignada.

#### HU-06-002 — Recibir un aviso de vencimiento cercano

**Actividad:** A2. Vigilar plazos.  
**Historia:** Como integrante asignado, quiero recibir un aviso antes del vencimiento de una tarea abierta para poder atenderla a tiempo.  
**Dependencias:** fecha de HU-03-003 y estado de HU-04-001.

**Criterios de aceptación:**

1. Al entrar una tarea abierta en el plazo de anticipación acordado, su responsable recibe un aviso con la fecha vigente.
2. Una tarea terminada no genera nuevos avisos de vencimiento; al reprogramarla, los avisos futuros usan la fecha nueva.
3. El mismo vencimiento no genera avisos repetidos sin una regla de recordatorio acordada.

#### HU-06-003 — Avisar un bloqueo al responsable

**Actividad:** A3. Señalar bloqueo.  
**Historia:** Como responsable de proyecto, quiero recibir un aviso cuando una tarea quede bloqueada para intervenir sin esperar a la siguiente reunión.  
**Dependencias:** bloqueo de HU-04-003.

**Criterios de aceptación:**

1. Un bloqueo confirmado produce un aviso para el responsable autorizado del proyecto que identifica la tarea afectada.
2. El aviso abre el bloqueo para consultar su motivo, sujeto a los permisos vigentes.
3. Resolver el bloqueo no elimina el historial del aviso, aunque deje de figurar como pendiente de atención.

#### HU-06-004 — Avisar un cambio relevante del plan

**Actividad:** A4. Cambiar el plan.  
**Historia:** Como integrante afectado, quiero saber cuando cambien mi asignación o la fecha de una tarea para trabajar con el plan vigente.  
**Dependencias:** cambios de HU-03-006 y permisos de EP-01.

**Criterios de aceptación:**

1. Un cambio confirmado de responsable o fecha produce un aviso para las personas afectadas que aún tengan acceso, según la regla acordada.
2. El aviso identifica qué cambió y enlaza con la tarea vigente; un cambio no confirmado no genera aviso.
3. Un reintento del mismo cambio no duplica los avisos.

#### HU-06-005 — Consultar y abrir mis avisos

**Actividad:** A5. Consultar y actuar.  
**Historia:** Como usuario, quiero consultar mis avisos y abrir el trabajo relacionado para saber qué ocurrió y actuar.  
**Dependencias:** HU-06-001 a HU-06-004.

**Criterios de aceptación:**

1. La consulta muestra mis avisos en orden, permite distinguir los pendientes de los ya vistos y señala su motivo y fecha.
2. Al abrir un aviso con acceso vigente, se muestra el proyecto o tarea relacionado.
3. Si el acceso fue retirado, el enlace no revela información protegida y el aviso se trata según la política acordada.

### 7.5. Trazabilidad y decisiones pendientes

| Resultado de EP-06 | Historias |
| --- | --- |
| Una asignación nueva produce un aviso útil. | HU-06-001 y HU-06-005. |
| Vencimientos y bloqueos llegan a quien debe actuar. | HU-06-002, HU-06-003 y HU-06-005. |
| Un cambio relevante se comunica sin duplicados y conduce al origen. | HU-06-004, HU-06-005 y RP-06-02. |

**Por confirmar:** destinatarios de cada evento; anticipación y horario de vencimientos; reglas de recordatorio; qué cambios del plan merecen aviso; tratamiento de avisos cuando se retira el acceso.

## 8. EP-07 — Consulta del avance e informes

### 8.1. Objetivo, participantes y alcance

**Objetivo:** ofrecer una visión confiable y actualizada del trabajo para detectar pendientes, retrasos y bloqueos, y llegar desde cualquier resumen a las tareas que lo explican.

**Recorrido principal:** ver las tareas del proyecto por estado → filtrar lo que interesa → revisar el resumen del proyecto → comparar la carga por responsable → consultar el estado general de los proyectos → abrir el detalle que sustenta cada dato.

| Participante | Necesidad |
| --- | --- |
| Responsable de proyecto | Identificar qué está pendiente, en curso, vencido o bloqueado en su proyecto y quién lo atiende. |
| Supervisor o dirección | Conocer el estado general de los proyectos autorizados y profundizar en los que presentan retrasos. |
| Integrante del equipo | Ubicar el trabajo del proyecto por estado o fecha, según sus permisos. |

Incluye tablero o lista de tareas por estado, filtros básicos, resumen por proyecto, resumen por responsable, vista general de proyectos y paso del resumen al detalle. La lista simple de tareas de un proyecto pertenece a HU-03-005; esta épica la amplía con agrupaciones, indicadores y filtros. Los estados, bloqueos y vencimientos provienen de EP-04. No incluye análisis financiero, predicción de fechas, exportación a otros formatos ni reportes a medida ilimitados.

### 8.2. Mapa de actividades e historias

| Entrega / actividad → | A1. Ver por estado | A2. Filtrar | A3. Resumir el proyecto | A4. Revisar responsables | A5. Supervisar proyectos |
| --- | --- | --- | --- | --- | --- |
| **E1. Seguimiento del proyecto** | 001 Consultar tablero de tareas | 002 Filtrar tareas | 003 Consultar resumen del proyecto | — | — |
| **E2. Visión de supervisión** | Se reutiliza 001 | Se reutiliza 002 | Se reutiliza 003 | 004 Consultar carga por responsable | 005 Consultar estado general de los proyectos |

**Resultado de E1:** el responsable identifica en cada proyecto qué tareas están pendientes, en curso, terminadas, vencidas o bloqueadas, y abre la tarea que explica cada cifra. Requiere estados, bloqueos y vencimientos de EP-04. **Resultado de E2:** la dirección revisa la distribución del trabajo y el estado de los proyectos que tiene autorizados; E1 y E2 forman el alcance propuesto de la primera versión.

### 8.3. Reglas propuestas

- **RP-07-01. Una sola fuente:** todas las vistas y resúmenes se calculan a partir de la información confirmada de proyectos y tareas; una tarea no puede aparecer con estados, responsables o fechas distintos en dos vistas.
- **RP-07-02. Resúmenes con permisos:** los conteos e indicadores consideran solo los proyectos y tareas a los que la persona tiene acceso; un total no revela la existencia de información restringida.
- **RP-07-03. Del resumen al detalle:** cada cifra o indicador permite abrir la lista de tareas que la componen. Se propone señalar un proyecto como *requiere atención* cuando tenga al menos una tarea vencida o bloqueada; el criterio definitivo lo confirmará el cliente.

### 8.4. Historias de usuario

#### HU-07-001 — Consultar el tablero de tareas de un proyecto

**Actividad:** A1. Ver por estado.  
**Historia:** Como responsable de proyecto, quiero ver las tareas de mi proyecto agrupadas por estado para entender de un vistazo cómo avanza el trabajo.  
**Dependencias:** HU-03-005 y estados de HU-04-001.

**Criterios de aceptación:**

1. Las tareas del proyecto se muestran agrupadas por estado con responsable, prioridad y fecha límite; las vencidas y bloqueadas se distinguen con texto o símbolo, no solo con color.
2. Un cambio de estado confirmado en EP-04 aparece en el grupo correspondiente en la siguiente consulta, sin que la tarea figure en dos grupos a la vez.
3. La vista puede leerse y usarse desde un teléfono, aunque su presentación cambie a una lista.

#### HU-07-002 — Filtrar las tareas

**Actividad:** A2. Filtrar.  
**Historia:** Como responsable de proyecto, quiero filtrar las tareas por estado, responsable, prioridad o fecha límite para concentrarme en lo que necesito revisar.  
**Dependencias:** HU-07-001.

**Criterios de aceptación:**

1. Al aplicar uno o varios filtros, se muestran solo las tareas que cumplen todos y se indica qué filtros están activos.
2. Si ninguna tarea cumple los filtros, se informa claramente y los filtros pueden quitarse con una sola acción.
3. Ninguna combinación de filtros muestra tareas de proyectos sin autorización.

#### HU-07-003 — Consultar el resumen de un proyecto

**Actividad:** A3. Resumir el proyecto.  
**Historia:** Como responsable de proyecto, quiero ver cuántas tareas están pendientes, en curso, terminadas, vencidas y bloqueadas para detectar retrasos sin revisar tarea por tarea.  
**Dependencias:** HU-04-001, HU-04-003 y HU-04-005.

**Criterios de aceptación:**

1. El resumen muestra los conteos por estado, las tareas vencidas y bloqueadas, y las próximas fechas límite del proyecto.
2. Cada conteo abre la lista de tareas que lo componen y coincide con lo que muestra el tablero de HU-07-001.
3. El resumen refleja los cambios confirmados; una actualización fallida no altera las cifras, conforme a EP-08.

#### HU-07-004 — Consultar la carga por responsable

**Actividad:** A4. Revisar responsables.  
**Historia:** Como responsable de proyecto o supervisor, quiero ver cuántas tareas abiertas, vencidas y bloqueadas tiene cada persona para equilibrar el trabajo y detectar sobrecargas.  
**Dependencias:** HU-03-002 y HU-07-003.

**Criterios de aceptación:**

1. Para cada persona con tareas en los proyectos autorizados se muestran sus tareas abiertas, vencidas y bloqueadas, y es posible abrirlas.
2. Las tareas sin responsable se presentan por separado para que no queden ocultas.
3. Los conteos solo incluyen proyectos a los que quien consulta tiene acceso; las tareas de otros proyectos no se suman a lo que ve.

#### HU-07-005 — Consultar el estado general de los proyectos

**Actividad:** A5. Supervisar proyectos.  
**Historia:** Como supervisor o miembro de la dirección, quiero consultar el estado de los proyectos que tengo autorizados para identificar cuáles requieren atención y profundizar en ellos.  
**Dependencias:** HU-02-002, HU-07-003 y permisos de EP-01.

**Criterios de aceptación:**

1. La vista lista cada proyecto autorizado con responsable, estado, fecha prevista de término y cantidad de tareas vencidas y bloqueadas; los que requieren atención se distinguen según RP-07-03.
2. Desde cada proyecto puede abrirse su resumen y, desde él, las tareas que explican cada dato.
3. Los proyectos cerrados pueden incluirse o excluirse de la consulta, y los proyectos sin autorización no aparecen ni se cuentan.

### 8.5. Trazabilidad y decisiones pendientes

| Resultado de EP-07 | Historias |
| --- | --- |
| Un responsable identifica las tareas pendientes, vencidas o bloqueadas de cada proyecto. | HU-07-001 a HU-07-003. |
| La dirección consulta el estado general y abre el detalle que sustenta cada resumen. | HU-07-003, HU-07-005 y RP-07-03. |
| Los resúmenes reflejan los cambios confirmados y respetan los permisos. | HU-07-002 a HU-07-005; RP-07-01 y RP-07-02. |

**Por confirmar:** métricas indispensables para la dirección; criterio para marcar un proyecto como *requiere atención*; si se necesita porcentaje de avance o bastan los conteos; necesidad de exportar o imprimir informes; si la dirección verá todos los proyectos o solo los asignados (ver EP-01).

## 9. EP-08 — Conservación y recuperación de la información

### 9.1. Objetivo, participantes y alcance

**Objetivo:** que cada persona sepa si su acción se guardó, que el trabajo confirmado no se pierda ni se duplique y que la organización pueda retomar sus actividades después de un fallo.

**Recorrido principal:** confirmar una acción → reintentarla tras una interrupción sin duplicarla → resolver un cambio simultáneo → respaldar la información → restaurarla y verificar el resultado.

| Participante | Necesidad |
| --- | --- |
| Cualquier usuario | Saber con certeza si su cambio quedó guardado y poder reintentar sin crear duplicados. |
| Responsable de proyecto | Evitar que dos personas sobrescriban sin aviso los datos de un proyecto o de una tarea. |
| Administrador de la organización | Contar con respaldos y comprobar que la información puede recuperarse dentro de los límites acordados. |

Incluye confirmación de guardado o error, protección frente a envíos repetidos y cambios simultáneos, respaldos periódicos y pruebas de restauración. Esta épica atraviesa todas las demás: además de sus historias, aporta los criterios compartidos de la sección 9.5, a los que remiten las historias de EP-01 a EP-07 cuando indican «conforme a EP-08». No incluye funcionamiento sin conexión ni recuperación de información que nunca llegó a confirmarse.

### 9.2. Mapa de actividades e historias

| Entrega / actividad → | A1. Confirmar | A2. Reintentar | A3. Resolver conflictos | A4. Respaldar | A5. Restaurar |
| --- | --- | --- | --- | --- | --- |
| **E1. Guardado confiable en el uso diario** | 001 Saber si una acción se guardó | 002 Reintentar sin duplicar | 003 Evitar sobrescribir cambios ajenos | — | — |
| **E2. Continuidad ante fallos** | — | — | — | 004 Respaldar la información | 005 Restaurar y verificar la recuperación |

**Resultado de E1:** ninguna acción se presenta como guardada si falló, un reintento no genera duplicados y los cambios simultáneos no se pierden en silencio. Se verifica junto con las historias de EP-01 a EP-07. **Resultado de E2:** la organización puede recuperar la información confirmada dentro de los límites acordados y lo comprueba con una prueba de restauración; E1 y E2 forman el alcance propuesto de la primera versión.

### 9.3. Reglas propuestas

- **RP-08-01. Confirmación explícita:** una acción solo se presenta como guardada después de que el sistema la confirma; mientras tanto se muestra en proceso, y un fallo se comunica junto con lo que el usuario puede hacer.
- **RP-08-02. Operación única:** cada envío de creación o modificación puede reconocerse si se repite; el mismo envío produce como máximo un resultado.
- **RP-08-03. Sin sobrescritura silenciosa:** si un dato cambió desde que la persona lo abrió, se informa el conflicto y se muestra el valor vigente antes de aceptar otro cambio. Esta regla generaliza el criterio 3 de HU-03-006.
- **RP-08-04. Límites de recuperación:** la frecuencia de respaldo, la pérdida máxima tolerable y el tiempo máximo de restauración se acordarán con el cliente antes de cerrar los criterios de E2.

### 9.4. Historias de usuario

#### HU-08-001 — Saber si una acción se guardó

**Actividad:** A1. Confirmar.  
**Historia:** Como usuario, quiero que la aplicación me indique claramente si mi acción se guardó o falló para no trabajar con información que creo registrada y no lo está.  
**Dependencias:** aplica a las acciones de EP-01 a EP-07; RP-08-01.

**Criterios de aceptación:**

1. Una acción confirmada muestra un mensaje de éxito y el cambio aparece en las consultas correspondientes.
2. Si la acción falla o se pierde la conexión, se informa que no se guardó, el cambio no se muestra como vigente y, cuando sea posible, se conserva lo escrito para reintentar.
3. Mientras la acción está en proceso se indica claramente y se impide enviarla otra vez por accidente.

#### HU-08-002 — Reintentar una acción sin duplicarla

**Actividad:** A2. Reintentar.  
**Historia:** Como usuario, quiero reintentar una acción interrumpida sin temor a crear duplicados para recuperar mi trabajo después de un corte de conexión.  
**Dependencias:** HU-08-001; RP-08-02.

**Criterios de aceptación:**

1. Si el primer envío sí se guardó, el reintento muestra el resultado existente y no crea un segundo proyecto, tarea, comentario, adjunto o aviso.
2. Si el primer envío no se guardó, el reintento lo registra una sola vez.
3. Dos acciones intencionales distintas, aunque tengan contenido parecido, no se confunden con un reintento.

#### HU-08-003 — Evitar sobrescribir cambios de otra persona

**Actividad:** A3. Resolver conflictos.  
**Historia:** Como responsable de proyecto, quiero que se me avise si otra persona modificó el mismo dato mientras yo lo editaba para no borrar su cambio sin saberlo.  
**Dependencias:** HU-02-003, HU-03-006 y HU-04-001; RP-08-03.

**Criterios de aceptación:**

1. Si el dato cambió desde que lo abrí, al confirmar se informa el conflicto, se muestra el valor vigente y mi cambio no se aplica automáticamente.
2. Después de revisar el valor vigente puedo volver a confirmar mi cambio; ambos cambios quedan en el historial con actor y fecha.
3. Cambios simultáneos sobre datos distintos de un mismo proyecto o tarea no generan un conflicto innecesario.

#### HU-08-004 — Respaldar la información periódicamente

**Actividad:** A4. Respaldar.  
**Historia:** Como administrador de la organización, quiero que la información confirmada se respalde de forma periódica para poder recuperarla si ocurre un fallo grave.  
**Dependencias:** frecuencia y conservación de respaldos según RP-08-04.

**Criterios de aceptación:**

1. Los respaldos incluyen cuentas, permisos, proyectos, tareas, avances, bloqueos, comentarios, archivos, avisos e historial.
2. Cada respaldo registra su fecha y resultado; un respaldo fallido queda señalado para el administrador y no se considera disponible.
3. Los respaldos se guardan separados de la información en uso y solo personas autorizadas pueden acceder a ellos.

#### HU-08-005 — Restaurar la información y verificar la recuperación

**Actividad:** A5. Restaurar.  
**Historia:** Como administrador de la organización, quiero restaurar la información desde un respaldo y comprobar que quedó completa para que el equipo retome el trabajo después de una interrupción.  
**Dependencias:** HU-08-004.

**Criterios de aceptación:**

1. Una prueba de restauración recupera los proyectos y tareas confirmados hasta el último respaldo válido, dentro del tiempo acordado con el cliente.
2. Después de restaurar, la información conserva sus relaciones, autoría, permisos e historial; ningún proyecto queda visible para personas sin acceso.
3. El resultado de la prueba queda documentado, incluida la información posterior al último respaldo que no pudo recuperarse.

### 9.5. Criterios compartidos para todas las épicas

- **Guardado:** toda acción que crea, modifica, cierra o retira información cumple HU-08-001; nunca se muestra como guardado un cambio que falló.
- **Reintento:** las acciones de creación (cuentas, proyectos, tareas, avances, bloqueos, comentarios, adjuntos y avisos) cumplen HU-08-002.
- **Cambios simultáneos:** la edición de datos compartidos de proyectos y tareas cumple HU-08-003.
- **Historial:** los cambios confirmados conservan actor y fecha, y se recuperan junto con el resto de la información en una restauración.
- **Permisos:** reintentar o restaurar nunca amplía el acceso que una persona tenía antes del fallo.

### 9.6. Trazabilidad y decisiones pendientes

| Resultado de EP-08 | Historias |
| --- | --- |
| Si una acción falla, la aplicación lo informa y no la presenta como guardada. | HU-08-001; RP-08-01. |
| Repetir una acción tras una interrupción no crea duplicados. | HU-08-002; RP-08-02. |
| Los cambios simultáneos no se sobrescriben en silencio. | HU-08-003; RP-08-03. |
| Una prueba de restauración recupera la información confirmada dentro de los límites acordados. | HU-08-004 y HU-08-005; RP-08-04. |

**Por confirmar:** pérdida máxima tolerable y tiempo máximo de recuperación; frecuencia y tiempo de conservación de los respaldos; quién realiza y aprueba las pruebas de restauración y con qué periodicidad; conservación a largo plazo de proyectos cerrados; si se necesita exportar la información de un proyecto.
