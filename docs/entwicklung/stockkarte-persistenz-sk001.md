# Stockkarte SK-001 – persistente Revisionen

**Status:** Eigenständiger Bienenlogger-Entwurf, D1/T1, nicht für den Produktivserver freigegeben.

Die neue PostgreSQL-16-Migration server/datenbank/migrations/001_stockkarte.sql ergänzt ausschließlich Tabellen unter dem vorhandenen Schema bienen. Es gibt in dieser Migration weder DROP noch TRUNCATE.

## Daten- und Zeitvertrag

- Die Stammdaten bienen.volk und bienen.koenigin werden wiederverwendet. Beutenaufbau bleibt bei bienen.beute_konfiguration, historische Volk-/Königinnenzuordnungen bei den bestehenden Tabellen.
- Kategorie-/Options-IDs werden dauerhaft gespeichert; Checklisten erhalten unveränderliche Versionsnummern und Positionen.
- Die Identität einer Durchsicht bleibt stabil. Jede Korrektur schreibt eine eigene revisionsnummerierte Zeile mit dem vollständigen Wertesnapshot.
- Trigger verhindern UPDATE und DELETE auf Revisionszeilen und dem unveränderlichen Durchsichtsstamm.
- Der Datenbanktyp DATE enthält den dokumentierten Kalendertag. Bei Zeitgenauigkeit nur_datum muss der UTC-Zeitstempel NULL bleiben, damit keine künstliche Messzeit erfunden wird.
- Die Werte sind ein JSONB-Objekt mit stabilen Kategorien-IDs; die Python-Schicht prüft Typen, Auswahl-IDs, Pflichten und Grenzen vor dem SQL-Insert.
- Eine externe BEEP-Inspektions-ID ist eindeutig; erneuter Import erzeugt keine zusätzliche Durchsicht.
- Korrekturen benötigen die aktuell erwartete Revisionsnummer. Row Lock und Versionskontrolle verhindern verlorene konkurrierende Änderungen.
- Zusätzliche Königinneninformationen werden als unveränderliche Revisionen abgelegt, während die Volkzuordnung separat historisiert bleibt.

## Wichtige Architekturgrenzen

Das bestehende Datenbank-Grundschema server/datenbank/schema.sql enthält DROP SCHEMA bienen CASCADE. Es darf ausschließlich auf einer leeren Testdatenbank verwendet werden. Der neue Test überprüft deshalb den Datenbanknamen bienen_test, bevor er dieses Grundschema lädt.

Die neuen sk_-Tabellen sind eine additive **Entwicklungs-Erweiterung** des bereits vorhandenen Schema-Entwurfs. Die älteren Entwurfstabellen merkmal, checkliste und durchsicht müssen vor der Inbetriebnahme mit dem neuen Revisionsmodell konsolidiert oder sauber migriert werden. Es soll keine zweite produktive Stockkartenverwaltung entstehen.

Der Python-Baustein server/datenbank/stockkarte_store.py ist ausschließlich eine interne Schreib-/Lese-Komponente. Noch nicht vorhanden: geschützte HTTP-API, Anmelde-/Rollenprüfung, echte Benutzeridentitäten, Migration der lokalen Browserentwürfe, serverseitige Bildspeicherung, Backup-/Wiederherstellungsprozess und Auditprotokoll außerhalb der Datenbank.

**Keine BEEP-Vue-Anwendung und keine BEEP-API als Laufzeitabhängigkeit.** BEEP ist weiterhin alleinige Referenz für Kategorien, Datenverträge und Benutzerführung. In den öffentlichen Tests stehen ausschließlich künstliche Testvölker und Referenzkennungen.

## Nachweis

Die separate GitHub-Action stockkarte-fast betreibt für die Datenbanktests einen eigenen temporären PostgreSQL-16-Service mit Datenbanknamen bienen_test. Der Test tests/datenbank/test_stockkarte_persistenz.py prüft u. a. Identitäten, Revisionen, false vs. 0, Nur-Datum-Ereignisse, Pflichtkategorien, ungültige Optionen, Konflikte, Import-Idempotenz und Königinnenkorrekturen.

Auch bei grüner CI gilt: **Keine Produktivmigration ohne Betreiberfreigabe, Backup, Restore-Test und Freigabe der finalen Schemakonsolidierung.**