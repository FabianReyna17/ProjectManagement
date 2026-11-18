// Comentarios y archivos de proyectos y tareas (Sprint 4). Los usan la ficha del proyecto y el detalle de la tarea.

// HU-05-004: solo su autor corrige o retira lo que publicó (y solo si el proyecto sigue abierto)
const esMio = (x) => x.autor_id === API.usuario()?.id;

function constanciaRetiro(x, que) {
  return `<p class="retirado">${icono("cerrar")}${que} retirado por ${escapar(x.retirado_por_nombre)} · ${momento(x.retirado_en)}</p>`;
}

function itemComentario(c, { editable = true } = {}) {
  if (c.retirado_en) {
    return `
      <li class="comentario" data-tipo="comentario">
        <p class="comentario-autor">${persona(c.autor_nombre)} <span class="meta">${momento(c.creado_en)}</span></p>
        ${constanciaRetiro(c, "Comentario")}
      </li>`;
  }
  return `
    <li class="comentario" data-tipo="comentario" data-comentario="${Number(c.id)}">
      <p class="comentario-autor">${persona(c.autor_nombre)} <span class="meta">${momento(c.creado_en)}</span>
        ${c.editado_en ? `<button type="button" class="enlace meta" data-accion="ver-ediciones" data-id="${Number(c.id)}"
            aria-expanded="false">Editado ${momento(c.editado_en)}</button>` : ""}
        ${editable && esMio(c) ? `<span class="acciones-propias">
          <button type="button" class="boton chico secundario" data-accion="editar-comentario" data-id="${Number(c.id)}">Editar</button>
          <button type="button" class="boton chico peligro-suave" data-accion="retirar-comentario" data-id="${Number(c.id)}">Retirar</button>
        </span>` : ""}</p>
      <p class="texto-largo">${escapar(c.texto)}</p>
      <div class="ediciones" hidden></div>
    </li>`;
}

ACCIONES["editar-comentario"] = (btn) => {
  const li = btn.closest("li");
  const texto = li.querySelector(".texto-largo");
  if (li.querySelector("form")) return;
  const form = document.createElement("form");
  form.className = "formulario compacto";
  form.id = `f-editar-comentario-${btn.dataset.id}`;
  form.innerHTML = `
    <label><span class="solo-lector">Corregir comentario</span>
      <textarea name="texto" required rows="3" maxlength="2000"></textarea></label>
    <p class="pista-campo">Quedará la marca "Editado" y quien tenga acceso podrá ver el texto anterior.</p>
    <div class="acciones-form">
      <button class="boton chico">Guardar corrección</button>
      <button type="button" class="boton chico secundario" data-cancelar>Cancelar</button>
    </div>`;
  const area = form.querySelector("textarea");
  area.value = texto.textContent;
  texto.hidden = true;
  texto.after(form);
  Formularios.mejorar(form);
  area.focus();
  form.querySelector("[data-cancelar]").addEventListener("click", () => {
    Formularios.marcarLimpio(form);
    form.remove();
    texto.hidden = false;
    btn.focus();
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const ok = await guardar(form.querySelector("button:not([type=button])"),
      () => API.put(`/api/comentarios/${btn.dataset.id}`, datosForm(form)), "Comentario corregido", { form });
    if (ok) recargar();
  });
};

ACCIONES["retirar-comentario"] = async (btn) => {
  const si = await confirmar({
    titulo: "¿Retirar este comentario?",
    mensaje: "Dejará de verse su texto. Quedará la constancia de que lo retiraste y cuándo.",
    aceptar: "Retirar comentario", peligro: true,
  });
  if (si && await guardar(btn, () => API.del(`/api/comentarios/${btn.dataset.id}`), "Comentario retirado")) recargar();
};

// Textos anteriores de un comentario editado, con quién y cuándo
ACCIONES["ver-ediciones"] = async (btn) => {
  const caja = btn.closest("li").querySelector(".ediciones");
  const abrir = caja.hidden;
  btn.setAttribute("aria-expanded", String(abrir));
  if (!abrir) { caja.hidden = true; return; }
  try {
    const ediciones = await API.get(`/api/comentarios/${btn.dataset.id}/ediciones`);
    caja.innerHTML = `<p class="meta">Versiones anteriores</p><ol>${ediciones.slice().reverse().map((e) => `
      <li><p class="texto-largo">${escapar(e.texto_anterior)}</p>
          <p class="meta">Reemplazado por ${escapar(e.editado_por_nombre)} · ${momento(e.editado_en)}</p></li>`).join("")}</ol>`;
    caja.hidden = false;
  } catch (e) {
    toast(e.message, "error");
  }
};

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
        ? `<ol class="lista-cambios lista-actividad">${actividad.map((x) => (x.tipo === "archivo"
            ? itemArchivo(x, { editable: !soloLectura }) : itemComentario(x, { editable: !soloLectura }))).join("")}</ol>`
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

function itemArchivo(f, { editable = true } = {}) {
  if (f.retirado_en) {
    return `
      <li class="archivo" data-tipo="archivo">
        ${constanciaRetiro(f, "Archivo")}
        <p class="meta">Adjuntado por ${escapar(f.autor_nombre)} · ${momento(f.creado_en)}</p>
      </li>`;
  }
  return `
    <li class="archivo" data-tipo="archivo">
      <p>${icono("clip")}<button type="button" class="enlace" data-accion="descargar" data-id="${Number(f.id)}"
           data-nombre="${escapar(f.nombre)}">${escapar(f.nombre)}</button>
         <span class="meta">${tamano(f.tamano)}</span>
         ${editable && esMio(f) ? `<span class="acciones-propias"><button type="button" class="boton chico peligro-suave"
            data-accion="retirar-archivo" data-id="${Number(f.id)}" data-nombre="${escapar(f.nombre)}">Retirar</button></span>` : ""}</p>
      <p class="meta">Adjuntado por ${escapar(f.autor_nombre)} · ${momento(f.creado_en)}</p>
    </li>`;
}

ACCIONES["retirar-archivo"] = async (btn) => {
  const si = await confirmar({
    titulo: `¿Retirar «${btn.dataset.nombre}»?`,
    mensaje: "Ya no se podrá descargar ni se verá su nombre. Quedará la constancia de que lo retiraste y cuándo.",
    aceptar: "Retirar archivo", peligro: true,
  });
  if (si && await guardar(btn, () => API.del(`/api/archivos/${btn.dataset.id}`), "Archivo retirado")) recargar();
};

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
