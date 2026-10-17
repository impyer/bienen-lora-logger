# R1.1: vollständige Umwelt-Zeitreihen und sichere Monatsarchive

**Datum:** 17.10.2026. **Klasse/Gate:** D2, T0/T1/T2/T3, G1-Entwicklungsstand.
Basis: R1 `91284796ab25e78d8a9efc9dd790820faed2f3e7` aus PR #22,
vor Beginn und erneut per `git ls-remote` bestätigt. Separater Branch
`refactor/r1-1-umweltarchive-20261017`, vorgesehene PR-Basis
`refactor/r1-umweltdaten-20261017`.

Der Betreiber hat ADR-0005 am 17.10.2026 mit „Entwurf für synthetische Tests
freigeben“ angenommen. Ausschließlich selbst erzeugte synthetische Dateien und
selbst angelegte Cloud-/CI-Testdatenbanken; keine echte Quelle, ThinkStation,
Produktivdatei, bestehende R1-Docker-Volumes oder laufende Dienste verändert.
Kein Merge oder Deployment. Aktuelle Befundstände nur im
[Befundregister](befunde.md#refactoring-r11).

## Geprüfte Stände und Umgebung

| Stand | Nachweisbezug |
|---|---|
| `be66748509f4f2925e81979db97eba74aed214d5` | Neue rote Tests auf R1; [Bestandsbericht](2026-10-17-refactoring-r1-1-bestand.md) |
| `2f9cedec46d8b58d8bba2278fdade6be232835af` | Snapshot-/Verdichtungsimplementierung, später ergänzte Grenzfälle |
| `b3ff09df2acb9e838c575a6a69be31a4a25d75f3` | Streamingarchive, additive 004 und separates Import-Login |
| `9d657e2e1c4751d2ac3e3862ea00d2ee297db806` | 53 Tests, Rollen-/Inventurprüfung, Jahresprofil, Container; alte Host-/Stockkarten-/Browserregressionen |
| `d3b7970e3010bfb1c2bea805088be00268656ec3` | Kurzer und langer echter Browserlauf, finale Jahresprobe; ausschließlich E2E-DSN-Ergänzung gegenüber 9d657e2 |
| `20700cd9196251cb8fc897aa7762bab851284b65` | 53 Tests erneut; Browser mit echten Monatsverzeichnissen, 20,569 s Aktualisierung; Änderungen gegenüber d3b7970 nur Testaufbau |
| `3febaad8241e46488e26341545b0e1ab541d8510` | Reconnect-Watcher: echter Monatsarchiv-Browser, 21,057 s Aktualisierung |
| `3370f8ec7c2bc175570d24787b9b67397a390aa3` | Identische App wie 3febaad; Containerprüfung mit expliziten eigenen 172.16/12-Netzen: volle Neustarts, danach DB-Neustart bei weiterlaufendem Importer und automatisch neuer Messung |

Letzter Implementierungsstand: **`7f03834d1fa6d70595ef47e895d3ff05098e0218`**.
54/54 Umwelt-Tests PASS (24,730 s), einschließlich echter 5-s-Sperrkonkurrenz
mit Rollback und Wiederanlauf. Gegenüber 3370f8e nur Import-Timeouts und deren
Negativtest. Auf diesem Stand zusätzlich PASS:

- Echter Monatsarchiv-Browserlauf `r11-acceptance-browser`: 19,847 s bis zum
  neuen CSV-Wert im regulären 30-s-Poll (Watcher 5 s); HTTPS/CA, alle langen
  Fenster, tatsächliches Paging, mobile Ansicht und Mikrosekundenordnung.
- Neues Containerprojekt `bienenlogger-r1-r11-acceptance`: zwei RO-Verzeichnisse,
  realer eingeschränkter Login ohne App-Geheimnisse, Dump/Restore, kompletter
  Neustart mit 20 aktuellen Werten/identischen Checkpoints/Benutzer/Sitzung/CA;
  danach DB-only-Neustart und 5 zusätzliche Werte über denselben weiterlaufenden
  Watcher-Prozess. Volumes erhalten, alle Dienste gestoppt.
- Jahresprobe mit den aktuellen Messzahlen unten. Image
  `sha256:375cccff51da94e17e080b035277d438ccfa198b2d0bc987e2286ef2cb98059c`.
  Nach diesem Stand nur Dokumentation/Beispielkonfiguration geändert.

Debian GNU/Linux 13, Python 3.12.14, PostgreSQL lokal 17.11 über privaten
Unix-Socket (eigene R1.1-Instanz, Portkennung 55434, kein TCP), Container PostgreSQL
16-alpine mit gepinntem Digest, Docker 28.4.0 / Compose 2.40.3, Caddy lokal 2.6.2
und Container mit gepinntem Digest. FastAPI 0.143.3, psycopg 3.2.13, Node 24.19.0,
Playwright 1.56.1, signiertes Debian Chromium 155.0.8059.79, ECharts 5.6.0.
Python-/UI-Abhängigkeiten aus vorhandenen Locks. Die Starlette-httpx-Warnung ist
eine Deprecation, kein deaktivierter Test. Die 54er-Umwelt-Suite hat keine übersprungenen Fälle. Letzte Ergänzung: echter konkurrierender Geräte-
Advisory-Lock, 5-s-Timeout mit Rollback/Fehlerstatus und anschließendem Wiederanlauf.

Cloud-BuildKit erreicht PyPI nicht per DNS. Container mit gelocktem Dockerfile,
identischen Versionslocks und zuvor TLS-validiert heruntergeladenen Wheels als
zusätzlichem Offline-Buildkontext gebaut. **Der normale Online-Dockerfile-Build
in GitHub Actions wurde in diesem Abschnitt nicht nachgewiesen.** Workflow
um neue Tests erweitert; Remote-CI und PR-Erstellung sind unten ausdrücklich offen.

## Umsetzung und erhaltene Verträge

Neue `/api/v1/umwelt/zeitreihen`-Version 2 erzeugt eine kurze konsistente SQL-
Lesetransaktion und liefert begrenzte unveränderliche Seiten. HMAC-Cursor sind
an Benutzer/Abfrage gebunden, jedes Paging prüft das aktuelle Standrecht.
Späte Werte/Korrekturen erscheinen erst im nächsten Snapshot. Bestehende Roh-API
`/messreihen`, Sitzungen, Identitäten und unveränderliche Revisionen bleiben.
[API-Vertrag](../entwicklung/umwelt-zeitreihen-api.md) nennt Limits und Fehler.

Temperatur/geeignete kontinuierliche Größen werden durch Auswahl realer
First/Last/Min/Max-Beobachtungen reduziert, mit Null-/Lückengrenzen und QC.
Keine erfundenen Mittelwerte. Regenzähler unklarer Semantik, Windrichtung und
Status bleiben roh und können eine klare Budgetmeldung auslösen. Alle Seiten
werden geladen und geprüft; veraltete Requests werden abgebrochen. Erfolg erst
nach vollständigem Paging, tatsächliche Kanalfilter, aktuelle Quellen-/Importzeit.
Tooltip mit Europe/Berlin und Sommerzeitoffset, Gerät/Kanal, Tiefe/Position,
Einheit, Zeitbasis, QC und Verdichtungsdaten; synthetische Quellen klar markiert.
Punktzeiten behalten Mikrosekunden, die ECharts-Achse verwendet Millisekunden;
die menschliche Berlin-Zeitbeschriftung zeigt Sekunden.

004 ergänzt explizite Archivkonfiguration, Datei-Checkpoints und unveränderliche
Fundstellen. 003 bleibt bytegleich. Streaming/500er-SQL-Batches statt kompletter
Dateispeicherung in Python, Prefixprüfung bei Append, Replay bei Rotation/Kürzung,
keine Rückaktivierung bekannter alter Rohvarianten durch Backfill. Separates
Import-Login ohne App-DSN oder Sitzungsschlüssel; negative SQL-Rechteprüfungen
mit realer Verbindung und im PostgreSQL-16-Container. Inventur/Registrierung,
Upgrade, Einschränkungen und manuelle Abnahme stehen in der
[Betriebsanleitung](../entwicklung/umwelt-r1-1.md) und
[ADR-0005](../entwicklung/entscheidungen/ADR-0005-umweltarchive-und-langzeitreihen.md).

## Abnahmematrix

| Kennung | Ergebnis | Tatsächlich geprüfter Umfang |
|---|---|---|
| R11-A01 | PASS | 35 Tage, 5042 Bodenrecords/25210 Bodenpunkte plus Wetter, tatsächliche mehrseitige HTTPS-API und ECharts; 7/30 Tage einschließlich jüngstem Wert, zusätzlich Rohmodus >3000 Temperaturpunkte; keine doppelten/fehlenden Seitenübergänge |
| R11-A02 | PASS | 24 h, 7/30 Tage, Saison, frei, schneller Wechsel, leerer/anderer Stand im Browser; echte DB-Backfills während Paging; ungültige, abgelaufene/verdrängte Cursor, Neustart, fremde Sitzung, Rechteentzug und fremder Stand in DB/API-Tests |
| R11-A03 | PASS | Bekannte Temperaturminima/-maxima und Null/QC erhalten; echte Zeitlücken; Status, Windrichtung und unklarer Regenzähler bleiben roh; Units/Anzahl/Bucketmetadaten geprüft |
| R11-A04 | PASS | Boden und Wetter in Folgemonaten, Append/partielles Ende/Vervollständigung, atomarer Rename/Inode-Wechsel, Kürzung, verspäteter alter Monat, Korrektur und zweimaliger Import; Roh-/Revisions-/Fundstellenzahlen explizit geprüft |
| R11-A05 | PASS | Beschädigter Header/UTF-8, falscher Stand/Gerät/Zeit, defekte Zeilen, 64-KiB-Grenze, Rechtefehler, Symlink in Datei/Elternpfad, FIFO, Traversal, Änderung während Lesen mit Datei-Rollback und Wiederanlauf; andere Monate werden trotz Fehler weiter geprüft, Fehlerstatus bleibt sichtbar, konkurrierende Importsperre endet begrenzt |
| R11-A06 | PASS | Hash/Größe/Modus/Inode/mtime unverändert durch Import; zwei tatsächliche RO-Mounts; Kernel weist synthetischen Schreibversuch mit EROFS ab; keine Produktivbäume gemountet |
| R11-A07 | PASS | Monatliche synthetische CSV → echter 5-s-Watcher mit eingeschränktem Login → PostgreSQL → FastAPI → Caddy-HTTPS mit CA-Prüfung/SPKI-Pins → Chromium/ECharts; reale 30-s-UI-Polls, mobile 390 px, 5/20/50 cm, Null/0, Zeitqualität, Einheiten, Login/Stockkartenwechsel/Logout/Rechteentzug; keine HTTP-Mocks in diesen Nachweisen |
| R11-A08 | PASS | Vor 004 gefüllten R1-Stand gedumpt, neue separate Restore-DB mit vollständigem Inhaltsvergleich; additive 004 zweimal; Container-Dump/Restore, Neustart DB/App/Proxy/Importer, gleiche Revisionen/Checkpoints/Benutzer, authentifizierte Sitzung und CA; Wiederaufnahme des Imports zusätzlich geprüft |
| R11-A09 | PASS (lokal) | 54 Umwelt-Tests, 24 Stockkarten-Persistenztests, Stockkarten-API, 61 Sitzungsprüfungen, Host-/PHP-/Formatter-/Wetter-/LoRa-Regression und vier bisherige UI-Browsersuiten; Remote-CI NICHT GELAUFEN |
| R11-A10 | PASS (deklarierter Umfang) | 24 Monatsdateien, 365 Tage/147310658 Bytes, Jahresimport plus 48-MB-Datei/Append, idempotenter Folgelauf und begrenzte Temperatur-Jahresabfrage; konkrete Messzahlen unten, keine Produktions-/Mehrbenutzerlast |
| R11-A11 | NICHT GELAUFEN | Keine ThinkStation, kein anderer physischer Laptop, keine echten CSV/IDs/Zeitbedeutungen/Sondenbelegung freigegeben; eigene manuelle Abnahmefolge bereitgestellt |

Die reine Parser-Speicherprobe arbeitet mit mehr als 32 MiB generiertem Input
und misst unter 2 MiB tracemalloc-Peak; sie ersetzt weder Datei-/DB- noch
Browser-E2E. Die Jahres-/Containerprüfungen ergänzen genau diese echten Komponenten.

## Gemessene Jahresprobe

Stand **7f03834d1fa6d70595ef47e895d3ff05098e0218**,
`tests/umwelt/year_load.py`, frischer Ausgabeordner `r11-acceptance-year`.
12 Boden- und 12 Wetterdateien; Boden alle 15 Minuten, Wetter stündlich, Jahr
2026. 35040 + 8760 Records, unbekanntes 4096-Byte-Feld im Bodenrohrecord
absichtlich enthalten. 175200 + 87600 Messrevisionen beim Erstimport.

| Messung | Ergebnis |
|---|---:|
| Boden-Erstimport, eingeschränktes Login | 18,634 s |
| Wetter-Erstimport, eingeschränktes Login | 5,311 s |
| Unveränderter Folgelauf beider Quellen | 0,022 s |
| 8500 neue Records an Bodenarchiv, Datei danach 48007727 Bytes | 4,050 s |
| Temperatur-Jahresabfrage nach Append | 130620 Quellpunkte → 13908 Originalpunkte |
| Vollständige Antwort | 3 Seiten, 9018323 Bytes, 4,688 s |
| Python-Prozess Spitzen-RSS | 147028 KiB ≈ 144 MiB |

Python-RSS schließt DB-/Caddy-Prozesse und Browser aus; API in diesem Lasttest
über echten FastAPI-TestClient mit tatsächlicher PostgreSQL-Verbindung. Echter
HTTPS-/Browsernachweis separat mit 35 Tagen. Kein gleichzeitiger Benutzerlasttest,
keine Langzeitdauerzusage, kein 1-Minuten-Jahresprofil. API maximal 5000 Punkte je
Seite, 40000 je Snapshot, zwei Millionen Eingabepunkte, 30 Kanäle, 366 Tage;
Cache höchstens vier Snapshots/64 MiB serialisiert/120 s pro Prozess.
Importer-Dateitransaktionen begrenzen SQL-Statements auf 60 s und Sperrwartezeit
auf 5 s; 300-s-Dateibudget wird zwischen Records/I/O geprüft (laufendes Statement
kann noch bis zu seinem Timeout dauern). Ein Worker
ist Voraussetzung. Gesamtrss kann größer als das serialisierte Cachebudget sein.
Zu große Roh-/Spezialkanalabfragen werden explizit abgewiesen statt abgeschnitten.
Importlog-Aufbewahrung ist vor Dauerbetrieb noch zu planen; kein automatisches Löschen.

Die erste Jahresprobe wurde nach deutlichem Laufzeitanstieg abgebrochen. Ursache:
Text/char-Mismatch und fehlende Batchstatistik verursachten ungünstige Joinpläne.
Angeglichene Hash-/Ereignistypen, temporäre ANALYZE-Statistiken und einmalige
Konfliktzählung je Batch beheben dies im gemessenen Folgelauf. Der abgebrochene
Lauf wird nicht als PASS gezählt. Ein erster Containerlauf hatte unlesbare,
mit restriktiver Cloud-umask kopierte synthetische Fixtures; nach ausdrücklichen
Fixture-Leserechten in neuem eigenen Projekt bestanden. Ein späterer Docker-
Bridgewechsel auf 192.168.0.0/20 wurde durch die alte 172.16/12-Testfreigabe
korrekt blockiert. Die App vertraut im Docker-Modus ebenfalls nur 172.16/12;
die reine Erweiterung der Caddy-Testfreigabe auf RFC1918 reicht deshalb nicht.
Für den erfolgreichen Recovery-Test wurden explizit zwei freie eigene /28-Netze
in 172.16/12 gewählt; App-Vertrauensgrenze unverändert. Die bestehende Betreiberkonfiguration blieb unverändert. Ein erster kurzer
Browser-Regressionslauf nutzte noch die alte CLI-DSN; der Testtreiber wurde auf
das bereits geprüfte separate Login umgestellt und erneut bestanden.

## Reproduktion und Belege

Aktivierung in dieser Cloud: `/workspace/bienen-env/r11-activate.sh`, eigener
PG-Start `/workspace/bienen-env/r11-start-postgres.sh`; keine existierende
Betreiberdatenbank verwenden. Datenbanktests nacheinander:

```sh
python3 -m unittest discover -s tests/umwelt -p 'test_*.py' -v
python3 tests/umwelt/e2e.py --output build/neuer-kurzlauf
python3 tests/umwelt/e2e.py --long-history --output build/neuer-monatslauf
python3 tests/umwelt/year_load.py --output build/neues-jahr
python3 tests/datenbank/test_stockkarte_persistenz.py
python3 tests/datenbank/test_stockkarte_api.py
python3 tests/datenbank/test_stockkarte_session.py
SERVER_UHR='2026-10-09 05:00:00' BROWSER_PFLICHT=1 bash tests/alle_tests_linux.sh
node tests/server/test_claude_ui.js
node tests/server/test_native_stockkarte_browser.js
node tests/server/test_stockkarte_catalog_browser.js
node tests/server/test_stockkarte_live_browser.js
```

Containerbefehl und Backup-/Abbruch-/Rückfallfolge stehen in der Betriebsanleitung.
Alle lokalen Ergebnisse in `/workspace/bienen-env/logs/r11-*`, JSON/Screenshots
in `r11-final-small-2`, `r11-acceptance-browser`, `r11-acceptance-year` und ergänzenden
Recovery-Läufen (`r11-recovery-browser`, `logs/r11-recovery-compose-c.log`);
auch alter Einzeldatei-Modus mit separater DSN/Neustart/Wiederaufnahme PASS
(`logs/r11-legacy-compose.log`). Tatsächliche CLI-Inventur, Monatsdatei-Inspektion
und wiederholte Registrierung an den vorhandenen synthetischen IDs PASS
(`logs/r11-cli-*`).
Früheres Recovery-Image: `sha256:97666e751b411fd9a64960c9000553d7a1c7200a99e06e3fbf1a4f87629e90f1`. Diese Verzeichnisse sind **keine öffentlichen Artefakte**:
sie enthalten auch private Test-CA-Schlüssel und DB-Dumps. Der CI-Workflow
lädt ausschließlich synthetische Ergebnis-JSON, Screenshot und bereinigtes
Browserlog hoch. Keine echten Dateien oder Secretwerte in Git übernommen.

## Offene Übergabe

Git-Push ist möglich. `api.github.com` wird bereits beim CONNECT-Tunnel mit
HTTP 403 vom Netzwerkproxy abgewiesen, einschließlich anonymem öffentlichen
Read, trotz Betreiberfreigabe, gespeicherter Hostfreigabe und separatem
Berechtigungsversuch. Dies ist vor einer GitHub-Authentifizierungsprüfung;
zusätzliche Tokens wurden weder ausgelesen noch angefordert. Deshalb **R1.1-PR
noch nicht erstellt und dessen Remote-CI NICHT GELAUFEN**. PR #23 ist der
Auftrags-Dokumentationsbranch und kein Implementierungs-PR. Reviewtext:
[R1.1-PR-Vorlage](2026-10-17-refactoring-r1-1-pr.md).
Nach wirksamer Plattform-/Proxykorrektur eigenen PR gegen R1 anlegen und
CI tatsächlich prüfen; kein Merge. Ausstehend bleiben Betreiberabnahme des
fertigen Entwicklungsstands und R11-A11, R2–R5/BEEP-/Volkdaten, Produktions-
und Lastfreigabe. Keine vollständige Funktionsfähigkeit behauptet.
