# R1.1 – Stabilisierung und Abschlussprüfung, 18.10.2026

**Prüfung:** Codex/Cloud; keine unabhängige Betreiber- oder Feldabnahme.
**Klasse/Gate:** D2, T0/T1/T2/T3, G1 bleibt bis unabhängigem CI-/PR-Nachweis offen.
**Auftrag:** Betreiber-Abschlussauftrag vom 18.10.2026, T01–T10.
**Ausgangs-SHA:** `974c6c486a600c306aac7266d5fe1fbceedeaa32`, sauberer Working Tree,
`git pull --ff-only`: bereits aktuell. R1-Basis erneut per Git bestätigt:
`91284796ab25e78d8a9efc9dd790820faed2f3e7`.
Entwicklungsbranch bleibt `refactor/r1-1-umweltarchive-20261017`;
PR ausschließlich gegen `refactor/r1-umweltdaten-20261017`.

**Kein technischer Abschluss behauptet:** Implementierungs-PR und unabhängige
GitHub-CI sind durch den API-Proxy blockiert. Ein lokaler PASS ersetzt diesen
Nachweis ausdrücklich nicht. Reale ThinkStation-/Laptop-Abnahme bleibt separat.
Aktuelle Befundstände stehen nur im [Befundregister](befunde.md#r11-stabilisierung-18102026).
Historischer [R1.1-Bericht](2026-10-17-refactoring-r1-1.md) bleibt erhalten.

## Tatsächlich reproduzierte Ursachen

| Bereich | Gegenbeispiel auf dem bisherigen Stand | Korrektur / Grenze |
|---|---|---|
| Batch-/Monats-QC | Ein neuer widersprüchlicher Record jenseits einer 2er-Testbatch bzw. im Folgemonat erhält nur `quellinhalt_geaendert`; `quellkonflikt_selber_zeitpunkt` fehlt. Im selben Batch vorhanden. | Neben Batch-SHA-Konflikten vorherige Kanal-/Zeitrevision mit anderer Roh-ID berücksichtigen. Keine Änderung unveränderlicher Originale, keine Rückaktivierung bekannter älterer Varianten. |
| Parallele Zeitreihen | Zwei tatsächlich durch SQL-Lock wartende Abfragen hindern eine dritte auf 974c6c4 nicht am Aufbau eines weiteren Snapshots. | Zwei zugelassene Diagrammverarbeitungen pro App-Prozess einschließlich Paging/Response-Abschluss. Weitere Abfrage liefert 503 mit Wiederholhinweis; Slots im finally freigegeben. |
| Standardauswahl | Echter Browser zeigt 17 ausgewählte Kanäle statt der vier vorhandenen Temperaturkanäle. | Tatsächliches Register nach Messgröße Temperatur filtern, höchstens 30, kein fester Geräte-/Stand-ID-Katalog und keine erfundenen Sonden. Weitere Kanäle bleiben manuell auswählbar. |
| Poll-Zustand | Realer nächster 30-s-Poll ersetzt ECharts-Instanz/DOM und verliert Zoom/Legende. | Bestehende Gruppe/Instanz aktualisieren, Serien per stabiler Kanal-ID ersetzen, Zoom/Legende beim regulären Poll nicht überschreiben. Bewusster Auswahlwechsel/Fehler räumt alte Instanzen auf. |
| Gemeinsame Sitzungs-DB | Reale Verbindungsunterbrechung wirft im Principal einen ungefangenen OperationalError/HTTP 500 statt hilfreicher Wiederaufnahmeantwort. | Gemeinsamer enger OperationalError-Handler: 503 ohne interne Details, Retry-After 30, no-store; weder Sitzung noch Rechte/Daten werden verändert. |
| Saison | Tatsächlich gesendetes `von=2026-01-01T00:00:00Z` statt Berliner Mitternacht `2025-12-31T23:00:00Z`. | Berliner Kalenderjahr und IANA-Offset am Jahresbeginn bestimmen; API weiterhin UTC, freie Eingaben ausdrücklich UTC. |
| Staging-Verkürzung | Eine formal gültige, unerwartet auf Header gekürzte Originaldatei könnte die letzte vollständige Kopie ersetzen. | Größenabnahme kontrolliert abweisen; letzte Kopie behalten, auch kürzere legitime Korrekturen erfordern Betreiberprüfung. |
| CI-Auswahl | Allgemeiner Workflow reagiert auf PRs nur gegen main, nicht auf die vereinbarte R1-PR-Kette. | Branchfilter für R1 gezielt ergänzt; Umwelt-Workflow führt den erweiterten echten Stabilitätsbrowser aus. Ausführung bleibt bis API-Korrektur unbewiesen. |

Rote Logs: `/workspace/bienen-env/logs/r11-close-red-{qc,admission,defaults,zoom,season,shrink}*`.
Keine echten Daten zur Fehlerreproduktion verwendet. Die kleine Batchgröße wird
nur im Regressionstest injiziert; produktiv bleiben 500 Records je SQL-Batch.
Die Konfliktkennzeichnung gilt für **neu erzeugte** Revisionen. Bereits
unveränderlich gespeicherte historische QC wird durch Replay nicht nachträglich
umgeschrieben; eine solche Umdeutung wäre ein eigener kontrollierter Schritt.

## Umsetzung und bewusst begrenzte Vorbereitung

`archive_batch.py`: bisherige Korrektur-/Idempotenzregel erhalten, zusätzlicher
QC-Vergleich über Batch-/Dateigrenzen. `series_api.py`: begrenzte Admission;
kurze Repeatable-Read-Abfrage, autorisierte Cursor, TTL/Verdrängung und
40000-Punkte-/64-MiB-Cachevertrag erhalten. Kein neuer DB- oder Datenmodellzweig.
Session-/ACL-Abfragen benutzen weiter die bestehende Session-API. Die Admission
ist keine globale Begrenzung sämtlicher HTTP-/Authentifizierungsverbindungen.

UI: Temperaturüberblick, echte Kanalwahl, Zustandserhalt, Berliner Saisonanfang,
handlungsorientierte 422/404/503-Meldungen. Bei Fehlern keine scheinbar
vollständigen alten/lediglich leeren Kurven. Drei echte normale Polls prüfen
identischen ECharts- und DOM-Verweis, Zoom 20–80 %, abgewählte 20-cm-Legende,
zwei Instanzen und JS-Heap unter dem 256-MiB-Budget dieser 35-Tage-Fixture.
Browserfehler werden nicht durch HTTP-Interception erzeugt: ein ungültiges reales
Zeitfenster liefert 422, eine gesonderte nur für die eigene `bienen_test` gedachte
Testhilfe sperrt Datenbankverbindungen zeitweise und gibt sie über Admin-Verbindung
spätestens nach 20 s wieder frei. Tabellen und Messdaten bleiben dabei unverändert.

[Staging-Konzept und genaue synthetische Befehle](../entwicklung/umwelt-staging-sync.md):
neuer separater Publisher ohne DB-/Session-/Netzwerkzugang. Wiederverwendung der
Quellauswahl-/Parserbausteine. Nur deklarierte synthetische Quellidentitäten,
eigene geschützte Staging-Verzeichnisse, Hash/CSV-Prüfung, temporäre Kopie, fsync,
atomarer Rename und nachvollziehbares `prepared/published/unchanged/failed`-Audit.
Idempotenter Folgelauf ersetzt keinen Inode. Kein Löschen alter Monate und keine
Änderung der Originale. Unterbrechungen, partielle Dateien, Symlinks/FIFO/Hardlinks,
Parallelpublisher und unerwartete Kürzung werden kontrolliert behandelt.
Eine tatsächliche Sync→PostgreSQL-Prüfung erhält Korrektur und Fundstellen bei
altem Monats-Backfill. Rechte-/Betriebsentscheidungen für reale Quellen sind
explizit offen, keine produktive Synchronisierung freigegeben oder eingerichtet.

## Prüfumgebung und Commitbezug

Debian 13, Python 3.12.14 mit bestehendem requirements.lock, lokales PostgreSQL
17.11 am eigenen Unix-Socket/Portkennung 55434, Container PostgreSQL 16-alpine
mit vorhandenem Digest. Node 24.19.0, Playwright 1.56.1, signiertes Debian Chromium
155.0.8059.79, ECharts 5.6.0, Caddy lokal 2.6.2 bzw. vorhandener gepinnter Container,
Docker 28.4.0/Compose 2.40.3. Keine zusätzlichen Laufzeitabhängigkeiten.
Nur eigene synthetische `bienen_test` und neue Cloud-Compose-Projekte.

| SHA | Bezug |
|---|---|
| `ad9d940ab67e0ba06691b6cf0e0b5165ca580afd` | Rote Batch-/Datei-QC, 17-Kanal-Vorauswahl, parallele SQL-Abfrage; neue reproduzierbare Tests |
| `c28d7488137f8ad099b3bd9723606597b0fc5b94` | QC-/Admission-/Poll-Korrektur; echter Browser über drei normale Polls bereits PASS |
| `a6532b04288fc38d97f5b6854381683a23223adb` | Berliner Saisonanfang und CI-Branchfilter; 64er-Testsuite/erweiterter Browser PASS |
| `413d82f7220c98fbfc6d2468834f67e640d2c0b1` | Heapmessung und Staging-Eigentümer-/Hardlink-Schutz |
| `cf66da64e487226ef8d1ebe8725f05612f1eb32a` | Erhalt letzter Staging-Kopie bei gültiger, unerwarteter Kürzung |
| `6a8835144b557fa3479e2f5302b45be4d0d8c516` | 66/66 Tests PASS; kurzer Browser und Stabilitätsbrowser mit Heapmessung; aktuelle Jahresprobe. Ein alter Sync-Test hatte bei Korrektur zusätzlich einen angehängten Record entfernt; Testeingabe bewahrt diesen jetzt, Schutzprüfung bleibt erhalten. |
| `86a6ae21623e0573fd47ebd482994735f6f7779c` | Zusätzliche echte DB-Unterbrechung reproduziert HTTP 500 im gemeinsamen Principal; neuer Browserlauf zunächst FAIL |
| `95c006252428f567204e82c19d446d1172cef139` | Enger gemeinsamer 503-Handler für verlorene/abgewiesene DB-Verbindungen, ohne Schema-/Sitzungsdatenänderung |
| `837b7f23e3cef3c05b7925f8e6fd50ea07a966f9` | Zusätzliche Assertions für 503/Retry-After/Body ohne interne Details im finalen Browsernachlauf; Basis-Unterbrechung/Wiederaufnahme mit Handler 95c0062 bereits PASS |

Anschließend ausschließlich Berichte/Anleitungen/PR-Text/Belegablage. Der finale
Nachlauf wird auf dem anschließend gepushten Dokumentationscommit durchgeführt;
sein SHA und die Resultate werden in `/workspace/bienen-env/r11-stabil-final-evidence.json` gespeichert. Es werden
keine veralteten Ergebnisse als unabhängige CI umbenannt.

## Matrix zum Abschlussauftrag

| Test | Lokaler Nachweis | Ergebnis / praktische Grenze |
|---|---|---|
| T01 | Widerspruch im selben Batch, hinter Batchgrenze und im Folgemonat, tatsächliche PostgreSQL-QC, Originalzahl | PASS |
| T02 | Monatswechsel/Append/Rename/Backfill, Korrektur, zweimaliger Import, Sync→DB mit Fundstellen | PASS |
| T03 | >5000 Werte, lückenlose/duplikatfreie API-Seiten, neue Werte/Korrektur erst im neuen Snapshot | PASS |
| T04 | Echter Browser 7/30 Tage/Saison, vier tatsächlich vorhandene Temperaturkanäle, Berliner Saisonbeginn, zusätzlicher Registrykanal | PASS |
| T05 | Drei automatische 30-s-Zyklen, gleiche zwei Instanzen/DOM, Zoom/Legende erhalten, Heap gemessen, neue Messung erscheint | PASS im erklärten Testumfang; kein Dauerbetriebs-/Langzeitleaknachweis |
| T06 | Tatsächliche Ressourcenmeldung/Erholung im Browser, paralleler DB-Lock/503-Admission und Freigabe, DB-Verbindungsunterbrechung, Container-DB-Neustart mit automatischer Aufnahme danach | PASS lokal; keine kontrollierten Original-/Produktivstörungen |
| T07 | Sessions, Stand-/Volkrechte, Entzug, fremde/abgelaufene Cursor, aktuelle ACL pro Seite, DST-Offsets und Nullwerte | PASS |
| T08 | Reale Dateisync-/CLI-Prüfungen ohne DB-Zugang; Quellenfingerprint, atomare Kopie, Idempotenz, Fehler/Wiederanlauf und getrennte Rechte | PASS ausschließlich synthetisch |
| T09 | Neues eigenes Compose-Projekt, RO-Mounts, Dump/Restore, alle Container neu starten; Daten/Benutzer/Sitzung/CA identisch; weiterer DB-Neustart ohne Watcher-Neustart, neue Werte | PASS |
| T10 | Gesamte lokale Regressionen und für R1 korrigierte Workflowauswahl; unabhängige GitHub-Actions-Checks | Lokal PASS; unabhängige CI NICHT GELAUFEN, externer API-Blocker |

66er-Umweltsuite ohne übersprungene Tests. Zusätzlich 24 Stockkarten-Persistenz-
prüfungen, vorhandene Stockkarten-FastAPI-Verhaltensprüfung und 61 Sitzungsprüfungen,
Host-/PHP-/LoRa-/Wetter-/Formatter-Regressionen und vier vorhandene UI-Browsersuiten
PASS. Neue End-to-End-Nachweise verwenden tatsächliche CSV, PostgreSQL, FastAPI,
CA-geprüftes Caddy-HTTPS und Chromium/ECharts, keine simulierten HTTP-Antworten.
Gezielte Dateisystem-Fault-Injection und Parser-/Cache-Unit-Tests sind zusätzliche
Prüfungen und ersetzen diese Strecke nicht.

## Messzahlen und Grenzen

Jahresprobe auf 6a88351: 24 Dateien/365 Tage/147310658 Bytes; 35040 Boden- und
8760 Wetterrecords. Erstimport Boden 12,602 s/Wetter 3,440 s, unveränderter
Folgelauf 0,008 s. 8500 zusätzliche Records in danach 48007727 Byte großer Datei:
3,351 s. Jahresabfrage 130620 Temperaturquellwerte → 13908 reale Originalpunkte,
drei Seiten/9018323 Bytes, 3,069 s. Python-Spitzen-RSS 147296 KiB, ohne DB-/Browser-
Prozesse. Diese Probe ist kein mehrjähriger Mehrbenutzer- oder Produktionsnachweis.

Browser auf 6a88351: neuer CSV-Wert nach 27,784 s (Importer 5 s, UI-Poll 30 s).
Drei JS-Heapmessungen nach regulären Polls: 52688436, 49566180, 49651268 Bytes
(ca. 50/47/47 MiB); keine Aussage über kompletten Chromium-Prozess-RSS.
Auf Anwendungsstand 95c0062 zusätzlich reale DB-Unterbrechung/Wiederaufnahme PASS: 27,655 s bis zur neuen Messung, JS-Heap 52866916/49554760/49668560 Bytes. Die finalen Belegdateien enthalten die Wiederholung auf dem nachfolgenden Dokumentationscommit. Der erste Unterbrechungslauf war FAIL (HTTP 500 statt 503); dieser Nachweis wird nicht als PASS gezählt.

Container-Image `sha256:1ecd9e3d6217d95326f1dfd7e3f1202dd10aec1b5c5ea093c505bf261f7550f7`,
Projekt `bienenlogger-r1-r11-stabil-20261018`, Anwendungsstand 95c0062. Es wurde mit unverändertem
Versionslock und lokalem vertrauenswürdig bezogenem Offline-Wheelkontext gebaut,
weil Cloud-BuildKit PyPI nicht auflösen konnte. Der normale Online-Dockerfile-Build
auf GitHub ist weiterhin **nicht nachgewiesen**. Eigene freie /28-Netze innerhalb
der bestehenden 172.16/12-Vertrauensgrenze; keine App-/Caddy-Rechte aufgeweicht.
Alle Testdienste wieder gestoppt, Volumes erhalten; keine vorhandenen R1-Volumes
oder laufende ThinkStation-Dienste angefasst.

Unverändert offen: ein App-Worker für den lokalen Snapshotcache; maximal zwei
Diagrammverarbeitungen statt unbegrenzter gleichzeitiger Builds; kein globales
RSS-Versprechen. Historische unveränderliche QC wird nicht automatisch repariert.
Import- und Sync-Protokollaufbewahrung, Original-Zeitbasis, Message-ID-Eindeutigkeit,
Sondentiefen, echte Rechte/Pfade und kürzere Korrekturen benötigen Betreiberprüfung.
UI außerhalb Umwelt bleibt bis R3 Prototyp. R2/R3/R4 und reale BEEP-/Volkdaten
wurden nicht begonnen. Kein Merge, Deployment oder Produktivfreigabe.

## Reproduktion, unabhängige CI und Wiederaufnahme

Vorhandene Aktivierung/PG-Start aus der R1.1-Anleitung verwenden. DB-Prüfungen
**nacheinander**, nur in der selbst angelegten wegwerfbaren `bienen_test`:

```sh
python -m unittest discover -s tests/umwelt -p 'test_*.py' -v
python tests/umwelt/e2e.py --output build/neuer-kurzlauf
python tests/umwelt/e2e.py --stability --output build/neuer-stabilitaetslauf
python tests/umwelt/year_load.py --output build/neues-jahr
```

Weitere Regressionen/Compose-Befehl und kontrollierter Backup/Restore/Rückfall:
[aktualisierte Betriebsanleitung](../entwicklung/umwelt-r1-1.md) und
[Staging-Konzept](../entwicklung/umwelt-staging-sync.md). [Kleine synthetische Ergebnisbelege](artefakte/r11-stabilisierung-2026-10-18.json).
Lokale Logs:
`/workspace/bienen-env/logs/r11-close-*`; Ergebnis-JSON/Screenshots unter
`r11-close-final-*` bzw. `r11-close-outage-browser`. **Nicht ganze Verzeichnisse
veröffentlichen:** sie enthalten private Test-CA-Schlüssel und Dumps. Nur kleine,
explizit synthetische Ergebnisbelege sind zur Veröffentlichung vorgesehen.

Nachweis des externen Blockers am 18.10.2026 um 01:57 UTC (03:57 Europe/Berlin):

```text
gh api repos/impyer/bienen-lora-logger/actions/runs --method GET -f branch=refactor/r1-1-umweltarchive-20261017
Get "https://api.github.com/repos/impyer/bienen-lora-logger/actions/runs?...": Forbidden
curl https://api.github.com/repos/impyer/bienen-lora-logger
curl: (56) CONNECT tunnel failed, response 403
http=000 connect=403
```

Native Git-Pull/-Push funktioniert. Auch der anonyme öffentliche Read scheitert
**vor TLS/Authentifizierung**. Die gespeicherte Hostfreigabe enthält api.github.com;
deren Vorhandensein beweist keine funktionierende Runtime-Proxyroute. Keine neuen
Tokens angefordert, ausgelesen oder ersetzt. Git-PR-Refs enthalten bisher nur die
älteren PRs; #23 ist der Dokumentationsauftrag, kein Implementierungs-PR.
PR-Erstellung und Abruf/Prüfung unabhängiger Actions-Ergebnisse sind blockiert.

Nach wirksamer Plattform-/Proxykorrektur, ohne weitere Codeänderungen:

```sh
gh pr list --base refactor/r1-umweltdaten-20261017 --head refactor/r1-1-umweltarchive-20261017 --json number,url,headRefOid
# Falls kein Implementierungs-PR existiert:
gh pr create --draft --base refactor/r1-umweltdaten-20261017 --head refactor/r1-1-umweltarchive-20261017 --title 'R1.1: Umwelt-Zeitreihen, sichere Archive und Abschlussstabilisierung' --body-file docs/testberichte/2026-10-17-refactoring-r1-1-pr.md
# Tatsächliche Nummer aus obigem Ergebnis verwenden:
gh pr checks NUMMER --watch --fail-fast
gh run list --branch refactor/r1-1-umweltarchive-20261017 --json databaseId,workflowName,headSha,status,conclusion,url
```

Erwartete Workflows: `tests`, `stockkarte-fast`, `umwelt-r1`; konkrete Jobs und
Runs prüfen, ausgecheckten Head-/Merge-SHA und Artefakte dokumentieren. Fehlende,
übersprungene oder rote relevante Checks gelten nicht als PASS. Fehler auf dem
Branch beheben und den endgültigen SHA erneut prüfen. Erst danach kann der
Betreiber G1/technische Abnahmereife beurteilen. **Kein automatischer Merge.**
