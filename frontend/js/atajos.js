// Atajos de teclado y paleta de comandos (Ctrl/⌘ K). No se disparan mientras se escribe.

const ES_MAC = /Mac|iPhone|iPad/.test(navigator.platform);
const TECLA_MOD = ES_MAC ? "⌘" : "Ctrl";

const ATAJOS = [
  [[TECLA_MOD, "K"], "Buscar proyecto o tarea, o ejecutar un comando"],
  [["g", "p"], "Ir a Mis proyectos"],
  [["g", "t"], "Ir a Mis tareas"],
  [["g", "u"], "Ir a Usuarios (solo Admin)"],
  [["n"], "Nueva tarea (en un proyecto que gestionas) o nuevo proyecto (en la lista)"],
  [["/"], "Buscar en la lista de la vista"],
  [[TECLA_MOD, "Enter"], "Enviar el formulario"],
  [["?"], "Mostrar estos atajos"],
  [["Esc"], "Cerrar el diálogo abierto"],
];

/** Lo que la vista actual permite crear con "n" (lo fija el router). */
const VistaActual = { nueva: null, textoNueva: "" };

function escribiendo(el) {
  return el?.closest?.("input, textarea, select, [contenteditable='true']");
}

function mostrarAtajos() {
  const lista = document.getElementById("lista-atajos");
  lista.innerHTML = ATAJOS.map(([teclas, texto]) =>
    `<div><dt>${teclas.map((t) => `<kbd class="atajo-tecla">${escapar(t)}</kbd>`).join(" ")}</dt><dd>${escapar(texto)}</dd></div>`).join("");
  document.getElementById("dlg-atajos").showModal();
}

ACCIONES.atajos = () => mostrarAtajos();

const IR_A = { p: "#/proyectos", t: "#/mis-tareas", u: "#/usuarios" };
let prefijoG = 0;

document.addEventListener("keydown", (e) => {
  if (!API.token() || location.hash === "#/login") return;
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    Paleta.abrir();
    return;
  }
  if (e.ctrlKey || e.metaKey || e.altKey || e.defaultPrevented) return;
  if (escribiendo(e.target) || document.querySelector("dialog[open]")) return;

  const tecla = e.key;
  if (prefijoG && Date.now() - prefijoG < 1500) {
    prefijoG = 0;
    const destino = IR_A[tecla.toLowerCase()];
    if (destino && (destino !== "#/usuarios" || API.usuario()?.funcion === "Admin")) {
      e.preventDefault();
      location.hash = destino;
    }
    return;
  }
  prefijoG = 0;
  if (tecla === "g") {
    prefijoG = Date.now();
  } else if (tecla === "?") {
    e.preventDefault();
    mostrarAtajos();
  } else if (tecla === "n" && VistaActual.nueva) {
    e.preventDefault();
    location.hash = VistaActual.nueva;
  } else if (tecla === "/") {
    const filtro = document.querySelector("#app [data-filtra]");
    if (filtro) {
      e.preventDefault();
      filtro.focus();
    }
  }
});

// ---------- Paleta de comandos ----------

const Paleta = {
  dialogo: null,
  entrada: null,
  lista: null,
  items: [],
  visibles: [],
  activo: 0,

  iniciar() {
    this.dialogo = document.getElementById("dlg-paleta");
    this.entrada = document.getElementById("paleta-texto");
    this.lista = document.getElementById("paleta-lista");
    this.entrada.addEventListener("input", () => { this.activo = 0; this.pintar(); });
    this.entrada.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        this.mover(e.key === "ArrowDown" ? 1 : -1);
      } else if (e.key === "Enter") {
        e.preventDefault();
        this.ejecutar(this.activo);
      }
    });
    this.lista.addEventListener("click", (e) => {
      const opcion = e.target.closest("[role=option]");
      if (opcion) this.ejecutar(Number(opcion.dataset.indice));
    });
    // Clic fuera del recuadro cierra
    this.dialogo.addEventListener("click", (e) => { if (e.target === this.dialogo) this.dialogo.close(); });
  },

  comandos() {
    const u = API.usuario() || {};
    const cmds = [
      { texto: "Ir a Mis proyectos", atajo: "g p", ir: "#/proyectos" },
      { texto: "Ir a Mis tareas", atajo: "g t", ir: "#/mis-tareas" },
    ];
    if (u.funcion === "Admin") cmds.push({ texto: "Ir a Usuarios", atajo: "g u", ir: "#/usuarios" });
    if (VistaActual.nueva) cmds.push({ texto: VistaActual.textoNueva, atajo: "n", ir: VistaActual.nueva });
    if (["Admin", "Responsable"].includes(u.funcion) && VistaActual.nueva !== "#/proyectos/nuevo") {
      cmds.push({ texto: "Nuevo proyecto", ir: "#/proyectos/nuevo" });
    }
    cmds.push(
      { texto: `Cambiar tema (ahora: ${NOMBRES_TEMA[Tema.actual()]})`, accion: () => Tema.siguiente() },
      { texto: "Ver atajos de teclado", atajo: "?", accion: mostrarAtajos },
      { texto: "Cerrar sesión", accion: cerrarSesion },
    );
    return cmds.map((c) => ({ ...c, tipo: "Comando" }));
  },

  async abrir() {
    if (this.dialogo.open) return;
    this.entrada.value = "";
    this.activo = 0;
    this.items = this.comandos();
    this.pintar();
    this.dialogo.showModal();
    this.entrada.focus();
    try {
      const [proyectos, tareas] = await Promise.all([API.get("/api/proyectos"), API.get("/api/mis-tareas")]);
      Estado.proyectos = proyectos;
      pintarRecientes();
      const vistas = new Set();
      const deTareas = [...tareas, ...(Estado.tareasProyecto?.tareas || [])]
        .filter((t) => !vistas.has(t.id) && vistas.add(t.id))
        .map((t) => ({ tipo: "Tarea", texto: t.nombre,
                       detalle: t.proyecto_nombre || Estado.tareasProyecto?.nombre || "", ir: `#/tareas/${t.id}` }));
      this.items = [
        ...this.comandos(),
        ...proyectos.map((p) => ({ tipo: "Proyecto", texto: p.nombre, detalle: p.responsable_nombre, ir: `#/proyectos/${p.id}` })),
        ...deTareas,
      ];
      if (this.dialogo.open) this.pintar();
    } catch { /* la paleta sigue sirviendo con los comandos */ }
  },

  pintar() {
    const palabras = normalizar(this.entrada.value).split(/\s+/).filter(Boolean);
    let lista = this.items.filter((it) => {
      const texto = normalizar(`${it.texto} ${it.detalle || ""} ${it.tipo}`);
      return palabras.every((p) => texto.includes(p));
    });
    if (!palabras.length) {
      // Sin texto: comandos y unos pocos de cada tipo
      const cuenta = {};
      lista = lista.filter((it) => it.tipo === "Comando" || (cuenta[it.tipo] = (cuenta[it.tipo] || 0) + 1) <= 5);
    }
    this.visibles = lista.slice(0, 40);
    this.activo = Math.min(this.activo, Math.max(this.visibles.length - 1, 0));
    this.lista.innerHTML = this.visibles.length
      ? this.visibles.map((it, i) => `
          <li role="option" id="paleta-op-${i}" data-indice="${i}" aria-selected="${i === this.activo}">
            ${icono(it.tipo === "Proyecto" ? "proyectos" : it.tipo === "Tarea" ? "tareas" : "teclado")}
            <span class="paleta-texto">${escapar(it.texto)}${it.detalle ? `<span class="tenue"> · ${escapar(it.detalle)}</span>` : ""}</span>
            ${it.atajo ? `<kbd class="atajo-tecla">${escapar(it.atajo)}</kbd>` : `<span class="paleta-tipo">${it.tipo}</span>`}
          </li>`).join("")
      : `<li class="paleta-vacia" role="presentation">Sin resultados</li>`;
    this.entrada.setAttribute("aria-activedescendant", this.visibles.length ? `paleta-op-${this.activo}` : "");
  },

  mover(delta) {
    if (!this.visibles.length) return;
    this.activo = (this.activo + delta + this.visibles.length) % this.visibles.length;
    this.lista.querySelectorAll("[role=option]").forEach((op, i) => op.setAttribute("aria-selected", String(i === this.activo)));
    this.entrada.setAttribute("aria-activedescendant", `paleta-op-${this.activo}`);
    document.getElementById(`paleta-op-${this.activo}`)?.scrollIntoView({ block: "nearest" });
  },

  ejecutar(indice) {
    const it = this.visibles[indice];
    if (!it) return;
    this.dialogo.close();
    if (it.ir) location.hash = it.ir;
    else it.accion();
  },
};

ACCIONES.paleta = () => Paleta.abrir();
