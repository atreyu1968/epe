# Guía de instalación de EPE en Proxmox VE con Cloudflare en otro contenedor

**Destinatario:** administrador del servidor Proxmox. La instalación del ERP se realiza exclusivamente dentro de un nuevo LXC Ubuntu; se reutiliza el contenedor Cloudflare Tunnel existente.

## A. Preparar el LXC EPE desde la interfaz Proxmox

1. Descargar o seleccionar la plantilla `ubuntu-24.04-standard` disponible en tu Proxmox y crear un **CT** (contenedor LXC) nuevo, preferentemente **no privilegiado**.
2. Parámetros iniciales orientativos: **2 núcleos, 4 GB RAM, 20 GB de disco**, 1 NIC en el puente de red accesible para el LXC Cloudflare y arranque automático activado.
3. Configurar **dirección IPv4 privada fija**, máscara, puerta de enlace y DNS. Apuntar la IP de **ambos** LXC. Deben comunicarse por la red privada de Proxmox.
4. Comprobar desde la consola del nuevo CT que Ubuntu tiene `systemd`, DNS e Internet. **No se requieren características Docker, nesting ni un segundo cloudflared.**

En los ejemplos usaremos `192.168.1.60` para EPE y `192.168.1.61` para Cloudflare: **no son tus IP reales**. Sustitúyelas.

## B. Primer arranque: Ubuntu recién creado, sin git, curl ni sudo

Abrir **Consola** del CT EPE en Proxmox, como **root**, no desde la Shell del nodo Proxmox:

```bash
cat /etc/os-release
hostname -I
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl
```

Si `apt-get update` falla, comprobar primero DNS, puerta de enlace, conexión de red y fuentes APT del contenedor. No continuar con errores de paquetes.

## C. Obtener el instalador desde GitHub

En la consola **root del CT EPE**:

```bash
curl -fsSL https://raw.githubusercontent.com/atreyu1968/epe/main/install.sh -o /root/install-epe.sh
cat /root/install-epe.sh
```

El instalador instala posteriormente git, Python, módulos virtuales, dependencias, usuario sin login `epe`, servicio systemd y temporizador de copias SQLite. Ninguna modificación se realiza al contenedor de Cloudflare ni al nodo Proxmox.

## D. Transferir el ZIP real del ERP al nuevo CT

El original verificado se llama:

`EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip`

El archivo recibido contiene 7 unidades y 21 SCORM, **pero también siete claves de corrección del servidor y un solucionario docente**. Por eso no se ofrece públicamente desde el repositorio `atreyu1968/epe`.

Opción recomendada si has descargado el ZIP al equipo personal:

1. Transferirlo con `scp` al **host Proxmox** (si tienes acceso SSH) o por un canal privado autorizado, por ejemplo `/root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip`.
2. En la **Shell del host Proxmox** (no dentro del CT), ejecutar:

```bash
pct push ID_DEL_CONTENEDOR \
  /root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip \
  /root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip
```

3. Volver a la consola **root del CT EPE** y confirmar que existe:

```bash
ls -lh /root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip
sha256sum /root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip
```

La suma SHA-256 del ZIP original adjunto y comprobado es:

```text
a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d
```

Si se modifica el archivo o se genera una nueva versión, la suma será distinta; no utilizarla como comprobación de otras versiones.

## E. Instalar el ERP sin preguntas

Con el archivo ya en el CT, ejecutar en la consola **root del LXC ERP**:

```bash
EPE_BIND_HOST=192.168.1.60 \
EPE_PORT=8000 \
EPE_MOODLE_ORIGIN=https://moodle.atreyuediciones.net \
EPE_BUNDLE_FILE=/root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip \
EPE_BUNDLE_SHA256=a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d \
EPE_INIT_DEMO=1 \
bash /root/install-epe.sh
```

Cambiar `192.168.1.60` por la IP **privada del CT EPE**. Verifica antes que `https://moodle.atreyuediciones.net` es el origen correcto de tu plataforma; si usas otro Campus, sustitúyelo. La instalación con `EPE_INIT_DEMO=1` crea **dos empresas y nueve alumnos ficticios** solo cuando la base está vacía. Las cuentas se guardan privadamente en `/var/lib/epe/private/credenciales_epe.csv`. Para uso real sin alumnos ficticios, **omite `EPE_INIT_DEMO`**.

### ¿Qué hace automáticamente?

- Instala paquetes APT, crea entorno Python y dependencias FastAPI/SQLite.
- Crea el servicio `epe.service`, configurado para iniciar con Ubuntu y escuchar en la IP indicada.
- Crea el almacenamiento persistente `/var/lib/epe/data` y conserva datos en reinstalaciones.
- Crea clave administrativa aleatoria y guarda configuración en `/etc/epe/epe.env`, de acceso restringido.
- Programa copias SQLite consistentes mediante `epe-backup.timer`.
- Comprueba `http://IP_DEL_CT:8000/api/health` y muestra error si falla.

## F. Comprobar que funciona en la red interna

En **CT EPE**:

```bash
systemctl status epe --no-pager
curl -fsS http://192.168.1.60:8000/api/health
journalctl -u epe -n 60 --no-pager
```

La salida correcta debe incluir `"ok":true` y `"modules":7`. Si falla, no continuar todavía con Cloudflare.

## G. Reutilizar Cloudflare Tunnel (otro CT)

Desde **CT Cloudflare**, comprobar:

```bash
curl -fsS http://192.168.1.60:8000/api/health
```

Si este CT no tiene `curl`, instalarlo allí mediante APT o comprobar la conectividad con otra herramienta disponible. Si el acceso falla, revisar IP, conectividad entre contenedores y políticas de firewall.

En **Cloudflare Zero Trust > Networks > Tunnels**, abrir el **túnel existente** y registrar un **public hostname**, por ejemplo:

- Hostname: `erp.tudominio.es` (sustituir por el dominio propio).
- Tipo: `HTTP`.
- Destino/Service URL: `http://192.168.1.60:8000`.

La URL interna **NO** es `http://localhost:8000` cuando Cloudflare reside en un contenedor diferente. No hace falta instalar otro agente Cloudflare en EPE.

Comprobar después desde fuera: `https://erp.tudominio.es/api/health`.

**Firewall:** limitar acceso TCP 8000 al origen `192.168.1.61` (IP real del CT Cloudflare); verificar que el firewall de Proxmox está habilitado en los niveles pertinentes. No redirigir 8000 desde el router ni exponerlo públicamente.

## H. Configurar los SCORM para Campus

Tras activar el dominio HTTPS real, en **CT EPE**:

```bash
cd /opt/epe/app
runuser -u epe -- /opt/epe/venv/bin/python -m runtime.configurar_scorms \
  --servidor https://erp.tudominio.es \
  --salida /var/lib/epe/paquetes-campus
```

**Sustituir la URL de ejemplo** por la real. Deben producirse exactamente **21 archivos ZIP**.

Para descargar cómodamente los 21 ZIP a tu equipo (en **CT EPE**):

```bash
tar -czf /root/EPE_SCORM_CONFIGURADOS.tar.gz -C /var/lib/epe/paquetes-campus .
```

Después transfiere ese TAR mediante un canal privado al ordenador del profesor, descomprímelo y sube a Campus **cada ZIP SCORM por separado**. No intentes añadir el TAR como una actividad.

Continuar con [Campus y calificaciones](CAMPUS_SCORM.md).

## I. Mantenimiento y seguridad

```bash
systemctl status epe --no-pager
systemctl restart epe
systemctl list-timers --all | grep epe
journalctl -u epe -n 100 --no-pager
```

- Los valores de IP, puerto, CORS y clave docente quedan en `/etc/epe/epe.env`. **No compartir su contenido**.
- Si cambias la IP del CT, editar `EPE_BIND_HOST` en ese archivo y reiniciar `epe`; adaptar el destino en Cloudflare.
- Las bases se guardan en `/var/lib/epe/data`, no en el código. Probar una restauración de copia antes del uso real.
- El paquete **no se ha ensayado aún en tu Proxmox/Campus**, aunque sus pruebas locales automatizadas han pasado.
