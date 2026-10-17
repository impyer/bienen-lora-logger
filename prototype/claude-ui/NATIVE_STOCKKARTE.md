# Eigene Bienenlogger-Stockkarte – Code und Test (D1 / T0–T1)

Die Anwendung baut das **Funktionsprinzip** der offenen BEEP-Stockkarte selbst nach. Es handelt sich **nicht** um einen Vue-Fork, ein Git-Submodul oder eine Weiterleitung zu BEEP. Das äußere Design basiert weiterhin auf der Claude-UI-Referenz.

## Implementiert in eigenem Code

- `stockkarte_native.js` – generischer und separat testbarer Kategorienbaum, Kategorie-IDs und Eltern-/Kindrelationen, Eingabekomponenten nach Typ (Text/Datum/Ja-Nein/Anzahl/Prozent/Bewertung/Einzel-/Mehrfachwahl), Pflichteinträge/Validierung, Checklisten und Reihenfolge, `category_id -> value`.
- `app.js` – mehrere editierbare Checklisten, Bearbeitung und Revision von Inspektionen, originärer Quellverweis zu importierten BEEP-Inspektionen, bestehende lokale Königinnendaten und Beutenentwürfe.
- `index.html`, `style.css` – horizontale Claude-Navigation; eigenständig laufender Browserprototyp.
- `build_single.py` – reproduzierbare eigenständige Offline-Einzeldatei, die auch ohne Netz/Konto funktioniert.

## Abgleich mit BEEP Open Source

Konzeptionell ausgewertet:
- `beepnl/BEEP/app/Category.php`, `CategoryInput.php`, `Checklist.php`, `Inspection.php`, `InspectionsController.php`
- `beepnl/beep-vue-app/src/components/checklist-input.vue`, `checklist-fieldset.vue`, `src/router/views/inspect.vue`

**Keiner dieser BEEP-Quelltexte oder Bibliotheken wird zur Laufzeit eingebunden oder in den eigenen Code kopiert.** Die eigenen Klassen orientieren sich an den dokumentierten Feldern und Abläufen und verwenden eigene UI-Komponenten.

## Daten und Grenzen

Der öffentliche Code enthält **keine privaten BEEP-Exporte, echten Hive-IDs, Zugangsdaten oder Standortmetadaten**. Ohne Datendateien lädt er einen ausdrücklich gekennzeichneten Beispiel-Kategorienbaum. Der private Offline-Prototyp mit echten CSV-/Stockkarten-Daten liegt nur beim Betreiber.

Aus dem BEEP-Excel-Export lassen sich lediglich *benutzte Kategorienamen*, nicht alle Taxonomie-IDs, Felddatentypen, Rassen-/Behandlungsoptionen oder persönlichen Checklisten rekonstruieren. Der Editor akzeptiert ausdrücklich ein autorisiert lokal gespeichertes JSON-Paket mit `taxonomy` und `checklists`. Der Beispielimport ist in der privaten README beschrieben.

Offen: echte vollständige BEEP-Kategorientaxonomie testen, alle Eingabetypen einschließlich Fotos/Dokumenten, mehrbenutzerfähiges PostgreSQL-Backend, Rollen, Konfliktbehandlung, Online-/Offline-Synchronisation, BEEP-Datenrückschreiben (hier ausdrücklich nicht vorgesehen), komplexe Beuten- und Königinnenhistorie. **Keine 1:1-Funktionsparität behaupten.**

## Reproduzierbarer Test

```bash
node --check prototype/claude-ui/app.js
node --check prototype/claude-ui/stockkarte_native.js
node tests/server/test_stockkarte_native.js
python3 prototype/claude-ui/build_single.py
# CI: git diff --exit-code -- prototype/claude-ui/bienenlogger-claude-prototyp.html
node tests/server/test_native_stockkarte_browser.js
```

Der UI-Test setzt `playwright` + Chromium voraus, bereits im Server-CI-Job vorhanden. Keine Live-API- oder Produktionsfreigabe, keine Änderung an LoRa-/TTN-Erfassung. Für reale Speicherung muss das weitere Bienenlogger-Datenmodell verwendet werden, nicht Browser-LocalStorage.
