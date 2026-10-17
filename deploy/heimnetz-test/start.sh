#!/bin/sh
# Verhindert versehentlichen Start auf 0.0.0.0 oder ohne Geheimnisse.
set -eu
cd "$(dirname "$0")"
if [ ! -f .env ]; then
    echo "Bitte .env.example nach .env kopieren und anpassen (chmod 600 .env)" >&2; exit 1
fi
python3 - <<'PY'
from pathlib import Path
from ipaddress import ip_address,ip_network
import socket
cfg={}
for line in Path('.env').read_text().splitlines():
    line=line.strip()
    if not line or line.startswith('#'):continue
    if '=' not in line:raise SystemExit('Ungültige .env-Zeile')
    k,v=line.split('=',1);cfg[k.strip()]=v.strip()
try:
    ip=ip_address(cfg['LAN_BIND_IP']);net=ip_network(cfg['LAN_ALLOWED_CIDR'],strict=False)
    if ip.version != 4 or net.version != 4:
        raise ValueError('Für diesen Heimnetz-Test ist derzeit nur eine private IPv4-Adresse unterstützt')
    if not ip.is_private or ip.is_loopback or ip.is_unspecified or ip not in net:
        raise ValueError('Bind-IP muss privat und im freigegebenen LAN-CIDR liegen')
    # IP muss tatsächlich auf der ThinkStation gebunden sein. Falsche
    # Beispieladressen aus .env.example sollen den Start sofort abbrechen.
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
        try:
            sock.bind((str(ip),0))
        except OSError as exc:
            raise ValueError('LAN_BIND_IP ist auf diesem Rechner nicht vorhanden: '+str(exc))
    port=int(cfg.get('LAN_PORT','8443'))
    if not 1024<=port<=65535:raise ValueError('LAN-Port unzulässig')
    for key in ['BL_DB_PASSWORD','BL_SESSION_SECRET']:
        value=cfg[key]
        if len(value)<48 or any(c not in '0123456789abcdefABCDEF' for c in value):
            raise ValueError(key+' muss aus openssl rand -hex 32 stammen')
    if cfg['BL_DB_PASSWORD']==cfg['BL_SESSION_SECRET']:raise ValueError('Geheimnisse müssen verschieden sein')
except (ValueError,KeyError) as e:raise SystemExit('ABBRUCH: '+str(e))
print('Teststack auf https://%s:%s, erlaubtes Netz %s'%(ip,port,net))
PY
chmod 600 .env
# Bei einer zuvor gestarteten Testinstallation niemals stillschweigend
# neue leere Volumes erzeugen, wenn alte Daten/CA-Volumes entfernt wurden.
marker='.bienenlogger-test-initialisiert'
if [ -f "$marker" ]; then
    for volume in bienenlogger-lan-test_pgdata bienenlogger-lan-test_caddydata; do
        if ! docker volume inspect "$volume" >/dev/null 2>&1; then
            echo "ABBRUCH: Früher vorhandenes Test-Volume $volume fehlt. Bitte Backup/Restore prüfen." >&2
            exit 1
        fi
    done
fi
docker compose --env-file .env -f compose.yaml up -d --build
printf 'Bienenlogger Heimnetz-Testinstallation – Volumes beim Neustart erhalten\n' > "$marker"
chmod 600 "$marker"
mkdir -p certs && chmod 700 certs
if docker compose --env-file .env -f compose.yaml cp proxy:/data/caddy/pki/authorities/local/root.crt certs/heimnetz-test-ca.crt 2>/dev/null; then
    echo "Lokales CA-Zertifikat: certs/heimnetz-test-ca.crt (auf Testgeräten bewusst vertrauen)."
else
    echo "CA-Zertifikat ist noch nicht erzeugt; siehe README.md"
fi
cat <<'MSG'
Container sind gestartet. Nächste Schritte:
  docker compose exec app python /srv/bienenlogger/server/datenbank/stockkarte_admin.py seed-demo
  docker compose exec -it app python /srv/bienenlogger/server/datenbank/stockkarte_admin.py create-user imker
  docker compose exec app python /srv/bienenlogger/server/datenbank/stockkarte_admin.py list-colonies
  docker compose exec app python /srv/bienenlogger/server/datenbank/stockkarte_admin.py grant imker <VOLK-ID> write
Kein produktiver TTN- oder BEEP-Zugang wurde verändert.
MSG
