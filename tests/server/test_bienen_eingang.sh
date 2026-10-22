#!/bin/bash
# Ende-zu-Ende-Test des Bienen-Eingangs:
# echte beelogger-Skripte M.40 (Original-ZIP) + server/eingang + server/bienen + echter TTN-Formatter + PHP-Testserver.
# Braucht: php (mit curl), node, unzip, curl. Zwei Testserver (Webhook-Eingang und beelogger_log.php getrennt), weil der Eingang
# beelogger_log.php über HTTP beim selben Server aufruft.
# Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
set -u
HIER="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HIER/../.." && pwd)"
W="$(mktemp -d)"
PORT=$((20000 + RANDOM % 20000))
PORT2=$((PORT + 1))   # zweiter Testserver nur für beelogger_log.php (siehe unten)
TOKEN="test-token-1234567890abcdef"
FEHLER=0; ANZ=0

aufraeumen() { [ -n "${SPID:-}" ] && kill "$SPID" 2>/dev/null; [ -n "${SPID2:-}" ] && kill "$SPID2" 2>/dev/null; if grep -qiE "PHP (Fatal|Parse|Warning)" "$W/server.log" 2>/dev/null; then echo "--- PHP-Meldungen im Server-Log ---"; grep -iE "PHP (Fatal|Parse|Warning)" "$W/server.log" | sort | uniq -c | head -20; fi; rm -rf "$W"; }
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
cp -r "$REPO/server/eingang" "$W/www/eingang"
cp -r "$REPO/server/bienen" "$W/www/bienen"
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
cfg_schreiben() {  # $1 = zusätzliche Einträge (PHP), $2 = Port für basis_url (Vorgabe: Testserver)
  cat > "$W/www/bienen/bienen_config.php" <<EOF
<?php
return array(
  'token' => '$TOKEN',
  'basis_url' => 'http://127.0.0.1:${2:-$PORT2}',
  'geraete' => array('beelogger-01' => array('verzeichnis' => 'beelogger1')),
  'log_verzeichnis' => '$W/log',
  ${1:-}
);
EOF
}
cfg_schreiben
# OPcache aus: der Test schreibt bienen_config.php, beelogger_ini.php und beelogger_log.php während des Laufs um.
# Zwei Testserver auf demselben Verzeichnis: PORT nimmt die Webhooks an, PORT2 bedient den Aufruf von beelogger_log.php.
# Der eingebaute PHP-Server verteilt Verbindungen ungleichmäßig auf seine Arbeitsprozesse; landet der interne Aufruf
# bei einem Prozess, der an der Sperre wartet, hängt er bis zum Zeitlimit. Apache/PHP-FPM haben das Problem nicht.
# SERVER_UHR (z. B. "2026-10-09 05:00:00"): Serveruhr per libfaketime festlegen (CI26-01). beelogger kürzt week.csv
# nur vor 08:00 Uhr (CSVbuilder_log); ohne Vorgabe hinge das Ergebnis von der Uhrzeit des Testlaufs ab.
UHR=()
if [ -n "${SERVER_UHR:-}" ]; then
  command -v faketime >/dev/null 2>&1 || { echo "FEHL - SERVER_UHR gesetzt, aber faketime fehlt (apt install faketime)"; exit 1; }
  UHR=(faketime -f "@${SERVER_UHR}")
  echo "info - Serveruhr: ${SERVER_UHR} (läuft ab dort weiter)"
fi
PHP_CLI_SERVER_WORKERS=8 "${UHR[@]}" php -d opcache.enable=0 -S 127.0.0.1:$PORT -t "$W/www" "$W/router.php" > "$W/server.log" 2>&1 &
SPID=$!
PHP_CLI_SERVER_WORKERS=4 "${UHR[@]}" php -d opcache.enable=0 -S 127.0.0.1:$PORT2 -t "$W/www" "$W/router.php" >> "$W/server.log" 2>&1 &
SPID2=$!
for i in $(seq 1 50); do curl -s -o /dev/null "http://127.0.0.1:$PORT2/" && break; sleep 0.1; done
for i in $(seq 1 50); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.1; done
# beelogger1 einrichten wie beim ersten Aufruf im Browser (legt beelogger_ini.php mit Log-Passwort "Log" an)
curl -s -o /dev/null "http://127.0.0.1:$PORT/beelogger1/beelogger_show.php"
[ -f "$W/www/beelogger1/beelogger_ini.php" ] && ok "beelogger1 eingerichtet" || nok "beelogger1 eingerichtet"

senden() {  # $1 = JSON-Parameter für ttn_nachricht.js, $2 = Token (optional)
  node "$HIER/ttn_nachricht.js" "$1" > "$W/msg.json"
  senden_datei "$W/msg.json" "${2:-$TOKEN}"
}
senden_datei() {  # $1 = fertige JSON-Datei, $2 = Token (optional)
  curl -s -w ' [%{http_code}]' -X POST -H "Content-Type: application/json" -H "X-Bienen-Token: ${2:-$TOKEN}" \
    --data-binary @"$1" "http://127.0.0.1:$PORT/bienen/bienen_eingang.php"
}
zeilen() { wc -l < "$W/www/beelogger1/$1" | tr -d ' '; }
nachholen_zahl() { ls "$W"/log/nachholen/*.json 2>/dev/null | wc -l | tr -d ' '; }
nachricht() {  # $1 = Datei, $2 = f_cnt, $3 = Unixzeit der Messung, $4 = weitere Werte (optional, JSON-Teil)
  node "$HIER/ttn_nachricht.js" "{\"geraet\":\"beelogger-01\",\"fport\":2,\"f_cnt\":$2,\"empfang\":\"$(date -u -d @$(($3+3)) +%Y-%m-%dT%H:%M:%SZ)\",\"werte\":{\"tOut\":6,${4:-}\"status\":1,\"zeit\":$3}}" > "$1"
}
zeitstempel() { letzte | awk -F, '{print $NF}'; }
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
enthaelt "gleiche Zeit, anderer Inhalt: abgelehnt (beelogger)" "$A" "abgelehnt: nicht gespeichert"
pruefe "gleiche Zeit: week.csv unverändert" "$(zeilen week.csv)" "1"

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
enthaelt "Gerät ohne beelogger-Weiterleitung → protokolliert, 200" "$(senden '{"geraet":"beep-base-01","fport":3,"empfang":"2026-10-08T13:30:00Z","hex":"00"}')" "protokolliert, ohne beelogger-Weiterleitung"
pruefe "Gerät ohne beelogger-Weiterleitung steht im Rohprotokoll (für den Importer)" "$(cat "$W"/log/*.jsonl | grep '"art":"uplink"' | grep -c '"geraet":"beep-base-01"')" "1"
enthaelt "ohne decoded_payload → ignoriert" "$(senden '{"geraet":"beelogger-01","fport":2,"empfang":"2026-10-08T13:30:00Z","ohne_decoded":true}')" "ignoriert: kein decoded_payload"
enthaelt "GET → 405" "$(curl -s -w ' [%{http_code}]' "http://127.0.0.1:$PORT/bienen/bienen_eingang.php")" "[405]"
[ "$(ls "$W"/log/*.jsonl 2>/dev/null | wc -l)" -ge 1 ] && ok "Protokoll geschrieben" || nok "Protokoll geschrieben"

# --- 6b. SRV26-03/04: exakt dieselbe Nachricht noch einmal → doppelt, beelogger wird nicht aufgerufen ---
nachricht "$W/m20.json" 20 1791532800   # 2026-10-09 08:00Z
W0=$(zeilen week.csv); Z0=$(zeilen lora_zusatz.csv)
enthaelt "neue Nachricht: gespeichert" "$(senden_datei "$W/m20.json")" "gespeichert"
A=$(senden_datei "$W/m20.json")
enthaelt "dieselbe Nachricht: doppelt" "$A" "doppelt: Nachricht schon verarbeitet"
enthaelt "dieselbe Nachricht: HTTP 200" "$A" "[200]"
pruefe "doppelt: genau 1 Zeile in week.csv dazu" "$(($(zeilen week.csv)-W0))" "1"
pruefe "doppelt: genau 1 Zeile in lora_zusatz.csv dazu" "$(($(zeilen lora_zusatz.csv)-Z0))" "1"

# --- 6c. SRV26-03: gleichzeitige Webhooks für denselben Logger ---
# (a) dieselbe Nachricht 4× gleichzeitig: genau einmal gespeichert, 3× doppelt
nachricht "$W/m21.json" 21 1791536400
W0=$(zeilen week.csv); Z0=$(zeilen lora_zusatz.csv); rm -f "$W"/par_*.txt
PIDS=""; for i in 1 2 3 4; do senden_datei "$W/m21.json" > "$W/par_$i.txt" & PIDS="$PIDS $!"; done; wait $PIDS   # nicht auf die Testserver warten
G=$(grep -l "^gespeichert" "$W"/par_*.txt | wc -l | tr -d ' '); D=$(grep -l "^doppelt" "$W"/par_*.txt | wc -l | tr -d ' ')
pruefe "parallel gleich: 1× gespeichert, 3× doppelt" "$G/$D" "1/3"
pruefe "parallel gleich: je 1 Zeile in week.csv und lora_zusatz.csv" "$(($(zeilen week.csv)-W0))/$(($(zeilen lora_zusatz.csv)-Z0))" "1/1"
# (b) 4 verschiedene Messungen gleichzeitig (10 min Abstand): jede Meldung stimmt mit der Datei überein
W0=$(zeilen week.csv); rm -f "$W"/par_*.txt
for k in 1 2 3 4; do nachricht "$W/p$k.json" $((30+k)) $((1791540000 + k*600)); done
PIDS=""; for k in 1 2 3 4; do senden_datei "$W/p$k.json" > "$W/par_$k.txt" & PIDS="$PIDS $!"; done; wait $PIDS
G=$(grep -l "^gespeichert" "$W"/par_*.txt | wc -l | tr -d ' '); AB=$(grep -l "^abgelehnt" "$W"/par_*.txt | wc -l | tr -d ' ')
pruefe "parallel verschieden: jede Antwort gespeichert oder abgelehnt" "$((G+AB))" "4"
pruefe "parallel verschieden: Zahl 'gespeichert' = neue Zeilen in week.csv" "$G" "$(($(zeilen week.csv)-W0))"
echo "info - parallel verschieden: $G gespeichert, $AB abgelehnt (Reihenfolge zufällig; beelogger nimmt nur neuere Zeiten an)"

# --- 6d. Nachholen: beelogger nicht erreichbar → 202 und Zwischenspeicher; danach bienen_nachholen.php ---
cfg_schreiben "" 1   # Port 1: nicht erreichbar
nachricht "$W/m40.json" 40 1791547200   # 2026-10-09 12:00Z
A=$(senden_datei "$W/m40.json")
enthaelt "nicht erreichbar: 202 zwischengespeichert" "$A" "[202]"
pruefe "nicht erreichbar: 1 Datei zum Nachholen" "$(nachholen_zahl)" "1"
senden_datei "$W/m40.json" > /dev/null
pruefe "nicht erreichbar, Wiederholung: keine zweite Datei" "$(nachholen_zahl)" "1"
cfg_schreiben
N=$(cd "$W/www/bienen" && php bienen_nachholen.php 2>&1)
enthaelt "nachholen: gespeichert" "$N" ": gespeichert"
pruefe "nachholen: Zwischenspeicher leer" "$(nachholen_zahl)" "0"
pruefe "nachholen: Zeile mit Messzeit 12:00Z in week.csv" "$(zeitstempel)" "1791547200"
enthaelt "nachholen: danach dieselbe Nachricht doppelt" "$(senden_datei "$W/m40.json")" "doppelt"
enthaelt "nachholen: nicht über das Web aufrufbar" "$(curl -s -w ' [%{http_code}]' "http://127.0.0.1:$PORT/bienen/bienen_nachholen.php")" "[403]"

# --- 6e. SRV26-07: Zeitbasis je Ziel-Logger (Fassung von beelogger_log.php × Merkmal im Hauptordner × utc_zeit) ---
LOGZIEL="$W/www/beelogger1/beelogger_log.php"
cp "$LOGZIEL" "$W/log_vorher.php"
cp "$REPO/server/beelogger_eigen/beelogger1/beelogger_log.php" "$W/log_eigen.php"
unzip -p "$REPO/server/M40_261004_ServerSkripte.zip" beelogger1/beelogger_log.php > "$W/log_original.php"
HAUPT_VORHER=$([ -f "$W/www/beelogger_zeitzone.php" ] && echo ja || echo nein)
matrix() {  # $1 Name, $2 log.php, $3 Merkmal im Hauptordner ja/nein, $4 utc_zeit (PHP), $5 f_cnt, $6 Unixzeit, $7 erwarteter Text
  cp "$2" "$LOGZIEL"
  if [ "$3" = ja ]; then echo '<?php $Zeitzone="Europe/Berlin";' > "$W/www/beelogger_zeitzone.php"; else rm -f "$W/www/beelogger_zeitzone.php"; fi
  cfg_schreiben "'utc_zeit' => $4,"
  nachricht "$W/mx.json" "$5" "$6"
  enthaelt "$1" "$(senden_datei "$W/mx.json")" "$7"
}
# Messzeiten 2026-10-10 10:00Z, 11:00Z … (MESZ 12:00, 13:00 …). Gespeicherter Zeitstempel muss immer die Messzeit sein.
matrix "Matrix: alte log.php + Merkmal, auto → Ortszeit-Modus (keine 2-h-Verschiebung)" "$W/log_original.php" ja "'auto'" 50 1791626400 "gespeichert 2026/10/10_12:00:00 (Ortszeit-Modus)"
pruefe "Matrix: alte log.php + Merkmal: Zeitstempel = Messzeit" "$(zeitstempel)" "1791626400"
grep -q "Mischinstallation" "$W"/log/*.jsonl && ok "Matrix: Mischinstallation im Protokoll gemeldet" || nok "Matrix: Mischinstallation im Protokoll gemeldet"
matrix "Matrix: alte log.php ohne Merkmal, auto → Ortszeit-Modus" "$W/log_original.php" nein "'auto'" 51 1791630000 "gespeichert 2026/10/10_13:00:00 (Ortszeit-Modus)"
pruefe "Matrix: alte log.php ohne Merkmal: Zeitstempel = Messzeit" "$(zeitstempel)" "1791630000"
matrix "Matrix: alte log.php, utc_zeit=true → 202, nichts gespeichert" "$W/log_original.php" ja "true" 52 1791633600 "[202]"
pruefe "Matrix: utc_zeit=true + alte log.php: week.csv unverändert" "$(zeitstempel)" "1791630000"
matrix "Matrix: eigene log.php ohne Merkmal im Hauptordner, auto → UTC-Modus" "$W/log_eigen.php" nein "'auto'" 53 1791637200 "gespeichert 2026/10/10_15:00:00 (UTC-Modus)"
pruefe "Matrix: eigene log.php: Zeitstempel = Messzeit" "$(zeitstempel)" "1791637200"
N=$(cd "$W/www/bienen" && php bienen_nachholen.php 2>&1)   # zurückgestellte Nachricht (14:00Z) jetzt mit eigener log.php
enthaelt "Matrix: zurückgestellte Nachricht nach dem Update verarbeitet (14:00Z vor 15:00Z → abgelehnt)" "$N" ": abgelehnt"
pruefe "Matrix: Zwischenspeicher danach leer" "$(nachholen_zahl)" "0"
matrix "Matrix: eigene log.php + Merkmal, utc_zeit=false → Ortszeit-Modus" "$W/log_eigen.php" ja "false" 54 1791640800 "gespeichert 2026/10/10_16:00:00 (Ortszeit-Modus)"
matrix "Matrix: eigene log.php + Merkmal, auto → UTC-Modus" "$W/log_eigen.php" ja "'auto'" 55 1791644400 "gespeichert 2026/10/10_17:00:00 (UTC-Modus)"
pruefe "Matrix: eigene log.php + Merkmal: Zeitstempel = Messzeit" "$(zeitstempel)" "1791644400"
cp "$W/log_vorher.php" "$LOGZIEL"
if [ "$HAUPT_VORHER" = ja ]; then echo '<?php $Zeitzone="Europe/Berlin";' > "$W/www/beelogger_zeitzone.php"; else rm -f "$W/www/beelogger_zeitzone.php"; fi
cfg_schreiben

# --- 6f. SRV26-05: BEEP nur für gespeicherte Datensätze (Nachbildung über BeepApiHeader.php, ohne Netz) ---
if [ "$VARIANTE" = "eigen" ]; then
  # beelogger_log.php bindet ../../BeepApiHeader.php nach curl_init() ein: dort auf die lokale Nachbildung umlenken
  printf '<?php curl_setopt($ch, CURLOPT_URL, "http://127.0.0.1:%s/beep_nachbildung.php?" . (string)parse_url($burl, PHP_URL_QUERY));\n' "$PORT" > "$W/BeepApiHeader.php"
  printf '<?php file_put_contents("%s/beep.log", $_SERVER["QUERY_STRING"] . " " . file_get_contents("php://input") . "\\n", FILE_APPEND | LOCK_EX); echo "{}";\n' "$W" > "$W/www/beep_nachbildung.php"
  INI="$W/www/beelogger1/beelogger_ini.php"; cp "$INI" "$W/ini_vorher.php"
  sed -i 's/^\$Beep="[^"]*";/$Beep="aktiviert";/; s/^\$BeepId="[^"]*";/$BeepId="testbeepid";/' "$INI"
  grep -q '^\$Beep="aktiviert";' "$INI" && ok "BEEP: in beelogger_ini.php aktiviert" || nok "BEEP: in beelogger_ini.php aktiviert"
  rm -f "$W/beep.log"; touch "$W/beep.log"
  T=1791648000   # 2026-10-10 18:00Z
  nachricht "$W/m60.json" 60 $T '"g1":40.5,'
  enthaelt "BEEP: neue Messung gespeichert" "$(senden_datei "$W/m60.json")" "gespeichert"
  pruefe "BEEP: genau 1 Übertragung" "$(wc -l < "$W/beep.log" | tr -d ' ')" "1"
  enthaelt "BEEP: mit Schlüssel und Unix-Zeit" "$(cat "$W/beep.log")" "key=testbeepid time=$T"
  nachricht "$W/m61.json" 61 $T '"g1":40.6,'   # gleiche Messzeit, andere Nachricht: beelogger lehnt ab
  enthaelt "BEEP: gleiche Zeit abgelehnt" "$(senden_datei "$W/m61.json")" "abgelehnt"
  pruefe "BEEP: abgelehnt → keine weitere Übertragung" "$(wc -l < "$W/beep.log" | tr -d ' ')" "1"
  enthaelt "BEEP: identische Nachricht doppelt" "$(senden_datei "$W/m60.json")" "doppelt"
  pruefe "BEEP: doppelt → keine weitere Übertragung" "$(wc -l < "$W/beep.log" | tr -d ' ')" "1"
  sed -i 's/^\$BeepId="[^"]*";/$BeepId="meine BeepID";/' "$INI"
  nachricht "$W/m62.json" 62 $((T+1800))
  enthaelt "BEEP: Platzhalter-ID, Messung gespeichert" "$(senden_datei "$W/m62.json")" "gespeichert"
  pruefe "BEEP: Platzhalter-ID → keine Übertragung (Prüfung war im Original immer wahr)" "$(wc -l < "$W/beep.log" | tr -d ' ')" "1"
  cp "$W/ini_vorher.php" "$INI"
  rm -f "$W/BeepApiHeader.php"
fi

# --- 6g. SRV26-04: Zusatzdatei nicht schreibbar (als Verzeichnis angelegt, wirkt auch als root) ---
ZD="$W/www/beelogger1/lora_zusatz.csv"; mv "$ZD" "$W/zusatz_sicher.csv"; mkdir "$ZD"
nachricht "$W/m70.json" 70 1791655200   # 2026-10-10 20:00Z
A=$(senden_datei "$W/m70.json")
enthaelt "Zusatz nicht schreibbar: Hauptdatensatz trotzdem gespeichert" "$A" "gespeichert"
enthaelt "Zusatz nicht schreibbar: Warnung in der Antwort" "$A" "WARNUNG: lora_zusatz.csv nicht geschrieben"
grep -q '"klasse":"zusatz_fehler"' "$W"/log/*.jsonl && ok "Zusatz nicht schreibbar: zusatz_fehler mit Zeile im Protokoll" || nok "Zusatz nicht schreibbar: zusatz_fehler mit Zeile im Protokoll"
rmdir "$ZD"; mv "$W/zusatz_sicher.csv" "$ZD"

# --- 7. Winterzeit-Umstellung 25.10.2026 (bekannter beelogger-Fehler B2, wird in Schritt 4 behoben) ---
# Messungen alle 30 min mit Gerätezeit 23:30Z … 02:30Z; Ortszeit 01:30 MESZ, 02:00 MESZ, 02:30 MESZ, 02:00 MEZ, 02:30 MEZ, 03:00 MEZ, 03:30 MEZ
GESP=0
for T in 1792884600 1792886400 1792888200 1792890000 1792891800 1792893600 1792895400; do
  E=$(date -u -d @$((T+5)) +%Y-%m-%dT%H:%M:%SZ)
  A=$(senden "{\"geraet\":\"beelogger-01\",\"fport\":2,\"f_cnt\":$T,\"empfang\":\"$E\",\"werte\":{\"tOut\":5,\"status\":1,\"zeit\":$T}}")
  echo "info - Winterzeit $T: $(printf "%s" "$A" | tr -d "\r" | cut -c1-140) | week.csv $(zeilen week.csv) Zeilen"
  case "$A" in "gespeichert"*) GESP=$((GESP+1));; esac
done
if [ "$VARIANTE" = "original" ]; then
  echo "info - Winterzeit: $GESP von 7 Messungen gespeichert (beelogger M.40 verwirft die doppelte Stunde)"
  pruefe "Winterzeit, Original: bekannter Fehler (5 von 7)" "$GESP" "5"
else
  pruefe "Winterzeit, eigene Fassung: alle 7 Messungen gespeichert" "$GESP" "7"
  if [ -n "${SERVER_UHR:-}" ]; then
    H=$(TZ=Europe/Berlin date -d "$SERVER_UHR" +%-H 2>/dev/null || echo 99)
    if [ "$H" -lt 8 ]; then
      pruefe "Winterzeit vor 08:00: week.csv auf 7 Tage gekürzt (Kürzungspfad durchlaufen)" "$(zeilen week.csv)" "7"
    else
      Z=$(zeilen week.csv); [ "$Z" -gt 7 ] && ok "Winterzeit ab 08:00: week.csv ungekürzt ($Z Zeilen)" || nok "Winterzeit ab 08:00: week.csv ungekürzt ($Z Zeilen)"
    fi
  fi
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
  elif [ "${BROWSER_PFLICHT:-0}" = "1" ]; then
    nok "Browser: Playwright fehlt, Prüfung ist verpflichtend (BROWSER_PFLICHT=1)"
  else
    echo "info - Playwright fehlt: Browserprüfung übersprungen (in der CI verpflichtend)"
  fi
fi

# --- PLT26-02: Rohprotokoll (R-1 vollständig vor Verarbeitung, R-2 Fehler sichtbar) ---
rohzeilen() { cat "$W"/log/*.jsonl 2>/dev/null | grep -c '"art":"uplink"'; }
L0=$(rohzeilen)
T0R=$(( $(zeitstempel) + 3600 ))
for i in 1 2 3 4 5; do nachricht "$W/r$i.json" $((600+i)) $((T0R+i*900)); senden_datei "$W/r$i.json" > /dev/null; done
for i in 1 2 3 4 5; do senden "{\"geraet\":\"unbekannt-$i\",\"fport\":2,\"f_cnt\":$((700+i)),\"empfang\":\"2026-10-08T1$i:00:00Z\",\"hex\":\"00\"}" > /dev/null; done
pruefe "R-1: 10 Uplinks (davon 5 unbekannte Geräte) → 10 Rohzeilen" "$(( $(rohzeilen) - L0 ))" "10"
pruefe "R-1: jede Rohzeile mit Prüfsumme des Eingangs" "$(cat "$W"/log/*.jsonl | grep '"art":"uplink"' | grep -c '"roh_sha256":"[0-9a-f]\{64\}"')" "$(rohzeilen)"
grep -q "\"roh_sha256\":\"$(sha256sum "$W/r1.json" | cut -d' ' -f1)\"" "$W"/log/*.jsonl && ok "R-1: Prüfsumme = SHA-256 des empfangenen Textes" || nok "R-1: Prüfsumme = SHA-256 des empfangenen Textes"
grep '"art":"uplink"' "$W"/log/*.jsonl | grep -q '"geraet":"unbekannt-3".*"uplink_message"' && ok "R-1: unbekanntes Gerät vollständig protokolliert" || nok "R-1: unbekanntes Gerät vollständig protokolliert"
M=$(ls "$W"/log/*.jsonl | tail -n 1); mv "$M" "$W/log_sicher.jsonl"; mkdir "$M"
nachricht "$W/r6.json" 606 $((T0R+6*900))
A=$(senden_datei "$W/r6.json")
enthaelt "R-2: Rohprotokoll gescheitert → Warnung in der Antwort" "$A" "WARNUNG: Rohprotokoll nicht geschrieben"
enthaelt "R-2: Messwert trotzdem gespeichert (HTTP 200)" "$A" "[200]"
pruefe "R-2: Datensatz in week.csv" "$(zeitstempel)" "$((T0R+6*900))"
grep -q "Rohprotokoll nicht geschrieben" "$W/server.log" && ok "R-2: Eintrag im PHP-Fehlerprotokoll" || nok "R-2: Eintrag im PHP-Fehlerprotokoll"
rmdir "$M"; mv "$W/log_sicher.jsonl" "$M"

echo "$((ANZ-FEHLER)) von $ANZ Prüfungen bestanden"
[ $FEHLER -eq 0 ] || { echo "--- Server-Log ---"; tail -20 "$W/server.log"; exit 1; }
