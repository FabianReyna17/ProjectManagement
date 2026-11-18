# Despliegue de la versión 1.0

Guía para instalar, operar y actualizar la aplicación en el servidor del cliente (single-tenant). Complementa [Respaldo y restauración](Respaldo_y_Restauracion.md).

## 1. Requisitos

| Elemento | Mínimo |
|---|---|
| Servidor | Windows 10/11, Windows Server 2019+ o Linux, siempre encendido en horario laboral |
| Python | 3.11 o superior |
| Memoria y disco | 2 GB de RAM; disco para la base y los adjuntos (10 MB por archivo como máximo) |
| Respaldos | Otro disco o equipo para `RESPALDOS_DIR` |
| Acceso | Nombre de dominio o IP fija en la red del cliente y certificado HTTPS |
| Equipos de las personas | Navegador actual (Chrome, Edge, Firefox o Safari) en computadora o teléfono |

La aplicación corre en **un solo proceso**: SQLite, el freno de intentos de inicio de sesión y los procesos programados (avisos y respaldos) viven en él. No levantar varios procesos ni réplicas.

## 2. Instalación

1. Copiar el código de la versión (por ejemplo `git clone` y `git checkout` de la versión 1.0.0, o el .zip del release) en una carpeta del servidor, **fuera de OneDrive** u otras carpetas sincronizadas.
2. Crear el entorno e instalar las versiones exactas probadas:

   ```bat
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements-lock.txt
   ```

3. Crear las carpetas de datos fuera del código, por ejemplo `D:\GestionProyectos\datos` (base y adjuntos) y `E:\Respaldos\GestionProyectos` (respaldos), con permisos solo para la cuenta del servicio y los administradores.
4. Definir las variables de entorno de la cuenta del servicio:

| Variable | Valor recomendado | Uso |
|---|---|---|
| `DATABASE_URL` | `sqlite:///D:/GestionProyectos/datos/gestion.db` | Base de datos |
| `ARCHIVOS_DIR` | `D:\GestionProyectos\datos\archivos` | Contenido de los adjuntos |
| `RESPALDOS_DIR` | `E:\Respaldos\GestionProyectos` | Respaldos (otro disco) |
| `RESPALDO_CADA_HORAS` | `24` | Frecuencia del respaldo automático |
| `RESPALDOS_CONSERVAR` | `14` | Respaldos válidos que se conservan |
| `ADMIN_PASSWORD_INICIAL` | una contraseña de un solo uso | Contraseña del `admin` en la instalación nueva; se pide cambiarla al primer ingreso |
| `ZONA_HORARIA` | `America/Guatemala` | Día de la organización para vencimientos |
| `DIAS_POR_VENCER` | `3` | Días de anticipación de los avisos de vencimiento |
| `AVISOS_CADA_MIN` | `60` | Frecuencia del proceso de avisos |
| `ARCHIVO_MAX_MB` | `10` | Tamaño máximo de un adjunto |
| `SESION_INACTIVIDAD_MIN` | `480` | Minutos sin actividad antes de cerrar la sesión |

   `ADMIN_CAMBIO_OBLIGATORIO=0` existe solo para las pruebas automáticas: no se usa en producción.

5. Arrancar como servicio (sin `--reload`), escuchando solo en el propio equipo:

   ```bat
   cd C:\GestionProyectos\backend
   .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers
   ```

   - **Windows:** registrarlo como servicio con [NSSM](https://nssm.cc/) (`nssm install GestionProyectos`, con ese comando, la carpeta `backend` como directorio de inicio, las variables de entorno y reinicio automático), o con una tarea del Programador de tareas "Al iniciar el sistema".
   - **Linux:** una unidad de systemd con `WorkingDirectory=.../backend`, `EnvironmentFile=` con las variables y `Restart=always`.

   Las migraciones pendientes se aplican solas al arrancar.

6. **HTTPS:** publicar la aplicación a través de un proxy inverso con certificado; no exponer el puerto 8000. Con [Caddy](https://caddyserver.com/), por ejemplo:

   ```
   gestion.cliente.com {
       reverse_proxy 127.0.0.1:8000
   }
   ```

   (IIS con URL Rewrite + ARR o nginx sirven igual.)

7. **Primer ingreso:** entrar con `admin` y `ADMIN_PASSWORD_INICIAL`; la aplicación exige elegir una contraseña nueva. Después, registrar las cuentas en **Usuarios** y quitar `ADMIN_PASSWORD_INICIAL` de las variables (solo se usa cuando la base está vacía).

## 3. Verificación después de instalar o actualizar

1. `GET https://gestion.cliente.com/api/salud` responde `{"estado": "ok", "version": "1.0.0", "esquema": "0021"}` (503 si la base no está disponible).
2. Recorrido corto: entrar, crear un proyecto de prueba, una tarea, y abrirlo desde un teléfono.
3. En **Respaldos**, "Respaldar ahora" termina como Correcto.
4. Ensayar una restauración en una carpeta aparte ([procedimiento](Respaldo_y_Restauracion.md#6-prueba-de-restauración-entorno-de-prueba)).

## 4. Actualizar a una versión nueva

1. Avisar a las personas y hacer un respaldo: `python -m app.programado respaldo` (debe terminar en "ok").
2. Detener el servicio.
3. Reemplazar el código por el de la versión nueva **sin tocar las carpetas de datos** y reinstalar dependencias con su `requirements-lock.txt`.
4. Iniciar el servicio (aplica las migraciones) y comprobar `/api/salud`: debe mostrar la versión y el esquema nuevos.
5. Si algo falla: detener, volver al código anterior y restaurar el respaldo del paso 1 siguiendo [Restaurar en producción](Respaldo_y_Restauracion.md#5-restaurar-en-producción-hu-08-005). Un esquema migrado no se usa con el código anterior.

## 5. Operación

| Qué | Cómo |
|---|---|
| Disponibilidad | Monitorear `/api/salud` cada pocos minutos |
| Respaldos | Revisar la vista **Respaldos**: señala si el último falló o está atrasado |
| Restauración | Ensayarla al menos una vez al mes y después de cada actualización con migraciones |
| Accesos | **Historial de accesos** muestra altas, retiros, cambios de función, desactivaciones y restablecimientos |
| Registros | La salida del servicio (NSSM o journald) guarda los errores de los procesos programados |

## 6. Limitaciones conocidas de la versión 1.0

- El token de sesión se guarda en el navegador (`localStorage`); queda pendiente pasarlo a una cookie HttpOnly con protección CSRF.
- El hash de contraseñas (PBKDF2-SHA256, 100 000 iteraciones) no guarda su algoritmo ni costo; queda pendiente una política con rehash al iniciar sesión.
- Un solo proceso con SQLite: suficiente para una organización; si el piloto muestra mucha escritura simultánea, se evaluará PostgreSQL.
- Los avisos se ven dentro de la aplicación; no se envían por correo.
- Los listados no están paginados.
