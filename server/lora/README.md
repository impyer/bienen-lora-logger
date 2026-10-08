# LoRa-Eingang für den beelogger-Webserver

`lora_eingang.php` ist das Webhook-Ziel für The Things Stack (TTN). Die beelogger-Skripte bleiben **unverändert**.

## Was er macht

1. Er nimmt den TTN-Webhook an und prüft das geheime Wort im Header `X-Bienen-Token`.
2. Er ordnet das Gerät über den TTN-Gerätenamen einem beelogger-Verzeichnis zu (`lora_config.php`).
3. Er wählt den **Messzeitpunkt**:
   - die Gerätezeit (Funkformat v2, Uhr abgeglichen, höchstens 15 min vor dem Empfang),
   - sonst die Empfangszeit `received_at` von TTN.
   Bisher nahm der beelogger-Server immer seine eigene Empfangszeit.
4. Er baut daraus einen Datensatz im Format, das beelogger für EE-Logger mit eigener Zeit vorsieht (`M1=Zeit,…`), und ruft damit `beelogger_log.php` des Loggers auf.
   - Gewichtskorrektur, Alarme, Anmerkungen, BEEP- und ThingSpeak-Weitergabe laufen also wie gewohnt, aber mit der richtigen Zeit.
5. Er prüft in `week.csv`, ob der Datensatz wirklich gespeichert wurde. `beelogger_log.php` antwortet auch bei verworfenen Datensätzen mit „…ok *“.
6. Er schreibt alles, wofür beelogger keine Spalte hat, in `lora_zusatz.csv` im Logger-Verzeichnis:
   - RSSI und SNR des besten Gateways, Anzahl Gateways, Spreizfaktor, Frame-Zähler
   - Firmware-ID, CPU-Temperatur, zweite Innentemperatur
   - FFT-Gesamt- und Bandpegel
   - Zustandsbits, Neustart-Grund, Warnungen des Formatters
   - Ergebnis der Speicherung
7. Er protokolliert jede Webhook-Nachricht als JSON-Zeile in `lora_log/JJJJ-MM.jsonl`.

### Zuordnung der Werte

| beelogger-Spalte | Formatter-Feld |
|---|---|
| TempIn, TempOut, FeuchteIn, FeuchteOut, Licht, Gewicht, VBatt, VSolar, Service | gleichnamig |
| TempIn2, FeuchteIn2, Gewicht2 … | gleichnamig, nur bei Duo usw. (Verzeichnis `Duo1` …) |
| Aux1 / Aux2 / Aux3 | einstellbar (`aux`), Vorgabe: Luftdruck / FFT-Frequenz / FFT-Pegel, wie beim WLAN-beelogger |

**RSSI und Sketch-ID landen nicht mehr in Aux2 und Aux3.**

## Einrichtung

1. Ordner `server/lora` auf den Server kopieren, und zwar **neben** die Verzeichnisse `beelogger1`, `beelogger2` …: `…/beelogger/lora/`.
2. `lora_config.beispiel.php` nach `lora_config.php` kopieren und eintragen:
   - `token`: ein langes Zufallswort, mindestens 16 Zeichen. Zum Beispiel unter Linux mit `openssl rand -hex 24` erzeugen.
   - `basis_url`: Adresse des beelogger-Ordners, z. B. `https://example.org/beelogger`.
   - `geraete`: TTN-Gerätename → Verzeichnis.
   - Optional `log_verzeichnis` außerhalb des Webverzeichnisses legen.
3. Voraussetzung: PHP 7.4 oder neuer mit der Erweiterung **curl**. Getestet ist mit PHP 8.3.
4. Schutz:
   - Apache: Die mitgelieferte `.htaccess` lässt nur `lora_eingang.php` von außen zu; `lora_log/` wird gesperrt.
   - **nginx** liest keine `.htaccess`. Dort `lora_log` außerhalb des Webverzeichnisses legen bzw. per Server-Konfiguration sperren.
5. TTN-Konsole → Applikation `beelog-de-sn` → Integrations → **Webhooks**. Den bisherigen beelogger-Webhook ändern oder einen neuen anlegen:
   - Webhook format: JSON
   - Base URL: `https://example.org/beelogger/lora/lora_eingang.php`
   - Additional headers: `X-Bienen-Token` = das Wort aus `token`
   - Enabled event types: nur **Uplink message**, Pfad leer lassen
6. Prüfen:
   - In TTN beim Gerät unter Messaging → **Simulate uplink**: FPort 2 und als Payload den Hexwert aus `docs/funkformat-v2.md`, Abschnitt „Beispiel“.
   - Danach sollte in `beelogger1/week.csv` eine neue Zeile stehen und in `lora_zusatz.csv` „gespeichert“.
   - **[P]** Ob TTN bei leerem Pfad genau die Base URL aufruft, mit diesem Test bestätigen.

Die alte Webhook-Adresse (`…/beelogger_log.php?…&LORA=1`) wird danach nicht mehr gebraucht.

## Antworten an TTN

| HTTP | Bedeutung |
|---|---|
| 200 | verarbeitet; im Text steht „gespeichert“ oder „nicht gespeichert“. Auch „ignoriert“ bei unbekanntem Gerät oder ohne `decoded_payload`; das steht dann im Protokoll. |
| 401 | Token falsch |
| 400 | kein JSON bzw. ohne `received_at` |
| 405 | kein POST |
| 500 | Einrichtungsfehler (Konfiguration, `beelogger_ini.php`) |
| 502 | `beelogger_log.php` nicht erreichbar |

## Grenzen (bekannt)

- **Winterzeit-Umstellung:** beelogger speichert die Ortszeit und rechnet sie mit `strtotime()` zurück. In der doppelten Stunde verwirft beelogger deshalb weiterhin Datensätze; im Test sind es 2 von 7 bei 30-min-Takt. Behoben wird das in Schritt 4. Die Zusatzdatei hat immer die richtige UTC-Zeit.
- Duo, Triple usw. sind nur über die Feldzahl geprüft, nicht mit echten Unterverzeichnissen. **[P]** Beim ersten Duo-Logger nachsehen.
- Der Testserver (`php -S`) braucht mehrere Arbeitsprozesse, weil der Eingang `beelogger_log.php` beim selben Server aufruft. Auf einem normalen Webserver ist das ohnehin gegeben.

## Tests

- `php tests/server/test_lora_funktionen.php`: Hilfsfunktionen
- `bash tests/server/test_lora_eingang.sh`: Ende-zu-Ende mit den echten beelogger-Skripten M.40, dem echten Formatter und einem PHP-Testserver, einschließlich Winterzeit-Fall
