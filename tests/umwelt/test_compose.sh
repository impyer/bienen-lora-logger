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
export R1_TEST_PASSWORD R1_IMPORT_PASSWORD
R1_TEST_PASSWORD=$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')
R1_IMPORT_PASSWORD=$(python3 -c 'import secrets;print(secrets.token_hex(32))')
export BL_IMPORT_DSN="host=db port=5432 dbname=bienenlogger_test user=bl_um_container password=$R1_IMPORT_PASSWORD"
export BL_IMPORT_INTERVAL=5
export BIENEN_AUTH_DSN
BIENEN_AUTH_DSN=$(python3 - "$R1_COMPOSE_ENV" <<'PY'
from pathlib import Path
import sys
password=next(x.split('=',1)[1] for x in Path(sys.argv[1]).read_text().splitlines() if x.startswith('BL_DB_PASSWORD='))
print('host=db port=5432 dbname=bienenlogger_test user=bienenlogger password='+password)
PY
)
overlay=deploy/heimnetz-test/compose.umwelt.yaml
export R11_ARCHIVE="${R11_ARCHIVE:-0}"
if [ "$R11_ARCHIVE" = 1 ]; then
 mkdir "$work/soil" "$work/weather"
 chmod 777 "$work/soil" "$work/weather"
 cp "$work/boden.csv" "$work/soil/soil-2026-10.csv"
 cp "$work/wetter.csv" "$work/weather/weather-2026-10.csv"
 chmod 644 "$work/soil/soil-2026-10.csv" "$work/weather/weather-2026-10.csv"
 export BL_BODEN_STAGING="$work/soil" BL_WETTER_STAGING="$work/weather"
 overlay=deploy/heimnetz-test/compose.umwelt-archive.yaml
fi
extra_files=()
if [ -n "${R1_NETWORK_OVERRIDE:-}" ]; then extra_files=(-f "$R1_NETWORK_OVERRIDE"); fi
dc(){ docker compose --env-file "$R1_COMPOSE_ENV" -f deploy/heimnetz-test/compose.yaml -f "$overlay" "${extra_files[@]}" "$@"; }
dc config --quiet
if [ "${R1_SKIP_BUILD:-0}" = 1 ]; then dc up -d --no-build db app proxy; else dc up -d --build db app proxy; dc build importer; fi
dc exec -T app python -m umwelt.cli migrate
dc run --rm --no-deps -T -e R1_TEST_PASSWORD -e R1_IMPORT_PASSWORD -e R11_ARCHIVE -e BIENEN_AUTH_DSN importer python - <<'PY'
import os,psycopg
from argon2 import PasswordHasher
from umwelt.ingest import register_source,import_source
from umwelt.roles import provision_importer
with psycopg.connect(os.environ['BIENEN_AUTH_DSN'],autocommit=True) as c:
 assert c.info.dbname=='bienenlogger_test'
 if c.execute('SELECT count(*) FROM bienen.stand').fetchone()[0]:
  raise RuntimeError('Expected empty owned test fixture state; existing apiaries are preserved')
 stand=c.execute("INSERT INTO bienen.stand(name) VALUES ('Synthetischer Containerstand') RETURNING id").fetchone()[0]
 for key,profile,path,kind in [('soil','boden','/sources/boden.csv','boden'),('weather','s2120','/sources/wetter.csv','wetter')]:
  device=c.execute('INSERT INTO bienen.geraet(name,art) VALUES (%s,%s)',('synthetic-'+key,kind))
  did=c.execute('SELECT id FROM bienen.geraet WHERE name=%s',('synthetic-'+key,)).fetchone()[0]
  extra={}
  if os.environ['R11_ARCHIVE']=='1':
   path='/sources/'+('soil' if key=='soil' else 'weather')
   extra={'pattern':('soil' if key=='soil' else 'weather')+'-{YYYY}-{MM}.csv'}
  sid=register_source(c,key=key,profile=profile,path=path,stand_id=stand,device_id=did,source_stand='synthetic',source_device='synthetic-'+key,synthetic=True,valid_from='2026-01-01T00:00:00Z',time_quality='empfang' if profile=='s2120' else 'unbekannt',**extra)
  import_source(c,sid)
 user=c.execute('INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id',('r1_container',PasswordHasher().hash(os.environ['R1_TEST_PASSWORD']))).fetchone()[0]
 c.execute('INSERT INTO bienen.sk_benutzer_stand VALUES (%s,%s,true)',(user,stand))
 provision_importer(c,'bl_um_container',os.environ['R1_IMPORT_PASSWORD'])
 print('Synthetic CSV records imported; explicit stand permission created')
PY
dc up -d --no-build importer
importer_id=$(dc ps -q importer)
docker inspect "$importer_id" --format '{{json .Mounts}}' | python3 -c 'import json,sys;m=[x for x in json.load(sys.stdin) if x["Destination"].startswith("/sources/")];assert len(m)==2 and all(not x["RW"] for x in m);print("Two explicit read-only source mounts: PASS")'
dc exec -T importer python - <<'PY'
import os,psycopg
assert 'BIENEN_AUTH_DSN' not in os.environ and 'BIENEN_AUTH_SECRET' not in os.environ
with psycopg.connect(os.environ['BIENEN_IMPORT_DSN'],autocommit=True) as c:
 assert c.execute('SELECT current_user').fetchone()[0]=='bl_um_container'
 try:c.execute('SELECT * FROM bienen.sk_benutzer')
 except psycopg.errors.InsufficientPrivilege:pass
 else:raise AssertionError('Importer can read private users')
 print('Restricted runtime DSN and no app/session secret: PASS')
PY
if [ "$R11_ARCHIVE" = 1 ]; then
 dc exec -T importer python - <<'PY'
from pathlib import Path
try:Path('/sources/soil/forbidden').write_text('synthetic')
except OSError as e:assert e.errno==30,e
else:raise AssertionError('Source mount is writable')
print('Kernel rejects source writes (EROFS): PASS')
PY
 # Deliberate changes by this test's fixture writer, never by the importer.
 python3 - "$work" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])/'soil'/'soil-2026-10.csv'
p.write_text(p.read_text().replace(';12;;13;', ';22;;13;'))
(p.parent/'soil-2026-11.csv').write_text('time_utc;stand;device_id;temp_5cm;temp_20cm;temp_50cm;battery_v;alarm_status;message_id\n2026-11-01T00:00:00Z;synthetic;synthetic-soil;8;9;10;3.2;0;november\n')
(p.parent/'soil-2026-11.csv').chmod(0o644)
PY
 dc exec -T importer python -m umwelt.cli import --source-id 1
 history=$(dc exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc 'SELECT count(*) FROM bienen.um_rohdatensatz')
 test "$history" = 4
fi
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
dc exec -T db pg_dump -U bienenlogger -d bienenlogger_test -Fc --no-owner --no-privileges > "$work/before-restart.dump"
dc exec -T db createdb -U bienenlogger bienen_r11_container_restore
dc exec -T db pg_restore -U bienenlogger -d bienen_r11_container_restore --no-owner --no-privileges < "$work/before-restart.dump"
restored=$(dc exec -T db psql -U bienenlogger -d bienen_r11_container_restore -Atqc "$sql_count")
test "$before" = "$restored"
state_sql="SELECT md5(string_agg(row_to_json(t)::text,',' ORDER BY row_to_json(t)::text)) FROM (SELECT 'raw' AS kind,to_jsonb(r) AS data FROM bienen.um_rohdatensatz r UNION ALL SELECT 'event',to_jsonb(e) FROM bienen.um_ereignis_revision e UNION ALL SELECT 'revision',to_jsonb(m) FROM bienen.um_messwert_revision m UNION ALL SELECT 'checkpoint',to_jsonb(c) FROM bienen.um_archiv_datei c UNION ALL SELECT 'user',to_jsonb(u) FROM bienen.sk_benutzer u) t"
state_before=$(dc exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc "$state_sql")
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
state_after=$(dc exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc "$state_sql")
test "$state_before" = "$state_after"
dc cp proxy:/data/caddy/pki/authorities/local/root.crt "$work/root-after.crt"
cmp "$work/root-before.crt" "$work/root-after.crt"
printf 'Container restart: %s current values retained; same CA and authenticated session: PASS\n' "$after"
importer_started=$(docker inspect "$importer_id" --format '{{.State.StartedAt}}')
dc restart db
# A genuinely new record must arrive through the periodic restricted watcher
# after restart, without an explicit CLI import or a simulated API response.
python3 - "$work" "$R11_ARCHIVE" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])/('soil/soil-2026-11.csv' if sys.argv[2]=='1' else 'boden.csv')
with p.open('a') as f:f.write('2026-11-02T00:00:00Z;synthetic;synthetic-soil;33;34;35;3.2;0;after-restart\n')
PY
expected_after=$((after+5))
for _ in $(seq 1 30); do
 observed=$(dc exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc "$sql_count")
 if [ "$observed" = "$expected_after" ]; then break; fi
 sleep 1
done
test "$observed" = "$expected_after"
test "$importer_started" = "$(docker inspect "$importer_id" --format '{{.State.StartedAt}}')"
echo 'Periodic import resumes after full restart: PASS'
dc stop importer proxy app db
echo 'Owned test project stopped; all volumes and synthetic fixture files retained.'
