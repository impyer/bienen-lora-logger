# Refactoring R1 – synthetische Umweltmessdaten durch den realen Softwarestack

**Prüfdatum:** 17.10.2026 UTC · **Autor:** Codex · **Klasse:** D2 ·
**Nachweise:** T0/T1/T2/T3, Entwicklung/G1; keine Produktionsfreigabe.

Ausgangsbasis des Auftrags: `034c9e1d31612679dcc3cc15155208b9c0c82e72`.
R0/angenommene ADR-0004: `9e071acc4ff7ea01be79ea76a879ce4737a8856c`,
[PR #21](https://github.com/impyer/bienen-lora-logger/pull/21).
Der Betreiber hat R0 und den R1-Start mit synthetischen CSV am 17.10.2026 in
der Projektunterhaltung ausdrücklich freigegeben.

**Geprüfter Implementierungsstand:**
`d30e7da37a816eb8e7cb7cddac9d602f4028b82b` auf
`refactor/r1-umweltdaten-20261017`; davor getrennte Commits für Backend
`c1dfbf8` und Browser `f94ed83`. Browser-E2E und Hostregression prüften
`f94ed83e00cb658189f1af8b82d29469b9d296b6`; `d30e7da` ergänzt ausschließlich
Container-/CI-Konfiguration und den Containerprüfer. Der abschließende
22er-Datenbanklauf und Containerneustart prüften dessen unveränderten Codebaum.
Spätere Dokumentationscommits verändern diese Anwendungsergebnisse nicht.

**Ergänzter Prüfstand:** `b33e9da5d40957a314a9d107f6f467362cc444ea`.
Er erweitert nur Tests und den Ignore-Schutz lokaler Quellkonfigurationen;
Anwendung und SQL bleiben auf obigem Stand. Der strengere A-01-Browserlauf
prüft auch Dubletten, ungültige Wetterzahlen/-zeitstempel und unbekannte Spalten
durch den gesamten Stack. Er bestand lokal mit **29 769 ms** Aktualisierungszeit.
Commit `eac8ef83fddd67a34ce24a98f7e61a67f44967ec` korrigiert zuvor ausschließlich
die Test-DSN für passwortgeschützte PostgreSQL-Verbindungen.

Aktuelle Befundstände ausschließlich im [Register](befunde.md#refactoring-webplattform-r0).
Architekturentscheidung: [ADR-0004](../entwicklung/entscheidungen/ADR-0004-umwelt-datenstrecke.md).
Betriebs-/Abnahmefolge: [R1-Anleitung](../entwicklung/umwelt-r1.md).

## Prüfling und reproduzierbares Ausgangsversagen

R0 dokumentiert die ursprüngliche Umwelt-404, fehlendes ECharts und SQL-Proben
zur Kanalgültigkeit bzw. rückwirkenden Faktoränderung. Zusätzlich schlug der
neue Regressionstest für eine korrigierte Ereigniszeit zunächst fehl: zwei
aktuelle Zeitpunkte statt eines. Ereignisrevisionen beheben das und erhalten
die ursprünglichen Records. Keine echte Sensormessung wurde erfunden.

Implementiert wurden zwei reine CSV-Adapter, atomarer revisionsbasierter Import,
additive explizite Migration 003, gemeinsame Sitzung und Standrechte,
begrenzte FastAPI-Lesepfade und lokale ECharts 5.6.0 auf der Umweltseite.
Das optionale Compose-Overlay mountet exakt zwei Dateien nur lesend und startet
einen separaten Watcher. Vorhandene PHP-Empfänger und Stockkartentabellen bleiben
erhalten; die Stockkarte wurde nicht fachlich neu implementiert.

## Umgebung und Grenzen des Aufbaus

- Debian 13, Python 3.12.14, Node.js 24.19, Playwright 1.56.1, tatsächlich
  **Debian Chromium 155.0.8059.79** (kein behaupteter Playwright-Standardbrowser).
- Host: PostgreSQL 17.11 an privatem Unix-Socket, psycopg 3.2.13, FastAPI 0.143.3,
  Uvicorn 0.54.0, Caddy 2.6.2. Exakte Python-Auflösung im eingecheckten Lockfile.
- Container: Docker 28.4, Compose 2.40.3, PostgreSQL **16.15**, Caddy **2.11.7**,
  App nicht als root; Basisimages über SHA256-Digests festgelegt.
- Nur eigens angelegte Datenbank `bienen_test` bzw. neue Compose-Projekte
  `bienenlogger-r1-*`; keine Verbindung zur ThinkStation, BEEP oder echten TTN-Daten.
- Echtes lokales HTTPS: Python validiert die Test-CA, Chromium vertraut nur den
  für diesen Lauf ermittelten CA-/Intermediate-SPKI-Pins. Kein allgemeines
  `ignoreHTTPSErrors`; Container-Curl verwendet `--cacert`.
- Docker-BuildKit konnte in dieser Cloud PyPI nicht auflösen. Für den lokalen
  Containerbeleg wurden dieselben exakt gelockten Wheels mit TLS-geprüftem
  Host-pip heruntergeladen und über einen zusätzlichen Build-Kontext offline
  eingebunden. Das temporäre Dockerfile verändert nur diesen Installationsweg.
  Der eingecheckte normale Online-Dockerbuild ist Aufgabe der neuen CI; sein
  CI-Ergebnis muss separat am PR geprüft werden. TLS wurde nicht abgeschaltet.

## Tatsächlich ausgeführte Prüfungen

| Prüfung / Bezug | Soll und beobachtetes Ist | Ergebnis |
|---|---|---|
| Parser, A-01/A-02/A-08 | 7 Tests: Semikolon/BOM, fehlend vs. 0, negativ/ungültig, unbekannte Spalten, UTC/DST, kaputte/partielle Zeilen und Header | **PASS 7/7** |
| Import und Migration, A-08/A-09 | 10 Tests mit echter DB: Read-only-Datei bleibt bytegleich, Wiederholung/Append/Rotation/Backfill, Konflikt/Revisionskorrektur einschließlich Zeitkorrektur, Fehlertransaktion/Checkpoint, Dateirechte/Wiederanlauf, gültige Zuordnung, Kanalschutz, idempotente Migration und fehlende Basis ohne Rebuild | **PASS 10/10** |
| Authentifizierte API, A-01/A-02/A-05/A-08 | 5 Tests mit echter DB: Cookie-Pfadwechsel, Werte/Metadaten/Provenienz/null, begrenzte Fenster/Cursor, fremde Stände und aktiver Rechteentzug, OpenAPI/CSRF/Logout | **PASS 5/5** |
| Vollständiger Software-E2E, A-01/A-02/A-04/A-05 | Echte CSV → laufender Watcher → PostgreSQL → HTTPS/FastAPI → ECharts. Wetter −2,5 °C, Dublette entfernt, ungültige Zahl als null mit QC, ungültige Zeit abgewiesen, unbekannte Spalte roh erhalten; Einheiten/Regenzählersemantik; drei Bodentiefen und Null-Lücke; Standwechsel/Leerstand; gemeinsame Sitzung/Volkwechsel; Mobilansicht; Logout/Login; Rechteentzug und Entfernung alter Kurve | **PASS**, einschließlich ergänztem A-01-Lauf |
| Reguläre Aktualisierung, A-04 | Angehängte synthetische CSV-Zeile ohne manuell ausgelösten Import; Watcher 5 s, normale UI-Abfrage 30 s; danach erneuter Import ohne neue Revision | **PASS: 29 631 ms**, ergänzter A-01-Lauf **29 769 ms** |
| Backup/Restore vor Migration, A-09 | Vorhandene synthetische Stockkartenrevision gesichert, `pg_restore` in neue zusätzliche DB, vollständiges Revisions-JSON identisch; Migration zweimal, ursprüngliches JSON unverändert | **PASS** |
| Container, A-09 | Frisches eigenes Projekt, genau zwei RO-Dateimounts, authentifiziertes CA-geprüftes HTTPS; kompletter Neustart von DB/App/Proxy/Importer, Werte/Zertifikat/Sitzung erhalten | **PASS: 15 aktuelle Werte** |
| Bestehende Stockkarte | Persistenz 24 Prüfungen, vorhandene FastAPI-Verhaltensprüfung, Sitzungs-API 61 Prüfungen mit echter DB | **PASS** |
| Bestehende Browserprüfungen | Claude-UI, native Stockkarte, Katalog und Server-Stockkarte, jeweils modulare und erzeugte Einzeldatei | **PASS: 4 Suiten** |
| Vorhandene Node-Domäne | Taxonomie 14, Werteprüfung 14, Katalogverwaltung 19 | **PASS: 47 Prüfungen** |
| Host-/PHP-Gesamtsuite | `SERVER_UHR='2026-10-09 05:00:00' BROWSER_PFLICHT=1 bash tests/alle_tests_linux.sh`: Zeit 70, FFT 32, Funkformat 303, Formatter 14/14/12, PHP 66/41, LoRa 82, Wetter 29 sowie Simulationen | **PASS**, keine gemeldeten Skips |
| Reproduktion/Syntax | Lokale ECharts aus npm-Lock reproduziert, Offline-HTML aus Quellen erzeugt, JS/Python/Shell geprüft, `git diff --check` | **PASS** |
| Echte Umweltmessdaten / physischer Laptop im Heimnetz | Betreiberfachprüfung, Sondenkabel-/Zeitsemantik und normale LAN-Konfiguration | **NICHT GELAUFEN** |
| Zielhardware / HiL / Feld / vollständige BEEP-Parität / Last-Dauertest | Nicht Gegenstand dieser Softwarestrecke | **NICHT GELAUFEN** |

Die TestClient-Suiten melden eine Starlette-Deprecation zur Verwendung von httpx;
die Prüfungen bestehen. Dies ist kein Beleg für langfristige Dependency-Kompatibilität.
Die vorhandenen vier Browserprüfer enthalten weiter simulierte API-Antworten;
sie sind zusätzliche Regression und ersetzen den neuen vollständigen E2E nicht.

## Unabhängige CI und Fehlerkorrektur

Der erste [R1-CI-Lauf](https://github.com/impyer/bienen-lora-logger/actions/runs/39032205767)
war **FAIL**: Die fünf neuen API-Tests hatten beim Erzeugen separater Verbindungen
`ConnectionInfo.dsn` verwendet. psycopg entfernt daraus bewusst das Passwort.
Der lokale Unix-Socket erlaubte Trust-Authentifizierung; der CI-Server verlangte
das konfigurierte Passwort. Der Browser-Schritt war in diesem Lauf **SKIP**,
der normale Online-Containerbuild mit Neustart bereits **PASS**.
Der Diagnosewiederholungslauf 39032398678 bestätigte denselben Testfehler.

Nach Korrektur wird die ursprüngliche, vom Fixture auf Datenbanknamen geprüfte
Testkonfiguration wiederverwendet. Ein zusätzlicher lokaler, passwortgeschützter
PostgreSQL-16.15-Container bestätigte **22/22 PASS**. Das lokale Protokoll
`/workspace/bienen-env/logs/r1-pg16-unit-final.log` enthält diesen Nachweis.
Keine Anwendungsauthentifizierung wurde dafür gelockert.

Auf `eac8ef8` bestehen [Umwelt-CI 39032527591](https://github.com/impyer/bienen-lora-logger/actions/runs/39032527591)
**2/2 Jobs** (DB/API/echter Browser und normaler Online-Containerbuild/Neustart)
und [Stockkarten-CI 39032527569](https://github.com/impyer/bienen-lora-logger/actions/runs/39032527569)
**4/4 Jobs**. Die CI verwendet Python 3.12.15, Node 22, PostgreSQL 16 und den
offiziellen Playwright-Chromium-Download. Der danach ergänzte A-01-Prüfer ist
oben mit seinem eigenen lokalen SHA/Nachweis abgegrenzt.

Die CI `umwelt-r1` wiederholt Parser/DB/API, Browser-E2E und den normalen
Containerbuild mit Neustart. Diese Definition ist kein vorweggenommenes CI-PASS.
Verbindlich sind die tatsächlichen Check-Ergebnisse am zugehörigen R1-PR.

## Belege und Rückfall

Cloud-Belege außerhalb von Git: `/workspace/bienen-env/logs/r1-final-db-api.log`,
`r1-stockkarte-db.log`, `r1-regression-host.log`, `r1-browser-regression.log`,
`r1-node-domain.log`, `r1-container-final-build.log`, `r1-container-final.log`.
Ergebnis/Screenshot des ursprünglichen realen Browserlaufs:
`/workspace/bienen-env/r1-e2e-final/result.json` und `environment-mobile.png`;
erweiterter A-01-Lauf: `/workspace/bienen-env/r1-e2e-acceptance-final/result.json`
und `environment-mobile.png`, Protokoll `logs/r1-e2e-acceptance-final.log`.
Die zugehörigen getrennten Restore-Datenbanken heißen
`bienen_r1_restore_29b9d88dc3` und `bienen_r1_restore_0274cb29d7`.
Alle Cloud-Testcontainer sind gestoppt; ihre Volumes und synthetischen Quellen
bleiben erhalten. Ein erster Cloud-Initialisierungsversuch scheiterte an lokalen
restriktiven Leserechten der öffentlichen Init-Dateien. Dieses unvollständige
Volume wurde erhalten; neue isolierte Projekte mit lesbaren öffentlichen
Init-Dateien bestanden. Kein produktiver Bestand wurde neu initialisiert.

Rückfall und manuelle Abnahme stehen in der R1-Anleitung. Keine automatische
Migration beim App-Start, keine Down-Migration, kein `down -v`, kein Merge und
kein ThinkStation-Deployment. Vor weiterem Gate ist Betreiberprüfung notwendig.
Eine fachlich vollständige, echt gespeiste Plattform wird hier nicht behauptet.
