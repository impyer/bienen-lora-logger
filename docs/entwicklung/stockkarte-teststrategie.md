# Teststrategie: native Bienenlogger-Stockkarte (16. Oktober 2026)

Die Stockkarte wird vollständig als Bienenlogger-eigener Code entwickelt. BEEP ist nur fachliche Referenz für Taxonomie, Formulare und Datenmodell; kein BEEP-Submodul, kein BEEP-Frontend, kein BEEP-Laufzeitservice.

## Warum alte CI-Läufe rot waren

Mehrere nacheinander korrigierte Zwischenstände enthielten fehlende Offline-Engine, Testserver-Auslieferungsliste und Playwright-Aufruffehler. Beide Endläufe auf 92b5ed9 waren erfolgreich. Der kombinierte Testjob übersprang bei einem frühen UI-Fehler die faketime-Installation, wodurch anschließende LoRa-Zeitprüfungen Folgefehler zeigten.

## Freigabestufen

| Stufe | Auslöser | Tests |
| --- | --- | --- |
| Stockkarten-Domain | Pull Request mit UI-Dateien und manuelle Ausführung | Kategorien, Auswahl-IDs, Pflichtangaben, Null/false/0, numerische Genauigkeit, Datum, Offline-Build |
| Stockkarten-Browser | nach bestandenen Domain-Tests | Arbeitsabläufe, modulare Ansicht und Einzeldatei, mobile Bedienung (keine Pixel-Snapshot-Gates) |
| Projekt-Volltest | PR nach main, Push auf main, manuell | vollständige Firmware-, KiCad-, Formatter-, Server- und LoRa-Matrix |
| Fachliche/visuelle Abnahme | gezielte Bewertung vor Layoutfreigabe | Vergleich mit Claude-Vorgabe und vollständigem BEEP-Funktionskatalog |

Die vollständigen Hardware-/Serverprüfungen bleiben verpflichtend vor Merge auf main. Zwischen-PRs gegen Entwicklungszweige lösen nicht für jeden UI-Commit die gesamte Hardwarematrix aus. Branch-Protection-/Required-Checks beim Wechsel gegebenenfalls prüfen. Veraltete PR-Läufe werden per Concurrency abgebrochen; ein Abbruch ist kein Codefehler.

## Domänenregeln

- Originale BEEP-Kategorie-IDs und Hierarchie bleiben referenzierbar; keine erfundenen Auswahlwerte.
- Nicht erfasst, false und 0 bleiben verschieden. Ungültige IDs, Kalenderdaten, Grenzen und Dezimalstellen werden vor dem Speichern verworfen.
- Bilder und Anhänge ohne sichere eigene Ablage dürfen nicht stillschweigend erfolgreich gespeichert werden.
- Importierte Stockkarteneinträge bleiben unverändert; Korrekturen erhalten Quellenverweis und Revision.
- Volk, Königin, Beute, Messgerät und Kanal erhalten eigene dauerhafte Identitäten und historisierte Beziehungen.
- Keine privaten Exportdaten, Standortangaben, DevEUIs oder Zugangsdaten in CI-Fixtures.

## Ausbaustufen bis zur vollständigen BEEP-Funktionsparität

1. Vollständige autorisierte BEEP-Kategorientaxonomie mit Optionen als eigene versionierte Katalogdaten gegen die offene Referenz prüfen.
2. Noch fehlende BEEP-Feldtypen, Checklisten, Bilder, Erinnerungen und Königinnen-/Beutenabläufe selbst implementieren.
3. Eigene PostgreSQL-Persistenz, Historie, Multiuser-Rechte, Backups, Konfliktmanagement und Anhänge.
4. Stockkartenereignisse mit beelogger-basierten Gewichts-/Temperatur-/Akustikanalysen verbinden.

Die neue Validierung ist ein fachlicher Teilschritt und kein Nachweis einer vollständigen Funktionsparität.