// Administración de cuentas (Sprint 6). HU-01-010: historial de cambios de acceso, solo Admin.

const TIPOS_ACCESO = {
  cuenta_alta: "Alta de cuenta",
  funcion: "Cambio de función",
  desactivacion: "Cuenta desactivada",
  restablecimiento: "Acceso restablecido",
  acceso_alta: "Acceso al proyecto",
  acceso_retiro: "Retiro del proyecto",
};

function valoresAcceso(x) {
  if (x.tipo === "restablecimiento") return `<span class="tenue">Contraseña temporal entregada</span>`;
  const antes = x.valor_anterior ? `<span class="valor-anterior">${escapar(x.valor_anterior)}</span> → ` : "";
  return `${antes}<strong>${escapar(x.valor_nuevo || "—")}</strong>`;
}

async function vistaCambiosAcceso(filtro, id) {
  if (API.usuario()?.funcion !== "Admin") throw sinAcceso();
  const params = filtro && id ? `?${filtro === "usuario" ? "usuario_id" : "proyecto_id"}=${Number(id)}` : "";
  const [datos, cuentas] = await Promise.all([API.get(`/api/cambios-acceso${params}`), API.get("/api/usuarios?todas=1")]);
  const { eventos, proyectos, limite } = datos;
  const total = `${eventos.length} cambio${eventos.length === 1 ? "" : "s"}` +
    (eventos.length >= limite ? ` (los ${limite} más recientes)` : "");
  const sel = (tipo, valor) => filtro === tipo && Number(id) === Number(valor) ? "selected" : "";
  return {
    titulo: "Historial de accesos",
    seccion: "usuarios",
    migas: [{ texto: "Usuarios", href: "#/usuarios" }, { texto: "Historial de accesos" }],
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Historial de accesos</h1>
          <p class="subtitulo" data-conteo="tabla-accesos" data-total="${total}">${total}</p>
        </div>
        <div class="encabezado-acciones">
          <label class="filtro-proyecto">Persona
            <select data-filtro-acceso="usuario">
              <option value="">Todas</option>
              ${cuentas.map((c) => `<option value="${Number(c.id)}" ${sel("usuario", c.id)}>${escapar(c.nombre)}${c.activo ? "" : " (desactivada)"}</option>`).join("")}
            </select>
          </label>
          <label class="filtro-proyecto">Proyecto
            <select data-filtro-acceso="proyecto">
              <option value="">Todos</option>
              ${proyectos.map((p) => `<option value="${Number(p.id)}" ${sel("proyecto", p.id)}>${escapar(p.nombre)}</option>`).join("")}
            </select>
          </label>
        </div>
      </header>
      <p class="tenue nota-estado">Altas y retiros de acceso a proyectos y cambios de cada cuenta, con quién los hizo y cuándo.
        Los registros no se modifican ni se borran. «No registrado»: cambio anterior a este historial.</p>
      ${eventos.length ? `
        <div class="tabla-marco">
          <table class="tabla tabla-tarjetas" id="tabla-accesos">
            <thead><tr>${th("Fecha", { clase: "col-principal" })}${th("Persona")}${th("Cambio")}${th("Proyecto")}${th("Antes → después", { ordenable: false })}${th("Hecho por")}</tr></thead>
            <tbody>
              ${eventos.map((x) => `
                <tr>
                  <td data-label="Fecha" class="celda-principal" data-orden="${escapar(x.creado_en)}">${momento(x.creado_en)}</td>
                  <td data-label="Persona" data-orden="${escapar(x.persona_nombre)}">
                    <a href="#/cambios-acceso?usuario=${Number(x.usuario_id)}">${escapar(x.persona_nombre)}</a></td>
                  <td data-label="Cambio">${escapar(TIPOS_ACCESO[x.tipo] || x.tipo)}</td>
                  <td data-label="Proyecto">${x.proyecto_id
                    ? `<a href="#/cambios-acceso?proyecto=${Number(x.proyecto_id)}">${escapar(x.proyecto_nombre)}</a>` : `<span class="tenue">—</span>`}</td>
                  <td data-label="Antes → después">${valoresAcceso(x)}</td>
                  <td data-label="Hecho por">${x.actor_nombre ? escapar(x.actor_nombre) : `<span class="tenue">No registrado</span>`}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>` : vacio("No hay cambios de acceso", filtro ? "Quita el filtro para ver todo el historial." : "")}`,
    montar() {
      document.querySelectorAll("[data-filtro-acceso]").forEach((s) => s.addEventListener("change", () => {
        location.hash = s.value ? `#/cambios-acceso?${s.dataset.filtroAcceso}=${s.value}` : "#/cambios-acceso";
      }));
    },
  };
}
