# Zwei Eingänge und einheitliche Messzeit (22.10.2026)

Änderungsklasse D2. Entscheidung PLT-01 (`docs/entwicklung/entscheidungen.md`), Befund PLT26-18.

## Anlass

- Philipp: Nicht jeder Sensor bekommt einen eigenen Eingang, sondern es gibt einen Umwelt-Eingang und einen Bienen-Eingang.
- Philipp: Umweltsensoren können eine Uhrzeit haben. Die erste Fassung dieses Umbaus gab dem Umwelt-Eingang fest die Empfangszeit; das war falsch.

## Geprüfte Quellen zur Gerätezeit

| Gerät | Ergebnis | Quelle |
|---|---|---|
| SenseCAP S2120 | Kein Datenblock (01–06, 10, 4A–4C) enthält einen Zeitstempel. Ob die Firmware Werte mit Zeitstempel nachsendet, ist nicht belegt [P] | offizieller Decoder `Seeed-Solution/SenseCAP-Decoder`, `S2120/TTN/SenseCAP_S2120_TTN_Decoder.js`, geladen 22.10.2026 |
| LSN50v2-D23 | Normaler Uplink wie LSN50v2 MOD1, ohne Zeitstempel. Dragino-Geräte stellen die Uhr per DeviceTimeReq (SYNCMOD) und senden gespeicherte Werte mit Unix-Zeitstempel nach (Datalog, dokumentiert für LSN50v2-S31 und D2x-LB/LS). Für die vorhandene LSN50v2-D23 nicht belegt [P] | docs.dragino.com, Seiten LSN50v2-D20-D22-D23, LSN50v2-S31, D20-D22-D23-LB |

## Änderungen

- `server/lora/` → `server/bienen/` (`bienen_eingang.php`, Protokoll `bienen_log/`). Geräte ohne beelogger-Eintrag: 200 „protokolliert, ohne beelogger-Weiterleitung“ statt „ignoriert“; der Uplink steht im Rohprotokoll und kommt in die Datenbank.
- `server/wetter/` entfällt. Neu `server/umwelt/umwelt_eingang.php`: kennt keine Geräte und Felder, schreibt nur das Rohprotokoll `umwelt_log/`; scheitert es bei einem Uplink mit Messwerten, Antwort 500 (einziger Speicher).
- Importer: `--bienen`, `--umwelt`; Altbestand `--lora`, `--wetter`. Eine Zeitregel für alle (Vertrag in `server/datenbank/README.md`): Gerätezeit bei `Status.zeit_ok`, höchstens 30 s vor und 30 Tage nach dem Empfang (`--max-alter-tage`), sonst Empfangszeit. Liste `Eintraege` für mehrere Messungen je Uplink.
- Synthetische Daten und Plattform-Konfiguration auf `bienen_log`/`umwelt_log`.

## Tests (lokal, T1/T2)

| Test | Ergebnis |
|---|---|
| `test_eingang_funktionen.php` | 57/57 |
| `test_bienen_funktionen.php` | 54/54 |
| `test_umwelt_funktionen.php` (neu) | 23/23 |
| `test_bienen_eingang.sh` eigen / original (ohne libfaketime, ohne Browserpflicht) | 82/82, 65/65 |
| `test_umwelt_eingang.sh` (neu) | 23/23 |
| `test_importer.py` (Europe/Berlin, UTC, America/New_York) | 16/16 je Zeitzone |
| `test_schema.py` | 24/24 |
| `test_plattform.py`, `test_verwaltung.py`, `test_stockkarte.py`, `test_diagramm.mjs` | 35/35, 14/14, 13/13, 26/26 |

Gegenproben: Importer mit fester Empfangszeit für `umwelt_log` → Fall „Zwei Eingänge“ schlägt fehl; ohne Auswertung von `Eintraege` → 2 Fälle schlagen fehl.

Nicht gelaufen: Browsertest (Playwright), libfaketime-Varianten, Mutationstest – in der CI bzw. offen.

## Bewusste Folgen und Grenzen

- Die 900-s-Plausibilitätsgrenze des Importers entfällt; innerhalb von 30 Tagen erkennt der Importer eine falsch gehende Uhr nur noch über `zeit_ok`. Der Altfall „Uhr weit daneben“ im Test liegt jetzt bei 31 Tagen.
- Einträge älter als 30 Tage bekommen die Empfangszeit; mehrere davon in einem Uplink kollidieren, nur der erste wird Messwert (Bericht „belegt“), die Rohnachricht bleibt vollständig.
- Die S2120-CSV je Stand und `staende.json` entfallen; die Zuordnung zum Stand steht nur in der Datenbank.
- Auf dem Produktivserver laufen noch die alten Eingänge. Umstellung der TTN-Webhooks und einmaliger Import des Altbestands sind Teil der Inbetriebnahme.
