// Utilidades de interfaz.

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto ?? "";
  return div.innerHTML;
}

// HU-08-001: confirmación o error visible para toda acción de guardado
let toastTimer;
function toast(mensaje, tipo = "ok") {
  const el = document.getElementById("toast");
  el.textContent = mensaje;
  el.className = `visible ${tipo}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.className = ""), 3500);
}

/**
 * Envía un formulario: deshabilita el botón, muestra "Guardado" solo si el servidor
 * confirma y el error en caso contrario (la vista no se actualiza si falla).
 */
async function guardar(boton, accion, mensajeOk = "Guardado correctamente") {
  boton.disabled = true;
  try {
    const resultado = await accion();
    toast(mensajeOk, "ok");
    return resultado;
  } catch (e) {
    toast(e.message, "error");
    return null;
  } finally {
    boton.disabled = false;
  }
}

function datosForm(form) {
  return Object.fromEntries(new FormData(form).entries());
}
