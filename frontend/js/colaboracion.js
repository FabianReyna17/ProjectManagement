// Comentarios y archivos de proyectos y tareas (Sprint 4). Los usan la ficha del proyecto y el detalle de la tarea.

function itemComentario(c) {
  return `
    <li class="comentario">
      <p class="comentario-autor">${persona(c.autor_nombre)} <span class="meta">${momento(c.creado_en)}</span></p>
      <p class="texto-largo">${escapar(c.texto)}</p>
    </li>`;
}

/** HU-05-001: sección de comentarios (en orden de publicación) con el formulario para comentar. */
function seccionComentarios(comentarios, destino) {
  return `
    <section class="bloque" aria-labelledby="titulo-comentarios">
      <h2 class="titulo-seccion" id="titulo-comentarios">Comentarios <span class="conteo">${comentarios.length}</span></h2>
      ${comentarios.length
        ? `<ol class="lista-cambios lista-comentarios">${comentarios.map(itemComentario).join("")}</ol>`
        : `<p class="tenue">Aún no hay comentarios. Deja aquí dudas y decisiones sobre ${escapar(destino)}.</p>`}
      <form id="f-comentario" class="formulario compacto form-avance">
        <label>Nuevo comentario <textarea name="texto" required rows="2" maxlength="2000"
          placeholder="Escribe una duda, una decisión o un dato útil"></textarea></label>
        <div class="acciones-form"><button class="boton secundario chico">Comentar</button></div>
      </form>
    </section>`;
}

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
    <li class="archivo">
      <p><button type="button" class="enlace" data-accion="descargar" data-id="${Number(f.id)}"
           data-nombre="${escapar(f.nombre)}">${escapar(f.nombre)}</button>
         <span class="meta">${tamano(f.tamano)}</span></p>
      <p class="meta">${escapar(f.autor_nombre)} · ${momento(f.creado_en)}</p>
    </li>`;
}

/** Sección de archivos con el formulario para adjuntar (tipos y tamaño máximo del servidor). */
function seccionArchivos(archivos, reglas) {
  const tipos = reglas.extensiones.map((e) => `.${e}`).join(",");
  return `
    <section class="bloque" aria-labelledby="titulo-archivos">
      <h2 class="titulo-seccion" id="titulo-archivos">Archivos <span class="conteo">${archivos.length}</span></h2>
      ${archivos.length
        ? `<ul class="lista-cambios lista-archivos">${archivos.map(itemArchivo).join("")}</ul>`
        : `<p class="tenue">Aún no hay archivos adjuntos.</p>`}
      <form id="f-archivo" class="formulario compacto form-avance" data-sin-aviso-cambios="1"
            data-max="${Number(reglas.max_bytes)}" data-tipos="${escapar(reglas.extensiones.join(","))}">
        <label>Adjuntar archivo <input type="file" name="archivo" required accept="${escapar(tipos)}"
          aria-describedby="pista-archivo"></label>
        <p class="pista-campo" id="pista-archivo">Hasta ${tamano(reglas.max_bytes)}.
          Tipos: ${escapar(reglas.extensiones.join(", "))}.</p>
        <div class="acciones-form"><button class="boton secundario chico">Adjuntar</button></div>
      </form>
    </section>`;
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
