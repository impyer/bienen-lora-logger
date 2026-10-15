# Webplattform / UI-MVP – Projektübergabe an Claude

**Stand:** 15.10.2026 · **Status:** Fachentwurf / Prototyp, kein Produktivbetrieb.  
**Git-Basis:** main `0142d39df2c3c4cbf6d1d427466589565035c495`  
**Änderung:** D0 (Dokumentation und Ablage eines unvernetzten Demo-HTML); T0 Dokumentenabgleich, kein HiL/Deployment.

## Einstieg

1. Zuerst [CLAUDE.md](../../CLAUDE.md), [AGENTS.md](../../AGENTS.md), [Entwicklungsregelwerk 1.1](../entwicklung/README.md), [Befundregister](../testberichte/befunde.md) lesen.
2. Fachliche bestehende Source of Truth: [Anforderungen Datenplattform](../architektur/anforderungen-datenplattform.md), [ER-Modell v0.1](../architektur/er-modell-datenplattform-v01.md), [Beute–Volk–Stand](../architektur/beute-volk-stand-beziehungen-v01.md) sowie [BEEP-Anbindung](../beep-anbindung.md).
3. Diese neuen Unterlagen: [UI-Anforderungen](ui-anforderungen.md), [Datenverträge/Erweiterbarkeit](datenvertraege.md), [BEEP-Migrationsstrategie](beep-migration.md), [Claude-Arbeitsauftrag](claude-arbeitsauftrag.md) und [Bodentemperatur-Konzept](konzept-v0.4-bodentemperaturen.md).
4. Funktionsdemo: [Standalone HTML-Prototyp v0.3](../../web/prototypes/Bienenlogger_UI_MVP_v0_3.html). Im Browser lokal öffnen, keine Serververbindung. Ausschließlich **synthetische** Werte und Beuten.

## Vier verbindliche UI-Funktionsbereiche

A. **Bienenstand-Dashboard:** Kacheln/Liste, Beutensymbole nach BEEP-Vorbild, verfügbare Messkanäle, getrennte biologisch/technisch/Aufgaben-Status.  
B. **Volk-Cockpit:** BEEP-Stockkarte/Checklisten, Messwerte mit gemeinsamer Zeitachse, Ereignissymbole und vertikale Referenzlinien, korrekte Skalen.  
C. **Wetter, Boden & Tracht:** Wetterstation, drei neu erfasste Bodentemperaturkanäle, GTS aus Lufttemperatur, schaltbare georeferenzierte Flugkreise und potenzielle Trachtflächen.  
D. **Vergleich & Analyse:** mehrere Völker und Bienenstände, Kennzahlen, reproduzierbare analytische Ergebnisse und Qualitätshinweise.

## Priorität: rasch nutzbare Weboberfläche

Phase 1: vorhandenen beelogger-Server und BEEP unverändert lassen; neue Webansicht **lesend** mit vorhandenen Daten verbinden, UI-MVP testbar machen. Phase 2: Kanalkatalog, Event-Overlay, Umweltansicht und Datenabgleich stabilisieren. Phase 3: eigene Stockkartenpflege nach vollständiger, geprüfter Migration. Keine vorzeitige BEEP-Abschaltung.

## Autorität / offene Entscheidungen

- **[BESTÄTIGT]:** BEEP-Stockkarte bleibt bis zur Umschaltung führend für bestehende Völker/Beuten/Inspektionen/Checklisten.
- **[BESTÄTIGT]:** Ein Ableger erhält neue Volk-ID und dokumentierte Muttervolkherkunft; eine Beute kann zu einem Zeitpunkt höchstens ein Volk enthalten.
- **[BESTÄTIGT]:** Normalfall ist **ein primäres Stockmesssystem je Volk** (beelogger ODER BEEP Base ODER keines); mehrere unabhängige Umweltquellen sind zulässig. Zukunftsfähige Mehrfachsysteme sind noch nicht Erstumfang.
- **[BESTÄTIGT]:** Drei Bodentemperatur-Messungen wurden laut Betreiber am 14.10.2026 begonnen; Sensorpositionen/-tiefen und echte Rohmesswerte sind noch nicht übergeben.
- **[BESTÄTIGT]:** Apache ECharts ist in der Datenplattform-Anforderungsbasis bereits als Chart-Technologie vorgesehen.
- **[VORSCHLAG]:** Vue 3/TypeScript, REST API, PostgreSQL mit optional PostGIS/TimescaleDB. **Kein** bereits genehmigtes SQL-Schema oder verpflichtender Technologiestack.
- **[OFFEN]:** echtes BEEP-API-Mapping/Auth, Basis-Firmwarestände, direkter TTN-Empfang, Datenexport-Vollständigkeit, Bodenfühlertypen und UI-Authentifizierung.

## Öffentliche Repo-Hygiene

Dieses Repository ist öffentlich. **Keine** privaten Messdaten, Stockkartenauszüge, genaue Bienenstandkoordinaten, TTN/BEEP-Tokens, Geräteschlüssel, Passwörter oder Kundendaten committen. Das Archiv `ZS_Test_261008.zip` wurde nicht übernommen: vorhandene Firmware/Tests sind bereits versioniert; Roharchiv nicht ohne Herkunfts- und Geheimnisprüfung veröffentlichen. Die Screenshots sind optional; die reproduzierbare HTML-Quelle hat Vorrang.

## Nachweispflicht

Claude soll in kleinem Branch/PR liefern: Änderungsklasse, Akzeptanzkriterien, Tests PASS/FAIL/SKIP, Grenzen, Basis-/Ergebnis-SHA. Kein „funktioniert produktiv“ aus lokalem HTML ableiten. Review durch ChatGPT erfolgt nach Bereitstellung eines überprüfbaren Commits/PRs, nicht automatisch durch diese Dokumentation.
