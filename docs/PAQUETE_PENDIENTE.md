# Estado real del paquete original y publicación en GitHub

**13 de octubre de 2026:** el archivo `EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip` fue **adjuntado de nuevo en la conversación, recuperado y abierto correctamente**. Contiene 436 entradas, 7 unidades U1–U7, 21 paquetes SCORM, código del backend FastAPI y herramientas de administración.

**SHA-256 del ZIP adjunto:** `a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d`.

**Pruebas locales repetidas:** 21/21 SCORM íntegros, manifiestos y referencias internos correctos; las cuatro pruebas unitarias/de integración `pruebas/test_curso_integrado.py` terminan correctamente con bases SQLite temporales.

## ¿Qué está en GitHub?

El repositorio **público** `atreyu1968/epe` contiene: instalador `install.sh`, servicio systemd, timer de copias, scripts auxiliares y las guías de implantación. **El ERP completo todavía NO ha sido publicado en GitHub.**

## Por qué no se publica directamente el ZIP original

El ZIP contiene siete archivos `unidades/U1…U7/servidor/answer_key.json` que guardan respuestas y criterios de corrección, además de `documentacion/referencias/Solucionario_Profesor_Empresa_en_el_Aula_Canarias_2026_2027.docx`. Publicarlos en un repositorio accesible a estudiantes permitiría acceder a respuestas de evaluación. Tampoco deben publicarse bases SQLite reales, CSV de contraseñas, nombres del alumnado ni claves del profesor.

Para una instalación inmediata, se puede **transferir por vía privada el ZIP original al LXC EPE** y utilizar `EPE_BUNDLE_FILE=/ruta/al/ZIP`; consultar [PROXMOX_LXC.md](PROXMOX_LXC.md).

Para permitir instalar **únicamente desde GitHub** preservando la evaluación, habrá que **separar el código público del paquete privado de claves/solucionarios**, o almacenar toda la distribución en un repositorio privado con acceso autenticado y definir una vía de descarga segura para el instalador. No existe todavía esa distribución desde GitHub público. No prometer un comando autónomo hasta verificarla.

## Pendientes

- Decidir el canal privado de distribución de claves de corrección y solucionarios.
- Realizar la prueba completa de instalación en un LXC Ubuntu limpio.
- Comprobar el túnel Cloudflare del otro LXC y el acceso HTTPS.
- Validar guardado, roles, siete unidades y reporte de calificaciones en Moodle/Campus real.

**El software puede ensayarse con dos empresas ficticias, pero no se considera validado aún para calificar alumnado real.**
