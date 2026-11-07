// Utilidades de interfaz: escape, iconos, avisos, guardado y fechas.

// Escapa también comillas: el resultado se usa dentro de atributos.
function escapar(texto) {
  return String(texto ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function icono(nombre, clase = "") {
  return `<svg class="icono ${clase}" aria-hidden="true" focusable="false"><use href="#i-${nombre}"/></svg>`;
}

// Sin acentos ni mayúsculas, para buscar "diseno" y encontrar "Diseño"
function normalizar(texto) {
  return String(texto ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

// ---------- Avisos (toasts) ----------

const DURACION_AVISO = { ok: 4000, error: 9000 };
const MAX_AVISOS = 4;

/** HU-08-001: aviso apilable con botón cerrar. Los errores duran más y se anuncian de inmediato. */
function toast(mensaje, tipo = "ok") {
  const region = document.getElementById(tipo === "error" ? "avisos-urgentes" : "avisos");
  const el = document.createElement("div");
  el.className = `aviso aviso-${tipo}`;
  el.innerHTML = `${icono(tipo === "error" ? "error" : "ok")}
    <p>${escapar(mensaje)}</p>
    <button type="button" class="aviso-cerrar" aria-label="Cerrar aviso">${icono("cerrar")}</button>`;
  region.append(el);
  while (region.children.length > MAX_AVISOS) region.firstElementChild.remove();

  let temporizador;
  const cerrar = () => {
    clearTimeout(temporizador);
    el.classList.add("saliendo");
    setTimeout(() => el.remove(), 160);
  };
  const programar = (ms) => { clearTimeout(temporizador); temporizador = setTimeout(cerrar, ms); };
  el.querySelector("button").addEventListener("click", cerrar);
  el.addEventListener("mouseenter", () => clearTimeout(temporizador));
  el.addEventListener("mouseleave", () => programar(2000));
  programar(DURACION_AVISO[tipo] || DURACION_AVISO.ok);
}

// ---------- Guardado ----------

/**
 * HU-08-001: envía una acción. Mientras tanto el botón queda deshabilitado y dice "Guardando…";
 * "Guardado" se muestra solo si el servidor confirma. Si falla, se informa el motivo, se marcan
 * los campos que indique el servidor y lo escrito se conserva para reintentar.
 * Un 403 deja a la persona en la vista y la recarga con sus permisos vigentes.
 * campoDe(error) puede devolver { campo: mensaje } para errores de negocio de un campo.
 */
async function guardar(boton, accion, mensajeOk = "Guardado correctamente", { form, campoDe } = {}) {
  const etiqueta = boton.innerHTML;
  boton.style.minWidth = `${boton.offsetWidth}px`;
  boton.disabled = true;
  boton.setAttribute("aria-busy", "true");
  boton.textContent = "Guardando…";
  if (form) Formularios.limpiarErrores(form);
  try {
    const resultado = await accion();
    if (form) Formularios.marcarLimpio(form);
    toast(mensajeOk, "ok");
    return resultado;
  } catch (e) {
    if (e.status === 401) return null;  // la sesión terminó: ya se fue al login
    if (form && e.campos?.length) Formularios.marcarErrores(form, e.campos);
    else if (form && campoDe?.(e)) Formularios.marcarErrores(form, campoDe(e));
    toast(e.message, "error");
    if (e.status === 403) recargar();
    return null;
  } finally {
    if (boton.isConnected) {
      boton.innerHTML = etiqueta;
      boton.disabled = false;
      boton.removeAttribute("aria-busy");
      boton.style.minWidth = "";
    }
  }
}

// HU-08-002: una clave por acción intencional; los reintentos de esa acción reusan la misma
function nuevaClave() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function datosForm(form) {
  return Object.fromEntries(new FormData(form).entries());
}

// ---------- Fechas (es-GT) ----------

const FMT_FECHA = new Intl.DateTimeFormat("es-GT", { day: "numeric", month: "short", year: "numeric" });
const FMT_FECHA_HORA = new Intl.DateTimeFormat("es-GT", { dateStyle: "medium", timeStyle: "short" });
const FMT_RELATIVA = new Intl.RelativeTimeFormat("es-GT", { numeric: "auto", style: "short" });

// "AAAA-MM-DD" como fecha local (sin desfase por zona horaria)
function aFecha(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
  return m ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : null;
}

// Fechas de la BD (UTC "AAAA-MM-DD HH:MM:SS") como Date
function aMomento(texto) {
  const d = new Date(String(texto || "").replace(" ", "T") + "Z");
  return isNaN(d) ? null : d;
}

/** Fecha de calendario legible: "12 nov 2026". */
function fecha(iso, vacio = "—") {
  if (!iso) return `<span class="tenue">${escapar(vacio)}</span>`;
  const d = aFecha(iso);
  return d ? `<time datetime="${escapar(iso)}">${escapar(FMT_FECHA.format(d))}</time>` : escapar(iso);
}

function relativa(d) {
  const seg = Math.round((d - Date.now()) / 1000);
  const abs = Math.abs(seg);
  if (abs < 60) return "hace un momento";
  if (abs < 3600) return FMT_RELATIVA.format(Math.round(seg / 60), "minute");
  if (abs < 86400) return FMT_RELATIVA.format(Math.round(seg / 3600), "hour");
  if (abs < 7 * 86400) return FMT_RELATIVA.format(Math.round(seg / 86400), "day");
  return FMT_FECHA.format(d);
}

/** Momento de un registro: relativo ("hace 3 h") con la fecha y hora exactas en title. */
function momento(texto) {
  const d = aMomento(texto);
  if (!d) return escapar(texto);
  return `<time datetime="${escapar(d.toISOString())}" title="${escapar(FMT_FECHA_HORA.format(d))}">${escapar(relativa(d))}</time>`;
}
