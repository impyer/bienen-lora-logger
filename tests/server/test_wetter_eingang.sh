#!/bin/bash
# Ende-zu-Ende-Test des Wetter-Eingangs (server/wetter) mit PHP-Testserver und echtem S2120-Formatter.
# Braucht: php, node, curl.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
set -u
HIER="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HIER/../.." && pwd)"
W="$(mktemp -d)"
PORT=$((20000 + RANDOM % 20000))
TOKEN="test-token-wetter-1234567890"
FEHLER=0; ANZ=0

aufraeumen() { [ -n "${SPID:-}" ] && kill "$SPID" 2>/dev/null; if grep -qiE "PHP (Fatal|Parse|Warning|Notice|Deprecated)" "$W/server.log" 2>/dev/null; then echo "--- PHP-Meldungen ---"; grep -iE "PHP (Fatal|Parse|Warning|Notice|Deprecated)" "$W/server.log" | head -20; FEHLER=$((FEHLER+1)); fi; rm -rf "$W"; }
trap aufraeumen EXIT
ok()   { ANZ=$((ANZ+1)); echo "ok   - $1"; }
nok()  { ANZ=$((ANZ+1)); FEHLER=$((FEHLER+1)); echo "FEHL - $1"; [ -n "${2:-}" ] && echo "       $2"; }
pruefe() { if [ "$2" = "$3" ]; then ok "$1"; else nok "$1" "erwartet: [$3]  ist: [$2]"; fi; }
enthaelt() { case "$2" in *"$3"*) ok "$1";; *) nok "$1" "erwartet enthalten: [$3]  ist: [$2]";; esac; }

mkdir -p "$W/www"
cp -r "$REPO/server/lora" "$W/www/lora"
cp -r "$REPO/server/wetter" "$W/www/wetter"
cat > "$W/www/wetter/wetter_config.php" <<EOF
<?php
return array(
  'token' => '$TOKEN',
  'staende' => array('hauptstand' => array('name' => 'Hauptstand am Haus', 'logger' => array('beelogger1')),
                     'wiese' => array('name' => 'Wiese')),
  'stationen' => array('wetterstation-01' => array('stand' => 'hauptstand'),
                       'wetterstation-02' => array('stand' => 'wiese'),
                       'wetterstation-kaputt' => array('stand' => 'gibtsnicht')),
  'daten_verzeichnis' => '$W/daten',
  'log_verzeichnis' => '$W/log',
  'test_pause_ms' => 300,   // Zeitfenster zwischen Doppelprüfung und Schreiben aufweiten (Paralleltest)
);
EOF
# mehrere Worker, damit die Sperre je Station bei gleichzeitigen Webhooks wirklich geprüft wird
PHP_CLI_SERVER_WORKERS=4 php -S 127.0.0.1:$PORT -t "$W/www" > "$W/server.log" 2>&1 &
SPID=$!
for i in $(seq 1 50); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.1; done

# TTN-Uplink mit dem echten Formatter bauen: nachricht <geraet> <hex|-> <received_at> <f_cnt>
nachricht() {
  node -e '
    const fs = require("fs"), vm = require("vm");
    const [datei, geraet, hex, zeit, fcnt] = process.argv.slice(1);
    const ctx = {}; vm.createContext(ctx); vm.runInContext(fs.readFileSync(datei, "utf8"), ctx);
    const up = { f_cnt: Number(fcnt), received_at: zeit,
      rx_metadata: [{ gateway_ids: { gateway_id: "gw" }, rssi: -66, snr: 14.75 }],
      settings: { data_rate: { lora: { bandwidth: 125000, spreading_factor: 7, coding_rate: "4/5" } } } };
    if (hex !== "-") {
      const bytes = Array.from(Buffer.from(hex, "hex"));
      up.f_port = 3; up.frm_payload = Buffer.from(bytes).toString("base64");
      up.decoded_payload = ctx.decodeUplink({ fPort: 3, bytes }).data;
    }
    process.stdout.write(JSON.stringify({ end_device_ids: { device_id: geraet, dev_eui: "2CF7F1C08200034F" }, received_at: zeit, uplink_message: up }));
  ' "$REPO/formatter/s2120_beep_formatter.js" "$@"
}
senden() {  # $1 = JSON, $2 = Token (Vorgabe: richtig) → "Code Text"
  curl -s -w ' %{http_code}' -X POST -H 'Content-Type: application/json' -H "X-Bienen-Token: ${2:-$TOKEN}" \
       --data-binary "$1" "http://127.0.0.1:$PORT/wetter/wetter_eingang.php" | tr '\n' ' ' | tr -s ' '
}
U="http://127.0.0.1:$PORT/wetter/wetter_eingang.php"
CSV="$W/daten/hauptstand/wetterstation-01_2026-10.csv"
HEX1=4A006E58000000000000004B00480000000026594C000A00000FE0

enthaelt "GET wird abgelehnt" "$(curl -s -w ' %{http_code}' "$U" | tr '\n' ' ' | tr -s ' ')" "nur POST 405"
enthaelt "falsches Token" "$(senden '{}' falsch-falsch-falsch-123)" "401"
enthaelt "kein JSON" "$(senden 'kein json')" "400"
enthaelt "Join-Meldung ohne uplink_message" "$(senden '{"end_device_ids":{"device_id":"wetterstation-01"},"join_accept":{}}')" "ignoriert: keine Uplink-Nachricht"
enthaelt "unbekannte Station" "$(senden "$(nachricht wetterstation-09 $HEX1 2026-10-10T03:21:48.4Z 7)")" "ignoriert: Station nicht in wetter_config.php"
enthaelt "Station mit falschem Stand" "$(senden "$(nachricht wetterstation-kaputt $HEX1 2026-10-10T03:21:48.4Z 7)")" " 500"
R=$(senden "$(nachricht wetterstation-01 - 2026-10-10T03:17:19.8Z 2)")
enthaelt "leerer Uplink nach Join wird mit 200 ignoriert" "$R" "ohne Nutzdaten 200"
pruefe "leerer Uplink legt keine Datei an" "$( [ -e "$CSV" ] && echo ja || echo nein)" "nein"

R=$(senden "$(nachricht wetterstation-01 $HEX1 2026-10-10T03:21:48.476207824Z 7)")
enthaelt "gültiger Uplink gespeichert" "$R" "gespeichert: hauptstand/wetterstation-01_2026-10.csv 200"
pruefe "Datei: Kopf + 1 Zeile" "$(wc -l < "$CSV" | tr -d ' ')" "2"
pruefe "Kopfzeile" "$(head -1 "$CSV")" "zeit_utc;unix;ortszeit;stand;station;t;h;p_hpa;l;uv;wind_ms;wind_dir_deg;gust_ms;rain_mmh;rain_mm;battery_pct;interval_min;f_cnt;f_port;rssi;snr;gateways;sf;payload_hex;warnungen"
pruefe "Datenzeile" "$(sed -n 2p "$CSV")" "2026-10-10T03:21:48Z;1791602508;2026/10/10_05:21:48;hauptstand;wetterstation-01;11;88;981.7;0;0;0;72;1;0;4.064;;;7;3;-66;14.75;1;7;$HEX1;"

enthaelt "dieselbe Nachricht nochmal → doppelt" "$(senden "$(nachricht wetterstation-01 $HEX1 2026-10-10T03:21:48.476207824Z 7)")" "doppelt"
pruefe "doppelte Nachricht nicht gespeichert" "$(wc -l < "$CSV" | tr -d ' ')" "2"

R=$(senden "$(nachricht wetterstation-01 046401010201000505A04A006E59000000000000004B01030000000026594C000000000FE0 2026-10-10T03:26:48Z 8)")
enthaelt "Uplink mit Batterieblock gespeichert" "$R" "gespeichert"
pruefe "Batterie und Intervall in der Zeile" "$(sed -n 3p "$CSV" | cut -d';' -f16,17)" "100;5"

enthaelt "zweiter Stand" "$(senden "$(nachricht wetterstation-02 $HEX1 2026-10-31T23:59:59Z 1)")" "gespeichert: wiese/wetterstation-02_2026-10.csv"
pruefe "Monat nach UTC (Ortszeit schon 01.11.)" "$( [ -f "$W/daten/wiese/wetterstation-02_2026-10.csv" ] && echo ja || echo nein)" "ja"

pruefe "staende.json: Stationen je Stand" "$(php -r '$s=json_decode(file_get_contents($argv[1]),true); echo implode(",",$s["hauptstand"]["stationen"])."|".implode(",",$s["wiese"]["stationen"])."|".$s["hauptstand"]["name"];' "$W/daten/staende.json")" "wetterstation-01|wetterstation-02|Hauptstand am Haus"
pruefe "staende.json enthält kein Token" "$(grep -c "$TOKEN" "$W/daten/staende.json")" "0"
pruefe "Datenverzeichnis geschützt (.htaccess)" "$(cat "$W/daten/.htaccess" 2>/dev/null)" "Require all denied"
pruefe "Protokoll geschrieben" "$(ls "$W/log"/*.jsonl 2>/dev/null | wc -l | tr -d ' ')" "1"

# Gleichzeitige Zustellung derselben Nachricht: genau eine Zeile (Sperre je Station)
M="$(nachricht wetterstation-01 $HEX1 2026-10-10T03:31:48Z 9)"
PIDS=""; for i in 1 2 3 4 5; do senden "$M" > "$W/par_$i.txt" & PIDS="$PIDS $!"; done; wait $PIDS
pruefe "parallel: genau einmal gespeichert" "$(cat "$W"/par_*.txt | grep -c gespeichert)" "1"
pruefe "parallel: Zeilenzahl" "$(wc -l < "$CSV" | tr -d ' ')" "4"

# PLT26-02: Rohprotokoll (R-1 Prüfsumme je Uplink, R-2 Fehler sichtbar, Messwert bleibt erhalten)
U=$(cat "$W"/log/*.jsonl | grep -c '"art":"uplink"')
pruefe "R-1: jede Rohzeile mit Prüfsumme des Eingangs" "$(cat "$W"/log/*.jsonl | grep '"art":"uplink"' | grep -c '"roh_sha256":"[0-9a-f]\{64\}"')" "$U"
M=$(ls "$W/log"/*.jsonl | tail -n 1); mv "$M" "$W/log_sicher.jsonl"; mkdir "$M"
R=$(senden "$(nachricht wetterstation-01 $HEX1 2026-10-10T03:36:48Z 10)")
enthaelt "R-2: Rohprotokoll gescheitert → Warnung in der Antwort" "$R" "WARNUNG: Rohprotokoll nicht geschrieben"
enthaelt "R-2: Messwert trotzdem gespeichert" "$R" "gespeichert"
pruefe "R-2: Zeile in der Wetter-CSV" "$(wc -l < "$CSV" | tr -d ' ')" "5"
grep -q "Rohprotokoll nicht geschrieben" "$W/server.log" && ok "R-2: Eintrag im PHP-Fehlerprotokoll" || nok "R-2: Eintrag im PHP-Fehlerprotokoll"
rmdir "$M"; mv "$W/log_sicher.jsonl" "$M"

kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; SPID=
echo "$( [ $FEHLER -eq 0 ] && echo OK || echo FEHLER ): Wetter-Eingang $((ANZ-FEHLER)) von $ANZ Prüfungen bestanden"
[ $FEHLER -eq 0 ]
