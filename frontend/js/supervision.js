// Supervisión de proyectos (Sprint 5). Cada vista devuelve { titulo, html, ... } y el router la pinta.

/** Funciones que consultan el estado general (mismo criterio que el servidor). */
const FUNCIONES_SUPERVISAN = ["Admin", "Responsable", "Supervisor"];

function puedeSupervisar() {
  return FUNCIONES_SUPERVISAN.includes(API.usuario()?.funcion);
}

// ---------- HU-07-005 Estado general de los proyectos ----------

const CLAVE_CERRADOS = "estado-incluir-cerrados";

/** Cifra que abre la lista del proyecto con el filtro que la compone (el servidor manda el filtro). */
function cifraProyecto(p, clave, texto) {
  const ind = p.indicadores[clave];
  if (!ind.total) return `<span class="cifra-cero num">0</span>`;
  return `<button type="button" class="cifra cifra-${clave}" data-accion="abrir-cifra" data-proyecto="${Number(p.id)}"
            data-filtro="${escapar(JSON.stringify(ind.filtro))}"
            aria-label="${escapar(`${ind.total} ${texto} en ${p.nombre}: ver la lista`)}">
            ${icono(clave === "vencidas" ? "aviso" : "bloqueo")}<span class="num">${ind.total}</span></button>`;
}

function etiquetaAtencion() {
  return `<span class="chip chip-atencion">${icono("aviso")}Requiere atención</span>`;
}

async function vistaEstadoProyectos() {
  if (!puedeSupervisar()) throw sinAcceso();
  const cerrados = almacen.leer(CLAVE_CERRADOS, sessionStorage) === "1";
  const { proyectos, totales } = await API.get(`/api/estado-proyectos${cerrados ? "?incluir_cerrados=true" : ""}`);
  const total = `${totales.proyectos} proyecto${totales.proyectos === 1 ? "" : "s"}`;
  return {
    titulo: "Estado general",
    seccion: "estado",
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Estado general</h1>
          <p class="subtitulo" data-conteo="tabla-estado" data-total="${total}">${total}</p>
        </div>
        <div class="encabezado-acciones">
          ${proyectos.length ? buscadorTabla("tabla-estado", "Buscar proyecto") : ""}
          <label class="casilla"><input type="checkbox" data-accion="incluir-cerrados" ${cerrados ? "checked" : ""}>Incluir cerrados</label>
          <a class="boton secundario" href="#/carga">${icono("usuarios")}Carga por responsable</a>
        </div>
      </header>
      ${proyectos.length ? `
        <ul class="totales-estado" aria-label="Totales de los proyectos consultados">
          <li class="${totales.requieren_atencion ? "con-atencion" : ""}"><span class="num">${totales.requieren_atencion}</span>
            ${totales.requieren_atencion === 1 ? "requiere atención" : "requieren atención"}</li>
          <li><span class="num">${totales.vencidas}</span>${totales.vencidas === 1 ? "tarea vencida" : "tareas vencidas"}</li>
          <li><span class="num">${totales.bloqueadas}</span>${totales.bloqueadas === 1 ? "tarea bloqueada" : "tareas bloqueadas"}</li>
        </ul>
        <p class="nota-estado tenue">Un proyecto requiere atención si tiene al menos una tarea vencida o bloqueada. Cada cifra abre las tareas que la explican.</p>
        <div class="tabla-marco">
          <table class="tabla tabla-tarjetas" id="tabla-estado">
            <thead><tr>${th("Proyecto", { clase: "col-principal" })}${th("Responsable")}${th("Estado")}${th("Fin previsto")}${th("Vencidas")}${th("Bloqueadas")}${th("Abiertas")}</tr></thead>
            <tbody>
              ${proyectos.map((p) => `
                <tr data-href="#/proyectos/${Number(p.id)}" class="${p.requiere_atencion ? "fila-atencion" : ""}">
                  <td data-label="Proyecto" class="celda-principal" data-orden="${p.requiere_atencion ? 0 : 1} ${escapar(p.nombre)}">
                    <a href="#/proyectos/${Number(p.id)}">${escapar(p.nombre)}</a>
                    ${p.requiere_atencion ? etiquetaAtencion() : ""}</td>
                  <td data-label="Responsable" data-orden="${escapar(p.responsable_nombre)}">${persona(p.responsable_nombre)}</td>
                  <td data-label="Estado" data-orden="${ORDEN_ESTADO[p.estado] || 9}">${etiquetaProyecto(p.estado)}</td>
                  <td data-label="Fin previsto" data-orden="${escapar(p.fecha_fin)}" class="num">${fecha(p.fecha_fin)}</td>
                  <td data-label="Vencidas" data-orden="${p.indicadores.vencidas.total}">${cifraProyecto(p, "vencidas", "vencidas")}</td>
                  <td data-label="Bloqueadas" data-orden="${p.indicadores.bloqueadas.total}">${cifraProyecto(p, "bloqueadas", "bloqueadas")}</td>
                  <td data-label="Abiertas" data-orden="${p.abiertas}" class="num">${p.abiertas} de ${p.total}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>`
      : vacio(cerrados ? "No tienes proyectos autorizados" : "No tienes proyectos activos autorizados",
              "Aquí aparecerán los proyectos en los que te den acceso, con sus tareas vencidas y bloqueadas.")}`,
  };
}

ACCIONES["incluir-cerrados"] = (casilla) => {
  almacen.guardar(CLAVE_CERRADOS, casilla.checked ? "1" : "0", sessionStorage);
  recargar();
};

// Abre el proyecto con su lista de tareas filtrada (la ficha muestra también su resumen, HU-07-003)
ACCIONES["abrir-cifra"] = (btn) => {
  guardarFiltros(btn.dataset.proyecto, JSON.parse(btn.dataset.filtro));
  almacen.guardar("vista-tareas", "tareas");
  location.hash = `#/proyectos/${Number(btn.dataset.proyecto)}`;
};

// ---------- HU-07-004 Carga por responsable ----------

function cifraCarga(n, texto, clase = "") {
  return `<span class="carga-cifra ${n && clase ? clase : ""}"><span class="num">${n}</span> ${texto}</span>`;
}

/** Una persona (o "Sin asignar"): cifras en el resumen y, al abrirla, sus tareas con su proyecto. */
function grupoCarga(g, maximo, { sinAsignar = false } = {}) {
  const ancho = maximo ? Math.round((g.abiertas / maximo) * 100) : 0;
  return `
    <details class="carga-persona${sinAsignar ? " carga-sin-asignar" : ""}">
      <summary>
        <span class="carga-quien">${sinAsignar ? etiquetaSinAsignar() : persona(g.nombre)}</span>
        <span class="carga-barra" aria-hidden="true"><span data-ancho="${ancho}"></span></span>
        <span class="carga-cifras">
          ${cifraCarga(g.abiertas, g.abiertas === 1 ? "abierta" : "abiertas")}
          ${cifraCarga(g.vencidas, g.vencidas === 1 ? "vencida" : "vencidas", "con-vencidas")}
          ${cifraCarga(g.bloqueadas, g.bloqueadas === 1 ? "bloqueada" : "bloqueadas", "con-bloqueadas")}
        </span>
      </summary>
      ${tablaTareas(g.tareas, { id: `carga-${g.usuario_id ?? "sin"}`, conProyecto: true })}
    </details>`;
}

function etiquetaSinAsignar() {
  return `<span class="persona">${icono("aviso")}<span>Sin asignar</span></span>`;
}

async function vistaCarga(proyectoId) {
  if (!puedeSupervisar()) throw sinAcceso();
  const r = await API.get(`/api/carga${proyectoId ? `?proyecto_id=${Number(proyectoId)}` : ""}`);
  const maximo = Math.max(0, ...r.personas.map((p) => p.abiertas), r.sin_asignar.abiertas);
  const elegido = r.proyectos.find((p) => p.id === Number(proyectoId));
  const total = r.personas.reduce((n, p) => n + p.abiertas, 0) + r.sin_asignar.abiertas;
  return {
    titulo: "Carga por responsable",
    seccion: "carga",
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Carga por responsable</h1>
          <p class="subtitulo">${total} tarea${total === 1 ? "" : "s"} abierta${total === 1 ? "" : "s"} ·
            ${elegido ? escapar(elegido.nombre) : "todos tus proyectos activos"}</p>
        </div>
        <div class="encabezado-acciones">
          <label class="filtro-proyecto">Proyecto
            <select data-accion-cambio="carga-proyecto">
              <option value="">Todos</option>
              ${r.proyectos.map((p) => `<option value="${Number(p.id)}" ${p.id === Number(proyectoId) ? "selected" : ""}>${escapar(p.nombre)}</option>`).join("")}
            </select>
          </label>
        </div>
      </header>
      ${total ? `
        <p class="nota-estado tenue">Tareas abiertas de cada persona; ábrela para ver cuáles son. Solo se cuentan los proyectos a los que tienes acceso.</p>
        <div class="lista-carga">
          ${r.personas.map((g) => grupoCarga(g, maximo)).join("")}
          ${r.sin_asignar.abiertas ? grupoCarga(r.sin_asignar, maximo, { sinAsignar: true }) : ""}
        </div>`
      : vacio("No hay tareas abiertas", elegido ? "Todas las tareas de este proyecto están terminadas." : "Tus proyectos activos no tienen tareas pendientes.")}`,
    montar(app) {
      // La CSP no permite estilos en línea: el ancho de cada barra se aplica desde aquí
      app.querySelectorAll(".carga-barra [data-ancho]").forEach((el) => el.style.setProperty("--ancho", `${el.dataset.ancho}%`));
      app.querySelector("[data-accion-cambio=carga-proyecto]")?.addEventListener("change", (e) => {
        location.hash = e.target.value ? `#/carga?proyecto=${Number(e.target.value)}` : "#/carga";
      });
    },
  };
}
