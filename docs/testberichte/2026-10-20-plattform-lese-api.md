# Prüfbericht: Plattform Phase B – Lese-API und Oberfläche mit synthetischen Daten

**Datum:** 20.10.2026 · **Prüfobjekt:** Branch `feature/plattform-lese-api-20261020`, Commit `0690bf4`. Er enthält den Importer-Stand `2ef8c95` (Branch `feature/importer-20261020`) und `main` `270abf1`. · **Prüfer:** Claude (Code-Session) · **Änderungsklasse:** D2 · **Teststufen:** T1/T2 (CI), keine T3–T6

## Prüfumfang

`server/plattform/` (Lese-API, Oberfläche, Generator synthetischer Daten) zusammen mit `server/datenbank/schema.sql` 0.4 und `importer.py`. Die Kette ist: synthetische Rohprotokolle im Format von `ein_rohprotokoll()` → Importer → PostgreSQL → API → Browser.

**Konfiguration der CI** (GitHub Actions, Lauf `tests` #39363302432 und `statische-analyse` #39363302452 für `0690bf4`, beide *success*):
- Job `datenbank`: `ubuntu-latest`, Dienst `postgres:16`, Python 3.12
- Pakete: fastapi 0.142.2, pydantic 2.13.5, uvicorn 0.54.0, psycopg[binary] 3.3.6, httpx 0.28.1
- Node 20, Playwright 1.56.1 mit Chromium
- Oberfläche: Vue 3.5.42, ECharts 6.1.0 (SHA-256 in `server/plattform/web/vendor/README.md`)

## Ergebnisse

| Prüfung | Ort | Soll | Ist |
|---|---|---|---|
| Hosttests (Verdichtung, Lücken, Anmeldung, Bremse auch bei 50 parallelen Versuchen, Generator, API ohne Datenbank, Parameterprüfung) | lokal Windows (Python 3.14, ohne PostgreSQL) und CI | 10/10 | 10/10 |
| Datenbankfälle `tests/plattform/test_plattform.py` (leere Datenbank, Import des synthetischen Oktobers, Dashboard, Winterzeit-Nacht 7/7, Lücke als `null`, Uhr nicht abgeglichen 48/48 mit Empfangszeit, Tagesbilanz mit Eingriff, Vereinigung, Kanalwechsel mit Versatz, Fehlwerte sichtbar, Wind-Kreismittel, Regenzähler nicht summiert, K-03/K-04/Varroa, Datenquellen K-06, 404/400) | CI, Sitzungszeitzonen Europe/Berlin und UTC | 14/14 je Zone | bestanden (Schritt *success*; Einzelzahlen nur im Lauf-Log) |
| Diagrammlogik `tests/plattform/test_diagramm.mjs` | lokal Node 18 und CI Node 20 | 10/10 | 10/10 |
| Oberfläche `tests/plattform/oberflaeche_testen.sh` (Chromium, Browser in America/New_York): leer und synthetisch | CI | alle Prüfungen bestanden | bestanden (Schritt *success*) |
| Statische Analyse (Syntax, Ruff, Bandit -lll, ShellCheck) | CI | grün | grün |
| Sichtprüfung im Browser mit nachgebildeten Abfragen (ohne PostgreSQL): Übersicht, Cockpit, Umwelt, Datenquellen ohne JavaScript-Fehler | lokal, eingebauter Browser | keine Fehler | keine Fehler. Dabei geändert: Vorwahl der Kurven, Zoom nur mit Strg, `Cache-Control: no-cache` |

**Verlauf:**
- Der erste CI-Lauf (`55cc6f6`) war beim Browsertest rot. Die erwarteten 404-Antworten der API im Leer-Modus zählten als JavaScript-Fehler, und es fehlte ein Favicon. Behoben in `0690bf4`.
- Bandit -lll war rot wegen `hashlib.sha1` in `tests/datenbank/test_importer.py` (B324). Behoben vom Importer in `2ef8c95`.
- Die automatische Sicherheitsprüfung meldete, dass parallele Anmeldeversuche die Bremse umgehen konnten (TOCTOU). Behoben in `7810d01`: Prüfen und Zählen geschehen jetzt unter einer Sperre vor scrypt.

## Befunde

- **PLT26-11 (neu):** Der Importer übernimmt Sensorfehlercodes ohne Plausibilitätsprüfung. Die DS18B20-Codes −127 °C und 85 °C und eine Gewichtsspitze von +50 kg landen als `qualitaet = 'ok'`. Die API zeigt sie unverändert an; das ist gewollt, damit nichts still korrigiert wird. Die Tagesreferenz (Median) dämpft Ausreißer, Kurven und Mittelwerte enthalten sie aber.
- **PLT26-04:** Der lesende Teil ist umgesetzt: Anmeldung, Sitzung, Herkunftsprüfung, Bremse, alle Lese-Endpunkte nur angemeldet. Schreiben mit CSRF-Schutz fehlt noch.

## Grenzen

- Nur synthetische Daten, kein Betrieb auf der ThinkStation, keine echten Protokolle, kein Apache-Proxy, kein TLS. Die Werte beziehen sich auf den CI-Lauf.
- Die Einzelzahlen der CI-Schritte stehen nur im Log, das ohne GitHub-Anmeldung nicht lesbar ist. Bewertet ist der Erfolg der Schritte; Fehlschläge würden als Annotation erscheinen.
- Leistung ist ungeprüft (ein Monat, vier Völker, ca. 42 000 Messwerte). Für mehrere Jahre und Indizes auf `messwert(kanal_id, zeit)` gibt es keine Messung.
- Keine Schreibfunktionen (Stammdaten, Stockkarte): Ein leerer Start zeigt nur Leerzustände, bis Stammdaten per SQL eingetragen werden.
