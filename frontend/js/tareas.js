// Vistas de tareas (Sprint 2).

function opcionesPersonas(personas, seleccionado, vacio) {
  return (vacio ? `<option value="">${vacio}</option>` : "") +
    personas.map((x) => `<option value="${x.id}" ${x.id === seleccionado ? "selected" : ""}>${escapar(x.nombre)}</option>`).join("");
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
    const t = await guardar(form.querySelector("button"),
      () => API.post(`/api/proyectos/${pid}/tareas`, d), "Tarea creada");
    if (t) location.hash = `#/tareas/${t.id}`;
  });
}

// Detalle de una tarea
async function vistaTarea(id) {
  const t = await API.get(`/api/tareas/${id}`);
  const participantes = t.puedo_planificar ? await API.get(`/api/proyectos/${t.proyecto_id}/participantes`) : [];
  const sinAsignar = `<span class="vacio">Sin asignar</span>`;

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
        <dt>Responsable</dt><dd>${t.responsable_nombre ? escapar(t.responsable_nombre) : sinAsignar}</dd>
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
}
