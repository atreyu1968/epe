# Instalación desatendida EPE Ubuntu dentro de Proxmox LXC

La instalación está diseñada para **Ubuntu completamente limpio** y con **Cloudflare Tunnel en otro LXC**. No hace falta Docker ni instalar cloudflared en el ERP. La guía más directa es [PROXMOX_LXC.md](PROXMOX_LXC.md).

## Pasos

1. Crear contenedor LXC Ubuntu 22.04/24.04 con systemd y acceso a Internet. Asignar IP privada fija.
2. Abrir la consola root del contenedor (no la del host Proxmox).
3. Instalar `curl` y certificados de CA, actualizar paquetes, descargar `install.sh`.
4. Ejecutar el instalador con `EPE_BIND_HOST=IP_DEL_LXC`, `EPE_MOODLE_ORIGIN=https://TU_CAMPUS`, `EPE_BUNDLE_FILE=/ruta/privada/ZIP_ORIGINAL`.
5. Verificar `systemctl status epe` y `curl http://IP_LXC:8000/api/health`.
6. En el contenedor Cloudflare, validar `curl http://IP_LXC:8000/api/health` y configurar el túnel existente con destino `http://IP_LXC:8000`.
7. Verificar `https://erp.TU_DOMINIO/api/health` y generar los SCORM.

El instalador configura usuario de servicio `epe`, dependencias, Python venv, `epe.service`, copias `epe-backup.timer`, secretos en `/etc/epe/epe.env` y bases en `/var/lib/epe/data`.

## Calificaciones Moodle

Se preparan **21 SCORM (U1–U7 × portafolio, examen, recuperación)**. En cada RA: portafolio 60 %, examen 40 %, recuperación independiente sin peso ordinario. Ponderación de RA: U1 15 %, U2 12 %, U3 12 %, U4 31 %, U5 15 %, U6 8 %, U7 7 %. La superación requiere todos los criterios, no solo la media. SCORM 1.2 registra una única nota global por paquete; consultar informes individuales por criterio en el ERP.

## Reinstalaciones

La configuración `/etc/epe/epe.env` y datos `/var/lib/epe/data` se mantienen. Si cambias IP u origen Campus, edita el archivo protegido manualmente y ejecuta `systemctl restart epe`. Copias diarias consistentes del SQLite en `/var/backups/epe` con retención de 14 días. Verifica la restauración en un entorno de prueba.

**Pendiente:** falta integrar en el repositorio el ZIP con los siete módulos y los 21 SCORM, por lo que no se ha validado el despliegue funcional.
