# Inventario y comprobación del paquete integrado EPE (U1–U7)

**Origen recibido:** `EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip`

**SHA-256 del ZIP original:** `a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d`

**Verificación (14/10/2026):** 436 ficheros extraídos correctamente; `ZipFile.testzip()` sin errores; 21 paquetes SCORM 1.2 (portafolio, examen y recuperación en cada una de las siete unidades). Se encuentran 7 servidores funcionales de unidad y los módulos `runtime/` de servicio unificado, provisión, generación de SCORM y gestión de expedientes, junto con documentación y pruebas.

## Estructura de contenido

| Ruta interior | Función |
| --- | --- |
| `LEEME_PRIMERO.md` | Descripción, limitaciones y prerrequisitos |
| `scorms/EPE_U{1..7}_{Portafolio,Examen,Recuperacion}_INTEGRADO.zip` | 21 paquetes |
| `unidades/U1/` … `unidades/U7/` | Fuentes SCORM y servidores por unidad |
| `runtime/unified.py` | Servidor común de U1–U7 |
| `runtime/course_core.py` | Identidad de empresa, documentos, aislamiento entre equipos |
| `runtime/manage.py` | Gestión de equipos de cuatro y cinco estudiantes y migración |
| `runtime/configurar_scorms.py` | Inserción de URL HTTPS final y recreación de ZIP |
| `documentacion/` | Instalación de Campus, migración, validación y fuentes docentes |
| `pruebas/` | Pruebas automatizadas de integración y comprobación de SCORM |

## Estado y precauciones

- El mismo paquete original ya está disponible **cifrado** en [releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip.enc](../releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip.enc). Se necesita la contraseña privada entregada fuera de GitHub. El instalador actual comprueba la suma SHA-256 tras el descifrado.
- No subir directamente el ZIP original, `unidades/U*/servidor/answer_key.json`, ni `documentacion/referencias/Solucionario_Profesor_Empresa_en_el_Aula_Canarias_2026_2027.docx` a un repositorio público: expondría las respuestas de evaluación.
- **LTI 1.3 no está implementado en este paquete**: la integración actual es SCORM 1.2 + autenticación EPE separada. La opción LTI de Campus fotografiada por el profesorado permite planificar un desarrollo posterior, pero no constituye una prueba funcional.
- La ejecución local de `python -m unittest discover -s pruebas -p 'test*.py' -v` concluyó con **4 pruebas superadas**. El informe incluido declara pruebas anteriores en Chromium, pero esa prueba de navegador no se ha reproducido en esta verificación.
- **Campus Moodle y Proxmox reales no están validados**. No usar calificaciones oficiales hasta un piloto con usuarios de prueba que verifique persistencia, reanudación SCORM, aislamiento entre empresas y transferencia de notas.

## Instalación

Consultar [README principal](../README.md), [manual Proxmox](PROXMOX_LXC.md) e [instrucciones Campus SCORM](CAMPUS_SCORM.md). El archivo cifrado y la instalación por ZIP original son las dos vías previstas. La aplicación se sirve en un LXC Ubuntu separado del contenedor de Cloudflare Tunnel.
