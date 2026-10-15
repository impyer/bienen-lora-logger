# Entwicklungsübergabe für Claude – nächster Arbeitsschritt

**Branch-Kontext:** `docs/webplattform-handoff-2026-10-15`; Basis-Main `0142d39df2c3c4cbf6d1d427466589565035c495` (14.10.2026).  
**Achtung:** Öffentlicher Code, keine produktiven Messdaten/Schlüssel. Umsetzung nur in eigenem Branch/PR; Hauptzweig unverändert lassen.

## Erst lesen

1. Root [CLAUDE.md](../../CLAUDE.md), [AGENTS.md](../../AGENTS.md), [Entwicklungsregelwerk](../entwicklung/README.md) und [Befundregister](../testberichte/befunde.md).
2. [Datenplattform-Anforderungen](../architektur/anforderungen-datenplattform.md), vorhandene Architekturentwürfe sowie [Webplattform-Index](README.md), [UI-Spezifikation](ui-anforderungen.md), [Datenverträge](datenvertraege.md), [BEEP-Migration](beep-migration.md).
3. HTML-Demo `web/prototypes/Bienenlogger_UI_MVP_v0_3.html` lokal prüfen. Alle dort gezeigten Werte sind synthetisch.

## Arbeitsauftrag – erste kleine, überprüfbare Lieferung (UI-MVP)

- Bestehenden `server/`-Stack und seine Generatorquelle `server/eigen_anpassen.py` **nicht** ungeprüft umbauen.
- Bestandsaufnahme der vorhandenen CSV-/PHP-Endpunkte (Auth, Zeitstempel, Datenformate, CORS, fehlende Werte) und BEEP-Anbindung als technische Notiz erstellen.
- Eine **separat startbare, responsive** UI-Ausführung auf Basis des MVP skizzieren bzw. implementieren: Standübersicht mit Kacheln/Liste und Volk-Cockpit. BEEP-ähnliche Beutensymbole als **eigene** grafische Darstellung; Bildrechte beachten.
- Dynamisches Channel Registry-Modell für Gewichte, Stocktemperatur/-feuchte/-akustik und 3 Bodentemperaturen; neue Kanalinstanzen ohne Änderung von Tabellenstruktur oder Kern-Kachelkomponente zulassen.
- Ereignisoverlay: Icons + durchgehende senkrechte Hilfslinien, gemeinsame X-Achse und *pro physikalischer Größe* klare Y-Achsen/Spuren. Ein nachgetragenes Ereignis liegt bei `event_occurred_at`, nicht bei `created_at`.
- Während des Prototyping ausschließlich synthetische Fixtures/Mocks verwenden, bis autorisierte echte API-Daten vorliegen. Keine Datenbank-, Firm- oder Geräte-Migration ohne separate Freigabe.
- Optional: Umweltbereich und Flugkreise als **klar markierte Demo** mit leeren/gefilterten States.

## Testbare Akzeptanzkriterien (Abnahme für diesen PR)

- [ ] Kachel/Liste, Stand- und Volkauswahl sowie sinnvolle Leerzustände.
- [ ] Ein neu registrierter Kanal erscheint automatisch in Kacheloptionen bzw. Sensor-/Chartauswahl, sofern fachlich passend.
- [ ] Drei Bodenkanäle werden **ohne erfundene Tiefen** separat geführt.
- [ ] Stockmessgerät nicht falsch gleichzeitig als beelogger und BEEP Base einem Volk zugewiesen (bestehender Normalfall).
- [ ] Ereignissymbole, Hilfslinien und zeitgenaue Tooltips in derselben zeitlichen Koordinate; fehlende Werte bleiben Lücken.
- [ ] Stocktemperatur, Gewicht, Niederschlag und Feuchte nicht mit gemeinsamer unbeschrifteter Skala gemischt.
- [ ] Quell- und Qualitätskennzeichnung, UTC und Datum/Lokalanzeige getestet (Sommer-/Winterzeit).
- [ ] Keine Secrets, privaten Daten oder unberechtigt kopierten BEEP-/beelogger-Dateien.
- [ ] Ausführ- und Testanleitung plus automatisierte relevante Tests, genaue PASS/FAIL/SKIP-Angaben im PR.
- [ ] Keine unbegründeten Aussagen über live TTN, BEEP-API, Bodensensoren oder produktive Tests.

## Architekturgrenzen

Fachliche Tabellen/Interfaces erst mit nachvollziehbarer ADR und Maintainer-Freigabe festlegen. Der Bestand enthält bereits verbindliche Entscheidungen zu Messgrößen und ECharts – nicht rückgängig machen. Abgeleitete Größen enthalten Methode, Quellversion und Datenabdeckung. D0/D1/D2-Klassifikation anhand tatsächlicher Änderung, nicht nur anhand Zeilenzahl.

## Übergabe an ChatGPT zur unabhängigen Prüfung

Nach Fertigstellung **Commit/PR-Link, Ziel- und Ausgangs-SHA, Änderungsumfang, Testausgaben und offene Fragen** bereitstellen. ChatGPT prüft dann den GitHub-Diff und die Tests gegen diese Anforderungen und schreibt einen überprüfbaren Reviewbericht / PR-Kommentar. Der reine Existenzstatus dieses Dokuments startet **noch keine laufende Prüfung**; produktive Freigaben bleiben beim Maintainer.
