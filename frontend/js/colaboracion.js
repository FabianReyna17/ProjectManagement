// Comentarios y archivos de proyectos y tareas (Sprint 4). Los usan la ficha del proyecto y el detalle de la tarea.

function itemComentario(c) {
  return `
    <li class="comentario" data-tipo="comentario">
      <p class="comentario-autor">${persona(c.autor_nombre)} <span class="meta">${momento(c.creado_en)}</span></p>
      <p class="texto-largo">${escapar(c.texto)}</p>
    </li>`;
}

// ---------- HU-05-003 Comentarios y archivos en una sola sección ----------

const FILTROS_ACTIVIDAD = { todo: "Todo", comentario: "Comentarios", archivo: "Archivos" };

/**
 * Comentarios y archivos del proyecto o la tarea en orden de publicación, con un filtro
 * (Todo / Comentarios / Archivos) y, debajo, los formularios para comentar y adjuntar.
 */
function seccionColaboracion(actividad, reglas, destino, { soloLectura = false } = {}) {
  const cuenta = { todo: actividad.length, comentario: 0, archivo: 0 };
  actividad.forEach((x) => cuenta[x.tipo]++);
  return `
    <section class="bloque" aria-labelledby="titulo-colaboracion">
      <div class="encabezado-seccion">
        <h2 class="titulo-seccion" id="titulo-colaboracion">Comentarios y archivos <span class="conteo">${actividad.length}</span></h2>
        ${actividad.length ? `<div class="selector-vista" role="group" aria-label="Mostrar">${Object.entries(FILTROS_ACTIVIDAD).map(([v, t]) => `
          <button type="button" class="boton chico ${v === "todo" ? "" : "secundario"}" data-accion="filtrar-actividad"
                  data-filtro="${v}" aria-pressed="${v === "todo"}" ${cuenta[v] ? "" : "disabled"}>${t} <span class="conteo">${cuenta[v]}</span></button>`).join("")}
        </div>` : ""}
      </div>
      ${actividad.length
        ? `<ol class="lista-cambios lista-actividad">${actividad.map((x) => (x.tipo === "archivo" ? itemArchivo(x) : itemComentario(x))).join("")}</ol>`
        : `<p class="tenue">${soloLectura ? "No hay comentarios ni archivos."
            : `Aún no hay comentarios ni archivos. Deja aquí dudas, decisiones y material sobre ${escapar(destino)}.`}</p>`}
      ${soloLectura ? "" : `<div class="colaboracion-formularios">
        <form id="f-comentario" class="formulario compacto">
          <label>Nuevo comentario <textarea name="texto" required rows="2" maxlength="2000"
            placeholder="Escribe una duda, una decisión o un dato útil"></textarea></label>
          <div class="acciones-form"><button class="boton secundario chico">Comentar</button></div>
        </form>
        ${formularioArchivo(reglas)}
      </div>`}
    </section>`;
}

ACCIONES["filtrar-actividad"] = (btn) => {
  const filtro = btn.dataset.filtro;
  btn.parentElement.querySelectorAll("button").forEach((b) => {
    const activo = b === btn;
    b.setAttribute("aria-pressed", activo);
    b.classList.toggle("secundario", !activo);
  });
  document.querySelectorAll(".lista-actividad > li").forEach((li) => {
    li.hidden = filtro !== "todo" && li.dataset.tipo !== filtro;
  });
};

/** Envía el comentario con su clave de operación (HU-08-002) y recarga la vista. */
function montarComentarios(url) {
  const form = document.getElementById("f-comentario");
  const clave = nuevaClave();
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const ok = await guardar(form.querySelector("button"), () => API.crear(url, datosForm(form), clave),
      "Comentario publicado", { form });
    if (ok) recargar();
  });
}

// ---------- HU-05-002 Adjuntar archivo ----------

const FMT_TAMANO = new Intl.NumberFormat("es-GT", { maximumFractionDigits: 1 });

function tamano(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${FMT_TAMANO.format(bytes / 1024)} KB`;
  return `${FMT_TAMANO.format(bytes / 1024 / 1024)} MB`;
}

function itemArchivo(f) {
  return `
    <li class="archivo" data-tipo="archivo">
      <p>${icono("clip")}<button type="button" class="enlace" data-accion="descargar" data-id="${Number(f.id)}"
           data-nombre="${escapar(f.nombre)}">${escapar(f.nombre)}</button>
         <span class="meta">${tamano(f.tamano)}</span></p>
      <p class="meta">Adjuntado por ${escapar(f.autor_nombre)} · ${momento(f.creado_en)}</p>
    </li>`;
}

/** Formulario para adjuntar (tipos y tamaño máximo los da el servidor). */
function formularioArchivo(reglas) {
  const tipos = reglas.extensiones.map((e) => `.${e}`).join(",");
  return `
      <form id="f-archivo" class="formulario compacto" data-sin-aviso-cambios="1"
            data-max="${Number(reglas.max_bytes)}" data-tipos="${escapar(reglas.extensiones.join(","))}">
        <label>Adjuntar archivo <input type="file" name="archivo" required accept="${escapar(tipos)}"
          aria-describedby="pista-archivo"></label>
        <p class="pista-campo" id="pista-archivo">Hasta ${tamano(reglas.max_bytes)}.
          Tipos: ${escapar(reglas.extensiones.join(", "))}.</p>
        <div class="acciones-form"><button class="boton secundario chico">Adjuntar</button></div>
      </form>`;
}

/** Revisa tipo y tamaño antes de subir (el servidor vuelve a validar) y sube con clave de operación. */
function montarArchivos(url) {
  const form = document.getElementById("f-archivo");
  if (!form) return;
  const entrada = form.querySelector("input[type=file]");
  let clave = nuevaClave();  // HU-08-002: el reintento del mismo archivo reusa la clave
  entrada.addEventListener("change", () => { clave = nuevaClave(); entrada.setCustomValidity(""); });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const archivo = entrada.files[0];
    if (!archivo) return;
    const ext = archivo.name.includes(".") ? archivo.name.split(".").pop().toLowerCase() : "";
    const problema = !form.dataset.tipos.split(",").includes(ext) ? "Ese tipo de archivo no está permitido."
      : archivo.size > Number(form.dataset.max) ? `El archivo supera el tamaño máximo de ${tamano(Number(form.dataset.max))}.`
      : archivo.size === 0 ? "El archivo está vacío." : "";
    if (problema) {
      entrada.setCustomValidity(problema);
      entrada.reportValidity();
      return;
    }
    const ok = await guardar(form.querySelector("button"), () => API.subir(url, archivo, clave), "Archivo adjuntado", { form });
    if (ok) recargar();
  });
}

ACCIONES.descargar = async (btn) => {
  try {
    await API.descargar(`/api/archivos/${btn.dataset.id}/descarga`, btn.dataset.nombre);
  } catch (e) {
    if (e.status !== 401) toast(e.message, "error");
    if (e.status === 403) recargar();
  }
};
