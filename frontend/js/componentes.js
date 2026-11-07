// Componentes de interfaz reutilizables por todas las vistas.

/** Acciones por delegación: un botón con data-accion="x" ejecuta ACCIONES.x(boton, evento). */
const ACCIONES = {};

/** Datos compartidos entre vistas, la barra lateral y la paleta de comandos. */
const Estado = { proyectos: [], tareasProyecto: null };

// ---------- Etiquetas de estado y prioridad (icono/forma + texto, nunca solo color) ----------

const ESTADOS_TAREA = { pendiente: "Pendiente", en_curso: "En curso", terminada: "Terminada" };
const ESTADOS_PROYECTO = { planificado: "Planificado", en_curso: "En curso", cerrado: "Cerrado" };
const PRIORIDADES = { alta: "Alta", media: "Media", baja: "Baja" };
// Claves para ordenar tablas en el cliente
const ORDEN_PRIORIDAD = { alta: 1, media: 2, baja: 3 };
const ORDEN_ESTADO = { pendiente: 1, en_curso: 2, terminada: 3, planificado: 1, cerrado: 3 };

function chip(estado, textos) {
  const clave = estado in textos ? estado : "desconocido";
  return `<span class="chip chip-${clave}">${icono(`est-${clave}`, "icono-estado")}${escapar(textos[estado] || estado)}</span>`;
}

function etiquetaEstado(estado, bloqueada = false) {
  return chip(estado, ESTADOS_TAREA) + (bloqueada ? ` ${etiquetaBloqueo()}` : "");
}

// HU-04-003: marca de bloqueo con icono + texto
function etiquetaBloqueo() {
  return `<span class="chip chip-bloqueo">${icono("bloqueo")}Bloqueada</span>`;
}

function etiquetaProyecto(estado) {
  return chip(estado, ESTADOS_PROYECTO);
}

// Prioridad como barras de señal (1/2/3) + texto
function etiquetaPrioridad(prioridad) {
  const clave = prioridad in PRIORIDADES ? prioridad : "media";
  return `<span class="prioridad prioridad-${clave}"><span class="senal" aria-hidden="true"><i></i><i></i><i></i></span>` +
    `${escapar(PRIORIDADES[prioridad] || prioridad)}</span>`;
}

function opcionesPrioridad(seleccionada = "media") {
  return Object.entries(PRIORIDADES)
    .map(([v, t]) => `<option value="${v}" ${v === seleccionada ? "selected" : ""}>${t}</option>`).join("");
}

function sinAsignar() {
  return `<span class="sin-asignar">${icono("aviso")}Sin asignar</span>`;
}

// HU-04-001: mismas transiciones que el servidor (el servidor es quien decide)
const TRANSICIONES = { pendiente: ["en_curso"], en_curso: ["pendiente", "terminada"], terminada: ["en_curso"] };
const ACCION_ESTADO = {
  "pendiente>en_curso": "Iniciar", "en_curso>pendiente": "Volver a pendiente",
  "en_curso>terminada": "Terminar", "terminada>en_curso": "Reabrir",
};

function transicionesPosibles(estado, bloqueada) {
  return (TRANSICIONES[estado] || []).filter((e) => !(e === "terminada" && bloqueada));
}

function botonesEstado(tareaId, actual, permitidas = TRANSICIONES[actual] || []) {
  return permitidas.map((e) => `
    <button type="button" class="boton chico ${e === "terminada" ? "" : "secundario"}"
            data-accion="estado" data-id="${Number(tareaId)}" data-estado="${escapar(e)}">
      ${escapar(ACCION_ESTADO[`${actual}>${e}`] || ESTADOS_TAREA[e])}</button>`).join("");
}

ACCIONES.estado = async (btn) => {
  const ok = await guardar(btn,
    () => API.put(`/api/tareas/${btn.dataset.id}/estado`, { estado: btn.dataset.estado }), "Estado actualizado");
  if (ok) recargar();
};

// ---------- Personas ----------

function iniciales(nombre) {
  const partes = String(nombre || "?").trim().split(/\s+/).filter(Boolean);
  const letras = partes.length > 1 ? partes[0][0] + partes[partes.length - 1][0] : (partes[0] || "?").slice(0, 2);
  return letras.toUpperCase();
}

// Tono estable por persona, de una gama corta y apagada
function tonoAvatar(semilla) {
  let h = 0;
  for (const c of String(semilla)) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return (h % 6) + 1;
}

function avatar(nombre, semilla = nombre, clase = "") {
  return `<span class="avatar tono-${tonoAvatar(semilla)} ${clase}" aria-hidden="true">${escapar(iniciales(nombre))}</span>`;
}

function persona(nombre, semilla = nombre) {
  return `<span class="persona">${avatar(nombre, semilla)}<span>${escapar(nombre)}</span></span>`;
}

// ---------- Estructura de vistas ----------

function migas(items) {
  return `<nav class="migas" aria-label="Ruta de navegación"><ol>${items.map((m, i) => i === items.length - 1
    ? `<li><span aria-current="page">${escapar(m.texto)}</span></li>`
    : `<li><a href="${escapar(m.href)}">${escapar(m.texto)}</a></li>`).join("")}</ol></nav>`;
}

/** Estado vacío con la acción siguiente. */
function vacio(titulo, texto = "", accion = "") {
  return `<div class="vacio"><p class="vacio-titulo">${escapar(titulo)}</p>` +
    `${texto ? `<p>${escapar(texto)}</p>` : ""}${accion}</div>`;
}

function esqueleto(tipo = "tabla") {
  const linea = (clase = "") => `<span class="esq-linea ${clase}"></span>`;
  const cuerpo = {
    tabla: `${linea("esq-titulo")}${linea("esq-corta")}<div class="esq-tabla">${"<span class=\"esq-fila\"></span>".repeat(6)}</div>`,
    ficha: `${linea("esq-corta")}${linea("esq-titulo")}<div class="esq-columnas"><div>${linea()}${linea()}${linea("esq-media")}${linea()}${linea("esq-corta")}</div><div class="esq-panel"></div></div>`,
    form: `${linea("esq-corta")}${linea("esq-titulo")}${"<span class=\"esq-campo\"></span>".repeat(4)}`,
  }[tipo];
  return `<div class="esqueleto" aria-busy="true"><span class="solo-lector" role="status">Cargando…</span>${cuerpo}</div>`;
}

// ---------- Tablas: orden y búsqueda en el cliente ----------

/** Encabezado que ordena la columna al pulsarlo. */
function th(texto, { ordenable = true, clase = "" } = {}) {
  if (!ordenable) return `<th scope="col" class="${clase}"><span class="solo-lector">${escapar(texto)}</span></th>`;
  return `<th scope="col" class="${clase}"><button type="button" class="ordenar" data-accion="ordenar">` +
    `${escapar(texto)}${icono("orden", "icono-orden")}</button></th>`;
}

function valorOrden(celda) {
  return celda ? (celda.dataset.orden ?? celda.textContent.trim()) : "";
}

ACCIONES.ordenar = (btn) => {
  const celda = btn.closest("th");
  const tabla = celda.closest("table");
  const indice = [...celda.parentElement.children].indexOf(celda);
  const sentido = celda.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
  tabla.querySelectorAll("th[aria-sort]").forEach((x) => x.removeAttribute("aria-sort"));
  celda.setAttribute("aria-sort", sentido);
  const cuerpo = tabla.tBodies[0];
  const filas = [...cuerpo.rows].filter((f) => !f.classList.contains("fila-sin-resultados"));
  const factor = sentido === "ascending" ? 1 : -1;
  filas.sort((a, b) => {
    const va = valorOrden(a.cells[indice]);
    const vb = valorOrden(b.cells[indice]);
    if (!va || !vb) return va ? -1 : vb ? 1 : 0;  // los vacíos siempre al final
    return va.localeCompare(vb, "es", { numeric: true, sensitivity: "base" }) * factor;
  });
  cuerpo.append(...filas);
};

/** Búsqueda rápida: <input data-filtra="id-de-tabla">. Solo filtra lo ya cargado. */
function filtrarTabla(entrada) {
  const tabla = document.getElementById(entrada.dataset.filtra);
  if (!tabla) return;
  const palabras = normalizar(entrada.value).split(/\s+/).filter(Boolean);
  const cuerpo = tabla.tBodies[0];
  let visibles = 0;
  for (const fila of cuerpo.rows) {
    if (fila.classList.contains("fila-sin-resultados")) continue;
    const texto = normalizar(fila.textContent);
    const coincide = palabras.every((p) => texto.includes(p));
    fila.hidden = !coincide;
    if (coincide) visibles++;
  }
  let aviso = cuerpo.querySelector(".fila-sin-resultados");
  if (!visibles && !aviso) {
    aviso = cuerpo.insertRow();
    aviso.className = "fila-sin-resultados";
    const celda = aviso.insertCell();
    celda.colSpan = tabla.tHead.rows[0].cells.length;
  }
  if (aviso) {
    aviso.hidden = visibles > 0;
    aviso.cells[0].textContent = `Nada coincide con «${entrada.value.trim()}».`;
  }
  const conteo = document.querySelector(`[data-conteo="${entrada.dataset.filtra}"]`);
  if (conteo) conteo.textContent = palabras.length ? `${visibles} de ${cuerpo.rows.length - (aviso ? 1 : 0)}` : conteo.dataset.total;
}

function buscadorTabla(idTabla, etiqueta) {
  return `<label class="filtro">${icono("buscar")}<span class="solo-lector">${escapar(etiqueta)}</span>` +
    `<input type="search" data-filtra="${escapar(idTabla)}" placeholder="${escapar(etiqueta)}" autocomplete="off"></label>`;
}

// ---------- Enlaces ----------

function botonCopiarEnlace(ruta, texto = "Copiar enlace") {
  return `<button type="button" class="boton secundario chico" data-accion="copiar-enlace" data-ruta="${escapar(ruta)}">` +
    `${icono("enlace")}${escapar(texto)}</button>`;
}

ACCIONES["copiar-enlace"] = async (btn) => {
  const url = `${location.origin}${location.pathname}${btn.dataset.ruta}`;
  try {
    await navigator.clipboard.writeText(url);
    toast("Enlace copiado");
  } catch {
    toast(`No se pudo copiar automáticamente. Enlace: ${url}`, "error");
  }
};

// ---------- Diálogo de confirmación ----------

/** Confirmación accesible para acciones destructivas. Resuelve true si se acepta. */
function confirmar({ titulo, mensaje, aceptar = "Aceptar", peligro = false }) {
  const dlg = document.getElementById("dlg-confirmar");
  const anterior = document.activeElement;
  dlg.querySelector("h2").textContent = titulo;
  dlg.querySelector("p").textContent = mensaje;
  const boton = dlg.querySelector("[data-aceptar]");
  boton.textContent = aceptar;
  boton.classList.toggle("peligro", peligro);
  dlg.returnValue = "";
  dlg.showModal();
  dlg.querySelector("[data-cancelar]").focus();  // lo seguro queda por defecto
  return new Promise((resolver) => dlg.addEventListener("close", () => {
    if (anterior?.isConnected) anterior.focus();
    resolver(dlg.returnValue === "si");
  }, { once: true }));
}

// ---------- Formularios ----------

const Formularios = {
  sucios: new Set(),

  /** Contador de caracteres, Ctrl+Enter para enviar, mostrar contraseña y aviso de cambios sin guardar. */
  mejorar(form) {
    form.querySelectorAll("textarea[maxlength]").forEach((ta) => {
      const contador = document.createElement("small");
      contador.className = "contador";
      contador.id = `contador-${form.id}-${ta.name}`;
      ta.setAttribute("aria-describedby", [ta.getAttribute("aria-describedby"), contador.id].filter(Boolean).join(" "));
      const max = Number(ta.maxLength);
      const actualizar = () => {
        contador.textContent = `${ta.value.length} / ${max}`;
        contador.classList.toggle("cerca", ta.value.length > max * 0.9);
      };
      ta.after(contador);
      ta.addEventListener("input", actualizar);
      actualizar();
    });

    form.querySelectorAll("input[type=password]").forEach((entrada) => {
      const envoltura = document.createElement("span");
      envoltura.className = "campo-con-boton";
      entrada.replaceWith(envoltura);
      envoltura.append(entrada);
      envoltura.insertAdjacentHTML("beforeend",
        `<button type="button" class="boton-icono" aria-pressed="false" aria-label="Mostrar contraseña">${icono("ojo")}</button>`);
      const boton = envoltura.querySelector("button");
      boton.addEventListener("click", () => {
        const visible = entrada.type === "password";
        entrada.type = visible ? "text" : "password";
        boton.setAttribute("aria-pressed", String(visible));
        boton.innerHTML = icono(visible ? "ojo-no" : "ojo");
      });
    });

    form.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        form.requestSubmit();
      }
    });
    form.addEventListener("input", (e) => {
      if (!form.dataset.sinAvisoCambios) this.sucios.add(form);
      this.limpiarError(e.target);
    });
  },

  marcarLimpio(form) { this.sucios.delete(form); },
  descartarTodos() { this.sucios.clear(); },

  hayCambios() {
    for (const f of this.sucios) if (!f.isConnected) this.sucios.delete(f);
    return this.sucios.size > 0;
  },

  /** campos: lista de nombres (mensaje genérico) u objeto { nombre: mensaje }. */
  marcarErrores(form, campos) {
    const lista = Array.isArray(campos) ? campos.map((c) => [c, "Revisa este campo"]) : Object.entries(campos);
    let primero = null;
    for (const [nombre, mensaje] of lista) {
      const campo = form.elements[nombre];
      if (!campo || !campo.name) continue;
      campo.setAttribute("aria-invalid", "true");
      const error = document.createElement("small");
      error.className = "error-campo";
      error.id = `error-${form.id}-${nombre}`;
      error.innerHTML = `${icono("error")}${escapar(mensaje)}`;
      (campo.closest(".campo-con-boton") || campo).after(error);
      campo.setAttribute("aria-describedby", [campo.getAttribute("aria-describedby"), error.id].filter(Boolean).join(" "));
      primero ??= campo;
    }
    primero?.focus();
  },

  limpiarError(campo) {
    if (!campo?.hasAttribute?.("aria-invalid")) return;
    campo.removeAttribute("aria-invalid");
    const id = `error-${campo.form?.id}-${campo.name}`;
    document.getElementById(id)?.remove();
    const resto = (campo.getAttribute("aria-describedby") || "").split(" ").filter((x) => x && x !== id).join(" ");
    resto ? campo.setAttribute("aria-describedby", resto) : campo.removeAttribute("aria-describedby");
  },

  limpiarErrores(form) {
    form.querySelectorAll("[aria-invalid]").forEach((c) => this.limpiarError(c));
  },
};

window.addEventListener("beforeunload", (e) => {
  if (Formularios.hayCambios()) e.preventDefault();
});

// ---------- Tema ----------

const NOMBRES_TEMA = { sistema: "Según el sistema", claro: "Claro", oscuro: "Oscuro" };

const Tema = {
  actual() { return almacen.leer("tema") || "sistema"; },
  aplicar(tema) {
    almacen.guardar("tema", tema);
    if (tema === "sistema") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = tema === "oscuro" ? "dark" : "light";
    pintarMenusCuenta();
  },
  siguiente() {
    const orden = Object.keys(NOMBRES_TEMA);
    const tema = orden[(orden.indexOf(this.actual()) + 1) % orden.length];
    this.aplicar(tema);
    toast(`Tema: ${NOMBRES_TEMA[tema]}`);
  },
};

ACCIONES.tema = () => Tema.siguiente();
