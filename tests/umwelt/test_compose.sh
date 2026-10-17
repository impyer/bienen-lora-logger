#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Starts/restarts ONLY an explicitly named isolated cloud/CI test project.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
cd "$repo"
: "${R1_COMPOSE_ENV:?Explicit synthetic env file required}"
: "${COMPOSE_PROJECT_NAME:?Explicit isolated test project required}"
case "$COMPOSE_PROJECT_NAME" in bienenlogger-r1-*) ;; *) echo 'Refuse non-R1 project' >&2; exit 1;; esac
mkdir -p "$repo/build"
work=$(mktemp -d "$repo/build/r1-compose.XXXXXX")
chmod 755 "$work"
trap 'rm -f "$work/login.json" "$work/cookies"' EXIT
# Contains generated SYNTHETIC fixtures only. Existing env files are never edited.
python3 - "$R1_COMPOSE_ENV" "$work" <<'PY'
from pathlib import Path
import sys
from datetime import datetime,timezone,timedelta
env=Path(sys.argv[1]).read_text().splitlines()
assert 'LAN_BIND_IP=127.0.0.1' in env, 'Cloud/CI test only; never contact a LAN host'
now=datetime.now(timezone.utc)-timedelta(minutes=5)
p=Path(sys.argv[2])
(p/'boden.csv').write_text('time_utc;stand;device_id;temp_5cm;temp_20cm;temp_50cm;battery_v;alarm_status;message_id\n'+now.isoformat()+';synthetic;synthetic-soil;12;;13;3.2;0;docker-1\n')
(p/'wetter.csv').write_text('zeit_utc;stand;station;t;h;p_hpa;l;uv;wind_ms;wind_dir_deg;gust_ms;rain_mmh;rain_mm\n'+now.isoformat()+';synthetic;synthetic-weather;-2.5;80;1013;0;0;0;359;0;0;7\n')
for f in p.iterdir(): f.chmod(0o644)
PY
export BL_WETTER_CSV="$work/wetter.csv" BL_BODEN_CSV="$work/boden.csv"
export R1_TEST_PASSWORD
R1_TEST_PASSWORD=$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')
dc(){ docker compose --env-file "$R1_COMPOSE_ENV" -f deploy/heimnetz-test/compose.yaml -f deploy/heimnetz-test/compose.umwelt.yaml "$@"; }
dc config --quiet
if [ "${R1_SKIP_BUILD:-0}" = 1 ]; then dc up -d --no-build db app proxy; else dc up -d --build db app proxy; dc build importer; fi
dc exec -T app python -m umwelt.cli migrate
dc run --rm --no-deps -T -e R1_TEST_PASSWORD importer python - <<'PY'
import os,psycopg
from argon2 import PasswordHasher
from umwelt.ingest import register_source,import_source
with psycopg.connect(os.environ['BIENEN_AUTH_DSN'],autocommit=True) as c:
 assert c.info.dbname=='bienenlogger_test'
 if c.execute('SELECT count(*) FROM bienen.stand').fetchone()[0]:
  raise RuntimeError('Expected empty owned test fixture state; existing apiaries are preserved')
 stand=c.execute("INSERT INTO bienen.stand(name) VALUES ('Synthetischer Containerstand') RETURNING id").fetchone()[0]
 for key,profile,path,kind in [('soil','boden','/sources/boden.csv','boden'),('weather','s2120','/sources/wetter.csv','wetter')]:
  device=c.execute('INSERT INTO bienen.geraet(name,art) VALUES (%s,%s)',('synthetic-'+key,kind))
  did=c.execute('SELECT id FROM bienen.geraet WHERE name=%s',('synthetic-'+key,)).fetchone()[0]
  sid=register_source(c,key=key,profile=profile,path=path,stand_id=stand,device_id=did,source_stand='synthetic',source_device='synthetic-'+key,synthetic=True,valid_from='2026-01-01T00:00:00Z',time_quality='empfang' if profile=='s2120' else 'unbekannt')
  import_source(c,sid)
 user=c.execute('INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id',('r1_container',PasswordHasher().hash(os.environ['R1_TEST_PASSWORD']))).fetchone()[0]
 c.execute('INSERT INTO bienen.sk_benutzer_stand VALUES (%s,%s,true)',(user,stand))
 print('Synthetic CSV records imported; explicit stand permission created')
PY
dc up -d --no-build importer
importer_id=$(dc ps -q importer)
docker inspect "$importer_id" --format '{{json .Mounts}}' | python3 -c 'import json,sys;m=[x for x in json.load(sys.stdin) if x["Destination"].startswith("/sources/")];assert len(m)==2 and all(not x["RW"] for x in m);print("Two explicit read-only source mounts: PASS")'
dc cp proxy:/data/caddy/pki/authorities/local/root.crt "$work/root-before.crt"
port=$(python3 - "$R1_COMPOSE_ENV" <<'PY'
from pathlib import Path
import sys
lines=Path(sys.argv[1]).read_text().splitlines()
print(next((x.split('=',1)[1] for x in lines if x.startswith('LAN_PORT=')),'8443'))
PY
)
origin="https://127.0.0.1:$port"
python3 - "$work/login.json" <<'PY'
import json,os,sys
from pathlib import Path
p=Path(sys.argv[1]);p.write_text(json.dumps({'username':'r1_container','password':os.environ['R1_TEST_PASSWORD']}));p.chmod(0o600)
PY
curl --fail --silent --show-error --cacert "$work/root-before.crt" -c "$work/cookies" -H 'Content-Type: application/json' --data-binary @"$work/login.json" "$origin/api/v1/stockkarte/session/login" -o /dev/null
curl --fail --silent --show-error --cacert "$work/root-before.crt" -b "$work/cookies" "$origin/api/v1/umwelt/staende" > "$work/stands.json"
python3 - "$work/stands.json" <<'PY'
import json,sys
assert len(json.load(open(sys.argv[1])))==1
print('Real container HTTPS/API authentication: PASS')
PY
sql_count='SELECT count(*) FROM bienen.um_messwert_aktuell'
before=$(dc exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc "$sql_count")
test "$before" -gt 3
dc restart db app proxy importer
for _ in $(seq 1 40); do
 if curl --fail --silent --cacert "$work/root-before.crt" -b "$work/cookies" "$origin/api/v1/umwelt/staende" -o "$work/after.json"; then break; fi
 sleep 1
done
python3 - "$work/after.json" <<'PY'
import json,sys
assert len(json.load(open(sys.argv[1])))==1
PY
after=$(dc exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc "$sql_count")
test "$before" = "$after"
dc cp proxy:/data/caddy/pki/authorities/local/root.crt "$work/root-after.crt"
cmp "$work/root-before.crt" "$work/root-after.crt"
printf 'Container restart: %s current values retained; same CA and authenticated session: PASS\n' "$after"
dc stop importer proxy app db
echo 'Owned test project stopped; all volumes and synthetic fixture files retained.'
