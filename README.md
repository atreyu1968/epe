# EPE · Empresa en el Aula (0446) · U1–U7

**ERP didáctico cooperativo para 2.º de CFGM de Gestión Administrativa (Canarias, 2026–2027).** Siete unidades, 21 paquetes SCORM 1.2 (portafolio, examen y recuperación), empresas simuladas de 4–5 alumnos y backend FastAPI/SQLite.

> **Estado real (13/10/2026):** ZIP original recibido y verificado localmente: **21/21 SCORM íntegros y cuatro pruebas de integración superadas**. El paquete completo **ya se encuentra publicado CIFRADO** en [releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip.enc](releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip.enc), sin exponer en abierto las claves de corrección ni el solucionario docente. Para instalarlo desde GitHub hace falta la clave privada `EPE_BUNDLE_PASSWORD`, entregada por separado. La instalación en Ubuntu y la integración en Campus real todavía requieren una prueba con el servidor definitivo.

## Inventario del ZIP original y compatibilidad LTI

- [Inventario verificado de los 436 archivos, 21 SCORM y resultados de las pruebas](docs/INVENTARIO_ZIP_INTEGRADO_2026_2027.md).
- **El paquete original no incorpora aún LTI 1.3**: utiliza SCORM 1.2 con cuentas EPE propias. El registro de una herramienta LTI 1.3 y el envío automático de calificaciones mediante AGS son desarrollos pendientes; no basta con seleccionar esas opciones en Campus.
- El ZIP sin cifrar contiene claves de corrección y solucionario. Mantener la distribución completa **cifrada**, con la contraseña por canal privado; no descomprimir directamente todo su contenido en este repositorio público.

## LTI Advantage 1.3: integrado en el instalador (14/10/2026)

La rama `main` contiene ahora el [módulo LTI 1.3](runtime/lti.py), las [pruebas automáticas](pruebas/test_curso_integrado.py), y la [guía de registro en Campus](docs/LTI_CAMPUS.md). **La nueva versión de `install.sh` incorpora estas fuentes al ZIP original cifrado**, instala PyJWT y las dependencias necesarias, genera en el LXC una clave RSA privada y conserva los expedientes y las siete unidades existentes.

- El usuario abre la herramienta desde Campus; el ERP valida la firma y los campos OIDC obligatorios de LTI 1.3.
- La primera vez, el profesor vincula cada identidad firmada con una cuenta EPE y su empresa mediante `/lti/admin/`. El alumnado entra posteriormente al portafolio sin otra contraseña.
- El informe de portafolio puede enviarse a Campus mediante AGS; **por defecto está desactivado** hasta superar la prueba real con alumnos ficticios. NRPS puede consultar participantes, pero **no garantiza la información de grupos**.
- Los exámenes individuales continúan como paquetes SCORM 1.2. No ponderar simultáneamente un portafolio SCORM y su homólogo LTI.
- La integración se ha **probado localmente** mediante pruebas criptográficas, replay, asignación de cuentas, aislamiento y simulaciones AGS. **No está instalada ni validada todavía en tu Moodle/Proxmox real**.
- No es necesario publicar sin cifrar el ZIP completo ni el solucionario; el instalador combina la distribución cifrada ya publicada con el código LTI público.

Consulta [instalación LTI en Campus](docs/LTI_CAMPUS.md) para los campos concretos, la clave pública y las variables de `/etc/epe/epe.env`.

## Rotación de clave del ZIP cifrado — versión 2 (19/10/2026)

Se ha generado y **verificado mediante descifrado completo** el nuevo archivo privado
`EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027_v2.zip.enc`, de 2.290.352 bytes. Conserva el ZIP original, cuyo SHA-256 descifrado es `a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d`.

**Estado de publicación:** el binario **v2 todavía NO está subido a GitHub**. El código ya admite `EPE_BUNDLE_VERSION=v2`, pero no intentes ejecutar la descarga cifrada de v2 hasta completar la carga. La versión anterior sigue disponible mientras tanto.

Una sola vez, desde la sesión del propietario del repositorio en GitHub, abre [releases](https://github.com/atreyu1968/epe/tree/main/releases), pulsa **Add file > Upload files**, selecciona el fichero v2 descargado del chat y confirma **Commit changes** sobre `main`. El archivo a cargar debe tener exactamente el nombre:

`releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027_v2.zip.enc`

**No subas el archivo de clave privada.** Clave y ZIP se entregan por separado fuera del repositorio público. SHA-256 del fichero cifrado v2:

`8d0adf50d855ec9b06cc04984f0dff9e67de72d34a23b57575c258c1943c88e8`

Después de subirlo a GitHub y guardar la clave privada en el CT con permisos 0600:

```bash
apt-get update && apt-get install -y ca-certificates curl
curl -fsSL https://raw.githubusercontent.com/atreyu1968/epe/main/scripts/auto-install.sh -o /root/epe-auto-install.sh
EPE_BIND_HOST=172.16.180.31 EPE_BUNDLE_VERSION=v2 EPE_INIT_DEMO=1 bash /root/epe-auto-install.sh
```

El instalador utilizará `/root/.config/epe/bundle-password` por defecto, donde debe haberse colocado la nueva clave de descifrado sin el salto de línea final. La instalación no solicita datos, verifica **dos SHA-256**, configura LTI, datos, servidor y servicio, y ejecuta la prueba `/api/health`.

Como alternativa privada se puede asignar `EPE_BUNDLE_PASSWORD` mediante variable de entorno para una ejecución sin fichero, pero evita dejar secretos en el historial de comandos, capturas de terminal o procesos visibles para otros usuarios.

## Instalación totalmente desatendida desde GitHub (contenedor EPE 110)

Se ha añadido [scripts/auto-install.sh](scripts/auto-install.sh) para que un Ubuntu limpio instale sus dependencias, detecte su IPv4, descargue el ERP **cifrado desde el propio repositorio**, verifique las sumas SHA-256, configure las siete unidades, LTI 1.3, systemd y copias SQLite y realice una comprobación local. No necesita copiar el ZIP desde Windows ni instalar Docker.

**Única condición previa:** el ZIP contiene las respuestas de evaluación y está cifrado; el instalador no puede conocer su clave de forma pública. Deposita **una vez** la contraseña de descifrado en `/root/.config/epe/bundle-password` con propietario root y permisos `0600` (nunca dentro de GitHub). Si no dispones de esa clave, solicita la reemisión privada del paquete cifrado; no hay forma segura de descifrarlo sin ella.

Para evitar incluir la clave en el historial, en la consola root del CT se puede crear con un editor de texto privado, o mediante una transferencia segura ya autorizada. **El auto-instalador no pide claves ni datos durante su ejecución**: aborta antes de modificar Ubuntu si falta la clave.

En la consola root del **contenedor 110** (IP detectada: `172.16.180.31`):

```bash
# Ejecutar SOLO tras guardar la clave privada en /root/.config/epe/bundle-password
apt-get update && apt-get install -y ca-certificates curl
curl -fsSL https://raw.githubusercontent.com/atreyu1968/epe/main/scripts/auto-install.sh -o /root/epe-auto-install.sh
bash -n /root/epe-auto-install.sh
EPE_BIND_HOST=172.16.180.31 EPE_INIT_DEMO=1 bash /root/epe-auto-install.sh
```

`EPE_INIT_DEMO=1` crea dos empresas ficticias con 4 y 5 alumnos; omítelo para no crear datos de prueba. El instalador conserva `/etc/epe/epe.env` y las bases de datos en reinstalaciones. Si el servidor tiene varias interfaces, define `EPE_BIND_HOST` explícitamente.

**Sin contraseña del ZIP cifrado**, también se admite el ZIP original transferido privadamente al contenedor; ejecutar `EPE_BUNDLE_FILE=/ruta/ERP.zip bash /root/epe-auto-install.sh`. Esto no requiere cifrado, pero sí copiar el archivo.

El autoinstalador instala todo **en el LXC ERP**, pero no debe intervenir en el túnel Cloudflare del otro LXC ni registrar una herramienta LTI en Moodle sin sus identificadores reales (Client ID, Deployment ID, issuer), que emite Campus. Tras instalar, ver [registro LTI](docs/LTI_CAMPUS.md).

## Arquitectura de despliegue prevista

```text
Alumnado ─ HTTPS ─► Cloudflare Tunnel (LXC ya existente)
                               │ HTTP en LAN privada
                               ▼
                  Ubuntu 24.04 LXC en Proxmox (EPE)
                  FastAPI :8000 + SQLite + systemd
                               ▲
                      SCORM 1.2 desde Moodle
```

No se instala Docker ni un segundo Cloudflare Tunnel. El ERP escucha en la **IP privada del propio LXC**, no en `127.0.0.1`, porque Cloudflare se ejecuta en otro contenedor.

## Instalación en un contenedor Ubuntu totalmente vacío

Requisitos recomendados para empezar: Ubuntu 24.04 LXC no privilegiado, 2 vCPU, 4 GB RAM, 20 GB de disco, systemd, IP privada fija y conectividad a Internet. **Ejecuta los siguientes comandos en la consola root del LXC EPE, NO en el host Proxmox.**

**1. Actualizar e instalar lo imprescindible para descargar el instalador.** No se presupone que `curl`, `git` o `sudo` estén preinstalados:

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl
```

**2. Descargar el instalador desde GitHub y revisarlo:**

```bash
curl -fsSL https://raw.githubusercontent.com/atreyu1968/epe/main/install.sh -o /root/install-epe.sh
cat /root/install-epe.sh
```

**3. Instalar automáticamente desde GitHub con la clave privada del paquete cifrado.**

La clave privada de despliegue se entrega al profesor por un canal distinto a GitHub. **Nunca la publiques en el repositorio.** El siguiente comando la solicita sin mostrarla en pantalla y la utiliza durante la instalación:

```bash
read -rsp 'Clave privada del ZIP EPE: ' EPE_BUNDLE_PASSWORD; echo
export EPE_BUNDLE_PASSWORD

EPE_BIND_HOST=192.168.1.60 \
EPE_MOODLE_ORIGIN=https://moodle.atreyuediciones.net \
EPE_INIT_DEMO=1 \
bash /root/install-epe.sh

unset EPE_BUNDLE_PASSWORD
```

Reemplaza `192.168.1.60` por la **IP privada REAL del LXC EPE**. `EPE_INIT_DEMO=1` crea únicamente si la base está vacía dos empresas de prueba de 4 y 5 integrantes; omite esa variable si no deseas datos demostrativos.

**Alternativa:** si prefieres trasladar personalmente el ZIP original al LXC, usa:

```bash
EPE_BIND_HOST=192.168.1.60 \
EPE_MOODLE_ORIGIN=https://moodle.atreyuediciones.net \
EPE_BUNDLE_FILE=/root/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip \
EPE_INIT_DEMO=1 bash /root/install-epe.sh
```

En esta vía manual puedes trasladarlo desde el host Proxmox con `pct push ID_CT /ruta/ZIP /root/ZIP` (solo en el host, no dentro del LXC).

El instalador automatizado verifica el SHA-256 del cifrado (`123a2db15706bac900e3ffc00a33d73f98e5aeb0832cfc3ed3360ee64d10d84e`) y el del ZIP descifrado (`a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d`). Ante cualquier error, se detiene.

**5. Comprobar el servicio**, todavía sin Cloudflare:

```bash
systemctl status epe --no-pager
curl -fsS http://192.168.1.60:8000/api/health
journalctl -u epe -n 50 --no-pager
```

La respuesta esperada incluye `"ok":true` y `"modules":7`.

**6. En el OTRO LXC (donde ya funciona Cloudflare Tunnel):** comprobar que `http://192.168.1.60:8000/api/health` responde, y añadir un hostname público al **túnel existente** cuyo destino sea `http://IP_PRIVADA_LXC_EPE:8000`. **No uses `localhost` en Cloudflare**, porque señalaría al propio LXC del túnel. Limita el puerto TCP 8000 por firewall a la IP del LXC de Cloudflare.

**7. Generar los 21 ZIP destinados a Campus** cuando el dominio HTTPS definitivo funcione:

```bash
cd /opt/epe/app
runuser -u epe -- /opt/epe/venv/bin/python -m runtime.configurar_scorms \
  --servidor https://erp.tudominio.es \
  --salida /var/lib/epe/paquetes-campus
```

La URL anterior es un **ejemplo**, no una dirección instalada. Subir a Campus los 21 ZIP **individuales y sin descomprimir**. No subir el ZIP original completo como actividad.

## Organización docente en Campus

- Cada unidad U1–U7 tiene **portafolio cooperativo (60 %)**, **examen individual (40 %)** y **recuperación independiente** (sin sumar como tercer instrumento ordinario).
- Pesos del módulo: U1 **15 %**, U2 **12 %**, U3 **12 %**, U4 **31 %**, U5 **15 %**, U6 **8 %**, U7 **7 %**.
- Aprobar exige superar **todos los criterios y resultados**, no únicamente la media. SCORM 1.2 comunica una nota por paquete; el detalle por criterio se consulta en el ERP.
- Cada alumno utiliza identidad y contraseña propia. Los grupos de Moodle no crean automáticamente las cuentas ERP.

## Archivos y operación

| Ruta | Uso |
| --- | --- |
| `/opt/epe/app` | Código activo del ERP |
| `/opt/epe/source` | Scripts obtenidos de GitHub |
| `/etc/epe/epe.env` | Clave administrativa, CORS, IP y puerto (privado) |
| `/var/lib/epe/data` | Ocho SQLite persistentes |
| `/var/lib/epe/paquetes-campus` | ZIP SCORM configurados |
| `/var/backups/epe` | Copias SQLite consistentes y programadas |

## Manuales

- [Instalación completa en Proxmox LXC con Cloudflare separado](docs/PROXMOX_LXC.md)
- [Instalación y administración en Ubuntu](docs/INSTALACION_UBUNTU.md)
- [Importar los 21 SCORM en Campus y verificar calificaciones](docs/CAMPUS_SCORM.md)
- [Estado del paquete, publicación y seguridad](docs/PAQUETE_PENDIENTE.md)

**Seguridad:** el repositorio es público; no subir soluciones, contraseñas, informes nominativos ni datos SQLite. Antes de emplearlo con alumnado real, verificar el inicio/cierre/reentrada, la persistencia, la comunicación de notas con Moodle, el aislamiento entre empresas y la autorización del tratamiento de datos. **No se ha realizado todavía esa prueba piloto en tu Campus ni en tu contenedor Proxmox.**
