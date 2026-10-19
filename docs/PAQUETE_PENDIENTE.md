# Publicación segura del curso integrado EPE U1–U7

**13 de octubre de 2026:** recuperado y comprobado el archivo original `EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip`: 2.290.328 bytes, 436 entradas y 21 SCORM correspondientes a las siete unidades. `ZipFile.testzip()` sin errores.

SHA-256 del ZIP original: `a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d`.

## Publicación en GitHub

El archivo integrado completo se ha publicado **cifrado** (AES-256-CBC, PBKDF2, 250.000 iteraciones) en:

[releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip.enc](../releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip.enc)

SHA-256 del archivo cifrado: `123a2db15706bac900e3ffc00a33d73f98e5aeb0832cfc3ed3360ee64d10d84e`.

La copia cifrada ha sido descifrada localmente y comparada byte a byte con el original, sin diferencias. El objeto binario de GitHub se ha contrastado con su SHA-1 de blob calculado localmente.

La contraseña de descifrado **no figura en GitHub**. Está destinada exclusivamente al profesor y se facilita por separado; hay que indicarla como variable de entorno `EPE_BUNDLE_PASSWORD`.

El instalador `install.sh` descarga automáticamente este fichero si recibe `EPE_BUNDLE_PASSWORD`, comprueba los dos hashes, descifra, extrae de forma segura e instala el ERP en el contenedor Ubuntu. Se mantiene la opción de introducir directamente un ZIP mediante `EPE_BUNDLE_FILE`.

## Motivo del cifrado

El ZIP original contiene siete `unidades/U1…U7/servidor/answer_key.json` y un documento `Solucionario_Profesor_Empresa_en_el_Aula_Canarias_2026_2027.docx`. Como este repositorio es público, no se publican esas respuestas en abierto.

Tampoco deben publicarse bases SQLite reales, CSV de credenciales, configuraciones `.env` o datos de alumnos.

## Estado de las pruebas

**Comprobado:** integridad del ZIP original, cifrado y descifrado local, coincidencia de hash del objeto GitHub. La versión original incluía informes de pruebas locales automatizadas.

**Aún pendiente:** prueba completa del instalador modificado en Ubuntu LXC limpio; conexión de red con Cloudflare Tunnel en otro LXC; carga de SCORM en Campus real, persistencia y reporte efectivo de calificaciones. **LTI 1.3 no forma parte de esta versión integrada SCORM y no debe darse por implantado**.

Se recomienda ejecutar primero con empresas ficticias para validar el circuito completo antes de incorporar datos reales del alumnado.

## Paquete cifrado v2 (19/10/2026)

Se generó una nueva clave privada y un fichero cifrado v2 de 2.290.352 bytes a partir del ZIP original, descifrado y verificado localmente. **El binario v2 aún debe subirse manualmente una sola vez** a `releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027_v2.zip.enc` porque la conexión disponible no transfiere binarios locales de ese tamaño a GitHub. Contraseña privada fuera de GitHub. SHA256 cifrado: `8d0adf50d855ec9b06cc04984f0dff9e67de72d34a23b57575c258c1943c88e8`. Para la instalación usa `EPE_BUNDLE_VERSION=v2` tras verificar que el fichero está disponible en remoto.
