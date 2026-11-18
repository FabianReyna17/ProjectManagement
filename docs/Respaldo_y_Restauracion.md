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
