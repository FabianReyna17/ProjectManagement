// Utilidades de interfaz.

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto ?? "";
  return div.innerHTML;
}

// HU-08-001: confirmación o error visible para toda acción de guardado
let toastTimer;
function toast(mensaje, tipo = "ok") {
  const el = document.getElementById("toast");
  el.textContent = mensaje;
  el.className = `visible ${tipo}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.className = ""), 3500);
}

/**
 * Envía un formulario: deshabilita el botón, muestra "Guardado" solo si el servidor
 * confirma y el error en caso contrario (la vista no se actualiza si falla).
 */
async function guardar(boton, accion, mensajeOk = "Guardado correctamente") {
  boton.disabled = true;
  try {
    const resultado = await accion();
    toast(mensajeOk, "ok");
    return resultado;
  } catch (e) {
    toast(e.message, "error");
    return null;
  } finally {
    boton.disabled = false;
  }
}

function datosForm(form) {
  return Object.fromEntries(new FormData(form).entries());
}

// Fechas de la BD (UTC "AAAA-MM-DD HH:MM:SS") en hora local
function fechaHora(texto) {
  if (!texto) return "";
  const d = new Date(texto.replace(" ", "T") + "Z");
  return isNaN(d) ? texto : d.toLocaleString();
}

const ESTADOS_TAREA = { pendiente: "Pendiente", en_curso: "En curso", terminada: "Terminada" };

function etiquetaEstado(estado, bloqueada = false) {
  return `<span class="etiqueta estado-${estado}">${escapar(ESTADOS_TAREA[estado] || estado)}</span>` +
    (bloqueada ? ` <span class="etiqueta bloqueada">⛔ Bloqueada</span>` : "");
}

const PRIORIDADES = { alta: "Alta", media: "Media", baja: "Baja" };

function etiquetaPrioridad(prioridad) {
  return `<span class="etiqueta prioridad-${prioridad}">${escapar(PRIORIDADES[prioridad] || prioridad)}</span>`;
}

function opcionesPrioridad(seleccionada = "media") {
  return Object.entries(PRIORIDADES)
    .map(([v, t]) => `<option value="${v}" ${v === seleccionada ? "selected" : ""}>${t}</option>`).join("");
}

// HU-04-001: mismas transiciones que el servidor (el servidor es quien decide)
const TRANSICIONES = { pendiente: ["en_curso"], en_curso: ["pendiente", "terminada"], terminada: ["en_curso"] };
const ACCION_ESTADO = {
  "pendiente>en_curso": "Iniciar", "en_curso>pendiente": "Volver a pendiente",
  "en_curso>terminada": "Terminar", "terminada>en_curso": "Reabrir",
};

function botonesEstado(tareaId, actual, permitidas = TRANSICIONES[actual] || []) {
  return permitidas.map((e) => `
    <button class="${e === "terminada" ? "" : "secundario"} chico" data-tarea="${tareaId}" data-estado="${e}">
      ${ACCION_ESTADO[`${actual}>${e}`] || ESTADOS_TAREA[e]}</button>`).join("");
}

/** Conecta los botones de estado dentro de `raiz`; `alTerminar` recarga la vista. */
function conectarBotonesEstado(raiz, alTerminar) {
  raiz.querySelectorAll("[data-estado]").forEach((btn) =>
    btn.addEventListener("click", async (ev) => {
      ev.stopPropagation();
      const ok = await guardar(btn,
        () => API.put(`/api/tareas/${btn.dataset.tarea}/estado`, { estado: btn.dataset.estado }), "Estado actualizado");
      if (ok) alTerminar();
    }));
}
