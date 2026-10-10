# Wetter-Eingang (Wetterstation SenseCAP S2120)

Webhook-Ziel für The Things Stack. Speichert **alle** Werte der Wetterstation je Bienenstand in CSV-Dateien, auch Wind, Regen und UV, die BEEP nicht annimmt. Der beelogger-Code bleibt unverändert; der Eingang nutzt nur Hilfsfunktionen aus `../lora/lora_funktionen.php`.

| Datei | Zweck |
|---|---|
| `wetter_eingang.php` | Webhook-Ziel (einzige von außen erreichbare Datei, siehe `.htaccess`) |
| `wetter_funktionen.php` | Hilfsfunktionen ohne Seiteneffekte (Unit-Tests) |
| `wetter_config.beispiel.php` | Vorlage für `wetter_config.php` (Token, Stände, Stationen) – `wetter_config.php` bleibt lokal |

## Was er macht

1. Token im Header `X-Bienen-Token` prüfen.
2. Station (TTN-Gerätename) über `wetter_config.php` einem **Bienenstand** zuordnen.
3. Uplinks **ohne Nutzdaten** (die S2120 sendet nach jedem Join einige) und ohne Messwerte mit 200 „ignoriert“ beantworten. So schaltet TTN den Webhook nicht ab.
4. Doppelte Zustellung erkennen (Kennung wie im LoRa-Eingang, Sperre je Station).
5. Eine Zeile anhängen an `<daten_verzeichnis>/<stand>/<station>_<JJJJ-MM>.csv` (Monat in UTC, Trennzeichen `;`).
6. `<daten_verzeichnis>/staende.json` schreiben: je Stand Name, zugehörige beelogger-Verzeichnisse und Stationen (ohne Token). Damit ordnet die Auswertung Logger und Station einander zu.
7. Jede Webhook-Nachricht als JSON-Zeile in `<log_verzeichnis>/JJJJ-MM.jsonl` protokollieren.

Zeitstempel ist die Empfangszeit `received_at` von TTN; die S2120 sendet keine eigene Messzeit.

### Spalten

| Spalte | Inhalt |
|---|---|
| `zeit_utc`, `unix`, `ortszeit` | Empfangszeit (UTC, Unix-Sekunden, Europe/Berlin) |
| `stand`, `station` | Zuordnung zum Zeitpunkt des Empfangs |
| `t`, `h`, `p`, `l` | Lufttemperatur °C, Luftfeuchte %, Luftdruck hPa, Licht lx |
| `uv`, `wind_ms`, `wind_dir_deg`, `gust_ms` | UV-Index, Wind m/s, Windrichtung °, Spitzenböe m/s |
| `rain_mmh`, `rain_mm` | höchste Regenintensität im Intervall mm/h, Regensumme mm (Rücksetzzeitpunkt noch unbekannt) |
| `battery_pct`, `interval_min` | nur nach Join bzw. selten: Batterie % (laut Seeed-Handbuch nur 0 oder 100), Sendeintervall min |
| `f_cnt`, `f_port`, `rssi`, `snr`, `gateways`, `sf` | Funkdaten |
| `payload_hex` | Rohdaten zum späteren Neu-Dekodieren |
| `warnungen` | Warnungen des Formatters |

Leere Zellen = Wert nicht im Uplink. Es wird nichts geglättet oder verworfen; die Plausibilitätsprüfung macht die Auswertung.

### Antworten

| Code | Text | Fall |
|---|---|---|
| 200 | `gespeichert: …` | Zeile angehängt |
| 200 | `doppelt` | dieselbe Nachricht schon gespeichert |
| 200 | `ignoriert: …` | keine Uplink-Nachricht, unbekannte Station, Uplink ohne Nutzdaten/Messwerte |
| 400 | `kein JSON`, `received_at fehlt` | unbrauchbare Nachricht |
| 401 | `Token falsch` | |
| 500 | | Konfiguration fehlerhaft, Verzeichnis nicht beschreibbar |

## Einrichtung

1. Ordner `wetter/` **neben** `lora/` auf den Server kopieren (gleiche Ebene wie `beelogger1` …). `lora/` muss vorhanden sein.
2. `wetter_config.beispiel.php` nach `wetter_config.php` kopieren: Token, Stände und Stationen eintragen. Daten- und Protokollverzeichnis möglichst außerhalb des Webverzeichnisses; sonst legt der Eingang dort eine `.htaccess` mit `Require all denied` an (nur Apache).
3. TTN-Konsole → Applikation `beelog-de-sn` → **Webhooks** → **Add webhook** → Custom webhook:
   - Webhook ID z. B. `bienen-server`, Format **JSON**
   - Base URL `https://<dein-server>/<beelogger-ordner>/wetter/wetter_eingang.php`
   - Additional headers: `X-Bienen-Token` = Token aus `wetter_config.php`
   - nur **Uplink message** anhaken
4. Uplink-Formatter am Gerät: `formatter/s2120_beep_formatter.js` (derselbe wie für BEEP).
5. Nach dem nächsten Uplink prüfen: Datei `<stand>/<station>_<JJJJ-MM>.csv` hat eine neue Zeile; in TTN kein `as.webhook.fail`.

**Station umstellen:** in `wetter_config.php` den Stand der Station ändern. Neue Werte landen ab dann beim neuen Stand.

## Tests

```
php tests/server/test_wetter_funktionen.php
bash tests/server/test_wetter_eingang.sh
node tests/formatter/test_s2120_formatter.js
```

Geprüft sind Host-Tests (PHP-Testserver, kein Apache). Der echte Webhook von TTN an den Produktivserver ist ein Feldtest und steht noch aus.
