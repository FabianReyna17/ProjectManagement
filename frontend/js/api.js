// Cliente HTTP común. El frontend se sirve desde el mismo backend, así que la base es relativa.
const API = {
  token() { return localStorage.getItem("token"); },
  usuario() { return JSON.parse(localStorage.getItem("usuario") || "null"); },

  guardarSesion(data) {
    localStorage.setItem("token", data.token);
    localStorage.setItem("usuario", JSON.stringify(data.usuario));
  },

  limpiarSesion() {
    localStorage.removeItem("token");
    localStorage.removeItem("usuario");
  },

  async request(metodo, url, body, extra = {}) {
    const headers = { "Content-Type": "application/json", ...extra };
    if (this.token()) headers.Authorization = `Bearer ${this.token()}`;

    let res;
    try {
      res = await fetch(url, { method: metodo, headers, body: body ? JSON.stringify(body) : undefined });
    } catch {
      throw new Error("No se pudo conectar con el servidor");
    }

    const data = await res.json().catch(() => ({}));

    if (res.status === 401 && !url.endsWith("/login")) {
      this.limpiarSesion();
      location.hash = "#/login";
    }
    if (res.status === 403) {
      location.hash = "#/sin-acceso";
    }
    if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
    return data;
  },

  get(url) { return this.request("GET", url); },
  post(url, body) { return this.request("POST", url, body); },
  // HU-08-002: creación con clave de operación; repetir la misma clave no duplica
  crear(url, body, clave) { return this.request("POST", url, body, { "Idempotency-Key": clave }); },
  put(url, body) { return this.request("PUT", url, body); },
  del(url) { return this.request("DELETE", url); },
};
