# EPE · Empresa en el Aula (módulo 0446)

Instalación automatizada en Ubuntu del ERP educativo cooperativo y su integración posterior con Moodle/Campus.

> **Estado: infraestructura publicada; código original del ERP pendiente.** Se localizó `EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip`, pero no se pudo recuperar su contenido binario. Este repositorio **todavía no contiene** las siete unidades ni los 21 SCORM. No es una distribución autónoma hasta incorporar dicho paquete. El instalador detecta esa situación y se detiene.

## Instalación desde GitHub

Revisar el script antes de ejecutarlo:

```bash
curl -fL https://raw.githubusercontent.com/atreyu1968/epe/main/install.sh -o install-epe.sh
less install-epe.sh
sudo EPE_BUNDLE_FILE=/ruta/privada/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip \
  EPE_MOODLE_ORIGIN=https://TU-CAMPUS.example \
  bash install-epe.sh
```

Admite también `EPE_BUNDLE_URL` + `EPE_BUNDLE_SHA256` para obtener el paquete de forma verificable por HTTPS. Si el código se incorpora al propio repositorio, `sudo bash install-epe.sh` lo utilizará automáticamente. `EPE_INIT_DEMO=1` crea dos empresas ficticias (4 y 5 estudiantes) solo si la base está vacía.

Prepara dependencias, entorno Python, cuenta del sistema sin login, configuración privada, servicio systemd, copias SQLite consistentes y comprobación local de salud. **No configura automáticamente DNS/HTTPS/Cloudflare ni Moodle**: requieren datos reales y validación previa.

Consulta [instrucciones detalladas](docs/INSTALACION_UBUNTU.md) y [estado del paquete original](docs/PAQUETE_PENDIENTE.md).

## Comandos útiles

```bash
sudo systemctl status epe --no-pager
curl -fsS http://127.0.0.1:8000/api/health
sudo journalctl -u epe -n 100 --no-pager
```

Una vez publicado HTTPS, generar los 21 ZIP individuales para Campus desde `/opt/epe/app` con `runtime.configurar_scorms`. Evaluación prevista: portafolio 60 %, examen individual 40 %, recuperación separada.

## Privacidad

**Repositorio público.** No subir `.env`, claves, datos del alumnado, SQLite, listas de contraseñas ni materiales de corrección cuya divulgación comprometa las pruebas. El material reservado de evaluación debe distribuirse de forma privada. No utilizar con alumnado real hasta completar pruebas funcionales y de protección de datos.
