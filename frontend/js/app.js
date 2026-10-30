// Router por hash y vistas del Sprint 1.
const app = document.getElementById("app");

const rutas = [
  { patron: /^#\/login$/, vista: vistaLogin, publica: true },
  { patron: /^#\/proyectos$/, vista: vistaProyectos },
  { patron: /^#\/proyectos\/nuevo$/, vista: vistaNuevoProyecto },
  { patron: /^#\/proyectos\/(\d+)$/, vista: vistaProyecto },
  { patron: /^#\/usuarios$/, vista: vistaUsuarios },
  { patron: /^#\/sin-acceso$/, vista: vistaSinAcceso },
];

function actualizarBarra() {
  const u = API.usuario();
  document.getElementById("barra").classList.toggle("oculto", !u);
  if (!u) return;
  document.getElementById("usuario-actual").textContent = `${u.nombre} (${u.funcion})`;
  document.getElementById("nav-usuarios").classList.toggle("oculto", u.funcion !== "Admin");
}

async function router() {
  const hash = location.hash || "#/proyectos";
  const ruta = rutas.find((r) => r.patron.test(hash));
  if (!ruta) { location.hash = "#/proyectos"; return; }
  if (!ruta.publica && !API.token()) { location.hash = "#/login"; return; }
  actualizarBarra();
  const params = hash.match(ruta.patron).slice(1);
  try {
    await ruta.vista(...params);
  } catch (e) {
    if (location.hash === hash) app.innerHTML = `<div class="tarjeta"><p>${escapar(e.message)}</p></div>`;
  }
}

window.addEventListener("hashchange", router);
window.addEventListener("load", router);

// HU-01-004 Cerrar sesión
document.getElementById("btn-salir").addEventListener("click", async () => {
  try { await API.post("/api/auth/logout"); } catch { /* la sesión ya no era válida */ }
  API.limpiarSesion();
  location.hash = "#/login";
});

// ---------- Vistas ----------

// HU-01-003 Iniciar sesión
function vistaLogin() {
  if (API.token()) { location.hash = "#/proyectos"; return; }
  app.innerHTML = `
    <div class="tarjeta angosta">
      <h1>Iniciar sesión</h1>
      <form id="f-login">
        <label>Usuario <input name="usuario" required autocomplete="username"></label>
        <label>Contraseña <input name="password" type="password" required autocomplete="current-password"></label>
        <button>Entrar</button>
      </form>
    </div>`;
  const form = document.getElementById("f-login");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = form.querySelector("button");
    btn.disabled = true;
    try {
      API.guardarSesion(await API.post("/api/auth/login", datosForm(form)));
      location.hash = "#/proyectos";
    } catch (err) {
      toast(err.message, "error");
    } finally {
      btn.disabled = false;
    }
  });
}

// HU-01-006 Consultar proyectos autorizados
async function vistaProyectos() {
  const u = API.usuario();
  const puedeCrear = ["Admin", "Responsable"].includes(u.funcion);
  const proyectos = await API.get("/api/proyectos");
  app.innerHTML = `
    <div class="tarjeta">
      <div class="encabezado">
        <h1>Mis proyectos</h1>
        ${puedeCrear ? `<button onclick="location.hash='#/proyectos/nuevo'">+ Nuevo proyecto</button>` : ""}
      </div>
      ${proyectos.length === 0
        ? `<p class="vacio">No tienes proyectos asignados.</p>`
        : `<table>
            <thead><tr><th>Nombre</th><th>Responsable</th><th>Inicio</th><th>Fin</th><th>Estado</th></tr></thead>
            <tbody>
              ${proyectos.map((p) => `
                <tr class="clic" onclick="location.hash='#/proyectos/${p.id}'">
                  <td>${escapar(p.nombre)}</td>
                  <td>${escapar(p.responsable_nombre)}</td>
                  <td>${p.fecha_inicio}</td>
                  <td>${p.fecha_fin}</td>
                  <td><span class="etiqueta">${escapar(p.estado)}</span></td>
                </tr>`).join("")}
            </tbody>
          </table>`}
    </div>`;
}

// HU-02-001 Crear proyecto
async function vistaNuevoProyecto() {
  const usuarios = await API.get("/api/usuarios");
  const responsables = usuarios.filter((x) => ["Admin", "Responsable"].includes(x.funcion));
  const yo = API.usuario();
  app.innerHTML = `
    <div class="tarjeta">
      <h1>Nuevo proyecto</h1>
      <form id="f-proyecto">
        <label>Nombre <input name="nombre" required maxlength="120"></label>
        <label>Objetivo <textarea name="objetivo" required rows="3"></textarea></label>
        <label>Responsable
          <select name="responsable_id" required>
            ${responsables.map((r) => `<option value="${r.id}" ${r.id === yo.id ? "selected" : ""}>${escapar(r.nombre)}</option>`).join("")}
          </select>
        </label>
        <div class="fila">
          <label>Fecha de inicio <input type="date" name="fecha_inicio" required></label>
          <label>Fecha de fin <input type="date" name="fecha_fin" required></label>
        </div>
        <div>
          <button>Crear proyecto</button>
          <button type="button" class="secundario" onclick="location.hash='#/proyectos'">Cancelar</button>
        </div>
      </form>
    </div>`;
  const form = document.getElementById("f-proyecto");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = datosForm(form);
    if (d.fecha_fin < d.fecha_inicio) { toast("La fecha de fin no puede ser anterior a la de inicio", "error"); return; }
    d.responsable_id = Number(d.responsable_id);
    const p = await guardar(form.querySelector("button"), () => API.post("/api/proyectos", d), "Proyecto creado");
    if (p) location.hash = `#/proyectos/${p.id}`;
  });
}

// HU-02-002 Ficha del proyecto + HU-01-005 Participantes
async function vistaProyecto(id) {
  const p = await API.get(`/api/proyectos/${id}`);
  const participantes = await API.get(`/api/proyectos/${id}/participantes`);
  let candidatos = [];
  if (p.soy_responsable) {
    const ids = new Set(participantes.map((x) => x.id));
    candidatos = (await API.get("/api/usuarios")).filter((x) => !ids.has(x.id));
  }

  app.innerHTML = `
    <div class="tarjeta">
      <div class="encabezado">
        <h1>${escapar(p.nombre)}</h1>
        <span class="etiqueta">${escapar(p.estado)}</span>
      </div>
      <dl>
        <dt>Objetivo</dt><dd>${escapar(p.objetivo)}</dd>
        <dt>Responsable</dt><dd>${escapar(p.responsable_nombre)}</dd>
        <dt>Inicio</dt><dd>${p.fecha_inicio}</dd>
        <dt>Fin</dt><dd>${p.fecha_fin}</dd>
      </dl>
    </div>

    <div class="tarjeta">
      <h2>Participantes</h2>
      <table>
        <thead><tr><th>Nombre</th><th>Usuario</th><th>Función</th>${p.soy_responsable ? "<th></th>" : ""}</tr></thead>
        <tbody>
          ${participantes.map((x) => `
            <tr>
              <td>${escapar(x.nombre)}</td>
              <td>${escapar(x.usuario)}</td>
              <td>${escapar(x.funcion)}</td>
              ${p.soy_responsable
                ? `<td>${x.id !== p.responsable_id ? `<button class="peligro" data-retirar="${x.id}">Retirar</button>` : ""}</td>`
                : ""}
            </tr>`).join("")}
        </tbody>
      </table>
      ${p.soy_responsable ? `
        <form id="f-participante" class="fila" style="margin-top:1rem">
          <select name="usuario_id" required>
            <option value="">Seleccionar persona…</option>
            ${candidatos.map((c) => `<option value="${c.id}">${escapar(c.nombre)} (${escapar(c.funcion)})</option>`).join("")}
          </select>
          <button>Dar acceso</button>
        </form>` : ""}
    </div>`;

  if (!p.soy_responsable) return;

  const form = document.getElementById("f-participante");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const usuario_id = Number(datosForm(form).usuario_id);
    const ok = await guardar(form.querySelector("button"),
      () => API.post(`/api/proyectos/${id}/participantes`, { usuario_id }), "Participante agregado");
    if (ok) vistaProyecto(id);
  });

  app.querySelectorAll("[data-retirar]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      const ok = await guardar(btn,
        () => API.del(`/api/proyectos/${id}/participantes/${btn.dataset.retirar}`), "Participante retirado");
      if (ok) vistaProyecto(id);
    }));
}

// HU-01-001 Registrar cuenta + HU-01-002 Función inicial (solo Admin)
async function vistaUsuarios() {
  if (API.usuario().funcion !== "Admin") { location.hash = "#/sin-acceso"; return; }
  const [funciones, usuarios] = await Promise.all([API.get("/api/funciones"), API.get("/api/usuarios")]);
  app.innerHTML = `
    <div class="tarjeta">
      <h1>Registrar cuenta</h1>
      <form id="f-usuario">
        <div class="fila">
          <label>Usuario (identificador único) <input name="usuario" required minlength="3" maxlength="50"></label>
          <label>Nombre completo <input name="nombre" required maxlength="100"></label>
        </div>
        <div class="fila">
          <label>Contraseña <input name="password" type="password" required minlength="6"></label>
          <label>Función
            <select name="funcion_id" required>
              <option value="">Seleccionar…</option>
              ${funciones.map((f) => `<option value="${f.id}">${escapar(f.nombre)}</option>`).join("")}
            </select>
          </label>
        </div>
        <div><button>Registrar</button></div>
      </form>
    </div>
    <div class="tarjeta">
      <h2>Cuentas activas</h2>
      <table>
        <thead><tr><th>Nombre</th><th>Usuario</th><th>Función</th></tr></thead>
        <tbody>
          ${usuarios.map((x) => `<tr><td>${escapar(x.nombre)}</td><td>${escapar(x.usuario)}</td><td>${escapar(x.funcion)}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>`;
  const form = document.getElementById("f-usuario");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const d = datosForm(form);
    d.funcion_id = Number(d.funcion_id);
    const ok = await guardar(form.querySelector("button"), () => API.post("/api/usuarios", d), "Cuenta registrada");
    if (ok) vistaUsuarios();
  });
}

// HU-01-007 Pantalla de "sin acceso"
function vistaSinAcceso() {
  app.innerHTML = `
    <div class="tarjeta">
      <h1>Sin acceso</h1>
      <p>No tienes permiso para ver este recurso o realizar esta acción.</p>
      <button onclick="location.hash='#/proyectos'">Volver a mis proyectos</button>
    </div>`;
}
