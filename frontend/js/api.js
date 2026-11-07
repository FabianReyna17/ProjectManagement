// Cliente HTTP común. El frontend se sirve desde el mismo backend, así que la base es relativa.

// Almacenamiento del navegador: puede estar bloqueado (modo privado), por eso nunca lanza.
const almacen = {
  leer(clave, area = localStorage) { try { return area.getItem(clave); } catch { return null; } },
  guardar(clave, valor, area = localStorage) { try { area.setItem(clave, valor); } catch { /* sin almacenamiento */ } },
  borrar(clave, area = localStorage) { try { area.removeItem(clave); } catch { /* sin almacenamiento */ } },
};

/** Error de la API con su código HTTP y, si el servidor los indica, los campos inválidos. */
class ErrorApi extends Error {
  constructor(mensaje, status = 0, campos = []) {
    super(mensaje);
    this.status = status;
    this.campos = campos;
  }
}

// "Datos inválidos o incompletos: fecha_limite, nombre" → ["fecha_limite", "nombre"]
function camposConError(detalle) {
  const m = /^Datos inválidos o incompletos: (.+)$/.exec(detalle || "");
  return m ? m[1].split(",").map((c) => c.trim()) : [];
}

const API = {
  token() { return almacen.leer("token"); },
  usuario() {
    try { return JSON.parse(almacen.leer("usuario") || "null"); } catch { return null; }
  },

  guardarSesion(data) {
    almacen.guardar("token", data.token);
    this.guardarUsuario(data.usuario);
  },

  guardarUsuario(usuario) { almacen.guardar("usuario", JSON.stringify(usuario)); },

  limpiarSesion() {
    almacen.borrar("token");
    almacen.borrar("usuario");
  },

  /** Al volver a entrar se regresa a esta ruta (se guarda solo para esta pestaña). */
  recordarRuta(ruta) {
    if (ruta && ruta.startsWith("#/") && ruta !== "#/login") almacen.guardar("ruta-tras-login", ruta, sessionStorage);
  },

  /** 401: la sesión ya no sirve. Se muestra el motivo en el login y se recuerda dónde estaba. */
  sesionPerdida(motivo) {
    this.limpiarSesion();
    this.recordarRuta(location.hash);
    if (motivo) almacen.guardar("aviso-login", motivo, sessionStorage);
    if (typeof Formularios !== "undefined") Formularios.descartarTodos();
    location.hash = "#/login";
  },

  async request(metodo, url, body, extra = {}) {
    const headers = { "Content-Type": "application/json", ...extra };
    if (this.token()) headers.Authorization = `Bearer ${this.token()}`;

    let res;
    try {
      res = await fetch(url, { method: metodo, headers, body: body ? JSON.stringify(body) : undefined });
    } catch {
      throw new ErrorApi("No se pudo conectar con el servidor. No se guardó nada; inténtalo de nuevo");
    }

    const data = await res.json().catch(() => ({}));

    if (res.status === 401 && !url.endsWith("/auth/login")) this.sesionPerdida(data.detail);
    // El 403 no redirige aquí: el router muestra "Sin acceso" si falla una consulta y
    // guardar() muestra el motivo si falla una acción, sin sacar a la persona de la vista.
    if (!res.ok) throw new ErrorApi(data.detail || `Error ${res.status}`, res.status, camposConError(data.detail));
    return data;
  },

  get(url) { return this.request("GET", url); },
  post(url, body) { return this.request("POST", url, body); },
  // HU-08-002: creación con clave de operación; repetir la misma clave no duplica
  crear(url, body, clave) { return this.request("POST", url, body, { "Idempotency-Key": clave }); },
  put(url, body) { return this.request("PUT", url, body); },
  del(url) { return this.request("DELETE", url); },

  /** Datos vigentes de la cuenta (la función pudo cambiar con la sesión abierta, RP-04). */
  async refrescarUsuario() {
    const u = await this.get("/api/auth/me");
    this.guardarUsuario(u);
    return u;
  },
};
