# Código de aplicación pendiente

La fuente original del ERP EPE U1–U7 (`EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip`) fue localizada en la biblioteca del proyecto, pero la herramienta disponible no permitió copiar sus bytes. Por ello **no se ha transferido** ese archivo a GitHub.

El repositorio **sí incluye** infraestructura de instalación, servicio y copia de seguridad, pero no constituye aún una distribución autónoma de la aplicación.

## Finalizar el despliegue

1. Facilitar el ZIP original como archivo descargable en el chat o incorporarlo al servidor en una ubicación privada.
2. Verificar que contiene `runtime/requirements.txt`, `runtime/unified.py`, `runtime/manage.py` y `runtime/configurar_scorms.py`.
3. Ejecutar `sudo EPE_BUNDLE_FILE=/ruta/zip EPE_MOODLE_ORIGIN=https://campus.ejemplo.es bash install-epe.sh`.
4. Realizar prueba piloto de las 7 unidades, 21 SCORM, persistencia de datos, informes de evaluación, aislamiento por empresas y seguridad.

**No publicar contraseñas, datos personales, SQLite ni materiales de corrección reservados en el repositorio público.** Si la distribución del backend contiene respuestas de evaluación, decidir expresamente si deben permanecer en un artefacto privado en lugar de GitHub público.
