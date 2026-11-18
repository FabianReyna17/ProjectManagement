// Vistas de tareas (Sprint 2). Cada vista devuelve { titulo, html, montar, ... } y el router la pinta.

function opcionesPersonas(personas, seleccionado, vacioTexto) {
  return (vacioTexto ? `<option value="">${escapar(vacioTexto)}</option>` : "") +
    personas.map((x) => `<option value="${Number(x.id)}" ${x.id === seleccionado ? "selected" : ""}>${escapar(x.nombre)}</option>`).join("");
}

/** Tabla de tareas; cada fila abre el detalle. Reutilizada por el proyecto y "Mis tareas". */
function tablaTareas(tareas, { id = "tabla-tareas", conProyecto = false, conAcciones = false, vacioHtml = "" } = {}) {
  if (tareas.length === 0) return vacioHtml || vacio("No hay tareas.");
  return `
    <div class="tabla-marco">
    <table class="tabla tabla-tarjetas" id="${id}">
      <thead><tr>
        ${th("Tarea", { clase: "col-principal" })}${conProyecto ? th("Proyecto") : th("Responsable")}
        ${th("Prioridad")}${th("Fecha límite")}${th("Estado")}${conAcciones ? th("Acciones", { ordenable: false }) : ""}
      </tr></thead>
      <tbody>
        ${tareas.map((t) => `
          <tr data-href="#/tareas/${Number(t.id)}" class="${t.bloqueada ? "fila-bloqueada" : ""}">
            <td data-label="Tarea" class="celda-principal"><a href="#/tareas/${Number(t.id)}">${escapar(t.nombre)}</a></td>
            ${conProyecto
              ? `<td data-label="Proyecto">${escapar(t.proyecto_nombre)}</td>`
              : `<td data-label="Responsable" data-orden="${escapar(t.responsable_nombre || "")}">${t.responsable_nombre ? persona(t.responsable_nombre) : sinAsignar()}</td>`}
            <td data-label="Prioridad" data-orden="${ORDEN_PRIORIDAD[t.prioridad] || 9}">${etiquetaPrioridad(t.prioridad)}</td>
            <td data-label="Fecha límite" data-orden="${escapar(t.fecha_limite || "")}" class="num">
              <span class="fecha-con-marca">${fecha(t.fecha_limite, "Sin fecha")}${etiquetaVencimiento(t)}</span></td>
            <td data-label="Estado" data-orden="${t.bloqueada ? 0 : ORDEN_ESTADO[t.estado] || 9}">${etiquetaEstado(t.estado, t.bloqueada)}</td>
            ${conAcciones ? `<td data-label="Acciones" class="acciones">${botonesEstado(t.id, t.estado, transicionesPosibles(t.estado, t.bloqueada))}</td>` : ""}
          </tr>`).join("")}
      </tbody>
    </table>
    </div>`;
}

// ---------- HU-07-001 Tablero de tareas ----------

// El valor es también el recurso de la API: /api/proyectos/{id}/tareas o /tablero
const VISTAS_TAREAS = { tareas: { texto: "Lista", icono: "lista" }, tablero: { texto: "Tablero", icono: "tablero" } };

function vistaTareasElegida() {
  const v = almacen.leer("vista-tareas");
  return v in VISTAS_TAREAS ? v : "tareas";
}

function selectorVistaTareas(actual) {
  return `<div class="selector-vista" role="group" aria-label="Ver tareas como">${Object.entries(VISTAS_TAREAS).map(([v, x]) => `
    <button type="button" class="boton chico ${v === actual ? "" : "secundario"}" data-accion="vista-tareas"
            data-vista="${v}" aria-pressed="${v === actual}">${icono(x.icono)}${x.texto}</button>`).join("")}</div>`;
}

ACCIONES["vista-tareas"] = (btn) => {
  if (btn.getAttribute("aria-pressed") === "true") return;
  almacen.guardar("vista-tareas", btn.dataset.vista);
  recargar();
};

// ---------- HU-07-002 Filtros (por proyecto; se recuerdan solo en esta pestaña) ----------

const CAMPOS_FILTRO = ["estado", "responsable", "prioridad", "vencimiento", "bloqueo"];

function filtrosTareas(pid) {
  let guardados = {};
  try { guardados = JSON.parse(almacen.leer(`filtros-${pid}`, sessionStorage) || "{}"); } catch { /* valor dañado */ }
  return Object.fromEntries(CAMPOS_FILTRO.filter((c) => guardados[c]).map((c) => [c, String(guardados[c])]));
}

function guardarFiltros(pid, valores) {
  const activos = Object.fromEntries(CAMPOS_FILTRO.filter((c) => valores[c]).map((c) => [c, valores[c]]));
  almacen.guardar(`filtros-${pid}`, JSON.stringify(activos), sessionStorage);
}

function consultaFiltros(filtros) {
  const q = new URLSearchParams(filtros).toString();
  return q ? `?${q}` : "";
}

function barraFiltros(pid, filtros, participantes) {
  const opciones = {
    estado: ["Estado", "Todos", Object.entries(ESTADOS_TAREA)],
    responsable: ["Responsable", "Todos", [["sin_asignar", "Sin asignar"], ...participantes.map((x) => [String(x.id), x.nombre])]],
    prioridad: ["Prioridad", "Todas", Object.entries(PRIORIDADES)],
    vencimiento: ["Vencimiento", "Cualquiera", [["vencida", "Vencidas"], ["por_vencer", "Por vencer"]]],
    bloqueo: ["Bloqueo", "Todas", [["bloqueada", "Bloqueadas"], ["sin_bloqueo", "Sin bloqueo"]]],
  };
  const activos = CAMPOS_FILTRO.filter((c) => filtros[c]).map((c) => {
    const [etiqueta, , lista] = opciones[c];
    const texto = lista.find(([v]) => v === filtros[c])?.[1] || filtros[c];
    return `<span class="chip">${escapar(etiqueta)}: ${escapar(texto)}</span>`;
  });
  return `
    <form id="f-filtros" class="filtros-tareas" data-sin-aviso-cambios="1" aria-label="Filtrar tareas">
      ${CAMPOS_FILTRO.map((c) => {
        const [etiqueta, todos, lista] = opciones[c];
        return `<label>${etiqueta}<select name="${c}">
          <option value="">${todos}</option>
          ${lista.map(([v, t]) => `<option value="${escapar(v)}" ${filtros[c] === v ? "selected" : ""}>${escapar(t)}</option>`).join("")}
        </select></label>`;
      }).join("")}
    </form>
    ${activos.length ? `
      <div class="filtros-activos" role="status">
        <span class="tenue">Filtros activos:</span>${activos.join("")}
        <button type="button" class="boton chico secundario" data-accion="quitar-filtros" data-proyecto="${Number(pid)}">${icono("cerrar")}Quitar filtros</button>
      </div>` : ""}`;
}

ACCIONES["quitar-filtros"] = (btn) => {
  almacen.borrar(`filtros-${btn.dataset.proyecto}`, sessionStorage);
  recargar();
};

// ---------- HU-07-003 Resumen del proyecto ----------

const INDICADORES = [
  ["pendiente", "Pendientes", "est-pendiente"], ["en_curso", "En curso", "est-en_curso"],
  ["terminada", "Terminadas", "est-terminada"], ["vencidas", "Vencidas", "aviso"],
  ["por_vencer", "Por vencer", "reloj"], ["bloqueadas", "Bloqueadas", "bloqueo"],
];

/** Cifras del proyecto (todas sus tareas, sin filtros); cada una abre la lista que la compone. */
function resumenProyecto(pid, r) {
  return `
    <section class="bloque" aria-labelledby="titulo-resumen">
      <div class="encabezado-seccion">
        <h2 class="titulo-seccion" id="titulo-resumen">Resumen
          <span class="conteo">${r.abiertas} abierta${r.abiertas === 1 ? "" : "s"} de ${r.total}</span></h2>
        ${puedeSupervisar() && r.abiertas ? `<a class="boton chico secundario" href="#/carga?proyecto=${Number(pid)}">${icono("usuarios")}Carga por responsable</a>` : ""}
      </div>
      <ul class="indicadores">
        ${INDICADORES.map(([clave, texto, ico]) => {
          const ind = r.indicadores[clave];
          return `<li><button type="button" class="indicador indicador-${clave}" data-accion="ver-indicador"
                    data-proyecto="${Number(pid)}" data-filtro="${escapar(JSON.stringify(ind.filtro))}"
                    aria-label="${escapar(`${ind.total} ${texto.toLowerCase()}: ver la lista`)}">
                    <span class="indicador-valor num">${ind.total}</span>
                    <span class="indicador-texto">${icono(ico)}${texto}</span>
                  </button></li>`;
        }).join("")}
      </ul>
      ${r.proximas.length ? `
        <h3 class="subtitulo-seccion">Próximas fechas límite</h3>
        <ul class="lista-proximas">
          ${r.proximas.map((t) => `
            <li><a href="#/tareas/${Number(t.id)}">${escapar(t.nombre)}</a>
                <span class="fecha-con-marca">${fecha(t.fecha_limite)}${etiquetaVencimiento(t)}</span></li>`).join("")}
        </ul>` : ""}
    </section>`;
}

ACCIONES["ver-indicador"] = async (btn) => {
  guardarFiltros(btn.dataset.proyecto, JSON.parse(btn.dataset.filtro));
  almacen.guardar("vista-tareas", "tareas");  // la lista muestra todas las columnas del filtro
  await recargar();
  const titulo = document.getElementById("titulo-tareas");
  titulo?.scrollIntoView({ block: "start" });
  titulo?.setAttribute("tabindex", "-1");
  titulo?.focus({ preventScroll: true });
};

/** Una columna por estado; las tarjetas llegan del servidor en el mismo orden que la lista. */
function tableroTareas(columnas) {
  return `
    <div class="tablero">
      ${columnas.map((c) => `
        <section class="columna-tablero" aria-labelledby="columna-${escapar(c.estado)}">
          <h3 class="columna-titulo" id="columna-${escapar(c.estado)}">
            ${etiquetaEstado(c.estado)}<span class="conteo">${c.tareas.length}<span class="solo-lector"> tarea${c.tareas.length === 1 ? "" : "s"}</span></span>
          </h3>
          ${c.tareas.length
            ? `<ul class="lista-tarjetas">${c.tareas.map(tarjetaTarea).join("")}</ul>`
            : `<p class="columna-vacia">Sin tareas</p>`}
        </section>`).join("")}
    </div>`;
}

function tarjetaTarea(t) {
  return `
    <li class="tarjeta-tarea${t.bloqueada ? " tarjeta-bloqueada" : ""}" data-href="#/tareas/${Number(t.id)}">
      <a class="tarjeta-nombre" href="#/tareas/${Number(t.id)}">${escapar(t.nombre)}</a>
      ${t.bloqueada || t.vencimiento ? `<div class="ficha-chips">${t.bloqueada ? etiquetaBloqueo() : ""}${etiquetaVencimiento(t)}</div>` : ""}
      <div class="tarjeta-datos">
        ${etiquetaPrioridad(t.prioridad)}
        <span class="num">${fecha(t.fecha_limite, "Sin fecha")}</span>
      </div>
      <div>${t.responsable_nombre ? persona(t.responsable_nombre) : sinAsignar()}</div>
      ${t.transiciones.length ? `<div class="acciones">${botonesEstado(t.id, t.estado, t.transiciones)}</div>` : ""}
    </li>`;
}

// HU-03-004 Consultar mis tareas (de todos mis proyectos con acceso)
async function vistaMisTareas() {
  const tareas = await API.get("/api/mis-tareas");
  const abiertas = tareas.filter((t) => t.estado !== "terminada").length;
  const resumen = `${abiertas} abierta${abiertas === 1 ? "" : "s"} · ${tareas.length} en total`;
  return {
    titulo: "Mis tareas",
    seccion: "tareas",
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Mis tareas</h1>
          <p class="subtitulo" data-conteo="tabla-mis-tareas" data-total="${resumen}">${resumen}</p>
        </div>
        ${tareas.length ? `<div class="encabezado-acciones">${buscadorTabla("tabla-mis-tareas", "Buscar en mis tareas")}</div>` : ""}
      </header>
      ${tablaTareas(tareas, {
        id: "tabla-mis-tareas", conProyecto: true, conAcciones: true,
        vacioHtml: vacio("No tienes tareas asignadas",
          "Cuando el responsable de un proyecto te asigne una tarea, aparecerá aquí.",
          `<a class="boton secundario" href="#/proyectos">Ver mis proyectos</a>`),
      })}`,
  };
}

// HU-03-001 Crear tarea (solo el responsable del proyecto)
async function vistaNuevaTarea(pid) {
  const p = await API.get(`/api/proyectos/${pid}`);
  if (!p.soy_responsable) throw sinAcceso();
  const participantes = await API.get(`/api/proyectos/${pid}/participantes`);
  return {
    titulo: `Nueva tarea · ${p.nombre}`,
    seccion: "proyectos",
    foco: "campo",
    migas: [{ texto: "Mis proyectos", href: "#/proyectos" }, { texto: p.nombre, href: `#/proyectos/${p.id}` }, { texto: "Nueva tarea" }],
    html: `
      <div class="hoja">
        <h1 tabindex="-1">Nueva tarea</h1>
        <form id="f-tarea" class="formulario">
          <label>Nombre <input name="nombre" required maxlength="120"></label>
          <label>Descripción <textarea name="descripcion" required rows="4" maxlength="2000"></textarea></label>
          <label>Resultado esperado <span class="opcional">opcional</span>
            <textarea name="resultado_esperado" rows="2" maxlength="1000"></textarea></label>
          <div class="fila">
            <label>Responsable
              <select name="responsable_id">${opcionesPersonas(participantes, null, "Sin asignar")}</select>
            </label>
            <label>Prioridad <select name="prioridad">${opcionesPrioridad()}</select></label>
            <label>Fecha límite <span class="opcional">opcional</span> <input type="date" name="fecha_limite"></label>
          </div>
          <div class="acciones-form">
            <button class="boton">Crear tarea</button>
            <a class="boton secundario" href="#/proyectos/${p.id}">Cancelar</a>
            <span class="pista"><kbd class="atajo-tecla">${TECLA_MOD} Enter</kbd> para crear</span>
          </div>
        </form>
      </div>`,
    montar() {
      const form = document.getElementById("f-tarea");
      const clave = nuevaClave();  // HU-08-002: reintentar este formulario no duplica la tarea
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const d = datosForm(form);
        d.responsable_id = d.responsable_id ? Number(d.responsable_id) : null;
        d.fecha_limite = d.fecha_limite || null;
        const t = await guardar(form.querySelector("button"),
          () => API.crear(`/api/proyectos/${pid}/tareas`, d, clave), "Tarea creada", { form });
        if (t) location.hash = `#/tareas/${t.id}`;
      });
    },
  };
}

// HU-08-003: valor vigente de un campo del plan en el aviso de conflicto
function describirPlan(campo, v) {
  if (campo === "responsable_id") return `Responsable: ${v.responsable_nombre ? escapar(v.responsable_nombre) : "Sin asignar"}`;
  if (campo === "fecha_limite") return `Fecha límite: ${fecha(v.fecha_limite, "Sin fecha")}`;
  return `Prioridad: ${escapar(PRIORIDADES[v.prioridad] || v.prioridad)}`;
}

// HU-04-006: cada entrada del historial en orden cronológico, con actor y fecha
function valorHistorial(h, cual) {
  const valor = h[`valor_${cual}`];
  switch (h.tipo) {
    case "responsable": return h[`${cual}_nombre`] ? escapar(h[`${cual}_nombre`]) : "Sin asignar";
    case "fecha_limite": return fecha(valor, "Sin fecha");
    case "prioridad": return escapar(PRIORIDADES[valor] || valor);
    case "estado": return escapar(ESTADOS_TAREA[valor] || valor);
    default: return escapar(valor);
  }
}

const TEXTO_HISTORIAL = {
  responsable: "Responsable", fecha_limite: "Fecha límite", prioridad: "Prioridad", estado: "Estado",
  avance: "Registró un avance", bloqueo: "Reportó un bloqueo", resolucion_bloqueo: "Resolvió el bloqueo",
};

function entradaHistorial(h) {
  const titulo = escapar(TEXTO_HISTORIAL[h.tipo] || h.tipo);
  const cuerpo = ["avance", "bloqueo", "resolucion_bloqueo"].includes(h.tipo)
    ? `<span class="etiqueta-campo">${titulo}</span><span class="texto-largo">${valorHistorial(h, "nuevo")}</span>`
    : `<span class="etiqueta-campo">${titulo}</span><span class="valor-anterior">${valorHistorial(h, "anterior")}</span> → ${valorHistorial(h, "nuevo")}`;
  return `
    <li>
      <p>${cuerpo}</p>
      <p class="meta">${escapar(h.actor_nombre)} · ${momento(h.creado_en)}</p>
    </li>`;
}

function itemAvance(a) {
  return `
    <li>
      <p class="texto-largo">${escapar(a.texto)}</p>
      <p class="meta">${escapar(a.autor_nombre)} · ${momento(a.creado_en)}</p>
    </li>`;
}

function bloqueoResuelto(b) {
  return `
    <li class="bloqueo-resuelto">
      <p><span class="etiqueta-campo">Motivo</span>${escapar(b.motivo)}</p>
      <p class="meta">Reportado por ${escapar(b.abierto_por_nombre)} · ${momento(b.abierto_en)}</p>
      <p><span class="etiqueta-campo">Resolución</span>${escapar(b.resolucion)}</p>
      <p class="meta">Resuelto por ${escapar(b.resuelto_por_nombre)} · ${momento(b.resuelto_en)}</p>
    </li>`;
}

// Detalle de una tarea: contenido a la izquierda, propiedades a la derecha (inspector)
async function vistaTarea(id) {
  const t = await API.get(`/api/tareas/${id}`);
  const [participantes, bloqueos, avances, cambios, actividad, reglas] = await Promise.all([
    t.puedo_planificar ? API.get(`/api/proyectos/${t.proyecto_id}/participantes`) : [],
    API.get(`/api/tareas/${id}/bloqueos`), API.get(`/api/tareas/${id}/avances`),
    API.get(`/api/tareas/${id}/historial`), API.get(`/api/tareas/${id}/actividad`), API.get("/api/archivos/reglas"),
  ]);
  const resueltos = bloqueos.filter((b) => b.resuelto_en).reverse();
  const puedeEstado = t.transiciones.length || t.puedo_bloquear;

  return {
    titulo: t.nombre,
    seccion: "proyectos",
    nueva: t.puedo_planificar ? `#/proyectos/${t.proyecto_id}/tareas/nueva` : null,
    textoNueva: `Nueva tarea en «${t.proyecto_nombre}»`,
    migas: [{ texto: "Mis proyectos", href: "#/proyectos" },
            { texto: t.proyecto_nombre, href: `#/proyectos/${t.proyecto_id}` }, { texto: t.nombre }],
    html: `
      <header class="ficha-encabezado">
        <h1 tabindex="-1">${escapar(t.nombre)}</h1>
        <div class="ficha-chips">${etiquetaEstado(t.estado, t.bloqueada)}${etiquetaVencimiento(t)}</div>
        ${t.editable ? "" : `<p class="nota" role="note">${icono("est-cerrado")}El proyecto de esta tarea está cerrado: se conserva solo para consulta.</p>`}
      </header>
      <div class="ficha">
        <div class="ficha-contenido">
          ${t.bloqueo ? `
          <section class="bloqueo-abierto" aria-labelledby="titulo-bloqueo">
            <h2 id="titulo-bloqueo">${icono("bloqueo")}Bloqueo abierto</h2>
            <p class="texto-largo">${escapar(t.bloqueo.motivo)}</p>
            <p class="meta">Reportado por ${escapar(t.bloqueo.abierto_por_nombre)} · ${momento(t.bloqueo.abierto_en)}</p>
            ${t.puedo_planificar ? `
              <form id="f-resolver" class="formulario">
                <label>¿Cómo se resolvió? <textarea name="resolucion" required rows="2" maxlength="1000"></textarea></label>
                <div class="acciones-form"><button class="boton">Resolver bloqueo</button></div>
              </form>` : `<p class="meta">El responsable del proyecto registra la resolución.</p>`}
          </section>` : ""}

          <section class="bloque">
            <h2 class="titulo-seccion">Descripción</h2>
            <p class="texto-largo">${escapar(t.descripcion)}</p>
          </section>
          <section class="bloque">
            <h2 class="titulo-seccion">Resultado esperado</h2>
            ${t.resultado_esperado ? `<p class="texto-largo">${escapar(t.resultado_esperado)}</p>` : `<p class="tenue">Sin definir</p>`}
          </section>

          <section class="bloque" aria-labelledby="titulo-avances">
            <h2 class="titulo-seccion" id="titulo-avances">Avances <span class="conteo">${avances.length}</span></h2>
            ${avances.length
              ? `<ol class="lista-cambios">${avances.map(itemAvance).join("")}</ol>`
              : `<p class="tenue">Aún no hay avances registrados.</p>`}
            ${t.puedo_registrar_avance ? `
              <form id="f-avance" class="formulario compacto form-avance">
                <label>Nuevo avance <textarea name="texto" required rows="2" maxlength="1000"
                  placeholder="Qué se hizo y qué falta"></textarea></label>
                <div class="acciones-form"><button class="boton secundario chico">Registrar avance</button></div>
              </form>` : ""}
          </section>

          ${seccionColaboracion(actividad, reglas, "esta tarea", { soloLectura: !t.editable })}

          ${resueltos.length ? `
          <section class="bloque">
            <h2 class="titulo-seccion">Bloqueos resueltos <span class="conteo">${resueltos.length}</span></h2>
            <ul class="lista-bloqueos">${resueltos.map(bloqueoResuelto).join("")}</ul>
          </section>` : ""}

          <section class="bloque" aria-labelledby="titulo-historial">
            <h2 class="titulo-seccion" id="titulo-historial">Historial <span class="conteo">${cambios.length}</span></h2>
            ${cambios.length
              ? `<ol class="lista-cambios historial">${cambios.map(entradaHistorial).join("")}</ol>`
              : `<p class="tenue">Sin cambios desde que se creó.</p>`}
          </section>
        </div>

        <aside class="inspector" aria-label="Propiedades de la tarea">
          <section class="propiedad" id="prop-estado" tabindex="-1">
            <h2 class="propiedad-titulo">Estado</h2>
            <div class="ficha-chips">${etiquetaEstado(t.estado, t.bloqueada)}</div>
            ${puedeEstado ? `
              <div class="acciones">
                ${botonesEstado(t.id, t.estado, t.transiciones)}
                ${t.puedo_bloquear ? `<button type="button" class="boton chico peligro-suave" data-accion="mostrar-bloqueo">${icono("bloqueo")}Reportar bloqueo</button>` : ""}
              </div>` : ""}
            <form id="f-bloqueo" class="formulario" hidden>
              <label>Motivo del bloqueo <textarea name="motivo" required rows="3" maxlength="1000"></textarea></label>
              <div class="acciones-form">
                <button class="boton peligro">Registrar bloqueo</button>
                <button type="button" class="boton secundario" data-accion="ocultar-bloqueo">Cancelar</button>
              </div>
            </form>
          </section>

          ${t.puedo_planificar ? `
          <section class="propiedad">
            <h2 class="propiedad-titulo">Plan</h2>
            <form id="f-plan" class="formulario compacto"
                  data-anteriores="${escapar(JSON.stringify({ responsable_id: t.responsable_id, fecha_limite: t.fecha_limite, prioridad: t.prioridad }))}">
              <label>Responsable
                <select name="responsable_id">${opcionesPersonas(participantes, t.responsable_id, "Sin asignar")}</select>
              </label>
              <label>Prioridad <select name="prioridad">${opcionesPrioridad(t.prioridad)}</select></label>
              <label>Fecha límite <input type="date" name="fecha_limite" value="${escapar(t.fecha_limite || "")}"></label>
              <button class="boton secundario chico">Guardar cambios</button>
            </form>
          </section>` : `
          <section class="propiedad">
            <h2 class="propiedad-titulo">Responsable</h2>
            ${t.responsable_nombre ? persona(t.responsable_nombre) : sinAsignar()}
          </section>
          <section class="propiedad">
            <h2 class="propiedad-titulo">Planificación</h2>
            <dl class="propiedades">
              <dt>Prioridad</dt><dd>${etiquetaPrioridad(t.prioridad)}</dd>
              <dt>Fecha límite</dt><dd class="num">${fecha(t.fecha_limite, "Sin fecha")}</dd>
            </dl>
          </section>`}

          <section class="propiedad">
            <h2 class="propiedad-titulo">Registro</h2>
            <p class="meta">Creada por ${escapar(t.creado_por_nombre)} · ${momento(t.creado_en)}</p>
            ${botonCopiarEnlace(`#/tareas/${t.id}`)}
          </section>
        </aside>
      </div>`,

    montar() {
      montarComentarios(`/api/tareas/${id}/comentarios`);  // HU-05-001
      montarArchivos(`/api/tareas/${id}/archivos`);  // HU-05-002

      // HU-04-002 Registrar avance
      const fAvance = document.getElementById("f-avance");
      const claveAvance = nuevaClave();  // HU-08-002
      fAvance?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const ok = await guardar(fAvance.querySelector("button"),
          () => API.crear(`/api/tareas/${id}/avances`, datosForm(fAvance), claveAvance), "Avance registrado", { form: fAvance });
        if (ok) recargar();
      });

      // HU-04-003 Registrar bloqueo
      const fBloq = document.getElementById("f-bloqueo");
      const claveBloqueo = nuevaClave();  // HU-08-002
      fBloq.addEventListener("submit", async (e) => {
        e.preventDefault();
        const ok = await guardar(fBloq.querySelector("button"),
          () => API.crear(`/api/tareas/${id}/bloqueos`, datosForm(fBloq), claveBloqueo), "Bloqueo registrado", { form: fBloq });
        if (ok) recargar();
      });

      // HU-04-004 Resolver bloqueo
      const fRes = document.getElementById("f-resolver");
      fRes?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const ok = await guardar(fRes.querySelector("button"),
          () => API.post(`/api/tareas/${id}/bloqueos/${t.bloqueo.id}/resolver`, datosForm(fRes)), "Bloqueo resuelto", { form: fRes });
        if (ok) recargar();
      });

      // HU-03-006 Replanificar: responsable, prioridad y fecha en una sola confirmación
      const fPlan = document.getElementById("f-plan");
      fPlan?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const d = datosForm(fPlan);
        const cuerpo = {
          responsable_id: d.responsable_id ? Number(d.responsable_id) : null,
          fecha_limite: d.fecha_limite || null,
          prioridad: d.prioridad,
          anteriores: leidos(fPlan),  // HU-08-003
        };
        const ok = await guardar(fPlan.querySelector("button:not([type=button])"),
          () => API.put(`/api/tareas/${id}/plan`, cuerpo), "Plan actualizado",
          { form: fPlan, alConflicto: (err) => mostrarConflicto(fPlan, err, describirPlan) });
        if (ok) recargar();
      });
    },
  };
}

ACCIONES["mostrar-bloqueo"] = (btn) => {
  const form = document.getElementById("f-bloqueo");
  form.hidden = false;
  btn.hidden = true;
  form.querySelector("textarea").focus();
};

ACCIONES["ocultar-bloqueo"] = () => {
  const form = document.getElementById("f-bloqueo");
  form.hidden = true;
  form.reset();
  form.querySelector("textarea").dispatchEvent(new Event("input"));  // actualiza el contador
  Formularios.marcarLimpio(form);
  const btn = document.querySelector("[data-accion='mostrar-bloqueo']");
  if (btn) { btn.hidden = false; btn.focus(); }
};
