// Avisos dentro de la aplicación (Sprint 4). Cada vista devuelve { titulo, html, ... } y el router la pinta.

/** Texto de cada tipo de aviso; los nombres vienen del servidor y se escapan. */
const TEXTO_AVISO = {
  asignacion: (a) => `${escapar(a.actor_nombre)} te asignó la tarea ${enlaceAviso(a, a.tarea_nombre)}`,
  bloqueo: (a) => `${escapar(a.actor_nombre)} reportó un bloqueo en la tarea ${enlaceAviso(a, a.tarea_nombre)} ` +
    (a.bloqueo_resuelto ? `<span class="chip chip-resuelto">${icono("ok")}Resuelto</span>` : etiquetaBloqueo()),
  // HU-06-002: lo genera el sistema; muestra la fecha límite que tenía la tarea al avisar
  vencimiento: (a) => `${icono("reloj")} La tarea ${enlaceAviso(a, a.tarea_nombre)} que tienes asignada vence el ${fecha(a.fecha_limite)}`,
};

/** El enlace pasa por #/avisos/{id}: lo marca como leído y lleva a la tarea si el acceso sigue vigente. */
function enlaceAviso(a, texto) {
  return `<a href="#/avisos/${Number(a.id)}">${escapar(texto)}</a>`;
}

function itemAviso(a) {
  const pendiente = a.leido ? "" : `<span class="punto-nuevo" aria-hidden="true"></span><span class="solo-lector">Sin leer: </span>`;
  if (!a.con_acceso) {
    return `
      <li class="${a.leido ? "" : "no-leido"}">
        <p>${pendiente}${enlaceAviso(a, "Aviso de un proyecto al que ya no tienes acceso")}</p>
        <p class="meta">${momento(a.creado_en)}</p>
      </li>`;
  }
  const texto = TEXTO_AVISO[a.tipo]?.(a) || enlaceAviso(a, a.tipo);
  return `
    <li class="${a.leido ? "" : "no-leido"}">
      <p>${pendiente}${texto}</p>
      ${a.bloqueo_motivo ? `<p class="texto-largo">${escapar(a.bloqueo_motivo)}</p>` : ""}
      <p class="meta">${escapar(a.proyecto_nombre)} · ${momento(a.creado_en)}</p>
    </li>`;
}

// HU-06-005 Consultar mis avisos: del más reciente al más antiguo, los pendientes resaltados
async function vistaAvisos() {
  const avisos = await API.get("/api/avisos");
  const pendientes = avisos.filter((a) => !a.leido).length;
  ContadorAvisos.pintar(pendientes);
  const resumen = `${pendientes} sin leer · ${avisos.length} en total`;
  return {
    titulo: "Avisos",
    seccion: "avisos",
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Avisos</h1>
          <p class="subtitulo">${resumen}</p>
        </div>
        ${pendientes ? `<div class="encabezado-acciones">
          <button type="button" class="boton secundario" data-accion="leer-avisos">${icono("ok")}Marcar todos como leídos</button>
        </div>` : ""}
      </header>
      ${avisos.length
        ? `<ol class="lista-cambios lista-avisos">${avisos.map(itemAviso).join("")}</ol>`
        : vacio("No tienes avisos", "Cuando te asignen una tarea, se acerque su fecha límite o se bloquee una tarea de un proyecto a tu cargo, te avisaremos aquí.",
                `<a class="boton secundario" href="#/mis-tareas">Ver mis tareas</a>`)}`,
  };
}

// HU-06-005 Abrir un aviso: lo marca como leído y lleva a su tarea o proyecto.
// Sin acceso vigente no hay destino y se muestra "Sin acceso" sin revelar nada.
async function vistaAbrirAviso(id) {
  const aviso = await API.post(`/api/avisos/${id}/abrir`);
  ContadorAvisos.actualizar();
  if (!aviso.destino) return vistaSinAcceso();
  const ruta = aviso.destino.tipo === "tarea" ? `#/tareas/${Number(aviso.destino.id)}` : `#/proyectos/${Number(aviso.destino.id)}`;
  history.replaceState(null, "", ruta);  // "Atrás" vuelve a la lista de avisos, no a este paso
  hashAnterior = ruta;
  router();  // pinta el destino (esta navegación queda descartada)
  return null;
}

ACCIONES["leer-avisos"] = async (btn) => {
  if (await guardar(btn, () => API.post("/api/avisos/leer-todos"), "Avisos marcados como leídos")) recargar();
};

/** Insignia con los avisos sin leer en la navegación (barra lateral y barra inferior). */
const ContadorAvisos = {
  pintar(n) {
    document.querySelectorAll("[data-contador-avisos]").forEach((el) => {
      el.hidden = !n;
      el.innerHTML = n ? `<span aria-hidden="true">${n > 99 ? "99+" : n}</span><span class="solo-lector">, ${n} sin leer</span>` : "";
    });
  },
  async actualizar() {
    if (!API.token()) { this.pintar(0); return; }
    try {
      this.pintar((await API.get("/api/avisos/resumen")).no_leidos);
    } catch { /* el contador puede esperar a la siguiente navegación */ }
  },
};

// Se actualiza al navegar (router) y cada minuto mientras la pestaña está a la vista
setInterval(() => { if (document.visibilityState === "visible") ContadorAvisos.actualizar(); }, 60000);
