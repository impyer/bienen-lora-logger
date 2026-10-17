# Native Bienenlogger-Stockkarte: Katalogverwaltung

Die vom Betreiber gewünschte vollständige Bienenlogger-eigene Stockkarte erhält jetzt eine **lokale Verwaltung** für eigene Kategoriegruppen, Eingabefelder, Auswahloptionen und deren Bezeichnungen. BEEP bleibt ausschließlich Datenmodell- und Funktionsreferenz.

## Funktionen
- Gruppen anlegen, neue Felder mit Typ/Pflichtstatus hinzufügen; optional der aktiven Checkliste zuordnen.
- Auswahloptionen ergänzen und lokale Kategorien/Optionen umbenennen.
- Importierte BEEP-Kategorien **nicht** durch Bearbeiten oder Umbenennen verändern; eigene IDs benutzen das Präfix `bl:`.
- Bestehende Inspektionswerte speichern Kategorie-/Options-IDs. Umbenennungen verändern diese Identitäten nicht.
- Lokale Kategorien inklusive Checklisten als JSON exportieren und über den vorhandenen JSON-Katalogimport wieder einlesen.

## Grenzen
Diese Oberfläche ist weiterhin ein Offline-Prototyp mit lokaler Speicherung. Kategorie-IDs dürfen nicht gelöscht oder neu vergeben werden, wenn Inspektionen darauf verweisen. Eine vollständige BEEP-Taxonomie ist nicht im öffentlichen Projekt enthalten; sie muss für 1:1-Vergleiche separat autorisiert beschafft werden. Anhänge, Mehrbenutzerrechte und PostgreSQL sind noch nicht umgesetzt. Kein BEEP-Quellcode, keine private BEEP-Stockkarte oder Zugangsdaten werden übernommen.

## Teststrategie
`tests/server/test_stockkarte_catalog_editor.js` testet unveränderte Quellknoten, stabile IDs, Roundtrip-Export/Import, gültige und falsche Optionen und Schreibschutz importierter Kategorien. Daneben bleiben die vorhandenen Domain-, Offline-Build- und Browser-Tests aktiv.

Änderungsklasse D1, keine Produktivfreigabe.
