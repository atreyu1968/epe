# Instalación desatendida EPE en Ubuntu

## Requisitos

Ubuntu 22.04/24.04 o Debian con `apt-get`, sudo, salida HTTPS y conexión con GitHub. Se necesita el paquete original de código EPE (aún no incluido en este repositorio).

**Instala en una VM/servidor de pruebas antes de producción.** El instalador requiere privilegios root para crear cuentas, instalar dependencias y registrar systemd.

## 1. Descargar y revisar

```bash
curl -fL https://raw.githubusercontent.com/atreyu1968/epe/main/install.sh -o install-epe.sh
less install-epe.sh
```

## 2. Instalar utilizando el ZIP original local

```bash
sudo EPE_BUNDLE_FILE=/ruta/privada/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip \
 EPE_MOODLE_ORIGIN=https://campus.ejemplo.es \
 EPE_INIT_DEMO=1 \
 bash install-epe.sh
```

`EPE_INIT_DEMO=1` crea, una sola vez y solo con bases vacías, dos equipos de demostración de 4 y 5 miembros. Las credenciales quedan en `/var/lib/epe/private/credenciales_epe.csv`, accesibles únicamente al administrador. No mostrar las contraseñas en Moodle. Para instalación sin usuarios ficticios, omitir ese parámetro.

Un ZIP descargado desde Internet requiere `EPE_BUNDLE_URL` + `EPE_BUNDLE_SHA256`. El instalador rechaza URL sin hash.

## 3. Verificar

```bash
systemctl status epe --no-pager
curl -fsS http://127.0.0.1:8000/api/health
journalctl -u epe -n 100 --no-pager
systemctl list-timers | grep epe
```

El resultado de salud debe incluir `"ok": true`. El servicio **escucha solo en 127.0.0.1**: no abrir el puerto 8000 a Internet.

## 4. Acceso HTTPS externo

Configurar Cloudflare Tunnel, Caddy o Nginx con TLS, apuntando al servicio `http://127.0.0.1:8000`. Registrar dominio HTTPS real para el alumnado. No configurar este paso a ciegas: requiere conocer tu dominio, DNS y la existencia de otras aplicaciones del servidor.

Si Moodle tiene otro origen, modificar `EPE_ALLOWED_ORIGINS` en `/etc/epe/epe.env` y reiniciar: `sudo systemctl restart epe`. Respetar el formato exacto `https://host`, sin ruta ni barra final.

## 5. Generar los SCORM

```bash
cd /opt/epe/app
sudo -u epe /opt/epe/venv/bin/python -m runtime.configurar_scorms \
 --servidor https://erp.tu-dominio.es \
 --salida /var/lib/epe/paquetes-campus
```

Importar **21 ZIP individuales** en Campus: portafolio, examen y recuperación para cada U1–U7. No importar directamente el ZIP grande del curso. El examen es individual, el portafolio es cooperativo, y la recuperación no se suma como un tercer instrumento ordinario.

Pesos de las unidades: U1 15 %, U2 12 %, U3 12 %, U4 31 %, U5 15 %, U6 8 %, U7 7 %. Dentro de cada unidad: portafolio 60 % / prueba 40 %. Comprobar todos los criterios individualmente; Moodle no puede obtener todos como ítems separados mediante un único SCORM 1.2.

## 6. Persistencia, actualización y seguridad

- Código: `/opt/epe/app`; scripts de GitHub: `/opt/epe/source`.
- Contraseña y configuración: `/etc/epe/epe.env` (0600, no imprimir ni subir).
- Bases: `/var/lib/epe/data`; copias consistentes: `/var/backups/epe`.
- Copia programada mediante `epe-backup.timer`, retención inicial 14 días. Verificar restauración antes de producción.
- Actualizaciones conservan bases y archivo env. La versión de código previa se guarda en `/opt/epe/releases/`.
- Antes de conectar estudiantes reales: autorizar el tratamiento de datos, realizar prueba piloto de guardado, notas, confidencialidad de empresas, reentradas y evaluación individual.

**Estado:** instalador no ensayado todavía contra el ZIP original por falta de sus bytes; no afirmar que el despliegue ni sus 21 SCORM estén verificados.
