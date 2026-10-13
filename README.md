# EPE · Empresa en el Aula (módulo 0446)

ERP didáctico cooperativo U1–U7 para Campus/Moodle.

> **Estado:** instalador automatizado para Ubuntu Proxmox LXC publicado. **El código del ERP y los 21 SCORM aún no están publicados**: el ZIP original no se pudo recuperar desde la biblioteca y debe añadirse antes de una instalación funcional.

## Topología Proxmox

- **LXC Ubuntu EPE:** aplicación, SQLite, servicio systemd y backups.
- **LXC Cloudflare existente:** túnel HTTPS, compartiendo red privada con el contenedor EPE. No se instala otro cloudflared.
- Campus/Moodle: recibe 21 SCORM; las notas de cada actividad se comunican mediante SCORM 1.2.

## Ubuntu totalmente vacío: primeros pasos

Abrir la consola **root del contenedor Ubuntu** (no del host Proxmox). No hace falta que venga instalado git, curl o sudo:

```bash
apt-get update && apt-get upgrade -y && apt-get install -y ca-certificates curl
curl -fsSL https://raw.githubusercontent.com/atreyu1968/epe/main/install.sh -o /root/install-epe.sh
cat /root/install-epe.sh
```

Cuando hayas copiado el ZIP original del ERP al contenedor, ejecuta:

```bash
EPE_BIND_HOST=192.168.1.60 \
EPE_MOODLE_ORIGIN=https://moodle.atreyuediciones.net \
EPE_BUNDLE_FILE=/root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip \
bash /root/install-epe.sh
```

**192.168.1.60 es solo un ejemplo.** Usa la IP privada real del LXC ERP. Se puede indicar `EPE_SYSTEM_UPGRADE=1` al ejecutar el instalador para que también actualice los paquetes de Ubuntu; los comandos iniciales ya lo hacen. Para pruebas con dos empresas ficticias, añadir `EPE_INIT_DEMO=1`.

Para habilitar HTTPS, editar el **túnel Cloudflare existente** en su propio contenedor, añadiendo un servicio de destino `http://IP_LXC_EPE:8000`. No usar localhost. Asegurar acceso al puerto 8000 solo desde el LXC Cloudflare mediante firewall.

Consulta [guía específica de Proxmox LXC](docs/PROXMOX_LXC.md), [manual detallado Ubuntu](docs/INSTALACION_UBUNTU.md) y [estado del código pendiente](docs/PAQUETE_PENDIENTE.md).

## Seguridad y límites

Nunca subir claves administrativas, datos de estudiantes, CSV de credenciales, ficheros SQLite o respuestas privadas a este **repositorio público**. El instalador se detiene si falta el paquete de aplicación; el despliegue real y la integración de Campus aún están pendientes de pruebas.
