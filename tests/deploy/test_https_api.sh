#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Adversariale HTTPS-/Session-Prüfung MIT Docker-Proxy, ohne lokale BEEP-Daten.
set -euo pipefail
cd "$(dirname "$0")/../.."
cd deploy/heimnetz-test
compose() { docker compose --env-file .env -f compose.yaml "$@"; }
base="https://127.0.0.1:8443"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
# Benutzer in eigener Wegwerf-Testdatenbank explizit für diesen Test anlegen.
compose exec -T app python - <<'PY'
import os
import psycopg
from argon2 import PasswordHasher
with psycopg.connect(os.environ['BIENEN_AUTH_DSN']) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        assert cur.fetchone()[0]=='bienenlogger_test'
        cur.execute("INSERT INTO bienen.sk_benutzer (benutzername,passwort_hash) VALUES ('ci_audit',%s) RETURNING id",
                    (PasswordHasher().hash('CI-only-long-password-77777'),))
        uid=cur.fetchone()[0]
        cur.execute("SELECT id FROM bienen.volk WHERE name='Testvolk A'")
        volk=cur.fetchone()[0]
        cur.execute("""INSERT INTO bienen.sk_benutzer_volk (benutzer_id,volk_id,darf_lesen,darf_schreiben)
                       VALUES (%s,%s,true,true)""",(uid,volk))
        print('POST-API test user created for synthetic colony',volk)
PY
code=$(curl -ksS --max-time 10 -o "$tmp/unauth" -w '%{http_code}' "$base/api/v1/stockkarte/voelker")
test "$code" = 401
code=$(curl -ksS --max-time 10 -o "$tmp/login" -D "$tmp/login-headers" \
 -c "$tmp/cookies" -w '%{http_code}' -H 'Content-Type: application/json' \
 -d '{"username":"ci_audit","password":"CI-only-long-password-77777"}' \
 "$base/api/v1/stockkarte/session/login")
test "$code" = 200
grep -iq 'httponly' "$tmp/login-headers"
grep -iq 'secure' "$tmp/login-headers"
grep -iq 'samesite=strict' "$tmp/login-headers"
csrf=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["csrf_token"])' "$tmp/login")
code=$(curl -ksS --max-time 10 -o "$tmp/colonies" -w '%{http_code}' \
 -b "$tmp/cookies" -H 'X-Forwarded-For: 8.8.8.8' \
 "$base/api/v1/stockkarte/voelker")
test "$code" = 200
colony=$(python3 -c 'import json,sys; c=json.load(open(sys.argv[1]));assert len(c)==1 and c[0]["can_write"];print(c[0]["id"])' "$tmp/colonies")
route="$base/api/v1/stockkarte/voelker/$colony/durchsichten"
payload='{"event_date":"2026-10-17","accuracy":"nur_datum","values":{"bl:frames":2,"bl:queen_seen":false},"note":"HTTPS audit fixture","reason":"HTTPS-Proxydurchsicht"}'
code=$(curl -ksS --max-time 10 -o "$tmp/wrong-csrf" -w '%{http_code}' \
 -b "$tmp/cookies" -H 'Content-Type: application/json' -H 'X-CSRF-Token: wrong' \
 -H 'Origin: https://127.0.0.1:8443' -d "$payload" "$route")
test "$code" = 403
code=$(curl -ksS --max-time 10 -o "$tmp/wrong-origin" -w '%{http_code}' \
 -b "$tmp/cookies" -H 'Content-Type: application/json' -H "X-CSRF-Token: $csrf" \
 -H 'Origin: https://evil.invalid' -d "$payload" "$route")
test "$code" = 403
code=$(curl -ksS --max-time 10 -o "$tmp/created" -w '%{http_code}' \
 -b "$tmp/cookies" -H 'Content-Type: application/json' -H "X-CSRF-Token: $csrf" \
 -H 'Origin: https://127.0.0.1:8443' -H 'X-Forwarded-For: 8.8.8.8' \
 -d "$payload" "$route")
if [ "$code" != 201 ]; then
 echo "HTTPS API create expected 201, got $code" >&2
 cat "$tmp/created" >&2
 exit 1
fi
id=$(python3 -c 'import json,sys; c=json.load(open(sys.argv[1]));assert c["revision"]==1;print(c["id"])' "$tmp/created")
rev="$base/api/v1/stockkarte/durchsichten/$id/revisionen"
corrected='{"event_date":"2026-10-17","accuracy":"nur_datum","expected_revision":1,"values":{"bl:frames":3,"bl:queen_seen":false},"note":"HTTPS correction fixture","reason":"Audit-Revisionskorrektur"}'
code=$(curl -ksS --max-time 10 -o "$tmp/corrected" -w '%{http_code}' \
 -b "$tmp/cookies" -H 'Content-Type: application/json' -H "X-CSRF-Token: $csrf" \
 -H 'Origin: https://127.0.0.1:8443' -d "$corrected" "$rev")
test "$code" = 201
code=$(curl -ksS --max-time 10 -o "$tmp/stale" -w '%{http_code}' \
 -b "$tmp/cookies" -H 'Content-Type: application/json' -H "X-CSRF-Token: $csrf" \
 -H 'Origin: https://127.0.0.1:8443' -d "$corrected" "$rev")
test "$code" = 409
code=$(curl -ksS --max-time 10 -o "$tmp/revisions" -w '%{http_code}' \
 -b "$tmp/cookies" "$rev")
test "$code" = 200
python3 - "$tmp/revisions" <<'PY'
import json,sys
revisions=json.load(open(sys.argv[1]))
assert len(revisions)==2
assert revisions[0]['values']['bl:frames']==2
assert revisions[1]['values']['bl:frames']==3
assert revisions[0]['values']['bl:queen_seen'] is False
assert revisions[0]['event_time'] is None
PY
code=$(curl -ksS --max-time 10 -o "$tmp/logout" -w '%{http_code}' \
 -b "$tmp/cookies" -H "X-CSRF-Token: $csrf" -H 'Origin: https://127.0.0.1:8443' \
 -X POST "$base/api/v1/stockkarte/session/logout")
test "$code" = 200
code=$(curl -ksS --max-time 10 -o "$tmp/after" -w '%{http_code}' \
 -b "$tmp/cookies" "$route")
test "$code" = 401
echo 'HTTPS reverse-proxy E2E: login / forged XFF / origin / CSRF / create / revision / concurrency / logout PASS'
