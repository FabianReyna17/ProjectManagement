// Respaldos (Sprint 6, HU-08-004). Solo Admin: estado del último respaldo, historial y respaldo inmediato.

function tamanoLegible(bytes) {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function etiquetaRespaldo(resultado) {
  return resultado === "ok"
    ? `<span class="chip chip-resuelto">${icono("ok")}Correcto</span>`
    : `<span class="chip chip-atencion">${icono("error")}Fallido</span>`;
}

function frecuenciaTexto(horas) {
  if (!horas) return "El respaldo programado está desactivado en este servidor.";
  if (horas === 24) return "Se respalda automáticamente una vez al día.";
  return horas < 1 ? `Se respalda automáticamente cada ${Math.round(horas * 60)} minutos.`
    : `Se respalda automáticamente cada ${horas} horas.`;
}

async function vistaRespaldos() {
  if (API.usuario()?.funcion !== "Admin") throw sinAcceso();
  const e = await API.get("/api/respaldos");
  const u = e.ultimo_valido;
  const alerta = !u ? "Todavía no hay ningún respaldo válido."
    : e.ultimo_fallido ? "El último intento de respaldo falló. El último respaldo válido es el indicado arriba."
    : e.atrasado ? "El respaldo programado está atrasado: el último válido supera la frecuencia acordada." : "";
  return {
    titulo: "Respaldos",
    seccion: "respaldos",
    html: `
      <header class="encabezado">
        <div>
          <h1 tabindex="-1">Respaldos</h1>
          <p class="subtitulo">${escapar(frecuenciaTexto(e.frecuencia_horas))}</p>
        </div>
        <div class="encabezado-acciones">
          <button type="button" class="boton" data-accion="respaldar-ahora">${icono("ok")}Respaldar ahora</button>
        </div>
      </header>
      <section class="bloque" aria-labelledby="titulo-ultimo">
        <h2 class="titulo-seccion" id="titulo-ultimo">Último respaldo válido</h2>
        ${u ? `<p class="resumen-respaldo">${etiquetaRespaldo("ok")} ${momento(u.terminado_en)} · ${escapar(u.detalle || "")}
                 · ${escapar(tamanoLegible(u.tamano))}</p>` : ""}
        ${alerta ? `<p class="nota nota-peligro" role="status">${icono("aviso")}${escapar(alerta)}</p>` : ""}
        <p class="tenue">Cada respaldo incluye la base de datos completa (cuentas, permisos, proyectos, tareas, avances,
          bloqueos, comentarios, avisos e historiales) y los archivos adjuntos. Se guarda aparte de la información en uso
          y solo es accesible en el servidor; la restauración se describe en docs/Respaldo_y_Restauracion.md.</p>
      </section>
      <section class="bloque" aria-labelledby="titulo-ejecuciones">
        <h2 class="titulo-seccion" id="titulo-ejecuciones">Ejecuciones <span class="conteo">${e.respaldos.length}</span></h2>
        ${e.respaldos.length ? `
          <div class="tabla-marco">
            <table class="tabla tabla-tarjetas" id="tabla-respaldos">
              <thead><tr>${th("Fecha", { clase: "col-principal" })}${th("Resultado")}${th("Origen")}${th("Tamaño")}${th("Detalle")}</tr></thead>
              <tbody>
                ${e.respaldos.map((r) => `
                  <tr>
                    <td data-label="Fecha" class="celda-principal" data-orden="${escapar(r.terminado_en)}">${momento(r.terminado_en)}</td>
                    <td data-label="Resultado" data-orden="${r.resultado === "ok" ? 0 : 1}">${etiquetaRespaldo(r.resultado)}</td>
                    <td data-label="Origen">${r.origen === "manual" ? `A pedido de ${escapar(r.actor_nombre || "")}` : "Programado"}</td>
                    <td data-label="Tamaño" data-orden="${Number(r.tamano) || 0}">${escapar(tamanoLegible(r.tamano))}</td>
                    <td data-label="Detalle">${escapar(r.detalle || "")}${r.archivo ? `<br><small class="tenue">${escapar(r.archivo)}</small>` : ""}</td>
                  </tr>`).join("")}
              </tbody>
            </table>
          </div>` : vacio("Aún no se ha hecho ningún respaldo", "Usa «Respaldar ahora» o espera al respaldo programado.")}
      </section>`,
  };
}

ACCIONES["respaldar-ahora"] = async (btn) => {
  const r = await guardar(btn, () => API.post("/api/respaldos"), "Respaldo creado");
  if (!r) return;
  if (r.resultado !== "ok") toast(`El respaldo falló: ${r.detalle}`, "error");
  recargar();
};
