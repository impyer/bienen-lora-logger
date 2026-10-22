#!/bin/bash
# Ende-zu-Ende-Test des Umwelt-Eingangs (server/umwelt) mit PHP-Testserver, echtem S2120-Formatter und einem
# beliebigen weiteren Gerät (Bodensonde). Braucht: php, node, curl.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
set -u
HIER="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HIER/../.." && pwd)"
W="$(mktemp -d)"
PORT=$((20000 + RANDOM % 20000))
TOKEN="test-token-umwelt-1234567890"
FEHLER=0; ANZ=0

aufraeumen() { [ -n "${SPID:-}" ] && kill "$SPID" 2>/dev/null; if grep -qiE "PHP (Fatal|Parse|Warning|Notice|Deprecated)" "$W/server.log" 2>/dev/null; then echo "--- PHP-Meldungen ---"; grep -iE "PHP (Fatal|Parse|Warning|Notice|Deprecated)" "$W/server.log" | head -20; FEHLER=$((FEHLER+1)); fi; rm -rf "$W"; }
trap aufraeumen EXIT
ok()   { ANZ=$((ANZ+1)); echo "ok   - $1"; }
nok()  { ANZ=$((ANZ+1)); FEHLER=$((FEHLER+1)); echo "FEHL - $1"; [ -n "${2:-}" ] && echo "       $2"; }
pruefe() { if [ "$2" = "$3" ]; then ok "$1"; else nok "$1" "erwartet: [$3]  ist: [$2]"; fi; }
enthaelt() { case "$2" in *"$3"*) ok "$1";; *) nok "$1" "erwartet enthalten: [$3]  ist: [$2]";; esac; }

mkdir -p "$W/www"
cp -r "$REPO/server/eingang" "$W/www/eingang"
cp -r "$REPO/server/umwelt" "$W/www/umwelt"
cat > "$W/www/umwelt/umwelt_config.php" <<KONF
<?php
return array('token' => '$TOKEN', 'log_verzeichnis' => '$W/log');
KONF
PHP_CLI_SERVER_WORKERS=4 php -S 127.0.0.1:$PORT -t "$W/www" > "$W/server.log" 2>&1 &
SPID=$!
for i in $(seq 1 50); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.1; done

# TTN-Uplink mit dem echten S2120-Formatter: s2120 <geraet> <hex|-> <received_at> <f_cnt>
s2120() {
  node -e '
    const fs = require("fs"), vm = require("vm");
    const [datei, geraet, hex, zeit, fcnt] = process.argv.slice(1);
    const ctx = {}; vm.createContext(ctx); vm.runInContext(fs.readFileSync(datei, "utf8"), ctx);
    const up = { f_cnt: Number(fcnt), received_at: zeit, rx_metadata: [{ gateway_ids: { gateway_id: "gw" }, rssi: -66, snr: 14.75 }] };
    if (hex !== "-") {
      const bytes = Array.from(Buffer.from(hex, "hex"));
      up.f_port = 3; up.frm_payload = Buffer.from(bytes).toString("base64");
      up.decoded_payload = ctx.decodeUplink({ fPort: 3, bytes }).data;
    }
    process.stdout.write(JSON.stringify({ end_device_ids: { device_id: geraet }, received_at: zeit, uplink_message: up }));
  ' "$REPO/formatter/s2120_beep_formatter.js" "$@"
}
# beliebiges Gerät mit fertigem decoded_payload (Feldnamen sind dem Eingang egal): geraet <name> <received_at> <JSON>
geraet() {
  printf '{"end_device_ids":{"device_id":"%s"},"received_at":"%s","uplink_message":{"f_port":2,"f_cnt":1,"frm_payload":"AQI=","decoded_payload":%s}}' "$1" "$2" "$3"
}
U="http://127.0.0.1:$PORT/umwelt/umwelt_eingang.php"
senden() { curl -s -w ' %{http_code}' -X POST -H 'Content-Type: application/json' -H "X-Bienen-Token: ${2:-$TOKEN}" --data-binary "$1" "$U" | tr '\n' ' ' | tr -s ' '; }
uplinks() { cat "$W"/log/*.jsonl 2>/dev/null | grep '"art":"uplink"' | grep -c "$1"; }
HEX1=4A006E58000000000000004B00480000000026594C000A00000FE0

enthaelt "GET wird abgelehnt" "$(curl -s -w ' %{http_code}' "$U" | tr '\n' ' ' | tr -s ' ')" "nur POST 405"
enthaelt "falsches Token" "$(senden '{}' falsch-falsch-falsch-123)" "401"
enthaelt "kein JSON" "$(senden 'kein json')" "400"
enthaelt "Join-Meldung ohne uplink_message" "$(senden '{"end_device_ids":{"device_id":"wetterstation-01"},"join_accept":{}}')" "ignoriert: keine Uplink-Nachricht 200"
pruefe "Join-Meldung nicht im Rohprotokoll" "$(uplinks wetterstation-01)" "0"

enthaelt "leerer Uplink nach Join → 200 ignoriert" "$(senden "$(s2120 wetterstation-01 - 2026-10-10T03:17:19.8Z 2)")" "ignoriert: Uplink ohne Nutzdaten 200"
pruefe "leerer Uplink steht trotzdem im Rohprotokoll (R-1)" "$(uplinks wetterstation-01)" "1"

enthaelt "S2120: protokolliert" "$(senden "$(s2120 wetterstation-01 $HEX1 2026-10-10T03:21:48.476207824Z 7)")" "protokolliert: wetterstation-01 200"
pruefe "S2120: Rohzeile mit Prüfsumme und decoded_payload" "$(cat "$W"/log/*.jsonl | grep '"f_cnt":7' | grep -c '"roh_sha256":"[0-9a-f]\{64\}".*"decoded_payload":{')" "1"
enthaelt "Herkunftsfeld geraet (wie Bienen-Eingang)" "$(cat "$W"/log/*.jsonl | grep '"f_cnt":7')" '"geraet":"wetterstation-01","art":"uplink"'

# Ein Gerät, das der Eingang nicht kennt (z. B. Bodensonde), braucht keine Einrichtung auf dem Server
enthaelt "Bodensonde ohne Konfiguration: protokolliert" "$(senden "$(geraet lsn50-boden 2026-10-14T08:00:00Z '{"TempC1":12.5,"Temp_Red":"10.25","BatV":3.6}')")" "protokolliert: lsn50-boden 200"
pruefe "Bodensonde im Rohprotokoll" "$(uplinks lsn50-boden)" "1"
enthaelt "nur Texte → 200 ignoriert" "$(senden "$(geraet lsn50-boden 2026-10-14T08:20:00Z '{"modell":"LSN50"}')")" "ignoriert: Uplink keine Messwerte 200"
enthaelt "ohne decoded_payload → 200 ignoriert" "$(senden '{"end_device_ids":{"device_id":"lsn50-boden"},"received_at":"2026-10-14T08:40:00Z","uplink_message":{"frm_payload":"AQI="}}')" "kein decoded_payload"
enthaelt "Gerätename ungültig → 200 ignoriert" "$(senden "$(geraet ../boese 2026-10-14T08:00:00Z '{"t":1}')")" "ignoriert: Gerätename"
enthaelt "ohne received_at → 400" "$(senden '{"end_device_ids":{"device_id":"lsn50-boden"},"uplink_message":{"frm_payload":"AQI=","decoded_payload":{"t":1}}}')" "400"

# Doppelte und gleichzeitige Zustellung: alle stehen im Rohprotokoll, die Kennung ist gleich (der Importer verwirft Doppelte)
M="$(s2120 wetterstation-01 $HEX1 2026-10-10T03:31:48Z 9)"
PIDS=""; for i in 1 2 3 4 5; do senden "$M" > "$W/par_$i.txt" & PIDS="$PIDS $!"; done; wait $PIDS
pruefe "parallel: alle 5 beantwortet" "$(grep -l 'protokolliert' "$W"/par_*.txt | wc -l | tr -d ' ')" "5"
pruefe "parallel: 5 vollständige Rohzeilen, eine Kennung" "$(cat "$W"/log/*.jsonl | grep '"f_cnt":9' | php -r '$k=[]; while(($z=fgets(STDIN))!==false){$e=json_decode($z,true); if(!is_array($e)) exit("kaputt"); $k[$e["id"]]=1;} echo count($k);')" "1"
pruefe "parallel: Zeilenzahl" "$(cat "$W"/log/*.jsonl | grep -c '"f_cnt":9')" "5"
pruefe "Protokoll geschützt (.htaccess)" "$(cat "$W/log/.htaccess" 2>/dev/null)" "Require all denied"

# R-2: Rohprotokoll scheitert → einziger Speicher fehlt → 500 mit Warnung, sichtbar in TTN und im PHP-Fehlerprotokoll
M=$(ls "$W/log"/*.jsonl | tail -n 1); mv "$M" "$W/log_sicher.jsonl"; mkdir "$M"
R=$(senden "$(s2120 wetterstation-01 $HEX1 2026-10-10T03:36:48Z 10)")
enthaelt "R-2: Antwort 500" "$R" "nicht gespeichert | WARNUNG: Rohprotokoll nicht geschrieben 500"
grep -q "umwelt_eingang: Rohprotokoll nicht geschrieben" "$W/server.log" && ok "R-2: Eintrag im PHP-Fehlerprotokoll" || nok "R-2: Eintrag im PHP-Fehlerprotokoll"
R=$(senden "$(s2120 wetterstation-01 - 2026-10-10T03:37:00Z 11)")
enthaelt "R-2: leerer Uplink bleibt 200 (TTN schaltet nicht ab)" "$R" " 200"
rmdir "$M"; mv "$W/log_sicher.jsonl" "$M"

kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; SPID=
echo "$( [ $FEHLER -eq 0 ] && echo OK || echo FEHLER ): Umwelt-Eingang $((ANZ-FEHLER)) von $ANZ Prüfungen bestanden"
[ $FEHLER -eq 0 ]
