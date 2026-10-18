# R1.1: Umwelt-Zeitreihen, sichere Archive und Abschlussstabilisierung

**Basis:** `refactor/r1-umweltdaten-20261017`

**Head:** `refactor/r1-1-umweltarchive-20261017`

## Ziel / Änderung

Lange Umweltreihen zeigen vollständige Snapshot-Seiten mit echten Extrema,
Null-/Lückengrenzen und jüngstem Wert. Sichere Monatsarchive, Checkpoints,
Provenienz und getrenntes Import-Login erhalten Datenhistorie/Identitäten.
Additive 004 und bestehende Roh-API bleiben; 003/004 wurden durch die Stabilisierung
nicht geändert. Kein Eingriff in Receiver/ThinkStation oder echte Quellen.

Abschlusskorrekturen: Konflikt-QC über Batch-/Monatsgrenzen, begrenzte parallele
Diagrammverarbeitung, dynamischer Temperaturüberblick, erhaltener Zoom und
Legendenstatus beim normalen Poll, korrekter Berliner Saisonbeginn und klare
Fehler-/Wiederaufnahmeanzeige. Ein tatsächlicher DB-Ausfall erhält eine opaque 503-Antwort im gemeinsamen Session-Principal statt eines ungefangenen 500. Separater Publisher testet ausschließlich
synthetische Kopien mit atomarem Staging-Rename, Audit und Abbruch bei unsicherer
oder verkürzter Quelle. Keine neuen produktiven Zugriffsrechte.

**Klasse/Gate:** D2, T0–T3, G1 offen bis unabhängigem Nachweis/Betreiberreview.

**Bezug:** R1.1-01–06, R11-A01–A11, R11-S01–08, Abschlussauftrag T01–T10,
ADR-0004/0005.

[Aktueller Prüfbericht mit konkreten SHAs/Fehlläufen/Grenzen](2026-10-18-refactoring-r1-1-stabilisierung.md)

[Abnahme/Backup/Restore/Rückfall](../entwicklung/umwelt-r1-1.md)

[Staging-Konzept und offene reale Betreiberentscheidungen](../entwicklung/umwelt-staging-sync.md)

## Nachweis

| Prüfung | Ergebnis | Umfang |
|---|---|---|
| Umwelt/DB/API/Dateisync | PASS lokal | 66 Tests; echte PostgreSQL-Verbindungen, Batch-/Datei-QC, ACL/Cursor, zwei parallele Abfragen, gefülltes 003-Backup/Restore vor 004, Originalerhalt/atomare Kopien/periodische CLI |
| Echter Browser | PASS lokal | CA-validiertes HTTPS/CSV-Watcher/PostgreSQL/FastAPI/ECharts; >5000 Werte, 7/30 Tage/Saison, vier tatsächliche Temperaturkanäle, drei normale Polls mit Zoom/Legende/Heap, echte DB-Unterbrechung und Wiederaufnahme |
| Jahres-/Containerprobe | PASS lokal | 147-MB-Jahr/24 Dateien, 48-MB-Datei/Append, begrenzte API, RO-Mounts, Restore/Neustart/gleiche Historie und CA/Sitzung, neue periodische Werte nach DB-Neustart |
| Bestehende Regressionen | PASS lokal | Stockkartenpersistenz/API/61 Sitzungsprüfungen, Host/PHP/LoRa/Wetter/Formatter und vier UI-Browsersuiten |
| Unabhängige GitHub-CI/normaler Online-Imagebuild | NICHT GELAUFEN / blockiert | API-CONNECT 403 vor TLS; erwartete Workflows tests, stockkarte-fast, umwelt-r1 müssen auf endgültigem Commit tatsächlich grün werden |
| ThinkStation/Laptop/Echtdaten | NICHT GELAUFEN | Separater physischer Abnahmeschritt, keine reale Freigabe |

## Manuelle Abnahme

1. Im eigenen synthetischen Teststack privaten Dump vor Migration/Quellumstellung
   separat restoren; Roh-/Mess-/Stockkartenrevisionen, Benutzer und Checkpoints vergleichen.
2. Tatsächliche IDs inventarisieren, zwei getrennte RO-Staging-Mounts und separates
   Import-Login prüfen. Synchronisierung nur mit selbst erzeugten Quellen testen.
3. Zeitfenster, Temperaturvorauswahl, zusätzliche Kanalwahl, Null/0/Lücke/QC und
   jüngsten Wert vergleichen. Zoom/Legende über mehrere 30-s-Polls erhalten.
4. Monatswechsel/Append/Rename/Backfill und Fehler/Wiederanlauf prüfen. Alle eigenen
   Container sowie DB allein neu starten; gleiche Historie/Sitzung/CA und neue Werte.
5. Bei Abweichung Importer/Publisher stoppen, bisheriges Image/Konfiguration nutzen,
   additive Tabellen/Volumes und letzte Staging-Kopien erhalten. Keine Down-Migration,
   Volume-Löschung oder Rückschreiben in Originale. Realer Anschluss separat freigeben.

## Offene Bedingungen

- [x] Reproduzierbare rote Fälle, gezielte Korrekturen und lokale echte Softwaretests.
- [x] Daten-/API-/Zeitkompatibilität, ursprüngliche Migrationen und Lizenzhinweise erhalten.
- [x] Bericht, Befundregister, Betriebs-/Staging-Konzept und Changelog aktualisiert.
- [x] Keine produktiven Daten, Zugangsdaten oder Test-CA-Schlüssel in Git.
- [ ] Implementierungs-PR tatsächlich erstellen und Remote-CI auf finalem SHA prüfen.
- [ ] Technische G1-Abnahme durch Betreiber nach unabhängigen Nachweisen.
- [ ] Separater realer ThinkStation-/Laptop-Test und tatsächliche Quell-/Zeit-/Rechteprüfung.

Ein App-Worker/lokaler Snapshotcache; keine Produktions-/Mehrbenutzer- oder
Langzeitlastzusage. Historische QC wird nicht still umgeschrieben. Sync kürzerer
Korrekturen/Retention und reale Rechte bleiben eigene Betreiberentscheidungen.
R2–R4/BEEP-/Volkdaten nicht begonnen. **Kein automatischer Merge/Deployment.**
