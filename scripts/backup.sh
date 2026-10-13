#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
install -d -m 0700 /var/backups/epe
python3 - <<'PY'
import datetime, pathlib, sqlite3
source = pathlib.Path('/var/lib/epe/data')
destination = pathlib.Path('/var/backups/epe') / datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
dbs = sorted(source.rglob('*.sqlite'))
if not dbs:
    print('EPE: todavía no hay bases SQLite que respaldar')
    raise SystemExit(0)
destination.mkdir(mode=0o700)
for src in dbs:
    target = destination / src.relative_to(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    a = sqlite3.connect(f'file:{src}?mode=ro', uri=True)
    b = sqlite3.connect(str(target))
    try:
        a.backup(b)
    finally:
        b.close()
        a.close()
print('EPE: copia consistente creada:', destination)
PY
find /var/backups/epe -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf -- {} +
