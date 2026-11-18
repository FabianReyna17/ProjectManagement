# Respaldo y restauración

Procedimiento de operación para HU-08-004 (respaldo periódico) y HU-08-005 (restaurar y verificar la recuperación).

## 1. Qué se respalda

Cada respaldo es un archivo `respaldo-AAAAMMDD-HHMMSS-xxxxxx.zip` con:

| Parte | Contenido |
|---|---|
| `gestion.db` | Copia consistente de la base SQLite en uso, hecha con la API de respaldo de SQLite (no hace falta detener el servidor). Incluye cuentas, funciones, accesos a proyectos, eventos de cuenta, proyectos, tareas, avances, bloqueos, comentarios, datos de los archivos, avisos e historiales. |
| `archivos/` | El contenido de los adjuntos (carpeta `ARCHIVOS_DIR`). |
| `manifiesto.json` | Fecha, versión del esquema (migración de Alembic), filas por tabla y huella SHA-256 de la base y de cada adjunto. |

El respaldo se escribe como `.parcial`, se verifica (zip legible, `PRAGMA integrity_check`, filas y huellas iguales al manifiesto) y solo entonces se renombra a `.zip`. Un respaldo a medias o fallido nunca queda disponible.

## 2. Cuándo se respalda

| Variable | Por defecto | Uso |
|---|---|---|
| `RESPALDO_CADA_HORAS` | `24` | El servidor revisa cada hora y respalda si el último respaldo válido tiene más de estas horas. `0` desactiva el ciclo del servidor. |
| `RESPALDOS_DIR` | `backend/data/respaldos` | Carpeta de los respaldos. En producción debe estar en **otro disco o equipo**, no en la misma carpeta que la base ni en una carpeta sincronizada (OneDrive no sustituye un respaldo consistente). |
| `RESPALDOS_CONSERVAR` | `14` | Cantidad de respaldos válidos que se conservan; los más antiguos se borran. El registro de ejecuciones se conserva completo. |

La frecuencia diaria y los 14 días de conservación son la propuesta para RP-08-04; se ajustan cuando el cliente confirme la pérdida máxima tolerable.

Si el servidor no está siempre encendido, el respaldo también puede correrse desde el Programador de tareas de Windows o cron:

```bash
cd backend
python -m app.programado respaldo     # termina con código 1 si el respaldo falla
```

Un Admin también puede pedir un respaldo inmediato desde **Respaldos** (`g r`) en la aplicación.

## 3. Registro y alertas

Cada ejecución queda en la tabla `respaldos` con inicio, fin, resultado (`ok` o `fallido`), origen (programado o a pedido de quién), archivo, tamaño y detalle (o el motivo del fallo). La vista **Respaldos** (solo Admin) muestra el último respaldo válido y señala si el último intento falló o si el respaldo está atrasado. Un respaldo fallido o cuyo archivo ya no existe no cuenta como disponible.

## 4. Acceso

- Los respaldos nunca se sirven por HTTP: solo se pueden leer en el servidor.
- La carpeta se crea con permisos `700` y cada respaldo con `600` (en Linux). En Windows, la carpeta de respaldos debe quedar con permisos solo para la cuenta del servicio y los administradores.
- La API solo informa al Admin el nombre del archivo, no la ruta del servidor (`GET/POST /api/respaldos`).

## 5. Restaurar en producción (HU-08-005)

Tiempo máximo de recuperación propuesto para RP-08-04: **1 hora** desde que se decide restaurar. Pérdida máxima: lo registrado después del último respaldo válido (con la frecuencia diaria, hasta 24 horas).

1. **Elegir el respaldo.** En **Respaldos** (Admin) se ve el último válido; en el servidor está en `RESPALDOS_DIR` con el mismo nombre.
2. **Detener el servidor** para que nadie registre cambios durante la restauración.
3. **Apartar la información actual** sin borrarla (por si hace falta revisarla después), por ejemplo renombrar `backend/data/gestion.db` a `gestion.db.antes-AAAAMMDD` y `backend/data/archivos` a `archivos.antes-AAAAMMDD`.
4. **Restaurar** (verifica el respaldo antes de copiar nada y aplica las migraciones pendientes):

   ```bat
   cd backend
   python -m app.modules.respaldos.restauracion RUTA\respaldo-AAAAMMDD-HHMMSS-xxxxxx.zip ^
       --bd data\gestion.db --archivos data\archivos ^
       --comparar-con data\gestion.db.antes-AAAAMMDD --informe restauracion-AAAAMMDD.md --limite-seg 3600
   ```

   Si el respaldo está dañado o el destino ya existe, termina con código 1 y no escribe nada (`--forzar` reemplaza un destino existente).
5. **Iniciar el servidor** y comprobar: entrar con una cuenta de cada función, abrir un proyecto con tareas, descargar un adjunto y revisar que una persona sin acceso a un proyecto no lo vea.
6. **Comunicar lo no recuperado.** El informe lista, por tabla, lo registrado o cambiado después del respaldo (columna "Registradas después" y "Cambiadas después"): eso hay que volver a registrarlo. Guardar el informe junto con la fecha y quién restauró.

## 6. Prueba de restauración (entorno de prueba)

La restauración se ensaya **en otra carpeta**, sin tocar la información en uso, y se compara con el origen:

```bat
cd backend
python -m app.modules.respaldos.restauracion RUTA\respaldo-....zip ^
    --bd C:\prueba-restauracion\gestion.db --archivos C:\prueba-restauracion\archivos ^
    --comparar-con data\gestion.db --informe prueba-restauracion.md --limite-seg 3600
```

Para revisar la aplicación sobre lo restaurado, se levanta una segunda instancia apuntando a esa copia (`DATABASE_URL=sqlite:///C:/prueba-restauracion/gestion.db`, `ARCHIVOS_DIR=C:\prueba-restauracion\archivos`, `RESPALDO_CADA_HORAS=0`) en otro puerto.

Propuesta: ensayarla al menos una vez al mes y después de cada actualización que agregue migraciones.

Las pruebas automáticas (`tests/test_sprint6.py`) repiten este ensayo en cada push: restauran un respaldo, comparan con el origen (lo registrado después aparece como no recuperado), levantan la aplicación sobre la copia y comprueban relaciones, autoría, adjuntos y que nadie gane acceso a proyectos ajenos; además, que no se restaura encima de otra BD ni desde un respaldo dañado.

### Resultado del ensayo (2026-11-18)

Datos de prueba: 7 cuentas, 12 proyectos, 360 tareas con avances, comentarios y avisos, y 24 adjuntos (respaldo de 3.6 MB). Después del respaldo se registraron un proyecto nuevo con 3 tareas, que la comparación señala como no recuperables desde ese respaldo. Equipo: máquina virtual Linux de 2 núcleos.

- Respaldo: `respaldo-20261118-034649-627323.zip` (creado 2026-11-18 03:46:49 UTC)
- Esquema del respaldo: 0020 · después de restaurar: 0020
- Tiempo de recuperación: 0.071 s (límite 3600.0 s: cumple). Es el tiempo de verificar, copiar y migrar; no incluye los pasos manuales del procedimiento (detener el servidor, apartar la información y comprobar).
- Proyectos: 12 · tareas: 360 · adjuntos: 24

#### Comparación con la BD de origen

| Tabla | Iguales | Registradas después del respaldo | Cambiadas después | Solo en la restaurada |
|---|---|---|---|---|
| usuarios | 7 | — | — | — |
| participantes | 60 | 61 | — | — |
| eventos_cuenta | 0 | — | — | — |
| proyectos | 12 | 13 | — | — |
| historial_proyectos | 0 | — | — | — |
| tareas | 360 | 361, 362, 363 | — | — |
| historial_tareas | 600 | — | — | — |
| avances | 120 | — | — | — |
| bloqueos | 0 | — | — | — |
| comentarios | 72 | — | — | — |
| ediciones_comentario | 0 | — | — | — |
| archivos | 24 | — | — | — |
| avisos | 360 | — | — | — |

Lo registrado o cambiado después del respaldo no se puede recuperar desde él: hay que volver a registrarlo.

En la tabla, `participantes` se identifica por número de fila porque no tiene columna `id`.
