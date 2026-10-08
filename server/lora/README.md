# LoRa-Eingang für den beelogger-Webserver

`lora_eingang.php` ist das Webhook-Ziel für The Things Stack (TTN). Er arbeitet mit dem Original M.40 und mit der eigenen Fassung (`server/beelogger_eigen/`).

| Datei | Aufgabe |
|---|---|
| `lora_eingang.php` | Webhook annehmen (Token, JSON), Ergebnis an TTN melden |
| `lora_verarbeitung.php` | Verarbeitung eines Uplinks, gemeinsam für Eingang und Nachholen |
| `lora_nachholen.php` | zwischengespeicherte Nachrichten erneut verarbeiten (nur Kommandozeile, z. B. cron) |
| `lora_funktionen.php` | Hilfsfunktionen ohne Seiteneffekte (Unit-Tests) |

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
   - Je Logger arbeitet immer nur ein Aufruf (Sperre `lora_log/sperre_<verzeichnis>.lock`). Gleichzeitige Webhooks warten aufeinander. So ist die Prüfung über Dateigröße und letzten Zeitstempel eindeutig (SRV26-03).
   - Jede Nachricht bekommt eine Kennung aus Gerät, FPort, FCnt, Nutzdaten und `received_at`. FCnt allein reicht nicht, weil der Musterlogger den Zähler bei 16384 zurücksetzt. Kommt dieselbe Nachricht noch einmal, wird sie als „doppelt“ beantwortet und **nicht** an beelogger weitergegeben. Es entstehen also keine doppelten Zeilen und keine doppelte BEEP-Übertragung (SRV26-03/04/05). Liste: `lora_log/ids_<verzeichnis>.txt`, die letzten 5000.
6. Er schreibt alles, wofür beelogger keine Spalte hat, in `lora_zusatz.csv` im Logger-Verzeichnis:
   - RSSI und SNR des besten Gateways, Anzahl Gateways, Spreizfaktor, Frame-Zähler
   - Firmware-ID, CPU-Temperatur, zweite Innentemperatur
   - FFT-Gesamt- und Bandpegel
   - Zustandsbits, Neustart-Grund, Warnungen des Formatters
   - Ergebnis der Speicherung
   - Schlägt das Schreiben fehl, steht die Zeile im Protokoll („zusatz_fehler“) und die Antwort an TTN trägt eine Warnung (SRV26-04).
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
   - `utc_zeit` (Vorgabe `'auto'`): Zeitbasis **je Logger**. Der Eingang liest das `beelogger_log.php` des Ziel-Loggers. Enthält es das Merkmal `$BL_UTC_FAEHIG=1;` (eigene Fassung), sendet er UTC (`UTC=1`), sonst Ortszeit wie beim Original. `true` verlangt die eigene Fassung: Fehlt das Merkmal, wird die Nachricht zurückgestellt statt mit falscher Zeit gespeichert. `false` sendet immer Ortszeit.
   - Eine Datei `beelogger_zeitzone.php` im Hauptordner entscheidet **nicht** mehr über UTC. Liegt sie dort, aber ein Logger hat noch das alte `beelogger_log.php`, meldet das Protokoll „Mischinstallation“ (SRV26-07).
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

7. **Nachholen einrichten** (cron, z. B. alle 15 min):
   ```
   */15 * * * * cd /pfad/zu/beelogger/lora && php lora_nachholen.php >> lora_log/nachholen.txt 2>&1
   ```
   Ist `beelogger_log.php` nicht erreichbar oder passt die Einrichtung nicht, legt der Eingang die Nachricht in `lora_log/nachholen/` ab und antwortet TTN mit 202. Das Skript verarbeitet die Dateien später und löscht sie, sobald das Ergebnis endgültig ist. Doppelte Weitergabe verhindert die Kennung.

## Antworten an TTN

| HTTP | Ergebnis (Textanfang) | Bedeutung |
|---|---|---|
| 200 | `gespeichert` | Datensatz in `week.csv` angelegt |
| 200 | `abgelehnt` | beelogger hat geantwortet, aber nicht gespeichert (Zeit doppelt oder älter als der letzte Datensatz) |
| 200 | `doppelt` | dieselbe Nachricht wurde schon verarbeitet; beelogger nicht erneut aufgerufen |
| 200 | `ignoriert` | keine Uplink-Nachricht, unbekanntes Gerät oder ohne `decoded_payload`; steht im Protokoll |
| 202 | `zwischengespeichert` | vorübergehender Fehler (beelogger nicht erreichbar, Einrichtung passt nicht); `lora_nachholen.php` holt nach |
| 400 | | kein JSON bzw. ohne `received_at` |
| 401 | | Token falsch |
| 405 | | kein POST |
| 500 | | `lora_config.php` fehlt, oder Zwischenspeichern ist fehlgeschlagen (dann geht die Nachricht verloren; steht im Protokoll) |
| 502 | | nur wenn auch das Zwischenspeichern scheitert |

Warum 202 statt 5xx bei vorübergehenden Fehlern (SRV26-02): The Things Stack wiederholt einen einzelnen Webhook nach meinem Stand nicht. Gehäufte Fehlerantworten können den Webhook dagegen abschalten. Die Wiederholung übernimmt deshalb der Server selbst. **[P]** Das Verhalten von TTS bei Fehlerantworten ist aus dem Quelltext abgeleitet, nicht mit TTN gemessen.

## Grenzen (bekannt)

- **Winterzeit-Umstellung:** Mit dem **Original** M.40 verwirft beelogger in der doppelten Stunde weiterhin Datensätze (Test: 2 von 7 bei 30-min-Takt), weil es die Ortszeit speichert und mit `strtotime()` zurückrechnet. Mit der **eigenen Fassung** (`server/beelogger_eigen/`, siehe [`../../docs/server-utc.md`](../../docs/server-utc.md)) übergibt der Eingang die Zeit in UTC (`UTC=1`) und alle 7 Datensätze werden gespeichert. Umschalten: `'utc_zeit'` in `lora_config.php` (`'auto'` = UTC, wenn `beelogger_zeitzone.php` im beelogger-Ordner liegt). Die Zusatzdatei hat in beiden Fällen die richtige UTC-Zeit.
- Duo, Triple usw. sind nur über die Feldzahl geprüft, nicht mit echten Unterverzeichnissen. **[P]** Beim ersten Duo-Logger nachsehen.
- Der Testserver (`php -S`) verteilt Verbindungen ungleichmäßig auf seine Arbeitsprozesse. Der Test nutzt deshalb einen zweiten Testserver für `beelogger_log.php`. Auf Apache bzw. PHP-FPM ist das nicht nötig.
- Die Sperre wirkt nur zwischen Aufrufen des LoRa-Eingangs. Schreibt ein anderer Weg gleichzeitig in dasselbe Logger-Verzeichnis (z. B. ein WLAN-Logger mit demselben Verzeichnis), gilt die Speicherprüfung nicht sicher.
- Fällt der Server mitten in einer Verarbeitung aus (nach dem Speichern, vor dem Merken der Kennung), wird eine Wiederholung derselben Nachricht von beelogger als „abgelehnt“ erkannt (gleicher Zeitstempel). Eine doppelte Zeile entsteht nicht; eine zweite BEEP-Übertragung ist mit der eigenen Fassung ebenfalls ausgeschlossen.

## Tests

- `php tests/server/test_lora_funktionen.php`: Hilfsfunktionen (59 Tests)
- `bash tests/server/test_lora_eingang.sh`: Ende-zu-Ende mit dem echten Formatter und zwei PHP-Testservern. `VARIANTE=eigen` (Vorgabe, 73 Prüfungen) oder `VARIANTE=original` (56 Prüfungen, weist den Winterzeit-Fehler des Originals nach). Enthalten:
  - Funkformat v1/v2, Zeitquelle, Fehlerfälle, Winterzeit-Nacht
  - doppelte und gleichzeitige Nachrichten (4 parallele Webhooks), Nachholen nach Ausfall
  - Zeitbasis-Matrix: altes/eigenes `beelogger_log.php` × Merkmal im Hauptordner × `utc_zeit`
  - BEEP über eine lokale Nachbildung (nur `eigen`): genau eine Übertragung je gespeichertem Datensatz, keine bei „abgelehnt“, „doppelt“ oder Platzhalter-ID
  - Grafik im Browser mit Playwright; mit `BROWSER_PFLICHT=1` (CI) schlägt der Test fehl, wenn Playwright fehlt
