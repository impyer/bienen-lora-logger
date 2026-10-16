# Eigenständiger Bienenlogger-Katalogadapter

Quellreferenz: BEEP `CategoryInput.php`, `Checklist.php`, `CategoryController.php` und `beep-vue-app/checklist-input.vue`. Der Code ist neu implementiert; **keine BEEP-App wird eingebunden**.

Der lokale JSON-Import akzeptiert BEEP-artige hierarchische Kategorien (`taxonomy`/`categories`), flache Kategorien mit `parent`/`parent_id`, dazu `categoryinputs` mit `category_input_id`-Referenzen sowie `checklists.category_ids`. Kategorie-IDs und Reihenfolge bleiben erhalten. Fehlende Eltern, doppelte IDs und Zyklen werden verworfen.

`list_item` ist eine Ja/Nein-Eingabe wie im offiziellen Vue-Frontend. `required: 0` ist kein Pflichtfeld. Unbekannte Eingabetypen, dynamische Fremdlisten und Optionen ohne Katalogdaten werden kenntlich gemacht und vor einer falschen Speicherung blockiert.

**Kein vollständiger BEEP-Katalog:** Der Excel-Export enthält nur benutzte Kategorienamen. Eine vollständige, autorisiert beschaffte Taxonomie muss separat importiert und geprüft werden. Keine private BEEP-API, keine öffentlichen Hive-IDs, keine Server-Rückschreibung.

Test: `node tests/server/test_beep_catalog_adapter.js`. CI: `.github/workflows/stockkarte.yml`.
