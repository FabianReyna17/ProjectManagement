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
