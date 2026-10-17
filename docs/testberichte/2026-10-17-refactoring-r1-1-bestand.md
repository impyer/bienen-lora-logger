# R1.1 – technische Bestandsaufnahme und rote Regressionen

**Datum:** 17.10.2026, Europe/Berlin. **Klasse:** D2, R1.1/G1; T0/T1/T2.
**Anwendung:** unverändert `91284796ab25e78d8a9efc9dd790820faed2f3e7`.
**Neue Fehlertests:** `be66748509f4f2925e81979db97eba74aed214d5`.
**Branch:** `refactor/r1-1-umweltarchive-20261017`, Basis aktueller R1-HEAD;
Working Tree vor Beginn sauber, `git pull --ff-only` ohne neue Änderungen.
`origin/main`: `66a3ba26b49a7ccd53d94436708f6bd124b3e4da` (keine Arbeitsbasis).

Quellen: vollständiger [R1.1-Auftrag](https://github.com/impyer/bienen-lora-logger/blob/docs/codex-r1-1-20261017/docs/entwicklung/CODEX-AUFTRAG-R1-1-2026-10-17.md),
R0-/R1-Berichte, ADR-0004, Entwicklungsregelwerk 1.1. Aktueller Befundstand
ausschließlich im [Register](befunde.md#refactoring-r11).

## Tatsächliche Beobachtungen

| ID / Stelle | Beobachtung und Auswirkung |
|---|---|
| R1.1-01, `prototype/claude-ui/umwelt.js:refresh` | Erste Antwort mit 5000 Punkten, `next_cursor` wird ignoriert. Auch bei erfolgreichem Poll fehlen die jüngsten Werte eines langen Fensters. Kanalwahl filtert erst nach dem Download. |
| R1.1-02, `umwelt/ingest.py:register_source`, Compose-Overlay | Nur reguläre einzelne Datei erlaubt; Monatsmuster/Verzeichnisregistrierung fehlt. Ein Dateimount kann bei Rename an altem Inode hängen. |
| R1.1-03 | Sämtliche Nachweise synthetisch, keine echten Sensor-/LAN-Dateien autorisiert. Kein neuer Feldnachweis in diesem Auftrag. |
| R1.1-04, `_read_source`, `_import_source` | Vollständiger Byte-/Text-/Recordbestand bis 32 MiB; zahlreiche einzelne SQL-Abfragen pro Record/Kanal. Replays können bekannte alte Raw-Varianten wieder als Ereignis aktivieren. Jahresprofil noch nicht gemessen. |
| R1.1-05, `umwelt/cli.py` | Explizite IDs verhindern Raterei; Inventur und Archivdiagnose fehlen. Diese Schutzgrenze erhalten und benutzbar machen. |
| R1.1-06, `compose.umwelt.yaml` | Importer erbt App-Konfiguration einschließlich administrativer DSN/Sitzungsschlüssel. Separater eingeschränkter Betrieb fehlt. |

Erhalten werden reine Profile/Parser, UTC/null-Vertrag, kanonische Stammdaten,
Revisionsschutz, explizite Standrechte und bewährte Stockkartenbausteine.
Kein Eingriff in Receiver, reale Quelldateien, BEEP, Firmware oder ThinkStation.

## Ausgeführte Tests auf der unveränderten R1-Anwendung

Debian 13, Python 3.12.14, PostgreSQL 17.11 am privaten Unix-Socket, Node 24.19,
Playwright 1.56.1/Debian Chromium 155, Caddy 2.6.2. Ausschließlich die selbst
erzeugte Datenbank `bienen_test`, temporäre Loopback-Prozesse und synthetische CSV.

| Prüfung | Ergebnis / Grenze |
|---|---|
| Vorhandene Umwelt-Tests vor Hinzufügen des Archivtests | **PASS 22/22** |
| Stockkartenpersistenz, vorhandene FastAPI-Verhaltensprüfung, Sitzungs-API | **PASS 24 Prüfungen / API ohne Gesamtzählung / 61 Prüfungen** |
| Neue Archivregistrierung mit explizitem Monatsmuster | **FAIL:** `register_source(..., pattern=...)` nicht unterstützt; neuer Monat kann nicht als Archivquelle registriert werden. Das ist eine neue Opt-in-Schnittstelle, keine Forderung nach unautorisiertem Scannen neben einer alten Einzeldatei. |
| Echter HTTPS-/DB-/ECharts-Langzeittest, 5040 Soil-Records über 35 Tage, fünf Kanäle = 25200 Bodenwerte plus Wetter | **FAIL:** nach Wahl „7 Tage“ fehlt Originalwert 77.125 des jüngsten Records; ECharts enthält nur 3000 Bodentemperaturpunkte aus der global begrenzten ersten Seite. Kein HTTP-Mock. |
| 30 Tage/Saison im neuen Fehlertest | **NICHT GELAUFEN:** Test bricht am ersten nachgewiesenen 7-Tage-Fehler ab. |
| R11-A01–A10 nach Korrektur | **NICHT GELAUFEN** in dieser Bestandsaufnahme; gehören in den späteren Abnahmebericht. |
| R11-A11 echte Dateien/ThinkStation/Laptop | **NICHT GELAUFEN**, separate Betreiberabnahme. |

Reproduktion nach Aktivierung der vorbereiteten Cloud-Werkzeuge:

```sh
python3 -m unittest discover -s tests/umwelt -p 'test_archives.py' -v
python3 tests/umwelt/e2e.py --long-history --output build/r11-red-long
```

Die Skripte setzen ausschließlich die explizit benannte Wegwerf-Testdatenbank
`bienen_test` zurück. E2E sichert vorher eine synthetische Stockkartenrevision und
prüft Restore in eine neue zusätzliche DB; Prozesse werden danach beendet.
Keine bestehenden Docker-Volumes werden gelöscht oder verändert.
Cloud-Protokolle: `/workspace/bienen-env/logs/r11-baseline-db.log`,
`r11-red-archive.log`, `r11-red-long.log`; echter Browserfehler unter
`/workspace/bienen-env/r11-red-long/browser.log`.

## Korrekturplan und Entscheidungspunkt

[ADR-0005](../entwicklung/entscheidungen/ADR-0005-umweltarchive-und-langzeitreihen.md)
beschreibt begrenztes Snapshot-Paging und Min/Max-Auswahl echter Beobachtungen,
isolierte Staging-Verzeichnisse mit Monatsmustern, additive Datei-/Fundstellen-
Migration und einen eigenen eingeschränkten Importer. Sensibler Import-/DB-Teil
wird gemäß Auftrag §5 nach ausdrücklicher Zustimmung implementiert; die
unabhängige lesende Diagrammkorrektur kann währenddessen erfolgen.
