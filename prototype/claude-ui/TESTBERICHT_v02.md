# Bienenlogger – Testbericht zur korrigierten Claude-Vorschau

**Stand:** 16.10.2026 · **Artefakt:** `bienenlogger-claude-prototyp.html` und ZIP-Quellvariante · **Art:** Offline-UI-Prototyp, nicht Liveplattform.

## Reproduzierter Ausfall und Fix

Die ältere Einzelseiten-Datei enthält das zusammengeführte JavaScript direkt im HTML-`head` als synchrones Inline-Skript. Dabei ist `document.querySelector('#dataToggle')` noch `null` und ein Aufruf von `.addEventListener()` bricht die Initialisierung ab. Die Hauptansicht bleibt leer. Der damalige Browser-Smoke-Test testete nur `index.html` mit externem, `defer` geladenem `app.js` und fand den Fehler deshalb nicht.

**Fix:** Build aus `index.html`, `style.css` und `app.js` mit dem reproducible `build_single.py`. Das Skript fügt Styles in den `head` und JavaScript **nach die DOM-Elemente ans Ende des `body`** ein. Dadurch startet die gelieferte Einzeldatei ohne externe Skripte.

Ergänzter Fehlerfall: Wird JavaScript von einer Dateivorschau gesperrt, erscheint statt der bisher leeren Hauptansicht eine verständliche Öffnungsanleitung. Der Fallback wurde mit deaktiviertem JavaScript getestet.

Weitere Korrekturen: einzelner Messwert korrekt auf der Zeitachse und nur ein Datumslabel; fehlende FFT-Werte werden nicht in 0 umgewandelt; Importstatus der Völkerübersicht folgt tatsächlich importierten Reihen; Eingabe-Datumsfelder verwenden den lokalen Berlin-Tag.

## Ausgeführte Prüfungen

- **25 Interaktionstests:** Start, zwei Völker, echte Stichprobe, sieben Views, Volkwechsel, 24-h-Bereich, Modal und Escape, Checklistenpunkt, Durchsicht, Beutenänderung mit verknüpftem Stockkarteneintrag, neuer Messkanal, Simulation ein/aus, JSON-Import, Import zurücksetzen, Erhalt lokaler Testdaten, mobile Navigation. **25 bestanden.**
- **15 zusätzliche Testgruppen:** SVG-Einzelpunkt, Datum, ungültige/missing FFT-Felder, null-Gewicht, HTML-Injection-Escaping, ungültige Beutenkonfiguration, Browser-JSON-Download, sieben Ansichten bei **320 / 360 / 390 / 768 / 1024 / 1440 px** und keine JS-Laufzeitfehler. **15 bestanden.** Die sechs Viewport-Gruppen umfassen zusammen 42 Ansichts-/Breiten-Kombinationen. Es wurde kein horizontaler Überlauf protokolliert.
- **Syntaxprüfung:** `node --check app.js` – bestanden.
- **Buildprüfung:** Einzeldatei aus Quellstand erzeugt, im Head kein Inline-Skript, am Ende des Body ist das einzige Inline-Skript – bestanden.
- **Modulare Quellen:** Mit denselben Quellen mittels Browser-DOM-Injektion geladen; Bienenstand wurde aufgebaut, zwei Völker erschienen, keine JS-Ausnahme.
- **GitHub Actions:** Der automatisierte Test wurde erweitert, um **beide HTTP-ausgelieferten Varianten** (modular und Einzelseite) zu prüfen und das generierte Einzelseiten-HTML mit dem eingecheckten Artefakt zu vergleichen. CI ist **separat abzulesen**, nicht Teil der hier lokal durchgeführten Prüfungen.

## Prüfgrenzen

Die Browserumgebung blockiert die Navigation zu `file://` und `localhost` mit `ERR_BLOCKED_BY_ADMINISTRATOR`. Um den tatsächlichen HTML-Inhalt trotzdem zu prüfen, wurde das Dokument mit Playwright/Chromium direkt in eine Browserseite geladen (`set_content`). Das reproduziert die JavaScript-Ausführungsreihenfolge, testet aber **nicht** den Doppelklick-Start in allen Browsern oder die Darstellung in jeder Chat-Vorschau. GitHub Actions prüft zusätzlich HTTP mit Playwright.

LocalStorage wurde für die Testläufe beim Laden auf `about:blank` als Browser-Speicher-Simulation bereitgestellt; echtes `file://`-LocalStorage ist hier nicht end-to-end getestet. Die App fängt Browser-Speicherfehler ab und meldet sie. Livezugriff auf TTN, BEEP oder PostgreSQL ist **nicht** Bestandteil der Vorschau; Daten aus dem Browser bleiben lokale Testentwürfe. Der BEEP-Einzelmesspunkt von Volk 8 ist real, Trends im Simulationsmodus sind synthetisch.

**Kein Produktiv-Deployment**, keine Zugangsdatenänderungen, keine BEEP/TTN-Webhook-Änderung, kein Merge nach `main` durch diese Korrekturen.

## Wiederholbare Prüfung

1. `python3 build_single.py` zum Erzeugen des HTML-Downloads.
2. `node --check app.js` für JavaScript-Syntax.
3. Bei installierten Python-Paketen `playwright` und Chromium: `python tests/browser_check.py` und `python tests/edge_check.py`.
4. Im GitHub-PR den Browser-Smoke-Test sowie die Reproduzierbarkeitsprüfung der generierten Einzelseite verfolgen.