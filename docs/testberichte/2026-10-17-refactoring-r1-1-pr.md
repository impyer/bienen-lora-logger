# Vorbereiteter PR: R1.1 – vollständige Umwelt-Zeitreihen und sichere Monatsarchive

**Zielbranch:** `refactor/r1-umweltdaten-20261017`  
**Quellbranch:** `refactor/r1-1-umweltarchive-20261017`  
**Status:** PR-Erstellung durch CONNECT 403 zu api.github.com blockiert; dieser
Text ist die reviewbare Übergabe, keine behauptete PR/Remote-CI.

## Ziel / Änderung

R1 zeigte bei langen Messreihen nur die ersten 5000 Punkte und erkannte neue
Monatsdateien nicht. Die Umweltansicht lädt jetzt vollständige, konsistente
Snapshot-Seiten mit realen Temperatur-Extrema, Null-/Lückengrenzen, Zeit-/QC-
Metadaten und jüngstem Messpunkt. Roh-API, Sitzungen und kanonische Identitäten bleiben.

Der nach ADR-0005 ausdrücklich synthetisch freigegebene Monatsimport liest
isolierte RO-Staging-Verzeichnisse streamend und setzt atomare Datei-Checkpoints.
Rotation/Append/Backfill erhalten Roh-/Korrekturhistorie und Fundstellen.
Migration 004 ist additiv, 003 unverändert. Separates Import-Login, Inventur,
kontrollierte Konfigurationsänderung `BIENEN_IMPORT_DSN`, Backup/Restore und
manuelle Abnahme sind dokumentiert. Keine automatische Bestandsumstellung.

**Änderungsklasse:** D2, Entwicklungs-Gate G1.  
**Befunde/Anforderungen:** R1.1-01–06, R11-A01–A11; ADR-0004/0005.  
**Bericht:** [R1.1-Prüfbericht](2026-10-17-refactoring-r1-1.md).  
**Manuelle Abnahme/Rückfall:** [Betriebsanleitung](../entwicklung/umwelt-r1-1.md).

## Nachweis

| Prüfung | Ergebnis | Umfang |
|---|---|---|
| Unit/DB/API/Upgrade | PASS lokal | 54 Tests; echte PostgreSQL-Verbindungen, ACL/Cursor/Revisionen, Monatswechsel/Rotation/Fehler, eingeschränkte Rechte, gefülltes 003-Backup/Restore vor 004 |
| Echter Software-E2E | PASS lokal | CSV-Watcher, PostgreSQL, FastAPI, CA-validiertes Caddy-HTTPS, Chromium/ECharts, 24 h bis Saison, >5000 Punkte, Monatsverzeichnisse/live Poll/mobile; keine HTTP-Mocks |
| Jahres-/Containerprobe | PASS lokal | 147 MB/24 Dateien, 48-MB-Datei/Append, begrenzte Jahres-API, RO-Mounts, Backup/Restore/Neustart mit gleichen Daten/CA/Sitzung und neuer periodischer Messung danach |
| Bestehende Regressionen | PASS lokal | Stockkartenpersistenz/API/61 Sitzungsprüfungen, Host/PHP/LoRa/Wetter/Formatter und vier UI-Browsersuiten |
| GitHub-CI / normaler Online-Imagebuild | NICHT GELAUFEN | GitHub-API-Proxy blockiert PR/Checks; Cloud-Build mit identischem Lock und validiertem Offline-Wheelkontext |
| Physischer LAN-/Echtdaten-Feldtest | NICHT GELAUFEN | R11-A11 verlangt gesonderte Betreibererlaubnis und echte Geräte/CSV-Zuordnung |

Commit- und Messzuordnung im Bericht. Keine Hardware-/Firmware-/Akkuänderung,
kein HiL oder Produktionsrelease. Offene Risiken: tatsächliche Quellsemantik und
Sonden-/Message-ID-Zuordnung, Jahres-/Mehrbenutzerbetrieb, Importlog-Aufbewahrung,
ein App-Worker für lokalen Snapshotcache, Prefix-Hash weiterhin O(Dateigröße),
explizite Umstellung alter Importer-Konfiguration. R2–R5/BEEP-/Volkdaten bleiben offen.

## Manuelle Abnahme

1. Diff/ADR/API-Vertrag und dokumentierte Test-SHAs prüfen; synthetischen eigenen
   Loopback-Stack verwenden, Backup vor 004 separat wiederherstellen.
2. Exakte IDs inventarisieren; zwei isolierte RO-Staging-Verzeichnisse und
   separates Login einrichten. Beispiele enthalten absichtlich ungültige IDs 0.
3. Alle Zeitfenster/Rohmodus, Temperaturmin/max/null/0, Wetter und Tiefen,
   Standrechte, jüngsten Punkt und laufenden Poll prüfen.
4. Monatswechsel/Append/Rename/Backfill und Neustart vergleichen. Bei Fehler
   Importer stoppen, altes Image/alte Konfiguration nutzen und additive Daten
   erhalten; keine Down-Migration/Volume-Löschung.
5. Echte ThinkStation-/Laptop-Abnahme erst nach eigener ausdrücklicher Freigabe.

## Checkliste

- [x] Geprüfte SHAs, PASS/Fehlläufe/offene Nachweise im Bericht getrennt.
- [x] Neue Negativfälle, DB-/Browser-/Ressourcennachweise und Regressionen vorhanden.
- [x] Zeit-/Daten-/API-Kompatibilität und kontrollierter DSN-Wechsel dokumentiert.
- [x] Dokumentation, ADR, Befundregister und Changelog aktualisiert.
- [x] Keine realen Quellen, Zugangsdaten, privaten Messlogs oder CA-Schlüssel in Git.
- [x] Neue Python-/Shell-Dateien GPL-3.0-or-later; vorhandene Locks beibehalten.
- [ ] Remote-CI nach tatsächlicher PR-Erstellung prüfen.
- [ ] Betreiberabnahme des fertigen Entwicklungsstands; R11-A11 separat.

**Beanspruchter Freigabestand:** synthetisch geprüfter Entwicklungsstand,
keine automatische Freigabe. **Kein Merge/Deployment.**
