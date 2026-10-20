#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
# Oberfläche der Plattform im Browser: Lese-API (uvicorn) gegen die Testdatenbank, erst leer, dann mit dem
# synthetischen Oktober 2026; dazwischen die Verwaltung vom leeren Start aus. Löscht das Schema "bienen" der Testdatenbank.
# Braucht: BIENEN_TEST_DSN, python3 mit server/plattform/requirements.txt, node mit playwright (Chromium), curl.
set -euo pipefail
HIER="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HIER/../.." && pwd)"
W="$(mktemp -d)"
PORT=$((20000 + RANDOM % 20000))
PW="ui-test-passwort-1234"
SPID=""
aufraeumen() {
  local rc=$?
  if [ -n "$SPID" ]; then kill "$SPID" 2>/dev/null || true; fi
  if [ "$rc" -ne 0 ] && [ -f "$W/server.log" ]; then echo "--- Server-Log ---"; tail -40 "$W/server.log"; fi
  rm -rf "$W"
}
trap aufraeumen EXIT
: "${BIENEN_TEST_DSN:?BIENEN_TEST_DSN fehlt}"

cd "$REPO/server/plattform"
python3 - "$W/plattform_config.toml" "$PW" <<'PY'
import os, secrets, sys
sys.path.insert(0, ".")
from api.anmeldung import passwort_hash
with open(sys.argv[1], "w", encoding="utf-8") as f:
    f.write(f'dsn = "{os.environ["BIENEN_TEST_DSN"]}"\npasswort_hash = "{passwort_hash(sys.argv[2])}"\n'
            f'sitzungsschluessel = "{secrets.token_urlsafe(32)}"\ncookie_sicher = false\n')
PY
python3 -c 'import os, pathlib, psycopg
c = psycopg.connect(os.environ["BIENEN_TEST_DSN"], autocommit=True)
c.execute(pathlib.Path("../datenbank/schema.sql").read_text(encoding="utf-8"))'

BIENEN_PLATTFORM_CONFIG="$W/plattform_config.toml" python3 -m uvicorn --factory api.app:erstellen \
  --host 127.0.0.1 --port "$PORT" > "$W/server.log" 2>&1 &
SPID=$!
for _ in $(seq 1 50); do curl -fs -o /dev/null "http://127.0.0.1:$PORT/api/gesundheit" && break; sleep 0.2; done

echo "== leere Datenbank"
node "$HIER/test_oberflaeche.mjs" "http://127.0.0.1:$PORT" "$PW" leer
echo "== Verwaltung: leerer Start, alles über die Oberfläche anlegen"
node "$HIER/test_oberflaeche.mjs" "http://127.0.0.1:$PORT" "$PW" verwaltung
echo "== synthetischer Oktober 2026"
python3 synthetisch.py --verzeichnis "$W/syn" > "$W/syn.log"
head -5 "$W/syn.log"
node "$HIER/test_oberflaeche.mjs" "http://127.0.0.1:$PORT" "$PW" voll
