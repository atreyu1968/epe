#!/usr/bin/env bash
# Instalador EPE 0446. Ubuntu/Debian. Ejecutar como root.
set -Eeuo pipefail
umask 077
export DEBIAN_FRONTEND=noninteractive

log() { printf '[EPE] %s\n' "$*"; }
fail() { printf '[EPE] ERROR: %s\n' "$*" >&2; exit 1; }
[ "$(id -u)" -eq 0 ] || fail "Usa la consola root del LXC Ubuntu (no del host Proxmox), o sudo."
command -v apt-get >/dev/null || fail "Se requiere Ubuntu/Debian con apt-get."

EPE_REPO_URL="https://github.com/atreyu1968/epe.git"
EPE_BUNDLE_FILE="$(printenv EPE_BUNDLE_FILE 2>/dev/null || true)"
EPE_BUNDLE_URL="$(printenv EPE_BUNDLE_URL 2>/dev/null || true)"
EPE_BUNDLE_SHA256="$(printenv EPE_BUNDLE_SHA256 2>/dev/null || true)"
EPE_BUNDLE_PASSWORD="$(printenv EPE_BUNDLE_PASSWORD 2>/dev/null || true)"
EPE_BUNDLE_PASSWORD_FILE="$(printenv EPE_BUNDLE_PASSWORD_FILE 2>/dev/null || true)"
if [ -n "$EPE_BUNDLE_PASSWORD_FILE" ]; then
  [ -z "$EPE_BUNDLE_PASSWORD" ] || fail "No combines EPE_BUNDLE_PASSWORD y EPE_BUNDLE_PASSWORD_FILE."
  [ -f "$EPE_BUNDLE_PASSWORD_FILE" ] && [ -r "$EPE_BUNDLE_PASSWORD_FILE" ] || fail "No se puede leer el fichero de clave EPE_BUNDLE_PASSWORD_FILE."
  [ "$(stat -c '%u' "$EPE_BUNDLE_PASSWORD_FILE")" = 0 ] || fail "El archivo de clave debe pertenecer a root."
  PERMS="$(stat -c '%a' "$EPE_BUNDLE_PASSWORD_FILE")"
  case "$PERMS" in 400|600) ;; *) fail "El archivo de clave debe tener permisos 0600 o 0400 (actuales: $PERMS)." ;; esac
  EPE_BUNDLE_PASSWORD="$(cat "$EPE_BUNDLE_PASSWORD_FILE")"
  [ -n "$EPE_BUNDLE_PASSWORD" ] || fail "El fichero de clave está vacío."
fi
EPE_ENC_URL="https://raw.githubusercontent.com/atreyu1968/epe/main/releases/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip.enc"
EPE_ENC_SHA256="123a2db15706bac900e3ffc00a33d73f98e5aeb0832cfc3ed3360ee64d10d84e"
EPE_ORIGINAL_SHA256="a1cec0729106dc6ee62f7eca3d9108efc276e1b28222b87929ff076437eebd1d"
EPE_MOODLE_ORIGIN="$(printenv EPE_MOODLE_ORIGIN 2>/dev/null || true)"
EPE_PUBLIC_URL="$(printenv EPE_PUBLIC_URL 2>/dev/null || true)"
EPE_INIT_DEMO="$(printenv EPE_INIT_DEMO 2>/dev/null || true)"
EPE_PORT="$(printenv EPE_PORT 2>/dev/null || true)"
EPE_BIND_HOST="$(printenv EPE_BIND_HOST 2>/dev/null || true)"
EPE_SYSTEM_UPGRADE="$(printenv EPE_SYSTEM_UPGRADE 2>/dev/null || true)"
[ -n "$EPE_BIND_HOST" ] || EPE_BIND_HOST=127.0.0.1
[ -n "$EPE_PORT" ] || EPE_PORT=8000
[[ "$EPE_PORT" =~ ^[0-9]{2,5}$ ]] || fail "EPE_PORT debe ser numérico."
if [ -n "$EPE_MOODLE_ORIGIN" ]; then
  [[ "$EPE_MOODLE_ORIGIN" =~ ^https?://[a-zA-Z0-9._:-]+$ ]] || fail "EPE_MOODLE_ORIGIN debe ser un origen sin rutas, por ejemplo https://campus.ejemplo.es."
else
  EPE_MOODLE_ORIGIN="http://localhost:8000"
  log "No se ha indicado Campus. Se autoriza solo el origen de prueba localhost."
fi
if [ -n "$EPE_PUBLIC_URL" ]; then
  [[ "$EPE_PUBLIC_URL" =~ ^https://[a-zA-Z0-9._:-]+$ ]] || fail "EPE_PUBLIC_URL debe ser HTTPS sin rutas."
fi
if [ -n "$EPE_BUNDLE_URL" ]; then
  [[ "$EPE_BUNDLE_URL" =~ ^https:// ]] || fail "El paquete remoto debe descargarse por HTTPS."
  [[ "$EPE_BUNDLE_SHA256" =~ ^[a-fA-F0-9]{64}$ ]] || fail "EPE_BUNDLE_URL exige EPE_BUNDLE_SHA256 (64 caracteres hexadecimales)."
fi
if [ -n "$EPE_BUNDLE_FILE" ] && [ -n "$EPE_BUNDLE_URL" ]; then
  fail "Elige EPE_BUNDLE_FILE o EPE_BUNDLE_URL, no ambos."
fi
if [ -n "$EPE_BUNDLE_FILE" ]; then
  [ -f "$EPE_BUNDLE_FILE" ] || fail "No existe EPE_BUNDLE_FILE: $EPE_BUNDLE_FILE"
fi
log "Instalando dependencias básicas de Ubuntu..."
apt-get update -qq
if [ "$EPE_SYSTEM_UPGRADE" = 1 ]; then
  log "Actualizando paquetes del LXC Ubuntu (sin modificar el host Proxmox)..."
  apt-get upgrade -y -qq -o Dpkg::Options::="--force-confold"
fi
apt-get install -y -qq --no-install-recommends git curl ca-certificates python3 python3-venv python3-pip openssl rsync unzip >/dev/null
command -v systemctl >/dev/null || fail "Falta systemd; usa una plantilla Ubuntu LXC con systemd."
[ -d /run/systemd/system ] || fail "systemd no parece estar arrancado como PID 1."
python3 - "$EPE_BIND_HOST" <<'PY'
import ipaddress, sys
try:
    ipaddress.IPv4Address(sys.argv[1])
except ValueError:
    raise SystemExit("EPE_BIND_HOST necesita una IPv4 válida del LXC.")
PY
if [ "$EPE_BIND_HOST" != 127.0.0.1 ]; then
  log "Servicio accesible por red en $EPE_BIND_HOST; limita el puerto con el firewall de Proxmox."
else
  log "ATENCIÓN: para Cloudflare en otro LXC, define EPE_BIND_HOST=IP_PRIVADA_LXC_ERP."
fi

install -d -m 0755 /opt/epe
if [ -d /opt/epe/source/.git ]; then
  log "Actualizando scripts de GitHub..."
  git -C /opt/epe/source fetch --quiet --depth=1 origin main
  git -C /opt/epe/source reset --hard --quiet origin/main
else
  [ ! -e /opt/epe/source ] || fail "/opt/epe/source ya existe y no es un clon gestionado."
  log "Descargando instalador y archivos de GitHub..."
  git clone --quiet --depth=1 -b main "$EPE_REPO_URL" /opt/epe/source
fi

STAGE="$(mktemp -d /opt/epe/staging.XXXXXXXX)"
trap 'rm -rf "$STAGE"' EXIT
APPROOT=
if [ -n "$EPE_BUNDLE_FILE" ] || [ -n "$EPE_BUNDLE_URL" ] || [ -n "$EPE_BUNDLE_PASSWORD" ] || [ -f /opt/epe/source/dist/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip ]; then
  BUNDLE="$EPE_BUNDLE_FILE"
  if [ -n "$EPE_BUNDLE_URL" ]; then
    BUNDLE="$STAGE/epe-original.zip"
    log "Descargando paquete de aplicación..."
    curl -fL --retry 3 --connect-timeout 15 "$EPE_BUNDLE_URL" -o "$BUNDLE"
  fi
  if [ -z "$BUNDLE" ] && [ -n "$EPE_BUNDLE_PASSWORD" ]; then
    log "Descargando paquete EPE cifrado desde GitHub..."
    ENC="$STAGE/EPE-original.zip.enc"
    BUNDLE="$STAGE/epe-original.zip"
    curl -fsSL --retry 3 --connect-timeout 15 "$EPE_ENC_URL" -o "$ENC"
    printf '%s  %s\n' "$EPE_ENC_SHA256" "$ENC" | sha256sum -c --status || fail "El paquete cifrado no coincide con el SHA-256 publicado."
    log "Descifrando paquete para la instalación (sin publicar la clave)..."
    EPE_BUNDLE_PASSWORD="$EPE_BUNDLE_PASSWORD" openssl enc -d -aes-256-cbc -pbkdf2 -iter 250000 -in "$ENC" -out "$BUNDLE" -pass env:EPE_BUNDLE_PASSWORD || fail "No se pudo descifrar: comprueba la clave."
    printf '%s  %s\n' "$EPE_ORIGINAL_SHA256" "$BUNDLE" | sha256sum -c --status || fail "El SHA-256 del ZIP descifrado no coincide."
    unset EPE_BUNDLE_PASSWORD
  fi
  if [ -z "$BUNDLE" ]; then
    BUNDLE="/opt/epe/source/dist/EPE_0446_CURSO_INTEGRADO_U1_A_U7_2026_2027.zip"
  fi
  if [ -n "$EPE_BUNDLE_SHA256" ]; then
    printf '%s  %s\n' "$EPE_BUNDLE_SHA256" "$BUNDLE" | sha256sum -c --status || fail "El SHA-256 del paquete no coincide."
  fi
  log "Validando rutas y extrayendo paquete..."
  python3 - "$BUNDLE" "$STAGE/unzip" <<'PY'
import pathlib, stat, sys, zipfile
bundle, dest = sys.argv[1:]
with zipfile.ZipFile(bundle) as z:
    for entry in z.infolist():
        p = pathlib.PurePosixPath(entry.filename)
        kind = (entry.external_attr >> 16) & 0o170000
        if (entry.filename.startswith("/") or "\\" in entry.filename
                or ".." in p.parts or kind not in (0, stat.S_IFREG, stat.S_IFDIR)):
            raise SystemExit("ZIP no seguro: " + entry.filename)
    z.extractall(dest)
PY
  APPROOT="$(find "$STAGE/unzip" -type f -path '*/runtime/requirements.txt' -print -quit)"
  [ -n "$APPROOT" ] || fail "El ZIP carece de runtime/requirements.txt."
  APPROOT="$(dirname "$(dirname "$APPROOT")")"
elif [ -f /opt/epe/source/runtime/requirements.txt ]; then
  APPROOT="/opt/epe/source"
else
  fail "FALTA EL ERP: indica EPE_BUNDLE_PASSWORD para descargar desde GitHub el ZIP cifrado, o EPE_BUNDLE_FILE=/ruta/al/ZIP original. No se inicia el servicio."
fi
for f in runtime/requirements.txt runtime/unified.py runtime/manage.py runtime/configurar_scorms.py; do
  [ -f "$APPROOT/$f" ] || fail "Paquete incompleto: falta $f."
done
log "Preparando la versión de la aplicación..."
install -d -m 0755 "$STAGE/app"
rsync -a --exclude='.git/' --exclude='runtime/data/' --exclude='*.sqlite' --exclude='*.sqlite-wal' --exclude='*.sqlite-shm' --exclude='*.env' --exclude='*credenciales*.csv' "$APPROOT/" "$STAGE/app/"
# Integración pública LTI Advantage sobre el ZIP cifrado original. No copia soluciones a GitHub.
[ -f /opt/epe/source/runtime/lti.py ] || fail "Falta runtime/lti.py en el repositorio. Actualiza el instalador."
install -m 0644 /opt/epe/source/runtime/lti.py "$STAGE/app/runtime/lti.py"
if ! grep -q 'from \.lti import router as lti_router' "$STAGE/app/runtime/unified.py"; then
  printf '\n# LTI Advantage 1.3 (OIDC + AGS + NRPS)\nfrom .lti import router as lti_router\napp.include_router(lti_router)\n' >> "$STAGE/app/runtime/unified.py"
fi
cat >> "$STAGE/app/runtime/requirements.txt" <<'LTI_PYTHON_DEPENDENCIES'
PyJWT>=2.8,<3
cryptography>=42,<47
python-multipart>=0.0.12,<1
LTI_PYTHON_DEPENDENCIES
install -d -m 0755 "$STAGE/app/documentacion"
install -m 0644 /opt/epe/source/docs/LTI_CAMPUS.md "$STAGE/app/documentacion/LTI13_CAMPUS.md"
install -d -m 0755 "$STAGE/app/pruebas"
install -m 0644 /opt/epe/source/pruebas/test_curso_integrado.py "$STAGE/app/pruebas/test_curso_integrado.py"
log "Módulo LTI 1.3 incorporado. Permanecerá sin habilitar hasta registrar las credenciales reales de Campus."

if ! getent group epe >/dev/null 2>&1; then
  groupadd --system epe
fi
if ! id epe >/dev/null 2>&1; then
  useradd --system --gid epe --home-dir /var/lib/epe --create-home --shell /usr/sbin/nologin epe
fi
install -d -m 0750 -o epe -g epe /var/lib/epe /var/lib/epe/data /var/lib/epe/private /var/lib/epe/paquetes-campus
install -d -m 0750 /etc/epe /var/backups/epe /opt/epe/releases
chown root:epe /etc/epe
chmod 0750 /etc/epe
# La clave privada LTI no está en GitHub ni dentro del ZIP. Se conserva en reinstalaciones.
LTI_KEY_FILE=/etc/epe/lti-private.pem
if [ ! -f "$LTI_KEY_FILE" ]; then
  log "Creando clave RSA privada para LTI en el LXC..."
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$LTI_KEY_FILE" >/dev/null 2>&1
fi
chown root:epe "$LTI_KEY_FILE"
chmod 0640 "$LTI_KEY_FILE"
if [ ! -f /etc/epe/epe.env ]; then
  SECRET="$(openssl rand -hex 32)"
  {
    printf 'EPE_ADMIN_PASSWORD=%s\n' "$SECRET"
    printf 'EPE_ALLOWED_ORIGINS=%s\n' "$EPE_MOODLE_ORIGIN"
    printf 'EPE_COURSE_DATA=/var/lib/epe/data\n'
    printf 'EPE_BIND_HOST=%s\n' "$EPE_BIND_HOST"
    printf 'EPE_PORT=%s\n' "$EPE_PORT"
    [ -z "$EPE_PUBLIC_URL" ] || printf 'EPE_PUBLIC_URL=%s\n' "$EPE_PUBLIC_URL"
    printf 'EPE_LTI_PRIVATE_KEY_FILE=/etc/epe/lti-private.pem\n'
    printf 'EPE_LTI_GRADE_MODE=disabled\n'
  } >/etc/epe/epe.env
  chmod 0600 /etc/epe/epe.env
  log "Clave administrativa generada en /etc/epe/epe.env (no se muestra)."
else
  log "Conservando claves y configuración de /etc/epe/epe.env. Los parámetros nuevos no sobrescriben valores existentes."
  grep -q '^EPE_BIND_HOST=' /etc/epe/epe.env || printf 'EPE_BIND_HOST=%s\n' "$EPE_BIND_HOST" >> /etc/epe/epe.env
  grep -q '^EPE_PORT=' /etc/epe/epe.env || printf 'EPE_PORT=%s\n' "$EPE_PORT" >> /etc/epe/epe.env
  chmod 0600 /etc/epe/epe.env
fi
# Las credenciales efectivas issuer/client_id/deployment_id las entrega Campus tras registrar la herramienta.
if [ -n "$EPE_PUBLIC_URL" ] && ! grep -q '^EPE_PUBLIC_URL=' /etc/epe/epe.env; then
  printf 'EPE_PUBLIC_URL=%s\n' "$EPE_PUBLIC_URL" >> /etc/epe/epe.env
fi
grep -q '^EPE_LTI_PRIVATE_KEY_FILE=' /etc/epe/epe.env || printf 'EPE_LTI_PRIVATE_KEY_FILE=/etc/epe/lti-private.pem\n' >> /etc/epe/epe.env
grep -q '^EPE_LTI_GRADE_MODE=' /etc/epe/epe.env || printf 'EPE_LTI_GRADE_MODE=disabled\n' >> /etc/epe/epe.env
chmod 0600 /etc/epe/epe.env

python3 -m venv /opt/epe/venv
/opt/epe/venv/bin/python -m pip install -q --upgrade pip
/opt/epe/venv/bin/python -m pip install -q -r "$STAGE/app/runtime/requirements.txt" 'uvicorn>=0.30,<1'
if [ -d /opt/epe/app ]; then
  log "Deteniendo versión anterior y preservando su código..."
  systemctl stop epe.service >/dev/null 2>&1 || true
  mv /opt/epe/app "/opt/epe/releases/app-$(date +%Y%m%d-%H%M%S)"
fi
mv "$STAGE/app" /opt/epe/app
chown -R root:root /opt/epe/app
chmod -R go-w /opt/epe/app

install -m 0644 /opt/epe/source/systemd/epe.service /etc/systemd/system/epe.service
install -m 0750 /opt/epe/source/scripts/backup.sh /usr/local/sbin/epe-backup
install -m 0644 /opt/epe/source/systemd/epe-backup.service /etc/systemd/system/epe-backup.service
install -m 0644 /opt/epe/source/systemd/epe-backup.timer /etc/systemd/system/epe-backup.timer

if [ "$EPE_INIT_DEMO" = 1 ]; then
  if find /var/lib/epe/data -type f -name '*.sqlite' | grep -q .; then
    log "Se conservan las bases existentes; no se recrean los usuarios."
  else
    log "Creando dos empresas ficticias (4 y 5 alumnos)..."
    (
      cd /opt/epe/app
      set -a
      # shellcheck source=/dev/null
      . /etc/epe/epe.env
      set +a
      runuser -u epe -- /opt/epe/venv/bin/python -m runtime.manage crear --equipos 2 --tamanos 4,5 --salida /var/lib/epe/private/credenciales_epe.csv
    )
    chmod 0600 /var/lib/epe/private/credenciales_epe.csv
  fi
fi
if [ -n "$EPE_PUBLIC_URL" ]; then
  log "Generando 21 SCORM para la URL pública..."
  (
    cd /opt/epe/app
    runuser -u epe -- /opt/epe/venv/bin/python -m runtime.configurar_scorms --servidor "$EPE_PUBLIC_URL" --salida /var/lib/epe/paquetes-campus
  )
fi
# Usar los valores persistentes, incluso si el instalador se vuelve a ejecutar.
LIVE_HOST="$(sed -n 's/^EPE_BIND_HOST=//p' /etc/epe/epe.env | tail -n1)"
LIVE_PORT="$(sed -n 's/^EPE_PORT=//p' /etc/epe/epe.env | tail -n1)"
[ -n "$LIVE_HOST" ] && [ -n "$LIVE_PORT" ] || fail "Falta configuración IP/puerto."
CHECK_HOST="$LIVE_HOST"
[ "$CHECK_HOST" = 0.0.0.0 ] && CHECK_HOST=127.0.0.1
systemctl daemon-reload
systemctl enable --now epe-backup.timer >/dev/null
systemctl enable --now epe.service >/dev/null
log "Esperando a que se inicie el ERP..."
for i in $(seq 1 30); do
  if curl --silent --fail "http://$CHECK_HOST:$LIVE_PORT/api/health" -o "$STAGE/health.json"; then
    if python3 - "$STAGE/health.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    data = json.load(f)
raise SystemExit(0 if data.get("ok") is True else 1)
PY
    then
      log "Servidor EPE saludable: http://$CHECK_HOST:$LIVE_PORT/api/health"
      log "Servicio: systemctl status epe"
      log "Configura el Tunnel YA EXISTENTE en el otro LXC con servicio http://$LIVE_HOST:$LIVE_PORT y nombre público HTTPS."
      log "Datos conservados en /var/lib/epe/data; copia diaria en /var/backups/epe."
      exit 0
    fi
  fi
  sleep 2
done
journalctl -u epe.service -n 30 --no-pager >&2 || true
fail "El servicio no pasó la prueba local. Consulta journalctl -u epe -n 100."
