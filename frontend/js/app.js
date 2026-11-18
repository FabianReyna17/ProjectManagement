// Router por hash, marco de la aplicación y vistas del Sprint 1 (las de tareas están en tareas.js).
const app = document.getElementById("app");
const NOMBRE_APP = "Gestión de Proyectos";
const FUNCIONES_CREAN_PROYECTO = ["Admin", "Responsable"];

const rutas = [
  { patron: /^#\/login$/, vista: vistaLogin, publica: true, esqueleto: "form" },
  { patron: /^#\/proyectos(?:\?(cerrados))?$/, vista: vistaProyectos, esqueleto: "tabla" },
  { patron: /^#\/proyectos\/nuevo$/, vista: vistaNuevoProyecto, esqueleto: "form" },
  { patron: /^#\/proyectos\/(\d+)$/, vista: vistaProyecto, esqueleto: "ficha" },
  { patron: /^#\/proyectos\/(\d+)\/editar$/, vista: vistaEditarProyecto, esqueleto: "form" },
  { patron: /^#\/proyectos\/(\d+)\/cerrar$/, vista: vistaCerrarProyecto, esqueleto: "form" },
  { patron: /^#\/proyectos\/(\d+)\/historial$/, vista: vistaHistorialProyecto, esqueleto: "tabla" },
  { patron: /^#\/proyectos\/(\d+)\/tareas\/nueva$/, vista: vistaNuevaTarea, esqueleto: "form" },
  { patron: /^#\/tareas\/(\d+)$/, vista: vistaTarea, esqueleto: "ficha" },
  { patron: /^#\/mis-tareas$/, vista: vistaMisTareas, esqueleto: "tabla" },
  { patron: /^#\/avisos$/, vista: vistaAvisos, esqueleto: "tabla" },
  { patron: /^#\/avisos\/(\d+)$/, vista: vistaAbrirAviso, esqueleto: "ficha" },
  { patron: /^#\/estado-proyectos$/, vista: vistaEstadoProyectos, esqueleto: "tabla" },
  { patron: /^#\/carga(?:\?proyecto=(\d+))?$/, vista: vistaCarga, esqueleto: "tabla" },
  { patron: /^#\/usuarios$/, vista: vistaUsuarios, esqueleto: "tabla" },
  { patron: /^#\/sin-acceso$/, vista: vistaSinAcceso },
];

/** La vista no se puede consultar: el router muestra "Sin acceso" en su lugar (HU-01-007). */
function sinAcceso() {
  return new ErrorApi("No tienes permiso para realizar esta acción", 403);
}

// ---------- Router ----------

let navegacion = 0;  // cada navegación tiene un número; solo la última pinta

async function router({ recarga = false } = {}) {
  const hash = location.hash || "#/proyectos";
  const ruta = rutas.find((r) => r.patron.test(hash));
  if (!ruta) { location.replace("#/proyectos"); return; }
  if (!ruta.publica && !API.token()) {
    API.recordarRuta(hash);
    location.replace("#/login");
    return;
  }
  const id = ++navegacion;
  document.body.classList.toggle("sin-sesion", Boolean(ruta.publica));
  // Esqueleto solo si la carga tarda: evita parpadeos en respuestas rápidas
  const espera = recarga ? 0 : setTimeout(() => {
    if (id === navegacion) app.innerHTML = esqueleto(ruta.esqueleto);
  }, 120);

  let vista;
  try {
    vista = await ruta.vista(...hash.match(ruta.patron).slice(1));
  } catch (e) {
    if (e.status === 401) return;  // ya se fue al login
    vista = e.status === 403 ? vistaSinAcceso() : vistaError(e);
    if (e.status === 403) cargarProyectos();  // el acceso pudo cambiar: actualiza la barra lateral
  } finally {
    clearTimeout(espera);
  }
  // Si la persona ya navegó a otra parte, esta respuesta llegó tarde y no se pinta
  if (id !== navegacion || !vista) return;
  pintar(vista, recarga);
  if (!ruta.publica && ruta.vista !== vistaAvisos) ContadorAvisos.actualizar();  // la de avisos ya lo pinta
}

/** Vuelve a consultar la vista actual sin cambiar de ruta (tras guardar, con datos del servidor). */
function recargar() {
  return router({ recarga: true });
}

function pintar(vista, recarga) {
  const foco = recarga ? claveFoco(document.activeElement) : null;
  document.title = `${vista.titulo} · ${NOMBRE_APP}`;
  VistaActual.nueva = vista.nueva || null;
  VistaActual.textoNueva = vista.textoNueva || "";
  marcarSeccion(vista.seccion);
  app.innerHTML = (vista.migas ? migas(vista.migas) : "") + vista.html;
  app.querySelectorAll("form[id]").forEach((f) => Formularios.mejorar(f));
  vista.montar?.(app);
  if (recarga) {
    restaurarFoco(foco);
  } else {
    window.scrollTo(0, 0);
    enfocarVista(vista.foco);
  }
}

// Accesibilidad: al cambiar de ruta el foco va al título (o al primer campo en formularios)
function enfocarVista(tipo) {
  const campo = tipo === "campo" && app.querySelector("form :is(input, select, textarea):not([type=hidden])");
  (campo || app.querySelector("h1") || app).focus({ preventScroll: true });
}

function claveFoco(el) {
  if (!el || !app.contains(el) || el === app) return null;
  if (el.id) return `#${CSS.escape(el.id)}`;
  if (el.dataset.accion) {
    return ["accion", "id", "estado", "vista"].filter((k) => el.dataset[k])
      .map((k) => `[data-${k}="${CSS.escape(el.dataset[k])}"]`).join("");
  }
  if (el.name && el.form?.id) return `#${CSS.escape(el.form.id)} [name="${CSS.escape(el.name)}"]`;
  return null;
}

function restaurarFoco(selector) {
  const el = (selector && app.querySelector(selector)) || app.querySelector("#prop-estado") || app.querySelector("h1");
  el?.focus({ preventScroll: true });
}

// Aviso al salir de una vista con cambios sin guardar
let hashAnterior = location.hash;
window.addEventListener("hashchange", async () => {
  if (Formularios.hayCambios()) {
    const destino = location.hash;
    history.replaceState(null, "", hashAnterior || "#/proyectos");
    const salir = await confirmar({
      titulo: "¿Salir sin guardar?",
      mensaje: "Escribiste cambios que todavía no se guardaron. Si sales, se perderán.",
      aceptar: "Salir sin guardar", peligro: true,
    });
    if (!salir) return;
    Formularios.descartarTodos();
    location.hash = destino;
    return;
  }
  hashAnterior = location.hash;
  router();
});

// ---------- Marco: navegación, recientes y cuenta ----------

function marcarSeccion(seccion) {
  const actual = (el, si) => (si ? el.setAttribute("aria-current", "page") : el.removeAttribute("aria-current"));
  document.querySelectorAll("[data-seccion]").forEach((a) => actual(a, a.dataset.seccion === seccion));
  const proyecto = /^#\/proyectos\/(\d+)/.exec(location.hash)?.[1];
  document.querySelectorAll("#lista-recientes a").forEach((a) => actual(a, a.dataset.proyecto === proyecto));
}

function pintarMenusCuenta() {
  const u = API.usuario();
  document.querySelectorAll("[data-solo-admin]").forEach((el) => (el.hidden = u?.funcion !== "Admin"));
  document.querySelectorAll("[data-supervision]").forEach((el) => (el.hidden = !puedeSupervisar()));  // HU-07-005
  const html = u ? `
    <details class="menu-cuenta">
      <summary aria-label="Cuenta de ${escapar(u.nombre)}">
        ${avatar(u.nombre, u.nombre)}
        <span class="menu-cuenta-nombre"><strong>${escapar(u.nombre)}</strong><span>${escapar(u.funcion)}</span></span>
      </summary>
      <div class="menu-cuenta-panel">
        <button type="button" data-accion="tema">${icono("tema")}Tema: ${escapar(NOMBRES_TEMA[Tema.actual()])}</button>
        <button type="button" data-accion="atajos">${icono("teclado")}Atajos de teclado</button>
        <button type="button" data-accion="salir">${icono("salir")}Cerrar sesión</button>
      </div>
    </details>` : "";
  document.querySelectorAll("[data-menu-cuenta]").forEach((el) => (el.innerHTML = html));
}

function claveRecientes() {
  return `recientes-${API.usuario()?.id}`;
}

function anotarReciente(id) {
  let ids = [];
  try { ids = JSON.parse(almacen.leer(claveRecientes()) || "[]"); } catch { /* valor dañado */ }
  ids = [Number(id), ...ids.filter((x) => x !== Number(id))].slice(0, 5);
  almacen.guardar(claveRecientes(), JSON.stringify(ids));
  pintarRecientes();
}

// Solo muestra proyectos de la lista autorizada que devuelve el servidor
function pintarRecientes() {
  let ids = [];
  try { ids = JSON.parse(almacen.leer(claveRecientes()) || "[]"); } catch { /* valor dañado */ }
  const porId = new Map(Estado.proyectos.map((p) => [p.id, p]));
  const lista = ids.map((id) => porId.get(id)).filter(Boolean);
  for (const p of Estado.proyectos) if (lista.length < 5 && !lista.includes(p)) lista.push(p);
  document.getElementById("lista-recientes").innerHTML = lista.length
    ? lista.map((p) => `<li><a href="#/proyectos/${Number(p.id)}" data-proyecto="${Number(p.id)}">${escapar(p.nombre)}</a></li>`).join("")
    : `<li class="tenue">Aún no tienes proyectos</li>`;
  marcarSeccion(document.querySelector("[data-seccion][aria-current]")?.dataset.seccion);
}

async function cargarProyectos() {
  if (!API.token()) return;
  try {
    Estado.proyectos = await API.get("/api/proyectos");
    pintarRecientes();
  } catch { /* la barra lateral puede esperar a la siguiente consulta */ }
}

// HU-01-004 Cerrar sesión
async function cerrarSesion() {
  try { await API.post("/api/auth/logout"); } catch { /* la sesión ya no era válida */ }
  API.limpiarSesion();
  Formularios.descartarTodos();
  Estado.proyectos = [];
  Estado.tareasProyecto = null;
  ContadorAvisos.pintar(0);
  almacen.borrar("ruta-tras-login", sessionStorage);
  almacen.guardar("aviso-login", "Cerraste tu sesión.", sessionStorage);
  location.hash = "#/login";
}

ACCIONES.salir = cerrarSesion;
ACCIONES.recargar = () => recargar();
ACCIONES.saltar = () => (app.querySelector("h1") || app).focus();

// ---------- Delegación de eventos (sin onclick en las plantillas) ----------

document.addEventListener("click", (e) => {
  document.querySelectorAll("details.menu-cuenta[open]").forEach((d) => {
    if (!d.contains(e.target) || e.target.closest("[data-accion]")) d.open = false;
  });
  const el = e.target.closest("[data-accion]");
  if (el && ACCIONES[el.dataset.accion]) {
    ACCIONES[el.dataset.accion](el, e);
    return;
  }
  // La fila (o tarjeta) entera abre su elemento; el enlace del nombre sigue siendo lo accesible por teclado
  const fila = e.target.closest("[data-href]");
  if (fila && !e.target.closest("a, button, input, select, textarea, label")) {
    if (e.ctrlKey || e.metaKey) window.open(fila.dataset.href);
    else location.hash = fila.dataset.href;
  }
});

document.addEventListener("input", (e) => {
  if (e.target.matches("[data-filtra]")) filtrarTabla(e.target);
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  const menu = document.querySelector("details.menu-cuenta[open]");
  if (menu) {
    menu.open = false;
    menu.querySelector("summary").focus();
  }
});

// Al volver a la pestaña se refrescan función y nombre (pudieron cambiar con la sesión abierta)
let ultimoRefresco = Date.now();
document.addEventListener("visibilitychange", async () => {
  if (document.visibilityState !== "visible" || !API.token() || Date.now() - ultimoRefresco < 60000) return;
  ultimoRefresco = Date.now();
  const antes = API.usuario()?.funcion;
  try {
    const u = await API.refrescarUsuario();
    pintarMenusCuenta();
    if (u.funcion !== antes) recargar();
  } catch { /* 401: ya se mostró el login */ }
});

async function iniciar() {
  Paleta.iniciar();
  document.querySelectorAll("[data-tecla-mod]").forEach((k) => (k.textContent = `${TECLA_MOD} K`));
  if (API.token()) {
    try {
      await API.refrescarUsuario();  // localStorage puede tener una función vieja
      cargarProyectos();
    } catch { /* 401: la sesión expiró y ya se redirigió al login */ }
  }
  pintarMenusCuenta();
  router();
}

// ---------- Vistas ----------

function rutaTrasLogin() {
  const ruta = almacen.leer("ruta-tras-login", sessionStorage);
  almacen.borrar("ruta-tras-login", sessionStorage);
  return ruta && ruta.startsWith("#/") && ruta !== "#/login" ? ruta : "#/proyectos";
}

let avisoLogin = null;  // motivo de la salida; se conserva aunque el login se pinte dos veces

// HU-01-003 Iniciar sesión
function vistaLogin() {
  if (API.token()) { location.replace(rutaTrasLogin()); return null; }
  avisoLogin = almacen.leer("aviso-login", sessionStorage) || avisoLogin;
  almacen.borrar("aviso-login", sessionStorage);
  const aviso = avisoLogin;
  return {
    titulo: "Iniciar sesión",
    foco: "campo",
    html: `
      <div class="acceso">
        <p class="acceso-marca">${NOMBRE_APP}</p>
        <h1 tabindex="-1">Iniciar sesión</h1>
        ${aviso ? `<p class="nota" role="status">${icono("aviso")}${escapar(aviso)}</p>` : ""}
        <form id="f-login" class="formulario" data-sin-aviso-cambios="1">
          <label>Usuario <input name="usuario" required autocomplete="username" autocapitalize="none" spellcheck="false"></label>
          <label>Contraseña <input name="password" type="password" required autocomplete="current-password"></label>
          <p class="error-form" id="error-login" role="alert" hidden></p>
          <button class="boton ancho">Entrar</button>
        </form>
      </div>`,
    montar() {
      const form = document.getElementById("f-login");
      const error = document.getElementById("error-login");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const btn = form.querySelector("button.boton");
        btn.disabled = true;
        btn.textContent = "Entrando…";
        error.hidden = true;
        try {
          API.guardarSesion(await API.post("/api/auth/login", datosForm(form)));
          avisoLogin = null;
          pintarMenusCuenta();
          cargarProyectos();
          location.hash = rutaTrasLogin();
        } catch (err) {
          error.innerHTML = `${icono("error")}${escapar(err.message)}`;
          error.hidden = false;
          form.elements.password.select();
        } finally {
          btn.disabled = false;
          btn.textContent = "Entrar";
        }
      });
    },
  };
}

// HU-01-006 Consultar proyectos autorizados · HU-02-006 los cerrados en su propia pestaña
async function vistaProyectos(verCerrados) {
  const puedeCrear = FUNCIONES_CREAN_PROYECTO.includes(API.usuario()?.funcion);
  const todos = await API.get("/api/proyectos");
  Estado.proyectos = todos;
  pintarRecientes();
  const cerrados = todos.filter((p) => p.estado === "cerrado");
  const activos = todos.filter((p) => p.estado !== "cerrado");
  const proyectos = verCerrados ? cerrados : activos;
  const total = `${proyectos.length} proyecto${proyectos.length === 1 ? "" : "s"}${verCerrados ? ` cerrado${proyectos.length === 1 ? "" : "s"}` : ""}`;
  const pestana = (href, texto, n, actual) => `<a class="boton chico ${actual ? "" : "secundario"}" href="${href}"
      ${actual ? 'aria-current="page"' : ""}>${texto} <span class="conteo">${n}</span></a>`;
  return {
    titulo: verCerrados ? "Proyectos cerrados" : "Mis proyectos",
    seccion: "proyectos",
    nueva: puedeCrear ? "#/proyectos/nuevo" : null,
    textoNueva: "Nuevo proyecto",
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Mis proyectos</h1>
          <p class="subtitulo" data-conteo="tabla-proyectos" data-total="${total}">${total}</p>
        </div>
        <div class="encabezado-acciones">
          ${proyectos.length ? buscadorTabla("tabla-proyectos", "Buscar proyecto") : ""}
          ${puedeCrear ? `<a class="boton" href="#/proyectos/nuevo">${icono("mas")}Nuevo proyecto</a>` : ""}
        </div>
      </header>
      ${cerrados.length ? `<nav class="selector-vista pestanas-proyectos" aria-label="Proyectos">
        ${pestana("#/proyectos", "Activos", activos.length, !verCerrados)}${pestana("#/proyectos?cerrados", "Cerrados", cerrados.length, verCerrados)}
      </nav>` : ""}
      ${proyectos.length === 0
        ? (verCerrados
          ? vacio("No hay proyectos cerrados", "Cuando el responsable cierre un proyecto en el que participas, podrás consultarlo aquí.")
          : puedeCrear
          ? vacio("Aún no hay proyectos activos", "Crea uno y da acceso a tu equipo.",
              `<a class="boton" href="#/proyectos/nuevo">${icono("mas")}Crear proyecto</a>`)
          : vacio("Aún no participas en ningún proyecto activo",
              "Cuando el responsable de un proyecto te dé acceso, aparecerá aquí."))
        : `<div class="tabla-marco">
          <table class="tabla tabla-tarjetas" id="tabla-proyectos">
            <thead><tr>${th("Nombre", { clase: "col-principal" })}${th("Responsable")}${th("Inicio")}${th("Fin")}${
              verCerrados ? th("Cerrado") : th("Estado")}</tr></thead>
            <tbody>
              ${proyectos.map((p) => `
                <tr data-href="#/proyectos/${Number(p.id)}">
                  <td data-label="Nombre" class="celda-principal"><a href="#/proyectos/${Number(p.id)}">${escapar(p.nombre)}</a></td>
                  <td data-label="Responsable" data-orden="${escapar(p.responsable_nombre)}">${persona(p.responsable_nombre)}</td>
                  <td data-label="Inicio" data-orden="${escapar(p.fecha_inicio)}" class="num">${fecha(p.fecha_inicio)}</td>
                  <td data-label="Fin" data-orden="${escapar(p.fecha_fin)}" class="num">${fecha(p.fecha_fin)}</td>
                  ${verCerrados
                    ? `<td data-label="Cerrado" data-orden="${escapar(p.cerrado_en || "")}">${momento(p.cerrado_en)}
                         <span class="tenue">· ${escapar(p.cerrado_por_nombre || "—")}</span></td>`
                    : `<td data-label="Estado" data-orden="${ORDEN_ESTADO[p.estado] || 9}">${etiquetaProyecto(p.estado)}</td>`}
                </tr>`).join("")}
            </tbody>
          </table>
        </div>`}`,
  };
}

// Errores del servidor que corresponden a un campo concreto
const CAMPO_DEL_ERROR = [[/fecha de fin/i, "fecha_fin"], [/responsable/i, "responsable_id"]];

function campoDelError(e) {
  const campo = CAMPO_DEL_ERROR.find(([re]) => re.test(e.message))?.[1];
  return campo ? { [campo]: e.message } : null;
}

// HU-02-001 Crear proyecto
async function vistaNuevoProyecto() {
  if (!FUNCIONES_CREAN_PROYECTO.includes(API.usuario()?.funcion)) throw sinAcceso();
  const usuarios = await API.get("/api/usuarios");
  const responsables = usuarios.filter((x) => FUNCIONES_CREAN_PROYECTO.includes(x.funcion));
  const yo = API.usuario();
  return {
    titulo: "Nuevo proyecto",
    seccion: "proyectos",
    foco: "campo",
    migas: [{ texto: "Mis proyectos", href: "#/proyectos" }, { texto: "Nuevo proyecto" }],
    html: `
      <div class="hoja">
        <h1 tabindex="-1">Nuevo proyecto</h1>
        <form id="f-proyecto" class="formulario">
          <label>Nombre <input name="nombre" required maxlength="120"></label>
          <label>Objetivo <textarea name="objetivo" required rows="3" maxlength="1000"></textarea></label>
          <label>Responsable
            <select name="responsable_id" required>
              ${responsables.map((r) => `<option value="${Number(r.id)}" ${r.id === yo.id ? "selected" : ""}>${escapar(r.nombre)}</option>`).join("")}
            </select>
          </label>
          <div class="fila">
            <label>Fecha de inicio <input type="date" name="fecha_inicio" required></label>
            <label>Fecha de fin <input type="date" name="fecha_fin" required></label>
          </div>
          <div class="acciones-form">
            <button class="boton">Crear proyecto</button>
            <a class="boton secundario" href="#/proyectos">Cancelar</a>
            <span class="pista"><kbd class="atajo-tecla">${TECLA_MOD} Enter</kbd> para crear</span>
          </div>
        </form>
      </div>`,
    montar() {
      const form = document.getElementById("f-proyecto");
      const clave = nuevaClave();  // HU-08-002
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        Formularios.limpiarErrores(form);
        const d = datosForm(form);
        if (d.fecha_fin < d.fecha_inicio) {
          Formularios.marcarErrores(form, { fecha_fin: "No puede ser anterior a la fecha de inicio" });
          toast("La fecha de fin no puede ser anterior a la de inicio", "error");
          return;
        }
        d.responsable_id = Number(d.responsable_id);
        const p = await guardar(form.querySelector("button"), () => API.crear("/api/proyectos", d, clave),
          "Proyecto creado", { form, campoDe: campoDelError });
        if (p) {
          cargarProyectos();
          location.hash = `#/proyectos/${p.id}`;
        }
      });
    },
  };
}

// HU-02-002 Ficha del proyecto + HU-03-005 Tareas (lista o HU-07-001 tablero) + HU-01-005 Participantes
async function vistaProyecto(id) {
  const p = await API.get(`/api/proyectos/${id}`);
  const modo = vistaTareasElegida();
  const filtros = filtrosTareas(id);
  const hayFiltros = Object.keys(filtros).length > 0;
  const [participantes, datosTareas, usuarios, cambios, actividad, reglas, resumenTareas] = await Promise.all([
    API.get(`/api/proyectos/${id}/participantes`), API.get(`/api/proyectos/${id}/${modo}${consultaFiltros(filtros)}`),
    p.soy_responsable ? API.get("/api/usuarios") : [], API.get(`/api/proyectos/${id}/historial`),
    API.get(`/api/proyectos/${id}/actividad`), API.get("/api/archivos/reglas"),
    API.get(`/api/proyectos/${id}/resumen`),
  ]);
  const tareas = modo === "tablero" ? datosTareas.columnas.flatMap((c) => c.tareas) : datosTareas;
  const ids = new Set(participantes.map((x) => x.id));
  const candidatos = usuarios.filter((x) => !ids.has(x.id));
  Estado.tareasProyecto = { pid: p.id, nombre: p.nombre, tareas };
  anotarReciente(p.id);
  const nuevaTarea = `#/proyectos/${p.id}/tareas/nueva`;
  const planifica = p.soy_responsable && p.editable;  // HU-02-005: cerrado → solo consulta
  const abiertas = tareas.filter((t) => t.estado !== "terminada").length;
  const resumen = `${abiertas} abierta${abiertas === 1 ? "" : "s"} de ${tareas.length}`;

  return {
    titulo: p.nombre,
    seccion: "proyectos",
    nueva: planifica ? nuevaTarea : null,
    textoNueva: `Nueva tarea en «${p.nombre}»`,
    migas: [{ texto: p.estado === "cerrado" ? "Proyectos cerrados" : "Mis proyectos",
              href: p.estado === "cerrado" ? "#/proyectos?cerrados" : "#/proyectos" }, { texto: p.nombre }],
    html: `
      <header class="encabezado">
        <div>
          <div class="titulo-con-chip"><h1 tabindex="-1">${escapar(p.nombre)}</h1>${etiquetaProyecto(p.estado)}</div>
          <p class="subtitulo">
            Responsable: ${escapar(p.responsable_nombre)} ·
            <span class="num">${fecha(p.fecha_inicio)} – ${fecha(p.fecha_fin)}</span>
            ${p.estado_cambiado_en ? ` · ${escapar(ESTADOS_PROYECTO[p.estado])} desde ${momento(p.estado_cambiado_en)}, por ${escapar(p.estado_actor_nombre)}` : ""}
          </p>
        </div>
        <div class="encabezado-acciones">
          ${botonCopiarEnlace(`#/proyectos/${p.id}`)}
          ${p.transiciones.includes("en_curso") ? `<button type="button" class="boton secundario" data-accion="iniciar-proyecto"
              data-id="${Number(p.id)}" data-estado="${escapar(p.estado)}">${icono("est-en_curso")}Iniciar ejecución</button>` : ""}
          ${p.puedo_cerrar ? `<a class="boton secundario" href="#/proyectos/${p.id}/cerrar">${icono("est-cerrado")}Cerrar proyecto</a>` : ""}
          ${planifica ? `<a class="boton secundario" href="#/proyectos/${p.id}/editar">Editar proyecto</a>` : ""}
          ${planifica ? `<a class="boton" href="${nuevaTarea}">${icono("mas")}Nueva tarea</a>` : ""}
        </div>
      </header>

      ${p.estado === "cerrado" ? bandaCierre(p) : ""}

      <section class="bloque">
        <h2 class="titulo-seccion">Objetivo</h2>
        <p class="texto-largo">${escapar(p.objetivo)}</p>
      </section>

      ${resumenTareas.total ? resumenProyecto(p.id, resumenTareas) : ""}

      <section class="bloque" aria-labelledby="titulo-tareas">
        <div class="encabezado-seccion">
          <h2 class="titulo-seccion" id="titulo-tareas">Tareas
            <span class="conteo" data-conteo="tabla-tareas" data-total="${resumen}">${resumen}</span></h2>
          ${tareas.length || hayFiltros ? `<div class="encabezado-acciones">
            ${modo === "tareas" && tareas.length ? buscadorTabla("tabla-tareas", "Buscar tarea") : ""}
            ${selectorVistaTareas(modo)}
          </div>` : ""}
        </div>
        ${tareas.length || hayFiltros ? barraFiltros(p.id, filtros, participantes) : ""}
        ${tareas.length === 0 && hayFiltros
          ? vacio("Ninguna tarea cumple los filtros", "Cambia algún filtro o quítalos para ver todas las tareas.",
              `<button type="button" class="boton secundario" data-accion="quitar-filtros" data-proyecto="${p.id}">Quitar filtros</button>`)
          : tareas.length === 0
          ? (planifica
            ? vacio("Este proyecto no tiene tareas", "Divide el objetivo en tareas y asígnalas al equipo.",
                `<a class="boton" href="${nuevaTarea}">${icono("mas")}Crear la primera tarea</a>`)
            : vacio("Este proyecto no tiene tareas", "El responsable del proyecto aún no ha creado ninguna."))
          : modo === "tablero" ? tableroTareas(datosTareas.columnas) : tablaTareas(tareas)}
      </section>

      <section class="bloque" aria-labelledby="titulo-participantes">
        <h2 class="titulo-seccion" id="titulo-participantes">Participantes <span class="conteo">${participantes.length}</span></h2>
        <ul class="lista-personas">
          ${participantes.map((x) => `
            <li>
              ${persona(x.nombre)}
              <span class="tenue">${escapar(x.usuario)}</span>
              <span class="funcion">${escapar(x.funcion)}${x.id === p.responsable_id ? " · a cargo del proyecto" : ""}</span>
              ${p.soy_responsable && x.id !== p.responsable_id
                ? `<button type="button" class="boton chico peligro-suave" data-accion="retirar" data-id="${Number(x.id)}"
                     data-proyecto="${Number(p.id)}" data-nombre="${escapar(x.nombre)}">Retirar</button>` : ""}
            </li>`).join("")}
        </ul>
        ${p.soy_responsable ? (candidatos.length ? `
          <form id="f-participante" class="formulario en-linea" data-sin-aviso-cambios="1">
            <label><span class="solo-lector">Persona</span>
              <select name="usuario_id" required>
                <option value="">Seleccionar persona…</option>
                ${candidatos.map((c) => `<option value="${Number(c.id)}">${escapar(c.nombre)} (${escapar(c.funcion)})</option>`).join("")}
              </select>
            </label>
            <button class="boton secundario">Dar acceso</button>
          </form>` : `<p class="tenue">Todas las cuentas activas ya participan.</p>`) : ""}
      </section>

      ${seccionColaboracion(actividad, reglas, "el proyecto", { soloLectura: !p.editable })}

      ${cambios.length ? `
      <section class="bloque" aria-labelledby="titulo-cambios">
        <div class="encabezado-seccion">
          <h2 class="titulo-seccion" id="titulo-cambios">Cambios del plan <span class="conteo">${cambios.length}</span></h2>
          <a class="boton chico secundario" href="#/proyectos/${p.id}/historial">${icono("reloj")}Ver historial completo</a>
        </div>
        <ol class="lista-cambios">${cambios.slice(-RECIENTES_FICHA).reverse().map(cambioProyecto).join("")}</ol>
        ${cambios.length > RECIENTES_FICHA ? `<p class="tenue">Se muestran los ${RECIENTES_FICHA} más recientes.</p>` : ""}
      </section>` : ""}`,

    montar() {
      montarComentarios(`/api/proyectos/${id}/comentarios`);  // HU-05-001
      montarArchivos(`/api/proyectos/${id}/archivos`);  // HU-05-002

      // HU-07-002: cada cambio de filtro vuelve a consultar al servidor
      const fFiltros = document.getElementById("f-filtros");
      fFiltros?.addEventListener("change", () => {
        guardarFiltros(id, datosForm(fFiltros));
        recargar();
      });
      fFiltros?.addEventListener("submit", (e) => e.preventDefault());

      const form = document.getElementById("f-participante");
      form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const usuario_id = Number(datosForm(form).usuario_id);
        const ok = await guardar(form.querySelector("button"),
          () => API.post(`/api/proyectos/${id}/participantes`, { usuario_id }), "Participante agregado", { form });
        if (ok) recargar();
      });
    },
  };
}

// HU-02-004 Cambiar estado del proyecto: planificado → en curso (el cierre tiene su propio procedimiento)
ACCIONES["iniciar-proyecto"] = async (btn) => {
  const si = await confirmar({
    titulo: "¿Iniciar la ejecución del proyecto?",
    mensaje: "El proyecto pasará de «Planificado» a «En curso». Quedará registrado quién lo cambió y cuándo.",
    aceptar: "Iniciar ejecución",
  });
  if (!si) return;
  const ok = await guardar(btn, () => API.put(`/api/proyectos/${btn.dataset.id}/estado`,
    { estado: "en_curso", anterior: btn.dataset.estado }), "Proyecto en curso");
  if (ok) { cargarProyectos(); recargar(); }
  else recargar();  // 409/400: muestra el estado vigente
};

// ---------- HU-02-005 Cerrar proyecto ----------

/** Constancia del cierre: cuándo, quién, cuántas tareas seguían abiertas y por qué. */
function bandaCierre(p) {
  const abiertas = Number(p.cierre_tareas_abiertas) || 0;
  return `
    <section class="banda-cierre" aria-labelledby="titulo-cierre">
      <h2 id="titulo-cierre">${icono("est-cerrado")}Proyecto cerrado</h2>
      <p>Cerrado ${momento(p.cerrado_en)} por ${escapar(p.cerrado_por_nombre || "—")}.
        ${abiertas ? `${abiertas} tarea${abiertas === 1 ? " seguía abierta" : "s seguían abiertas"} al cerrarlo.` : "Todas sus tareas estaban terminadas."}
        Su información se conserva solo para consulta.</p>
      ${p.cierre_justificacion ? `<p class="texto-largo"><strong>Justificación:</strong> ${escapar(p.cierre_justificacion)}</p>` : ""}
    </section>`;
}

async function vistaCerrarProyecto(id) {
  const p = await API.get(`/api/proyectos/${id}`);
  if (!p.soy_responsable) throw sinAcceso();
  if (!p.puedo_cerrar) { location.replace(`#/proyectos/${p.id}`); return null; }  // ya cerrado
  const { abiertas } = await API.get(`/api/proyectos/${id}/cierre`);
  const n = abiertas.length;
  return {
    titulo: `Cerrar · ${p.nombre}`,
    seccion: "proyectos",
    migas: [{ texto: "Mis proyectos", href: "#/proyectos" }, { texto: p.nombre, href: `#/proyectos/${p.id}` },
            { texto: "Cerrar" }],
    html: `
      <div class="hoja hoja-ancha">
        <h1 tabindex="-1">Cerrar proyecto</h1>
        <p class="subtitulo">El proyecto dejará de estar activo. Sus tareas, comentarios, archivos e historial se conservan
          para consulta, pero ya no se podrán modificar. Quedará registrado quién lo cerró y cuándo.</p>
        <section class="bloque" aria-labelledby="titulo-abiertas">
          <h2 class="titulo-seccion" id="titulo-abiertas">Tareas abiertas <span class="conteo">${n}</span></h2>
          ${n ? `<p class="nota" role="note">${icono("aviso")}Estas tareas no están terminadas. Termínalas antes de cerrar
                   o documenta la excepción: seguirán abiertas tal como están.</p>
                 ${tablaTareas(abiertas, { id: "tabla-abiertas" })}`
              : `<p class="tenue">${icono("ok")} Todas las tareas están terminadas.</p>`}
        </section>
        <form id="f-cierre" class="formulario" data-revisadas="${escapar(JSON.stringify(abiertas.map((t) => t.id)))}">
          <label>${n ? "Justificación de la excepción" : "Nota de cierre (opcional)"}
            <textarea name="justificacion" rows="3" maxlength="1000" ${n ? "required" : ""}
              placeholder="${n ? "Por qué se cierra con tareas abiertas (p. ej. el cliente canceló esa fase)" : "Cómo terminó el proyecto"}"></textarea></label>
          <div class="acciones-form">
            <button class="boton peligro">${icono("est-cerrado")}Cerrar proyecto</button>
            <a class="boton secundario" href="#/proyectos/${p.id}">Cancelar</a>
          </div>
        </form>
      </div>`,
    montar() {
      const form = document.getElementById("f-cierre");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const si = await confirmar({
          titulo: `¿Cerrar «${p.nombre}»?`,
          mensaje: "Ya no se podrán crear ni modificar tareas, comentarios ni archivos. Esta acción no se puede deshacer desde la aplicación.",
          aceptar: "Cerrar proyecto", peligro: true,
        });
        if (!si) return;
        const datos = { justificacion: datosForm(form).justificacion || null, revisadas: JSON.parse(form.dataset.revisadas) };
        const ok = await guardar(form.querySelector("button:not([type=button])"),
          () => API.post(`/api/proyectos/${id}/cierre`, datos), "Proyecto cerrado", {
            form, alConflicto: () => { Formularios.marcarLimpio(form); recargar(); } });  // la lista cambió: mostrar la vigente
        if (ok) {
          cargarProyectos();
          location.hash = `#/proyectos/${id}`;
        }
      });
    },
  };
}

// ---------- HU-02-006 Historial del proyecto ----------

const RECIENTES_FICHA = 5;
// Grupos para filtrar el historial (las fechas de inicio y fin van juntas)
const GRUPOS_HISTORIAL = { estado: "Estado", responsable_id: "Responsable", fechas: "Fechas", objetivo: "Objetivo", nombre: "Nombre" };
const grupoCambio = (campo) => (campo.startsWith("fecha_") ? "fechas" : campo);

async function vistaHistorialProyecto(id) {
  const [p, cambios] = await Promise.all([API.get(`/api/proyectos/${id}`), API.get(`/api/proyectos/${id}/historial`)]);
  const cuenta = {};
  cambios.forEach((h) => (cuenta[grupoCambio(h.campo)] = (cuenta[grupoCambio(h.campo)] || 0) + 1));
  return {
    titulo: `Historial · ${p.nombre}`,
    seccion: "proyectos",
    migas: [{ texto: "Mis proyectos", href: p.estado === "cerrado" ? "#/proyectos?cerrados" : "#/proyectos" },
            { texto: p.nombre, href: `#/proyectos/${p.id}` }, { texto: "Historial" }],
    html: `
      <header class="encabezado">
        <div>
          <div class="titulo-con-chip"><h1 tabindex="-1">Historial del proyecto</h1>${etiquetaProyecto(p.estado)}</div>
          <p class="subtitulo">${escapar(p.nombre)} · ${cambios.length} cambio${cambios.length === 1 ? "" : "s"} registrado${cambios.length === 1 ? "" : "s"},
            del más reciente al más antiguo. Cada uno conserva quién lo hizo, cuándo y el valor anterior y el nuevo.</p>
        </div>
      </header>
      ${p.estado === "cerrado" ? bandaCierre(p) : ""}
      ${cambios.length ? `
        <div class="selector-vista filtro-historial" role="group" aria-label="Mostrar cambios de">
          <button type="button" class="boton chico" data-accion="filtrar-historial" data-grupo="" aria-pressed="true">Todos <span class="conteo">${cambios.length}</span></button>
          ${Object.entries(GRUPOS_HISTORIAL).filter(([g]) => cuenta[g]).map(([g, t]) => `
            <button type="button" class="boton chico secundario" data-accion="filtrar-historial" data-grupo="${g}" aria-pressed="false">${t} <span class="conteo">${cuenta[g]}</span></button>`).join("")}
        </div>
        <ol class="lista-cambios lista-historial">${cambios.slice().reverse().map((h) =>
          cambioProyecto(h).replace("<li>", `<li data-grupo="${grupoCambio(h.campo)}">`)).join("")}</ol>`
      : vacio("Sin cambios registrados", "El plan del proyecto no ha cambiado desde que se creó.")}`,
  };
}

ACCIONES["filtrar-historial"] = (btn) => {
  btn.parentElement.querySelectorAll("button").forEach((b) => {
    b.setAttribute("aria-pressed", b === btn);
    b.classList.toggle("secundario", b !== btn);
  });
  document.querySelectorAll(".lista-historial > li").forEach((li) => {
    li.hidden = Boolean(btn.dataset.grupo) && li.dataset.grupo !== btn.dataset.grupo;
  });
};

// HU-02-003: un cambio del plan con valor anterior, nuevo, actor y fecha
const CAMPOS_PROYECTO = { nombre: "Nombre", objetivo: "Objetivo", responsable_id: "Responsable",
                          fecha_inicio: "Fecha de inicio", fecha_fin: "Fecha de fin", estado: "Estado" };

function valorCambioProyecto(h, cual) {
  if (h.campo === "responsable_id") return escapar(h[`${cual}_nombre`]);
  const valor = h[`valor_${cual}`];
  if (h.campo === "estado") return escapar(ESTADOS_PROYECTO[valor] || valor);  // HU-02-004
  return h.campo.startsWith("fecha_") ? fecha(valor) : escapar(valor);
}

function cambioProyecto(h) {
  return `
    <li>
      <p><span class="etiqueta-campo">${escapar(CAMPOS_PROYECTO[h.campo] || h.campo)}</span>
        <span class="valor-anterior">${valorCambioProyecto(h, "anterior")}</span> → ${valorCambioProyecto(h, "nuevo")}</p>
      <p class="meta">${escapar(h.actor_nombre)} · ${momento(h.creado_en)}</p>
    </li>`;
}

// HU-02-003 Actualizar datos del proyecto (solo su responsable)
async function vistaEditarProyecto(id) {
  const p = await API.get(`/api/proyectos/${id}`);
  if (!p.soy_responsable) throw sinAcceso();
  const usuarios = await API.get("/api/usuarios");
  const responsables = usuarios.filter((x) => FUNCIONES_CREAN_PROYECTO.includes(x.funcion));
  if (!responsables.some((r) => r.id === p.responsable_id)) {
    responsables.unshift({ id: p.responsable_id, nombre: p.responsable_nombre });
  }
  return {
    titulo: `Editar · ${p.nombre}`,
    seccion: "proyectos",
    foco: "campo",
    migas: [{ texto: "Mis proyectos", href: "#/proyectos" }, { texto: p.nombre, href: `#/proyectos/${p.id}` },
            { texto: "Editar" }],
    html: `
      <div class="hoja">
        <h1 tabindex="-1">Editar proyecto</h1>
        <form id="f-editar-proyecto" class="formulario" data-anteriores="${escapar(JSON.stringify({
          nombre: p.nombre, objetivo: p.objetivo, responsable_id: p.responsable_id,
          fecha_inicio: p.fecha_inicio, fecha_fin: p.fecha_fin }))}">
          <label>Nombre <input name="nombre" required maxlength="120" value="${escapar(p.nombre)}"></label>
          <label>Objetivo <textarea name="objetivo" required rows="3" maxlength="1000">${escapar(p.objetivo)}</textarea></label>
          <label>Responsable
            <select name="responsable_id" required>
              ${responsables.map((r) => `<option value="${Number(r.id)}" ${r.id === p.responsable_id ? "selected" : ""}>${escapar(r.nombre)}</option>`).join("")}
            </select>
          </label>
          <div class="fila">
            <label>Fecha de inicio <input type="date" name="fecha_inicio" required value="${escapar(p.fecha_inicio)}"></label>
            <label>Fecha de fin <input type="date" name="fecha_fin" required value="${escapar(p.fecha_fin)}"></label>
          </div>
          <p class="pista-campo">Si cambias el responsable, dejarás de administrar este proyecto; seguirás como participante.</p>
          <div class="acciones-form">
            <button class="boton">Guardar cambios</button>
            <a class="boton secundario" href="#/proyectos/${p.id}">Cancelar</a>
          </div>
        </form>
      </div>`,
    montar() {
      const form = document.getElementById("f-editar-proyecto");
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        Formularios.limpiarErrores(form);
        const d = datosForm(form);
        if (d.fecha_fin < d.fecha_inicio) {
          Formularios.marcarErrores(form, { fecha_fin: "No puede ser anterior a la fecha de inicio" });
          toast("La fecha de fin no puede ser anterior a la de inicio", "error");
          return;
        }
        d.responsable_id = Number(d.responsable_id);
        d.anteriores = leidos(form);  // HU-08-003
        const ok = await guardar(form.querySelector("button:not([type=button])"), () => API.put(`/api/proyectos/${id}`, d),
          "Proyecto actualizado", { form, campoDe: campoDelError,
            alConflicto: (err) => mostrarConflicto(form, err, (c, v) => `${escapar(CAMPOS_PROYECTO[c] || c)}: ${
              c === "responsable_id" ? escapar(v.responsable_nombre) : c.startsWith("fecha_") ? fecha(v[c]) : escapar(v[c])}`) });
        if (ok) {
          cargarProyectos();
          location.hash = `#/proyectos/${id}`;
        }
      });
    },
  };
}

// HU-01-005 Retirar participante, con confirmación
ACCIONES.retirar = async (btn) => {
  const si = await confirmar({
    titulo: `¿Retirar a ${btn.dataset.nombre}?`,
    mensaje: "Dejará de ver el proyecto y no podrá hacer nuevas acciones en él. Lo que ya hizo se conserva.",
    aceptar: "Retirar acceso", peligro: true,
  });
  if (!si) return;
  const ok = await guardar(btn,
    () => API.del(`/api/proyectos/${btn.dataset.proyecto}/participantes/${btn.dataset.id}`), "Participante retirado");
  if (ok) recargar();
};

// HU-01-001 Registrar cuenta + HU-01-002 Función inicial (solo Admin)
async function vistaUsuarios() {
  if (API.usuario()?.funcion !== "Admin") throw sinAcceso();
  const [funciones, usuarios] = await Promise.all([API.get("/api/funciones"), API.get("/api/usuarios")]);
  const total = `${usuarios.length} cuenta${usuarios.length === 1 ? "" : "s"} activa${usuarios.length === 1 ? "" : "s"}`;
  return {
    titulo: "Usuarios",
    seccion: "usuarios",
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Usuarios</h1>
          <p class="subtitulo" data-conteo="tabla-usuarios" data-total="${total}">${total}</p>
        </div>
      </header>
      <div class="dos-columnas">
        <section class="bloque" aria-labelledby="titulo-registro">
          <h2 class="titulo-seccion" id="titulo-registro">Registrar cuenta</h2>
          <form id="f-usuario" class="formulario">
            <label>Usuario <span class="opcional">identificador único</span>
              <input name="usuario" required minlength="3" maxlength="50" autocomplete="off" autocapitalize="none" spellcheck="false"></label>
            <label>Nombre completo <input name="nombre" required maxlength="100" autocomplete="off"></label>
            <label>Contraseña inicial <input name="password" type="password" required minlength="6" maxlength="100" autocomplete="new-password"></label>
            <label>Función
              <select name="funcion_id" required>
                <option value="">Seleccionar…</option>
                ${funciones.map((f) => `<option value="${Number(f.id)}">${escapar(f.nombre)}</option>`).join("")}
              </select>
            </label>
            <div class="acciones-form"><button class="boton">Registrar cuenta</button></div>
          </form>
        </section>
        <section class="bloque" aria-labelledby="titulo-cuentas">
          <div class="encabezado-seccion">
            <h2 class="titulo-seccion" id="titulo-cuentas">Cuentas activas</h2>
            ${buscadorTabla("tabla-usuarios", "Buscar cuenta")}
          </div>
          <div class="tabla-marco">
            <table class="tabla tabla-tarjetas" id="tabla-usuarios">
              <thead><tr>${th("Nombre", { clase: "col-principal" })}${th("Usuario")}${th("Función")}</tr></thead>
              <tbody>
                ${usuarios.map((x) => `
                  <tr>
                    <td data-label="Nombre" class="celda-principal" data-orden="${escapar(x.nombre)}">${persona(x.nombre)}</td>
                    <td data-label="Usuario">${escapar(x.usuario)}</td>
                    <td data-label="Función">${escapar(x.funcion)}</td>
                  </tr>`).join("")}
              </tbody>
            </table>
          </div>
        </section>
      </div>`,
    montar() {
      const form = document.getElementById("f-usuario");
      const clave = nuevaClave();  // HU-08-002: un reintento no responde "ya existe"
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const d = datosForm(form);
        d.funcion_id = Number(d.funcion_id);
        const ok = await guardar(form.querySelector("button.boton"),
          () => API.crear("/api/usuarios", d, clave), `Cuenta «${d.usuario}» registrada`, { form });
        if (ok) recargar();
      });
    },
  };
}

// HU-01-007 Pantalla de "sin acceso" (misma para recursos ajenos e inexistentes)
function vistaSinAcceso() {
  return {
    titulo: "Sin acceso",
    html: `
      <div class="estado-pagina">
        ${icono("bloqueo", "icono-grande")}
        <h1 tabindex="-1">Sin acceso</h1>
        <p>No tienes permiso para ver este contenido o no está disponible.
           Si crees que deberías verlo, pide acceso al responsable del proyecto.</p>
        <a class="boton" href="#/proyectos">Volver a mis proyectos</a>
      </div>`,
  };
}

function vistaError(e) {
  return {
    titulo: "No se pudo cargar",
    html: `
      <div class="estado-pagina">
        ${icono("error", "icono-grande")}
        <h1 tabindex="-1">No se pudo cargar</h1>
        <p>${escapar(e.message)}</p>
        <button type="button" class="boton" data-accion="recargar">Reintentar</button>
      </div>`,
  };
}

// Al final: todas las declaraciones de este archivo ya existen
iniciar();
