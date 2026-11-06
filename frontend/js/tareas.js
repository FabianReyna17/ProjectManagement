// Vistas de tareas (Sprint 2).

function opcionesPersonas(personas, seleccionado, vacio) {
  return (vacio ? `<option value="">${vacio}</option>` : "") +
    personas.map((x) => `<option value="${x.id}" ${x.id === seleccionado ? "selected" : ""}>${escapar(x.nombre)}</option>`).join("");
}

const SIN_ASIGNAR = `<span class="aviso-sin-asignar">⚠ Sin asignar</span>`;

/** Tabla de tareas; cada fila abre el detalle. Reutilizada por el proyecto y "Mis tareas". */
function tablaTareas(tareas, { conProyecto = false, vacio = "No hay tareas." } = {}) {
  if (tareas.length === 0) return `<p class="vacio">${vacio}</p>`;
  return `
    <div class="tabla-scroll">
    <table>
      <thead><tr>
        <th>Tarea</th>${conProyecto ? "<th>Proyecto</th>" : "<th>Responsable</th>"}
        <th>Prioridad</th><th>Fecha límite</th><th>Estado</th>
      </tr></thead>
      <tbody>
        ${tareas.map((t) => `
          <tr class="clic" onclick="location.hash='#/tareas/${t.id}'">
            <td>${escapar(t.nombre)}</td>
            <td>${conProyecto ? escapar(t.proyecto_nombre) : (t.responsable_nombre ? escapar(t.responsable_nombre) : SIN_ASIGNAR)}</td>
            <td>${etiquetaPrioridad(t.prioridad)}</td>
            <td>${t.fecha_limite || "—"}</td>
            <td>${etiquetaEstado(t.estado)}</td>
          </tr>`).join("")}
      </tbody>
    </table>
    </div>`;
}

// HU-03-004 Consultar mis tareas (de todos mis proyectos con acceso)
async function vistaMisTareas() {
  const tareas = await API.get("/api/mis-tareas");
  app.innerHTML = `
    <div class="tarjeta">
      <h1>Mis tareas</h1>
      ${tablaTareas(tareas, { conProyecto: true, vacio: "No tienes tareas asignadas." })}
    </div>`;
}

// HU-03-001 Crear tarea (solo el responsable del proyecto)
async function vistaNuevaTarea(pid) {
  const p = await API.get(`/api/proyectos/${pid}`);
  if (!p.soy_responsable) { location.hash = "#/sin-acceso"; return; }
  const participantes = await API.get(`/api/proyectos/${pid}/participantes`);
  app.innerHTML = `
    <div class="tarjeta">
      <a class="volver" href="#/proyectos/${pid}">← ${escapar(p.nombre)}</a>
      <h1>Nueva tarea</h1>
      <form id="f-tarea">
        <label>Nombre <input name="nombre" required maxlength="120"></label>
        <label>Descripción <textarea name="descripcion" required rows="3" maxlength="2000"></textarea></label>
        <label>Resultado esperado (opcional) <textarea name="resultado_esperado" rows="2" maxlength="1000"></textarea></label>
        <label>Responsable
          <select name="responsable_id">${opcionesPersonas(participantes, null, "Sin asignar")}</select>
        </label>
        <div class="fila">
          <label>Fecha límite (opcional) <input type="date" name="fecha_limite"></label>
          <label>Prioridad <select name="prioridad">${opcionesPrioridad()}</select></label>
        </div>
        <div>
          <button>Crear tarea</button>
          <button type="button" class="secundario" onclick="location.hash='#/proyectos/${pid}'">Cancelar</button>
        </div>
      </form>
    </div>`;
  const form = document.getElementById("f-tarea");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = datosForm(form);
    d.responsable_id = d.responsable_id ? Number(d.responsable_id) : null;
    d.fecha_limite = d.fecha_limite || null;
    const t = await guardar(form.querySelector("button"),
      () => API.post(`/api/proyectos/${pid}/tareas`, d), "Tarea creada");
    if (t) location.hash = `#/tareas/${t.id}`;
  });
}

// Detalle de una tarea
async function vistaTarea(id) {
  const t = await API.get(`/api/tareas/${id}`);
  const participantes = t.puedo_planificar ? await API.get(`/api/proyectos/${t.proyecto_id}/participantes`) : [];

  app.innerHTML = `
    <div class="tarjeta">
      <a class="volver" href="#/proyectos/${t.proyecto_id}">← ${escapar(t.proyecto_nombre)}</a>
      <div class="encabezado">
        <h1>${escapar(t.nombre)}</h1>
        ${etiquetaEstado(t.estado)}
      </div>
      <dl>
        <dt>Descripción</dt><dd>${escapar(t.descripcion)}</dd>
        <dt>Resultado esperado</dt>
        <dd>${t.resultado_esperado ? escapar(t.resultado_esperado) : `<span class="vacio">Sin definir</span>`}</dd>
        <dt>Responsable</dt><dd>${t.responsable_nombre ? escapar(t.responsable_nombre) : SIN_ASIGNAR}</dd>
        <dt>Prioridad</dt><dd>${etiquetaPrioridad(t.prioridad)}</dd>
        <dt>Fecha límite</dt><dd>${t.fecha_limite || `<span class="vacio">Sin fecha</span>`}</dd>
        <dt>Creada por</dt><dd>${escapar(t.creado_por_nombre)} · ${fechaHora(t.creado_en)}</dd>
      </dl>
    </div>

    ${t.puedo_planificar ? `
    <div class="tarjeta">
      <h2>Planificación</h2>
      <form id="f-responsable" class="fila">
        <label>Responsable
          <select name="usuario_id" required>${opcionesPersonas(participantes, t.responsable_id, "Seleccionar persona…")}</select>
        </label>
        <div class="accion"><button>Asignar</button></div>
      </form>
      <form id="f-plan" class="fila" style="margin-top:1rem">
        <label>Fecha límite <input type="date" name="fecha_limite" value="${t.fecha_limite || ""}"></label>
        <label>Prioridad <select name="prioridad">${opcionesPrioridad(t.prioridad)}</select></label>
        <div><button>Guardar fecha y prioridad</button></div>
      </form>
    </div>` : ""}`;

  // HU-03-002 Asignar responsable
  const fResp = document.getElementById("f-responsable");
  fResp?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const usuario_id = Number(datosForm(fResp).usuario_id);
    const ok = await guardar(fResp.querySelector("button"),
      () => API.put(`/api/tareas/${id}/responsable`, { usuario_id }), "Responsable asignado");
    if (ok) vistaTarea(id);
  });

  // HU-03-003 Fecha límite y prioridad
  const fPlan = document.getElementById("f-plan");
  fPlan?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = datosForm(fPlan);
    const cuerpo = { fecha_limite: d.fecha_limite || null, prioridad: d.prioridad };
    const ok = await guardar(fPlan.querySelector("button"),
      () => API.put(`/api/tareas/${id}/planificacion`, cuerpo), "Planificación guardada");
    if (ok) vistaTarea(id);
  });
}
