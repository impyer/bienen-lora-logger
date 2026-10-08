#!/bin/bash
# Ende-zu-Ende-Test des LoRa-Eingangs:
# echte beelogger-Skripte M.40 (Original-ZIP) + server/lora + echter TTN-Formatter + PHP-Testserver.
# Braucht: php (mit curl), node, unzip, curl. Der Testserver läuft mit 4 Arbeitsprozessen, weil der Eingang
# beelogger_log.php über HTTP beim selben Server aufruft.
# Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
set -u
HIER="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HIER/../.." && pwd)"
W="$(mktemp -d)"
PORT=$((20000 + RANDOM % 20000))
TOKEN="test-token-1234567890abcdef"
FEHLER=0; ANZ=0

aufraeumen() { [ -n "${SPID:-}" ] && kill "$SPID" 2>/dev/null; if grep -qiE "PHP (Fatal|Parse|Warning)" "$W/server.log" 2>/dev/null; then echo "--- PHP-Meldungen im Server-Log ---"; grep -iE "PHP (Fatal|Parse|Warning)" "$W/server.log" | sort | uniq -c | head -20; fi; rm -rf "$W"; }
trap aufraeumen EXIT

ok()   { ANZ=$((ANZ+1)); echo "ok   - $1"; }
nok()  { ANZ=$((ANZ+1)); FEHLER=$((FEHLER+1)); echo "FEHL - $1"; [ -n "${2:-}" ] && echo "       $2"; }
pruefe() { if [ "$2" = "$3" ]; then ok "$1"; else nok "$1" "erwartet: [$3]  ist: [$2]"; fi; }
enthaelt() { case "$2" in *"$3"*) ok "$1";; *) nok "$1" "erwartet enthalten: [$3]  ist: [$2]";; esac; }

# --- Testserver aufbauen ---
# VARIANTE=eigen (Vorgabe): eigene Server-Fassung (UTC); VARIANTE=original: unverändertes beelogger M.40
VARIANTE="${VARIANTE:-eigen}"
if [ "$VARIANTE" = "original" ]; then
  unzip -q "$REPO/server/M40_261004_ServerSkripte.zip" -d "$W/www"
else
  mkdir -p "$W/www" && unzip -q "$REPO/server/M40_261004_ServerSkripte.zip" "beelogger_icons/*" -d "$W/www"   # Bilder nur im ZIP
  cp -r "$REPO/server/beelogger_eigen/." "$W/www/"
fi
echo "Variante: $VARIANTE"
cp -r "$REPO/server/lora" "$W/www/lora"
cat > "$W/router.php" <<'EOF'
<?php
// Testserver: HTTPS vortäuschen (beelogger_show.php verlangt es) und Skript im eigenen Verzeichnis starten
$p = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$f = $_SERVER['DOCUMENT_ROOT'] . $p;
if (!preg_match('/\.php$/', $p) || !is_file($f)) return false;
$_SERVER['HTTPS'] = 'on';
$_SERVER['SCRIPT_FILENAME'] = $f;
chdir(dirname($f));
require $f;
EOF
cat > "$W/www/lora/lora_config.php" <<EOF
<?php
return array(
  'token' => '$TOKEN',
  'basis_url' => 'http://127.0.0.1:$PORT',
  'geraete' => array('beelogger-01' => array('verzeichnis' => 'beelogger1')),
  'log_verzeichnis' => '$W/log',
);
EOF
PHP_CLI_SERVER_WORKERS=4 php -S 127.0.0.1:$PORT -t "$W/www" "$W/router.php" > "$W/server.log" 2>&1 &
SPID=$!
for i in $(seq 1 50); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.1; done
# beelogger1 einrichten wie beim ersten Aufruf im Browser (legt beelogger_ini.php mit Log-Passwort "Log" an)
curl -s -o /dev/null "http://127.0.0.1:$PORT/beelogger1/beelogger_show.php"
[ -f "$W/www/beelogger1/beelogger_ini.php" ] && ok "beelogger1 eingerichtet" || nok "beelogger1 eingerichtet"

senden() {  # $1 = JSON-Parameter für ttn_nachricht.js, $2 = Token (optional)
  node "$HIER/ttn_nachricht.js" "$1" > "$W/msg.json"
  curl -s -w ' [%{http_code}]' -X POST -H "Content-Type: application/json" -H "X-Bienen-Token: ${2:-$TOKEN}" \
    --data-binary @"$W/msg.json" "http://127.0.0.1:$PORT/lora/lora_eingang.php"
}
letzte() { tail -n 1 "$W/www/beelogger1/week.csv" 2>/dev/null | tr -d '\r'; }
zusatz() { tail -n 1 "$W/www/beelogger1/lora_zusatz.csv" 2>/dev/null; }

# --- 1. Funkformat v2 mit gültiger Gerätezeit ---
A=$(senden '{"geraet":"beelogger-01","fport":2,"f_cnt":10,"empfang":"2026-10-08T12:00:07.5Z","rssi":[-95,-71],
  "werte":{"tOut":12.34,"hOut":67,"p":1013.2,"tIn1":34.56,"tIn2":18.07,"g1":45.678,"vBatt":3.912,"vSolar":5.1,
  "fftHz":247.3,"fftDb":-23.5,"fftSum":-18,"baender":[-40,-22.5],"service":0,"status":1,"reset":1,"zeit":1791460800,
  "fw":261008,"tCpu":21.5}}')
enthaelt "v2: Antwort gespeichert" "$A" "gespeichert 2026/10/08_14:00:00"
enthaelt "v2: HTTP 200" "$A" "[200]"
pruefe "v2: Zeile in week.csv (Ortszeit MESZ, Gerätezeit, Aux2/Aux3 = FFT)" "$(letzte)" \
  "2026/10/08 14:00:00,34.6,12.3,,67.0,,45.68,3.91,5.10,0,45.68,1013.2,247.3,-23.5,,,1791460800"
Z=$(zusatz)
enthaelt "v2: Zusatz Zeitquelle Gerät" "$Z" "2026-10-08T12:00:00Z,1791460800,geraet,beelogger-01,10,2"
enthaelt "v2: Zusatz bestes Gateway (RSSI -71, SNR 8.5, 2 Gateways, SF7)" "$Z" ",-71,8.5,2,7,2,261008,21.5,18.07,247.3,-23.5,-18,-40;-22.5,1,1,"
enthaelt "v2: Zusatz Ergebnis" "$Z" "gespeichert | HTTP 200"

# --- 2. gleiche Nachricht noch einmal (TTN-Wiederholung) ---
A=$(senden '{"geraet":"beelogger-01","fport":2,"f_cnt":10,"empfang":"2026-10-08T12:00:07.5Z","werte":{"tOut":12.34,"status":1,"zeit":1791460800}}')
enthaelt "doppelt: nicht gespeichert" "$A" "nicht gespeichert"
pruefe "doppelt: week.csv unverändert" "$(wc -l < "$W/www/beelogger1/week.csv" | tr -d ' ')" "1"

# --- 3. Uhr nicht abgeglichen → Empfangszeit von TTN ---
A=$(senden '{"geraet":"beelogger-01","fport":2,"f_cnt":11,"empfang":"2026-10-08T12:15:09Z","werte":{"tOut":11,"status":0,"zeit":1600000000}}')
enthaelt "Uhr nicht abgeglichen: TTN-Zeit" "$A" "gespeichert 2026/10/08_14:15:09"
enthaelt "Uhr nicht abgeglichen: Zeitquelle ttn" "$(zusatz)" ",ttn,beelogger-01,11,"
enthaelt "Uhr nicht abgeglichen: Warnung aus dem Formatter" "$(zusatz)" "Uhr des Loggers nicht abgeglichen"

# --- 4. Gerätezeit zu weit weg (> 900 s) → TTN-Zeit ---
A=$(senden '{"geraet":"beelogger-01","fport":2,"f_cnt":12,"empfang":"2026-10-08T13:00:00Z","werte":{"tOut":10,"status":1,"zeit":1791462000}}')
enthaelt "Gerätezeit unplausibel: TTN-Zeit" "$A" "gespeichert 2026/10/08_15:00:00"

# --- 5. beelogger-Format (FPort 1): Sketch-ID landet nicht in Aux3 ---
# TempOut 12,34; Gewicht 45,67; TempIn 34,56; Aux1 1013,2; Service 0; Aux3 = Sketch-ID 260705
A=$(senden '{"geraet":"beelogger-01","fport":1,"f_cnt":13,"empfang":"2026-10-08T13:15:00Z","hex":"04d211d70d802794000003fa61e061"}')
enthaelt "FPort 1: gespeichert" "$A" "gespeichert 2026/10/08_15:15:00"
pruefe "FPort 1: Zeile ohne Sketch-ID in Aux3" "$(letzte)" \
  "2026/10/08 15:15:00,34.6,12.3,,,,45.67,,,0,45.67,1013.2,,,,,1791465300"
enthaelt "FPort 1: Sketch-ID in der Zusatzdatei" "$(zusatz)" ",1,260705,"

# --- 6. Fehlerfälle ---
enthaelt "falsches Token → 401" "$(senden '{"geraet":"beelogger-01","fport":2,"empfang":"2026-10-08T13:30:00Z"}' falsch-falsch-falsch-xx)" "[401]"
enthaelt "unbekanntes Gerät → ignoriert, 200" "$(senden '{"geraet":"sensecap-s2120-rad","fport":3,"empfang":"2026-10-08T13:30:00Z","hex":"00"}')" "ignoriert: Gerät nicht"
enthaelt "ohne decoded_payload → ignoriert" "$(senden '{"geraet":"beelogger-01","fport":2,"empfang":"2026-10-08T13:30:00Z","ohne_decoded":true}')" "ignoriert: kein decoded_payload"
enthaelt "GET → 405" "$(curl -s -w ' [%{http_code}]' "http://127.0.0.1:$PORT/lora/lora_eingang.php")" "[405]"
[ "$(ls "$W"/log/*.jsonl 2>/dev/null | wc -l)" -ge 1 ] && ok "Protokoll geschrieben" || nok "Protokoll geschrieben"

# --- 7. Winterzeit-Umstellung 25.10.2026 (bekannter beelogger-Fehler B2, wird in Schritt 4 behoben) ---
# Messungen alle 30 min mit Gerätezeit 23:30Z … 02:30Z; Ortszeit 01:30 MESZ, 02:00 MESZ, 02:30 MESZ, 02:00 MEZ, 02:30 MEZ, 03:00 MEZ, 03:30 MEZ
GESP=0
for T in 1792884600 1792886400 1792888200 1792890000 1792891800 1792893600 1792895400; do
  E=$(date -u -d @$((T+5)) +%Y-%m-%dT%H:%M:%SZ)
  A=$(senden "{\"geraet\":\"beelogger-01\",\"fport\":2,\"f_cnt\":$T,\"empfang\":\"$E\",\"werte\":{\"tOut\":5,\"status\":1,\"zeit\":$T}}")
  case "$A" in "gespeichert"*) GESP=$((GESP+1));; esac
done
if [ "$VARIANTE" = "original" ]; then
  echo "info - Winterzeit: $GESP von 7 Messungen gespeichert (beelogger M.40 verwirft die doppelte Stunde)"
  pruefe "Winterzeit, Original: bekannter Fehler (5 von 7)" "$GESP" "5"
else
  pruefe "Winterzeit, eigene Fassung: alle 7 Messungen gespeichert" "$GESP" "7"
  # Zeitstempel der Umstellungsnacht lückenlos und aufsteigend (Abstand 1800 s)
  ZS=$(tail -n 7 "$W/www/beelogger1/week.csv" | tr -d '\r' | awk -F, '{print $NF}' | tr '\n' ' ')
  pruefe "Winterzeit: Zeitstempel in week.csv" "$ZS" "1792884600 1792886400 1792888200 1792890000 1792891800 1792893600 1792895400 "
  ZT=$(tail -n 7 "$W/www/beelogger1/week.csv" | cut -d, -f1 | tr '\n' '|')
  pruefe "Winterzeit: Anzeige-Spalte in Ortszeit (doppelte Stunde sichtbar)" "$ZT" "2026/10/25 01:30:00|2026/10/25 02:00:00|2026/10/25 02:30:00|2026/10/25 02:00:00|2026/10/25 02:30:00|2026/10/25 03:00:00|2026/10/25 03:30:00|"
  # Grafik: die Datenzeilen gehen mit ISO-Zeit und Versatz an Dygraph, eindeutig und aufsteigend
  curl -s "http://127.0.0.1:$PORT/beelogger1/beelogger_show.php" -o "$W/show.html"
  enthaelt "Grafik: 02:30 Sommerzeit mit +02:00" "$(cat "$W/show.html")" "2026-10-25T02:30:00+02:00,"
  enthaelt "Grafik: 02:30 Winterzeit mit +01:00" "$(cat "$W/show.html")" "2026-10-25T02:30:00+01:00,"
  # Optional im echten Browser (wenn Playwright vorhanden): Dygraph liest alle Zeilen, Zeitachse steigt an
  if node -e "require('playwright')" 2>/dev/null; then
    G=$(node "$HIER/grafik_pruefen.js" "http://127.0.0.1:$PORT/beelogger1/beelogger_show.php")
    echo "info - Browser: $G"
    enthaelt "Browser: Zeitachse streng steigend" "$G" '"steigend":true'
    enthaelt "Browser: Umstellungsnacht lückenlos" "$G" '"letzte7":[1792884600,1792886400,1792888200,1792890000,1792891800,1792893600,1792895400]'
    enthaelt "Browser: keine JavaScript-Fehler" "$G" '"fehler":[]'
  else
    echo "info - Playwright fehlt: Browserprüfung übersprungen"
  fi
fi

echo "$((ANZ-FEHLER)) von $ANZ Prüfungen bestanden"
[ $FEHLER -eq 0 ] || { echo "--- Server-Log ---"; tail -20 "$W/server.log"; exit 1; }
