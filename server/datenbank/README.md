# Datenbank (PostgreSQL)

Schema 0.4 der Bienen-Plattform nach [`docs/architektur/konzept-plattform-v02.md`](../../docs/architektur/konzept-plattform-v02.md), Abschnitt 5.

**Status:** Entwurf. Schema 0.3 getestet auf einer Testinstanz (PostgreSQL 16.15, T1); seit 20.10.2026 laufen Schema und Importer bei jedem CI-Lauf (Job `datenbank` in `.github/workflows/tests.yml`: Dienst `postgres:16`, `test_schema.py` in den Sitzungszeitzonen Europe/Berlin, UTC und America/New_York, `test_importer.py` in Europe/Berlin und UTC). Der Importer (Schema 0.4, `import_position`) ist nur über diese Tests geprüft, nicht gegen echte Protokolle. Noch nicht auf der ThinkStation eingespielt, keine Produktivdaten.

| Datei | Zweck |
|---|---|
| `schema.sql` | Legt das Schema `bienen` neu an. **Löscht ein vorhandenes Schema `bienen` samt Daten** (`DROP SCHEMA … CASCADE`), deshalb nur auf einer leeren Datenbank verwenden |
| `importer.py` | Liest die Rohprotokolle der Eingänge (`lora_log/`, `wetter_log/`) in die Datenbank, siehe unten |
| `../../tests/datenbank/test_importer.py` | 4 Hosttests ohne Datenbank, 9 Datenbankfälle (Grundfall, fehlerhafte Einzelzeilen, K-06, K-09, R-4, R-5 Doppelimport, Zeitqualität, Kanalzeitraum, halbe Zeile) |
| `../../tests/datenbank/test_schema.py` | 24 Prüffälle (u. a. ER-01, ER-03–05, ER-07, ER-12, K-01, K-02, K-04–06, K-10, HB-01–04, HB-09, Zeitumstellung, Zeitgenauigkeit, Berechnungsversion) |

## Aufbau

| Modul | Tabellen |
|---|---|
| A – Stammdaten | `stand`, `volk`, `beute`, `beute_konfiguration`, `belegung`, `aufstellung`, `volk_ereignis`, `volk_ereignis_teil`, `koenigin`, `koenigin_volk`, `extern_ref` |
| B – Stockkarte | `merkmal`, `checkliste`, `checkliste_version`, `checkliste_merkmal`, `durchsicht`, `durchsicht_wert`, `massnahme`, `varroa_messung`, `aufgabe`, `anhang` |
| C – Messdaten | `messgroesse`, `geraet`, `geraet_zuordnung`, `messstelle`, `kanal`, `rohnachricht`, `messwert`, `quellfeld_ohne_kanal`, `import_position` |
| Auswertung | `berechnung` (Versionen der Berechnungen) |
| Sichten | `messwert_bezug`, `gewicht_tagesreferenz`, `gewicht_tagesbilanz`, `varroa_pro_tag`, `pruefung_geraet_zuordnung`; Funktion `stand_von_volk(volk, zeit)` |

**Regeln, die die Datenbank selbst durchsetzt:**
- Beute = Volk, 1:1 zu jedem Zeitpunkt.
- Höchstens ein Stockmesssystem je Volk zur selben Zeit.
- Ein Gerät nie an zwei Zielen gleichzeitig.
- Keine zwei Deutungen desselben Quellfelds im selben Zeitraum.
- Zeiträume immer `[von, bis)`.

## Test lokal

```bash
pip install "psycopg[binary]"
# leere Testdatenbank mit Erweiterung btree_gist (im Paket postgresql-contrib)
BIENEN_TEST_DSN="host=localhost dbname=bienen_test user=..." python3 tests/datenbank/test_schema.py
BIENEN_TEST_DSN="host=localhost dbname=bienen_test user=..." python3 tests/datenbank/test_importer.py
```

Beide Tests laden `schema.sql` und **löschen dabei das Schema `bienen`** der Testdatenbank. Ohne erreichbare Datenbank meldet `test_importer.py` die Datenbankfälle als NICHT GELAUFEN (Rückgabe 2). In der CI laufen beide im Job `datenbank` von `tests.yml` gegen PostgreSQL 16 (siehe Status).

Zeitangaben beim Schreiben immer mit Zeitzone angeben. Die Tests laufen mit den Sitzungszeitzonen Europe/Berlin, UTC und America/New_York gleich.

**Änderungen 0.3 (15.10.2026, Review Issue #11):** `zeitgenauigkeit` in Durchsicht, Maßnahme und Varroa-Messung; Kalibrierangaben am Kanal; Tabelle `berechnung` und Versionsangabe in den Sichten; Prüfsicht für vergessene Waagenzuordnungen. Bewertung: `docs/testberichte/2026-10-15-plattform-review-issue11.md`.

## Importer (`importer.py`)

Konzept 0.2 §10 Schritt 4; erfüllt im Entwurf R-5 und den Erkennungsteil von R-4 aus §4a (Befund PLT26-02), Akzeptanzfälle K-06 und K-09.

```bash
pip install "psycopg[binary]"          # psycopg ≥ 3.1
BIENEN_DSN="dbname=bienen user=bienen" python3 server/datenbank/importer.py     --lora /var/www/html/lora/lora_log --wetter /var/www/html/wetter/wetter_log
```

Gedacht für einen systemd-Timer oder cron alle 1–5 min. Ein zweiter gleichzeitiger Lauf beendet sich sofort (`pg_try_advisory_lock`). Rückgabe 0 = alles gelesen, 1 = eine Datei nicht lesbar oder umgeschrieben, 2 = Aufruf oder Verbindung.

**Was übernommen wird:**

| Protokollzeile | Ergebnis |
|---|---|
| `"art": "uplink"` mit `id`, Herkunft (`geraet` bzw. `station`), `nachricht` mit Empfangszeit | `rohnachricht`: Kennung `id`, Gerät, Empfangszeit (µs), Gerätezeit `Messzeit_unix` falls gesendet, Datei (`lora_log/2026-10.jsonl`), Zeilennummer, SHA-256 der Protokollzeile ohne Zeilenende. Der Inhalt bleibt in der Datei |
| Zahlenfeld aus `decoded_payload` mit gültigem `kanal` (Gerät, Quellfeld, Zeitraum enthält die Messzeit) | `messwert` mit dem Rohwert; `faktor`/`versatz` rechnet die Sicht `messwert_bezug` |
| Zahlenfeld ohne Kanal | kein Messwert, nur `quellfeld_ohne_kanal` (erste/letzte Zeit, Anzahl) – Anzeige „unbenannt“ (K-06) |
| andere Arten (`ergebnis`, `fehler`, `warnung`, `nachgeholt` …) | übersprungen, gezählt |
| kein JSON, Uplink ohne Kennung/Herkunft/Empfangszeit | übersprungen, als ungültig gezählt |
| Zeile, die sich nicht speichern lässt (z. B. NUL-Zeichen im Text, zu tief verschachteltes JSON) | eigener Sicherungspunkt je Zeile: übersprungen, mit `Datei:Zeile` im Bericht; die Datei läuft weiter. Gerätezeit außerhalb 1970–9999 gilt als nicht gesendet. Verbindungs- und Serverfehler brechen den Lauf dagegen ab, ohne die Position zu verschieben |

- **Quellfelder:** verschachtelte Felder mit Punkt (`Status.zeit_ok`), Listen mit Index (`FFT_Baender_dB[0]`), `true`/`false` als 1/0; Texte (z. B. `Messzeit`) werden nicht übernommen.
- **Messzeit:** wie `le_messzeit()` im LoRa-Eingang – Gerätezeit (`zeitqualitaet = 'geraet'`), wenn `Status.zeit_ok` und höchstens `--max-zeitabweichung` (Vorgabe 900 s wie `lora_config.beispiel.php`) vor dem Empfang, sonst Empfangszeit auf die Sekunde (`'empfang'`). Wetter immer Empfangszeit. Wer `max_zeitabweichung_s` im Eingang ändert, muss den Wert hier gleich setzen.
- **Unbekannte Geräte** werden angelegt (`lora_log`: Art `sonstiges`, `wetter_log`: `wetter`) und im Bericht genannt; Art und Kanäle danach in den Stammdaten pflegen. So geht keine Rohnachricht verloren.

**Wiederholbarkeit (R-5, K-09):**
- `import_position` speichert je Datei die gelesenen Bytes, Zeilen und die SHA-256 dieser Bytes. Jeder Lauf liest ab dort weiter; Daten und Position werden je Datei in einer Transaktion geschrieben.
- Eine schon vorhandene Kennung wird samt ihren Messwerten verworfen (doppelte TTN-Zustellung, Neulesen). Löscht man `import_position`, liest der Importer alles neu und die Datenbank bleibt gleich. Nach einem Ausfall der Datenbank holt der nächste Lauf alle Zeilen nach.
- Eine unvollständige letzte Zeile (Eingang schreibt gerade) bleibt für den nächsten Lauf liegen.
- Hat sich der schon gelesene Anfang einer Datei geändert, wird sie nicht weiter gelesen (Fehler im Bericht, Rückgabe 1); die anderen Dateien laufen weiter (R-4: Monatsdateien nur anhängen). Danach prüfen, was die Datei verändert hat; erst dann die Zeile in `import_position` löschen.
- Belegt ein anderer Wert schon `(kanal, zeit)`, bleibt der erste (gezählt als „belegt“).

**Nachtragen (`--nachtragen [--geraet NAME]`):**
- Werte, die vor dem Anlegen eines Kanals ankamen, stehen nur in `quellfeld_ohne_kanal`.
- Der Importer liest dafür die schon übernommenen Rohnachrichten erneut aus ihrer Protokollzeile, prüft die SHA-256 gegen `rohnachricht.sha256` und legt fehlende Messwerte an.
- Vorhandene Messwerte bleiben unverändert; eine abweichende Zeile wird gemeldet und übersprungen.
- Die Verwaltung der Plattform ruft dasselbe auf („Werte nachtragen“).

**Grenzen:** Prüfsumme je abgeschlossenem Monat (R-4) und Sicherung der Rohprotokolle (R-6) sind nicht Teil des Importers. Eingänge für BEEP Base und Bodensonde gibt es noch nicht. Kein Lauf gegen echte Protokolle oder auf der ThinkStation.
