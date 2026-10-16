# Bienenlogger – Claude-designgetreuer Prototyp v0.3

**Stand 16.10.2026 · Entwurf · keine Live-/BEEP-Schreibverbindung**

## Designquelle und Abnahmeregel

**Maßgeblich ist die originale, vom Betreiber bereitgestellte Datei `Bienenlogger Weboberfläche.html`, nicht der frühere Sidebar-Entwurf.** Das Original wurde tatsächlich im Browser gerendert und mit der neuen Startansicht verglichen. Die UI orientiert sich an der Claude-Struktur:

- Weißer, **horizontaler** Kopfbereich mit Sechseck-Logo, Navigationspunkten und Standortwahl.
- Maximal 1360 Pixel Inhaltsbreite, Farbwerte `#F4F5F2`, `#1A1F1C`, `#1F4E79`, `#9A5B00`; IBM Plex Sans / Plex Mono, falls lokal verfügbar (sonst Betriebssystemschrift).
- Bienenstand mit acht kompakten Kennzahlen, vier Hinweisen, **11 Völkerkacheln gemäß Claude-Ansicht**, Kachel-/Listenwechsel, Sortierung, schaltbaren Kennzahlen, Beutensymbol und kleinen Verlauf-/Temperatur-/Akustikfeldern.
- Volk-Cockpit, Stockkarte, Beute, Analyse, Umwelt & Tracht sowie kanalbasiertes Datenquellenregister.
- Gleiche horizontale Navigation auf Mobilgeräten scrollbar, keine neu erfundene linke Sidebar.

Die **elf Völker** stammen aus der Claude-Gestaltungsvorlage (1, 2, 4, 5, 6, 7, 8, 9, 10, 20, 21) und dienen hier der Bedienbewertung. Sie sind **nicht als elf gegenwärtig synchronisierte Datenbankdatensätze bestätigt**. Nur Volk 8 enthält einen belegten, aus dem TTN-Uplink des Betreibers berechneten Messpunkt (31,419 kg; 18,43 °C). Für Volk 5 ist die BEEP Base zugeordnet, aber es liegen in dieser Offline-Datei noch keine Messdaten vor. Andere Völker bekommen **keine erfundenen Messwerte**.

## Ausführen

Direkt `bienenlogger-claude-prototyp.html` herunterladen und in einem Browser öffnen. Alternativ den ZIP-Inhalt komplett entpacken und `index.html` öffnen. Für ein Test-HTTP-Setup: `python3 -m http.server 8000` im Projektordner.

Nur lokale Entwürfe von Stockkarte, Checklisten, Beutenänderung und Kanälen im `localStorage`. Kein Backend-Schreibzugriff; BEEP-Stockkarte bleibt bis zum freigegebenen Migrationskonzept die führende Quelle für den Beutenaufbau. Demodaten stehen hinter einer **bewussten** Umschaltung und werden gekennzeichnet.

## Tests und Reparatur der GitHub CI

`python3 build_single.py` baut die Einzeldatei **reproduzierbar** aus `index.html`, `style.css`, `app.js`. Die CI vergleicht den generierten Stand mit Git und verweigert nicht zusammengehörige Dateien. Der zusätzliche Playwright-Test `tests/server/test_claude_ui.js` läuft für *beide* HTML-Versionen und prüft Layout, Navigation, Stockkarte, Beutenänderung, dynamische Kanäle, Simulation und mobile Größen. Lokal liegt zusätzlich `tests/verify_claude_design.py` für die direkte Chromium-Prüfung der Einzeldatei vor.

Die alten roten CI-Läufe waren auf veralteten Zwischencommits; der Build-Drift ist durch diesen reproduzierbaren Build und Vergleich abgesichert. Vor Freigabe müssen die **aktuellen** GitHub-Actions-Läufe grün sein.

## Keine Produktivfreigabe

Weder PostgreSQL/FastAPI noch BEEP-Stockkartenimport oder Live-Webhooks wurden durch diese UI installiert. Die Empfangsimplementation liegt separat in GitHub PR #13. Änderungen am Beutenaufbau sind lokale BEEP-bezogene Testentwürfe, keine zweite produktive Stockkartenpflege.