# Instalación del ERP EPE en Proxmox con Cloudflare en otro LXC

## Arquitectura

```text
Navegador alumnado / Moodle
            │ HTTPS
            ▼
Cloudflare Tunnel (LXC YA EXISTENTE)
            │ Servicio HTTP interno: IP_LXC_EPE:8000
            ▼
ERP EPE (LXC Ubuntu nuevo, IP privada fija)
            ├─ FastAPI U1-U7
            ├─ SQLite persistente
            └─ servicio systemd + backups
```

**No instales Docker ni cloudflared en el contenedor EPE. No ejecutes comandos en el host Proxmox.**

## 1. Crear el LXC

En la interfaz de Proxmox, crear LXC Ubuntu 24.04 con 2 vCPU, 2–4 GB RAM y 15 GB de disco como orientación para una prueba. Puedes empezar con contenedor no privilegiado. Debe tener systemd y salida a Internet (DNS + GitHub + repositorios APT). Configurar **IP privada fija** o reserva DHCP. Apuntar las IP de los dos contenedores, por ejemplo EPE `192.168.1.60` y Cloudflare `192.168.1.61`; **son ejemplos, no valores que debas copiar**.

## 2. Preparar Ubuntu recién instalado (no necesita curl, git ni sudo)

Abrir **Consola** del LXC Ubuntu en Proxmox y entrar como `root`:

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl
curl -fsSL https://raw.githubusercontent.com/atreyu1968/epe/main/install.sh -o /root/install-epe.sh
less /root/install-epe.sh
```

El instalador descargado instalará automáticamente git, Python, venv, pip, SQLite (a través del módulo Python), dependencias del ERP y systemd. Si no tienes `less`, puedes usar `cat /root/install-epe.sh`.

## 3. Instalar ERP desatendidamente

**Solo cuando tengas el ZIP original del ERP** en el LXC (`/root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip`):

```bash
EPE_BIND_HOST=192.168.1.60 \
EPE_MOODLE_ORIGIN=https://moodle.atreyuediciones.net \
EPE_BUNDLE_FILE=/root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip \
bash /root/install-epe.sh
```

Sustituye `192.168.1.60` por la **IP privada del contenedor ERP**, no la de Proxmox ni la del LXC Cloudflare. El instalador conserva los datos y contraseñas en reinstalaciones. Para dos empresas ficticias con 4 y 5 alumnos, añadir `EPE_INIT_DEMO=1` solo en una base inicial vacía. El servicio se ejecutará como usuario sin login `epe`.

**Si aún no tenemos el ZIP:** el repositorio GitHub incluye por ahora solo infraestructura, no los archivos del ERP U1-U7. El instalador muestra un error explícito; no puede levantar una aplicación inexistente. No lo intentes con alumnos reales.

## 4. Comprobar ERP dentro de su LXC

```bash
systemctl status epe --no-pager
curl -fsS http://192.168.1.60:8000/api/health
journalctl -u epe -n 100 --no-pager
```

El endpoint debería devolver `"ok":true` y las siete unidades cuando se disponga del ERP original operativo.

## 5. Usar Cloudflare Tunnel YA EXISTENTE

Desde el contenedor que ejecuta cloudflared, comprobar conectividad con el LXC ERP:

```bash
curl -fsS http://192.168.1.60:8000/api/health
```

Si funciona, abrir Cloudflare Zero Trust, localizar el túnel existente y añadir un **public hostname**: nombre `erp.tudominio.es`, tipo HTTP, destino `192.168.1.60:8000`. La dirección destino **no es `localhost:8000`**, porque localhost en ese túnel apunta al LXC de Cloudflare.

Comprobar desde fuera `https://erp.tudominio.es/api/health` tras publicar el hostname. Entonces generar los 21 SCORM del curso con `https://erp.tudominio.es` y subirlos individualmente a Campus.

## 6. Seguridad

En el firewall de Proxmox, **permitir TCP 8000 solo desde la IP privada del LXC Cloudflare** hacia el LXC ERP. Debes verificar que la política firewall esté realmente activa (en Datacenter, nodo y/o contenedor según configuración). En ningún caso publicar el puerto 8000 en Internet. La IP del LXC ERP debe ser estable para no romper el destino de Cloudflare. Nunca copiar a GitHub `/etc/epe/epe.env` o `/var/lib/epe/data`.

Si cambia la IP del LXC, editar `EPE_BIND_HOST` en `/etc/epe/epe.env` del ERP, reiniciar `systemctl restart epe` y actualizar la ruta del túnel Cloudflare.

## 7. Estado actual

La automatización de infraestructura se ha escrito y publicado, pero **no se ha validado ejecutándose en tu LXC** ni contra el ZIP del ERP, que aún falta incorporar al repositorio.
