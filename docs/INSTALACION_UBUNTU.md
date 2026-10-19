# Instalación desatendida · EPE 0446 en Ubuntu LXC

Para una instalación nueva en Proxmox con Cloudflare Tunnel en otro contenedor, sigue preferentemente la [guía de Proxmox paso a paso](PROXMOX_LXC.md).

## Nuevo autoinstalador desatendido

Para el contenedor **110 (172.16.180.31)**, está disponible [scripts/auto-install.sh](../scripts/auto-install.sh). Desde Ubuntu sin curl, instalar primero certificados y curl, descargar ese script y ejecutarlo. **Requisito:** archivo privado `/root/.config/epe/bundle-password` con el secreto de descifrado y permisos `0600`, provisionado de forma segura. Sin secreto, el script termina antes de modificar nada. El sistema descarga y valida el ZIP cifrado desde GitHub; no hay que trasladar el ZIP original. El inicio LTI efectivo requiere dar de alta la herramienta desde el Campus real más adelante.

```bash
apt-get update && apt-get install -y ca-certificates curl
curl -fsSL https://raw.githubusercontent.com/atreyu1968/epe/main/scripts/auto-install.sh -o /root/epe-auto-install.sh
EPE_BIND_HOST=172.16.180.31 EPE_INIT_DEMO=1 bash /root/epe-auto-install.sh
```

## Resumen operativo

**Contexto:** Ubuntu 24.04 recién instalado; puede no tener `git`, `curl` ni `sudo`. Abrir la consola `root` del **contenedor ERP**, no la del host Proxmox.

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl
curl -fsSL https://raw.githubusercontent.com/atreyu1968/epe/main/install.sh -o /root/install-epe.sh
cat /root/install-epe.sh
```

Transferir por vía privada el archivo `EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip` a `/root/` del CT.

En la consola `root` del LXC EPE:

```bash
EPE_BIND_HOST=IP_PRIVADA_DEL_LXC_EPE \
EPE_MOODLE_ORIGIN=https://TU_CAMPUS \
EPE_BUNDLE_FILE=/root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip \
EPE_BUNDLE_SHA256=a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d \
EPE_INIT_DEMO=1 \
bash /root/install-epe.sh
```

**IP_PRIVADA_DEL_LXC_EPE** debe sustituirse por una IPv4 válida (p. ej. `192.168.1.60`). **https://TU_CAMPUS** debe sustituirse por el origen exacto del Moodle real, sin barra ni rutas. En un LXC inicial para pruebas, `EPE_INIT_DEMO=1` crea 2 empresas ficticias con 4 y 5 usuarios; omitirlo si no se desean.

### Opción de instalar desde un ZIP alojado en HTTPS

Se admite `EPE_BUNDLE_URL=https://url-de-descarga-privada` en vez de `EPE_BUNDLE_FILE`, acompañado obligatoriamente de `EPE_BUNDLE_SHA256`. No se ha publicado una URL permanente del ZIP en GitHub; por contener claves de corrección, el material debe permanecer bajo distribución privada.

## Servicio y diagnóstico

```bash
systemctl status epe --no-pager
curl -fsS http://IP_PRIVADA_DEL_LXC_EPE:8000/api/health
journalctl -u epe -n 100 --no-pager
systemctl list-timers --all | grep epe
```

El servidor debe devolver `"ok":true` y 7 módulos. Se instala un servicio `systemd` persistente y un `epe-backup.timer` con copias consistentes SQLite y retención inicial de 14 días. No se instala Docker ni cloudflared.

## Cloudflare en un LXC separado

1. Desde el CT de Cloudflare, comprobar `http://IP_PRIVADA_DEL_LXC_EPE:8000/api/health`.
2. En el túnel **ya existente** de Cloudflare, crear un hostname público HTTPS apuntando a `http://IP_PRIVADA_DEL_LXC_EPE:8000`.
3. Restringir el puerto TCP 8000 para que solo acepte conexiones desde la IP del CT Cloudflare (firewall en Proxmox).
4. Comprobar `https://DOMINIO_PUBLICO/api/health` desde un navegador externo.

No usar `127.0.0.1` como destino del túnel si los servicios están en distintos contenedores.

## Preparar Campus

Una vez que el dominio público HTTPS funcione:

```bash
cd /opt/epe/app
runuser -u epe -- /opt/epe/venv/bin/python -m runtime.configurar_scorms \
  --servidor https://DOMINIO_PUBLICO \
  --salida /var/lib/epe/paquetes-campus
```

Deben aparecer **21 SCORM individuales**: siete portafolios, siete exámenes y siete recuperaciones. Subirlos separadamente sin descomprimir. Ver [configuración Campus/Moodle](CAMPUS_SCORM.md).

## Almacenamiento, actualizaciones y precauciones

| Ruta | Finalidad |
|---|---|
| `/opt/epe/app` | Código EPE activo |
| `/opt/epe/source` | Scripts del repositorio |
| `/etc/epe/epe.env` | Clave docente, IP, puerto y orígenes CORS |
| `/var/lib/epe/data` | Bases persistentes `u1…u7.sqlite` y `course.sqlite` |
| `/var/lib/epe/private` | CSV de cuentas ficticias cuando se usa `EPE_INIT_DEMO=1` |
| `/var/backups/epe` | Copias consistentes |

El instalador conserva datos existentes y no recrea cuentas en bases ya pobladas. En reinstalaciones, el archivo `/etc/epe/epe.env` prevalece sobre nuevas variables; cambiar sus valores manualmente cuando proceda y reiniciar el servicio.

**Validación efectuada:** ZIP original recuperado, 21/21 SCORM íntegros y cuatro pruebas de integración local correctas. **Pendiente:** despliegue en LXC real, acceso HTTPS desde Cloudflare y comunicación real del SCORM con Campus. No evaluarlo con alumnos reales antes de esa prueba.
