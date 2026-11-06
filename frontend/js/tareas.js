// Vistas de tareas (Sprint 2).

// HU-03-001 Crear tarea (solo el responsable del proyecto)
async function vistaNuevaTarea(pid) {
  const p = await API.get(`/api/proyectos/${pid}`);
  if (!p.soy_responsable) { location.hash = "#/sin-acceso"; return; }
  app.innerHTML = `
    <div class="tarjeta">
      <a class="volver" href="#/proyectos/${pid}">← ${escapar(p.nombre)}</a>
      <h1>Nueva tarea</h1>
      <form id="f-tarea">
        <label>Nombre <input name="nombre" required maxlength="120"></label>
        <label>Descripción <textarea name="descripcion" required rows="3" maxlength="2000"></textarea></label>
        <label>Resultado esperado (opcional) <textarea name="resultado_esperado" rows="2" maxlength="1000"></textarea></label>
        <div>
          <button>Crear tarea</button>
          <button type="button" class="secundario" onclick="location.hash='#/proyectos/${pid}'">Cancelar</button>
        </div>
      </form>
    </div>`;
  const form = document.getElementById("f-tarea");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const t = await guardar(form.querySelector("button"),
      () => API.post(`/api/proyectos/${pid}/tareas`, datosForm(form)), "Tarea creada");
    if (t) location.hash = `#/tareas/${t.id}`;
  });
}

// Detalle de una tarea
async function vistaTarea(id) {
  const t = await API.get(`/api/tareas/${id}`);
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
        <dt>Creada por</dt><dd>${escapar(t.creado_por_nombre)} · ${fechaHora(t.creado_en)}</dd>
      </dl>
    </div>`;
}
