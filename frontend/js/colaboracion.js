// Comentarios de proyectos y tareas (Sprint 4). Componentes que usan la ficha del proyecto y el detalle de la tarea.

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
