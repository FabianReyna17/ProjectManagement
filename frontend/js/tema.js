// Tema claro/oscuro elegido por la persona. Se carga en <head> para aplicarlo antes de pintar.
// "sistema" (por defecto) sigue prefers-color-scheme; la preferencia vive solo en este navegador.
(function () {
  let tema = "sistema";
  try { tema = localStorage.getItem("tema") || "sistema"; } catch { /* almacenamiento bloqueado */ }
  if (tema === "claro" || tema === "oscuro") {
    document.documentElement.dataset.theme = tema === "oscuro" ? "dark" : "light";
  }
})();
