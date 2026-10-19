#!/usr/bin/env bash
# EPE 0446: bootstrap sin preguntas desde Ubuntu LXC en Proxmox.
# Instala dependencias base, detecta IPv4, descarga e inicia install.sh.
# La clave del paquete cifrado debe estar provisionada previamente y NO en GitHub.
set -Eeuo pipefail
umask 077
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

log() { printf '[EPE AUTO] %s\n' "$*"; }
fail() { printf '[EPE AUTO] ERROR: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "Ejecuta como root DENTRO del LXC Ubuntu, no en Proxmox host."
command -v apt-get >/dev/null || fail "Se necesita Ubuntu/Debian (apt-get)."
[ -d /run/systemd/system ] || fail "El LXC debe arrancar con systemd."

# No arrancar apt ni modificar el contenedor si falta el material privado.
if [ -z "${EPE_BUNDLE_FILE:-}" ] && [ -z "${EPE_BUNDLE_URL:-}" ] && [ -z "${EPE_BUNDLE_PASSWORD:-}" ]; then
  if [ -z "${EPE_BUNDLE_PASSWORD_FILE:-}" ]; then
    EPE_BUNDLE_PASSWORD_FILE=/root/.config/epe/bundle-password
  fi
  export EPE_BUNDLE_PASSWORD_FILE
  [ -s "$EPE_BUNDLE_PASSWORD_FILE" ] || fail "Falta la clave privada en $EPE_BUNDLE_PASSWORD_FILE. El ZIP cifrado se descarga solo de GitHub, pero no puede descifrarse sin su clave. No se ha modificado Ubuntu."
fi

# IP única preferida; en multihomed, especificar EPE_BIND_HOST expresamente.
if [ -z "${EPE_BIND_HOST:-}" ]; then
  IPS="$(hostname -I 2>/dev/null || true)"
  count=0
  for candidate in $IPS; do
    case "$candidate" in *:*) continue ;; esac
    case "$candidate" in 127.*|169.254.*) continue ;; esac
    count=$((count+1))
    EPE_BIND_HOST="$candidate"
  done
  [ "$count" -eq 1 ] || fail "No se puede seleccionar una IPv4 de forma inequívoca ($count candidatas). Indica EPE_BIND_HOST=IP_PRIVADA_LXC."
fi
export EPE_BIND_HOST
log "Instalación automatizada para LXC EPE: $EPE_BIND_HOST."
[ -n "${EPE_MOODLE_ORIGIN:-}" ] || log "No se ha indicado EPE_MOODLE_ORIGIN. Configúralo cuando conozcas el dominio real de Moodle."
[ -n "${EPE_PUBLIC_URL:-}" ] || log "La URL HTTPS del túnel Cloudflare se configurará después; no se instala otro túnel."

log "Actualizando índices e instalando curl y certificados (sin preguntas)..."
apt-get update -qq
if [ "${EPE_SYSTEM_UPGRADE:-0}" = 1 ]; then
  apt-get upgrade -y -qq -o Dpkg::Options::="--force-confold"
fi
apt-get install -y -qq --no-install-recommends ca-certificates curl >/dev/null

log "Descargando instalador oficial desde GitHub..."
curl -fL --retry 3 --connect-timeout 15 --proto '=https' --tlsv1.2 \
  https://raw.githubusercontent.com/atreyu1968/epe/main/install.sh \
  -o /root/install-epe.sh
chmod 0700 /root/install-epe.sh
bash -n /root/install-epe.sh || fail "El instalador descargado presenta un error de sintaxis."
log "Instalando ERP, LTI, servicio systemd y copias SQLite..."
bash /root/install-epe.sh
log "Fin: servicio EPE instalado en http://$EPE_BIND_HOST:${EPE_PORT:-8000}/api/health"
