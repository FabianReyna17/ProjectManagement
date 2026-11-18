"""Restaurar un respaldo y verificar la recuperación (HU-08-005).

    python -m app.modules.respaldos.restauracion RESPALDO.zip --bd DESTINO.db --archivos CARPETA
           [--forzar] [--comparar-con ORIGEN.db] [--informe INFORME.md]

1. Verifica el respaldo (zip legible, integridad de la BD, filas y huellas).
2. Copia la BD y los adjuntos al destino (nunca encima de otra BD salvo con --forzar).
3. Aplica las migraciones pendientes, por si el respaldo es de una versión anterior.
4. Opcional: compara con la BD de origen tabla por tabla y documenta qué coincide, qué se
   registró después del respaldo (no recuperable desde él) y qué cambió después.

El tiempo de recuperación se mide desde que empieza la verificación hasta que la BD queda lista.
El procedimiento completo está en docs/Respaldo_y_Restauracion.md.
"""
import argparse
import shutil
import sqlite3
import sys
import time
import zipfile
from pathlib import Path

from ...db.database import migrar
from .service import NOMBRE_BD, conteos, verificar, version_esquema

# Tablas cuyos registros se comparan fila por fila con la BD de origen
TABLAS_COMPARADAS = (
    "usuarios", "participantes", "eventos_cuenta", "proyectos", "historial_proyectos", "tareas",
    "historial_tareas", "avances", "bloqueos", "comentarios", "ediciones_comentario", "archivos", "avisos",
)
TABLAS_PRINCIPALES = ("proyectos", "tareas")


class RestauracionInvalida(Exception):
    pass


def restaurar(ruta_zip: Path, destino_bd: Path, destino_archivos: Path, forzar: bool = False) -> dict:
    """Restaura en destino_bd y destino_archivos. Si algo falla, no deja una BD a medias."""
    inicio = time.perf_counter()
    ruta_zip, destino_bd, destino_archivos = Path(ruta_zip), Path(destino_bd), Path(destino_archivos)
    if destino_bd.exists() and not forzar:
        raise RestauracionInvalida(f"{destino_bd} ya existe: usa otra ruta o --forzar")
    try:
        manifiesto = verificar(ruta_zip)
    except ValueError as e:
        raise RestauracionInvalida(str(e)) from e
    destino_bd.parent.mkdir(parents=True, exist_ok=True)
    destino_archivos.mkdir(parents=True, exist_ok=True)
    parcial = destino_bd.with_name(destino_bd.name + ".parcial")
    try:
        with zipfile.ZipFile(ruta_zip) as z:
            with z.open(NOMBRE_BD) as origen, open(parcial, "wb") as copia:
                shutil.copyfileobj(origen, copia)
            for nombre in manifiesto["archivos"]:
                with z.open(f"archivos/{nombre}") as origen, open(destino_archivos / nombre, "wb") as copia:
                    shutil.copyfileobj(origen, copia)
        for sufijo in ("-wal", "-shm"):  # restos de la BD anterior que SQLite aplicaría sobre la nueva
            Path(f"{destino_bd}{sufijo}").unlink(missing_ok=True)
        parcial.replace(destino_bd)
    finally:
        parcial.unlink(missing_ok=True)
    migrar(f"sqlite:///{destino_bd.as_posix()}")
    con = sqlite3.connect(destino_bd)
    try:
        filas, version = conteos(con), version_esquema(con)
    finally:
        con.close()
    return {
        "respaldo": ruta_zip.name, "creado_en": manifiesto["creado_en"],
        "version_respaldo": manifiesto["version_esquema"], "version_restaurada": version,
        "filas": filas, "adjuntos": len(manifiesto["archivos"]),
        "segundos": round(time.perf_counter() - inicio, 3),
    }


def _filas(con: sqlite3.Connection, tabla: str) -> dict:
    con.row_factory = sqlite3.Row
    columnas = [r["name"] for r in con.execute(f'PRAGMA table_info("{tabla}")')]
    clave = "rowid" if "id" not in columnas else "id"
    return {r[0]: tuple(r[1:]) for r in con.execute(f'SELECT {clave}, * FROM "{tabla}"')}


def comparar(bd_origen: Path, bd_restaurada: Path) -> dict:
    """Por tabla: filas iguales, filas registradas después del respaldo (solo en el origen),
    filas cambiadas después del respaldo y filas que solo están en la restaurada."""
    origen, restaurada = sqlite3.connect(bd_origen), sqlite3.connect(bd_restaurada)
    try:
        tablas_origen = set(conteos(origen))
        resultado = {}
        for tabla in TABLAS_COMPARADAS:
            if tabla not in tablas_origen:
                continue
            a, b = _filas(origen, tabla), _filas(restaurada, tabla)
            resultado[tabla] = {
                "iguales": sum(1 for k in b if a.get(k) == b[k]),
                "posteriores": sorted(k for k in a if k not in b),
                "cambiadas": sorted(k for k in b if k in a and a[k] != b[k]),
                "solo_restaurada": sorted(k for k in b if k not in a),
            }
        return resultado
    finally:
        origen.close()
        restaurada.close()


def _ids(xs: list) -> str:
    if not xs:
        return "—"
    return ", ".join(map(str, xs[:20])) + (" …" if len(xs) > 20 else "")


def informe(datos: dict, diferencias: dict | None, limite_seg: float | None = None) -> str:
    """Resultado de la prueba en Markdown (criterio 3 de HU-08-005)."""
    lineas = [
        "# Prueba de restauración", "",
        f"- Respaldo: `{datos['respaldo']}` (creado {datos['creado_en']} UTC)",
        f"- Esquema del respaldo: {datos['version_respaldo']} · después de restaurar: {datos['version_restaurada']}",
        f"- Tiempo de recuperación: {datos['segundos']} s" + (
            f" (límite {limite_seg} s: {'cumple' if datos['segundos'] <= limite_seg else 'NO cumple'})"
            if limite_seg else ""),
        f"- Proyectos: {datos['filas'].get('proyectos', 0)} · tareas: {datos['filas'].get('tareas', 0)}"
        f" · adjuntos: {datos['adjuntos']}", "",
    ]
    if diferencias is not None:
        lineas += ["## Comparación con la BD de origen", "",
                   "| Tabla | Iguales | Registradas después del respaldo | Cambiadas después | Solo en la restaurada |",
                   "|---|---|---|---|---|"]
        for tabla, d in diferencias.items():
            lineas.append(f"| {tabla} | {d['iguales']} | {_ids(d['posteriores'])} | {_ids(d['cambiadas'])} "
                          f"| {_ids(d['solo_restaurada'])} |")
        perdidos = {t: d for t, d in diferencias.items() if d["posteriores"] or d["cambiadas"]}
        lineas += ["", "Lo registrado o cambiado después del respaldo no se puede recuperar desde él: "
                   + ("hay que volver a registrarlo." if perdidos else "no hubo cambios posteriores."), ""]
    return "\n".join(lineas)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Restaura un respaldo y verifica la recuperación (HU-08-005)")
    p.add_argument("respaldo", type=Path)
    p.add_argument("--bd", type=Path, required=True, help="ruta de la BD restaurada")
    p.add_argument("--archivos", type=Path, required=True, help="carpeta de los adjuntos restaurados")
    p.add_argument("--forzar", action="store_true", help="reemplazar la BD de destino si ya existe")
    p.add_argument("--comparar-con", type=Path, help="BD de origen para comparar")
    p.add_argument("--informe", type=Path, help="escribir el resultado en este archivo .md")
    p.add_argument("--limite-seg", type=float, help="tiempo máximo de recuperación acordado")
    a = p.parse_args(argv)
    try:
        datos = restaurar(a.respaldo, a.bd, a.archivos, a.forzar)
    except RestauracionInvalida as e:
        print(f"No se restauró nada: {e}", file=sys.stderr)
        return 1
    diferencias = comparar(a.comparar_con, a.bd) if a.comparar_con else None
    texto = informe(datos, diferencias, a.limite_seg)
    if a.informe:
        a.informe.write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
