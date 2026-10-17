# Claude-Arbeitskontext – Bienenlogger UI-Prototyp (16.10.2026)

**Ergänzung 17.10.2026 (R1):** Die Umweltseite ist im explizit eingerichteten
HTTPS-Teststack an PostgreSQL/FastAPI angebunden und nutzt lokale Apache ECharts.
Die Offline-Einzeldatei enthält keine Servermessdaten. Andere lokale Ansichten
und die bisherige Stockkarten-Modalnavigation sind weiterhin Prototyp/R3-Arbeit.
Die folgenden Aussagen zum ursprünglichen UI-Stand sind entsprechend zeitlich
einzuordnen. Anleitung und Nachweise: [Umwelt R1](../../docs/entwicklung/umwelt-r1.md),
[Prüfbericht](../../docs/testberichte/2026-10-17-refactoring-r1.md).

## Auftrag und Referenz

Diese Oberfläche basiert gestalterisch und in der Navigation auf der vom Betreiber am 16.10.2026 übergebenen Claude-Datei `Bienenlogger Weboberfläche.html` mit den Referenzansichten:
1. Bienenstand
2. Volk-Cockpit
3. Umwelt & Tracht
4. Datenquellen & Kanäle

Zusätzlich wurden prototypisch **Stockkarte**, **Beutenkonfiguration** und **Analysen & Vergleich** eingeführt. Das Ziel ist die Kombination sinnvoller Eigenschaften von BEEP und beelogger, kein unreflektierter Quellcode-Fork.

## Bindende fachliche Regeln (nicht stillschweigend verändern)

- Volk, physische Beute, Bienenstand, Königin, Gerät, Messstelle und Messkanal haben eigene IDs und Lebenszyklen.
- **Je Volk gleichzeitig maximal ein primäres Stockmessgerät:** BEEP Base **oder** klassischer beelogger **oder** eigene beelogger-Entwicklung. Ergänzende Messgeräte dienen anderen Messgrößen wie CO₂, Feuchte usw.
- Erste priorisierte Messgrößen: **Gewicht, Temperatur, akustische Frequenzbänder**. Nicht jedes Modell muss alle Kanäle besitzen; fehlende Werte sind `null`, niemals 0.
- Physische Beute ist nicht identisch mit dem Volk. Eine Beute ist zeitgleich höchstens einem Volk zugeordnet. Beutenaufbau mit Zargen ist zeitabhängig.
- Die **BEEP-Stockkarte ist vorerst führende Erfassungsquelle** für den Beutenaufbau. Aufbauänderungen in unserer Plattform sollen aus BEEP-Ereignissen mit Provenienz und Gültigkeitszeitraum abgeleitet werden, nicht durch eine zweite unabhängige Pflege. Lokale Eingaben der Vorschau sind ausdrücklich nur Testentwürfe.
- Ein Ableger erhält eine neue Volk-ID mit dokumentierter Abstammung. Änderungen am Stockmessgerät ändern die Volk-ID nicht.
- Für Zeitreihen **UTC für Speicherung, Europe/Berlin für Anzeige und Tagesreferenz**; Datum ohne Uhrzeit darf nicht als gemessene Ereignisuhrzeit erfunden werden.
- Rohdaten, Kalibrierhistorie, Quelle, Messstellenposition, Qualität, Geräte-/Volkbezug und Zeiten müssen erhalten bleiben.

## Technischer Status (nicht übertreiben)

- `prototype/claude-ui/index.html`, `style.css`, `app.js`: **Browser-Prototyp**, keine produktive Backend-Integration. Läuft ohne Framework und ohne CDN direkt aus Dateien bzw. HTTP.
- `localStorage` ist nur eine Vorschau-Zwischenablage; kein revisionssicherer Datenbestand. Kein echter BEEP-API-Schreibzugriff und kein TTN-Liveempfang.
- Der einzige vorliegende BEEP-Base-Messpunkt liegt in einer **anonymisierten lokalen Fixture**. Musterzeitreihen laufen **ausschließlich im expliziten Simulationsmodus**.
- Zwei Testvölker dienen der Bedienbewertung. Aktuell noch kein generisches dynamisches Völker-/Standort-Verzeichnis.
- `server/datenbank/schema.sql`: PostgreSQL **Entwurf, noch keine Produktionsmigration**. Niemals ungeprüft einspielen; die Datei enthält `DROP SCHEMA ... CASCADE`.
- `feature/beep-base-stockansicht-20261016` / PR #13: separates Empfangs-/Decoder-Vorhaben, das Live-Uplinks an den gemeinsamen beelogger-TTN-Eingang anschließt; nicht durch diese UI überschreiben.
- `docs/architektur/konzept-plattform-v02.md`, `docs/architektur/anforderungen-datenplattform.md`, `docs/architektur/beute-volk-stand-beziehungen-v01.md`: verbindliche konzeptionelle Hintergründe; spätere ausdrückliche Betreiberkorrekturen haben Vorrang.
- BEEP-API-Dokumentation: https://api.beep.nl/docs/ – für echte Stockkartenimporte zuerst **autorisierte Read-only-Nutzung**, IDs/Zeiten/Checklistenstruktur und Vollständigkeit prüfen. Zugangsdaten niemals in GitHub.

## Nächster sauberer Ausbauschritt

1. UI und Benutzbarkeit (mobil und Desktop) auf Basis des vorliegenden Prototyps mit Betreiber evaluieren; UX-Funktionen nicht durch reine Mock-Grafiken ersetzen.
2. Realen Datenfluss aus PR #13 in PostgreSQL nach dem gemeinsam geprüften Datenmodell bringen; bestehende Daten niemals löschen. FastAPI als lokale Lese-API zur Oberfläche (gemäß Gesamtkonzept).
3. BEEP-Stockkarte, Königin, Beutenaufbau/Änderung, Checklisten und Maßnahmen **read-only** importieren. Quellen-IDs, Quell-Zeitgenauigkeit und Konflikte markieren.
4. Die bisher festen Testvölker/Standorte durch dynamische Entitäten und Mehrstandort-/Mehrvölkervergleich ersetzen.
5. Danach erst geschützte Bearbeitung, Synchronisations-/Konfliktstrategie, Benachrichtigungen und Analysejobs produktionsreif bauen.

## Nachweis und Handhabung

Tests: `node --check prototype/claude-ui/app.js`, `node tests/server/test_claude_ui.js` (Playwright). Vor Migration, Real-Time-Anschluss oder Freigabe muss der Betreiber die Fakten und die Darstellung prüfen.

**Keine Halluzinationen bei Produktivdaten.** Ein Geräte-Uplink ohne kalibrierten Gewichtskanal ergibt *kein Gewicht in kg*. Ein einzelnes FFT-Spektrum ermöglicht keine Schwarmdiagnose. Ein fehlender Wetterwert ergibt *keine* GTS oder Blütenprognose.
