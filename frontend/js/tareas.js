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
            <td data-label="Fecha límite" data-orden="${escapar(t.fecha_limite || "")}" class="num">${fecha(t.fecha_limite, "Sin fecha")}</td>
            <td data-label="Estado" data-orden="${t.bloqueada ? 0 : ORDEN_ESTADO[t.estado] || 9}">${etiquetaEstado(t.estado, t.bloqueada)}</td>
            ${conAcciones ? `<td data-label="Acciones" class="acciones">${botonesEstado(t.id, t.estado, transicionesPosibles(t.estado, t.bloqueada))}</td>` : ""}
          </tr>`).join("")}
      </tbody>
    </table>
    </div>`;
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
  const [participantes, bloqueos] = await Promise.all([
    t.puedo_planificar ? API.get(`/api/proyectos/${t.proyecto_id}/participantes`) : [],
    API.get(`/api/tareas/${id}/bloqueos`),
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
        <div class="ficha-chips">${etiquetaEstado(t.estado, t.bloqueada)}</div>
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

          ${resueltos.length ? `
          <section class="bloque">
            <h2 class="titulo-seccion">Bloqueos resueltos <span class="conteo">${resueltos.length}</span></h2>
            <ul class="lista-bloqueos">${resueltos.map(bloqueoResuelto).join("")}</ul>
          </section>` : ""}
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

          <section class="propiedad">
            <h2 class="propiedad-titulo">Responsable</h2>
            ${t.puedo_planificar ? `
              <form id="f-responsable" class="formulario compacto">
                <label><span class="solo-lector">Responsable</span>
                  <select name="usuario_id" required>${opcionesPersonas(participantes, t.responsable_id, "Seleccionar persona…")}</select>
                </label>
                <button class="boton secundario chico">Asignar</button>
              </form>` : (t.responsable_nombre ? persona(t.responsable_nombre) : sinAsignar())}
          </section>

          <section class="propiedad">
            <h2 class="propiedad-titulo">Planificación</h2>
            ${t.puedo_planificar ? `
              <form id="f-plan" class="formulario compacto">
                <label>Prioridad <select name="prioridad">${opcionesPrioridad(t.prioridad)}</select></label>
                <label>Fecha límite <input type="date" name="fecha_limite" value="${escapar(t.fecha_limite || "")}"></label>
                <button class="boton secundario chico">Guardar planificación</button>
              </form>` : `
              <dl class="propiedades">
                <dt>Prioridad</dt><dd>${etiquetaPrioridad(t.prioridad)}</dd>
                <dt>Fecha límite</dt><dd class="num">${fecha(t.fecha_limite, "Sin fecha")}</dd>
              </dl>`}
          </section>

          <section class="propiedad">
            <h2 class="propiedad-titulo">Registro</h2>
            <p class="meta">Creada por ${escapar(t.creado_por_nombre)} · ${momento(t.creado_en)}</p>
            ${botonCopiarEnlace(`#/tareas/${t.id}`)}
          </section>
        </aside>
      </div>`,

    montar() {
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

      // HU-03-002 Asignar responsable
      const fResp = document.getElementById("f-responsable");
      fResp?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const usuario_id = Number(datosForm(fResp).usuario_id);
        const ok = await guardar(fResp.querySelector("button"),
          () => API.put(`/api/tareas/${id}/responsable`, { usuario_id }), "Responsable asignado", { form: fResp });
        if (ok) recargar();
      });

      // HU-03-003 Fecha límite y prioridad
      const fPlan = document.getElementById("f-plan");
      fPlan?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const d = datosForm(fPlan);
        const cuerpo = { fecha_limite: d.fecha_limite || null, prioridad: d.prioridad };
        const ok = await guardar(fPlan.querySelector("button"),
          () => API.put(`/api/tareas/${id}/planificacion`, cuerpo), "Planificación guardada", { form: fPlan });
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
