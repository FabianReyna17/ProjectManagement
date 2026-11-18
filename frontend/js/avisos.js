// Avisos dentro de la aplicación (Sprint 4). Cada vista devuelve { titulo, html, ... } y el router la pinta.

/** Texto de cada tipo de aviso; los nombres vienen del servidor y se escapan. */
const TEXTO_AVISO = {
  asignacion: (a) => `${escapar(a.actor_nombre)} te asignó la tarea ${enlaceTarea(a)}`,
  bloqueo: (a) => `${escapar(a.actor_nombre)} reportó un bloqueo en la tarea ${enlaceTarea(a)} ` +
    (a.bloqueo_resuelto ? `<span class="chip chip-resuelto">${icono("ok")}Resuelto</span>` : etiquetaBloqueo()),
};

function enlaceTarea(a) {
  return `<a href="#/tareas/${Number(a.tarea_id)}">${escapar(a.tarea_nombre)}</a>`;
}

function itemAviso(a) {
  const texto = TEXTO_AVISO[a.tipo]?.(a) || escapar(a.tipo);
  return `
    <li>
      <p>${texto}</p>
      ${a.bloqueo_motivo ? `<p class="texto-largo">${escapar(a.bloqueo_motivo)}</p>` : ""}
      <p class="meta"><a href="#/proyectos/${Number(a.proyecto_id)}">${escapar(a.proyecto_nombre)}</a> · ${momento(a.creado_en)}</p>
    </li>`;
}

// HU-06-001 y HU-06-003: asignaciones y bloqueos, del más reciente al más antiguo
async function vistaAvisos() {
  const avisos = await API.get("/api/avisos");
  return {
    titulo: "Avisos",
    seccion: "avisos",
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Avisos</h1>
          <p class="subtitulo">${avisos.length} aviso${avisos.length === 1 ? "" : "s"}</p>
        </div>
      </header>
      ${avisos.length
        ? `<ol class="lista-cambios lista-avisos">${avisos.map(itemAviso).join("")}</ol>`
        : vacio("No tienes avisos", "Cuando te asignen una tarea o se bloquee una tarea de un proyecto a tu cargo, te avisaremos aquí.",
                `<a class="boton secundario" href="#/mis-tareas">Ver mis tareas</a>`)}`,
  };
}
