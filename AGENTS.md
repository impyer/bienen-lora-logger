# Regeln für Coding-Agents

**Verbindlicher Projektstandard:** [Entwicklungsregelwerk 1.0](docs/entwicklung/README.md) · [CLAUDE.md](CLAUDE.md) · [Entscheidungsregister](docs/entwicklung/entscheidungen.md).

1. Aktuellen `main`-SHA, relevante Regeln, Anforderungs-/Befund-IDs und [Prüfberichte](docs/testberichte/README.md) vor jeder Änderung prüfen.
2. Änderungsklasse D0–D3, erforderliche T0–T6-Nachweise und betroffenes G0–G4-Gate benennen.
3. **Kein HiL/Feldtest behaupten ohne echte Messung.** Bei Lithium-Akku, Lade-/Tiefentladeschutz und anderem D3-Gefahrenpotenzial sind unabhängige fachkundige Prüfung und geeignete Labornachweise vor sicherheitsbezogener Hardwarefreigabe erforderlich. `SCH26-01` bleibt ein offenes P0.
4. Führende Quellen bearbeiten: generierte KiCad-V0.1-Dateien über `hardware/kicad/*.py`, eigener Server über `server/eigen_anpassen.py`, TTN-Formatter über `formatter/formatter.js`.
5. Keine Schlüssel, Tokens, privaten Standorte oder unberechtigt übernommene fremde Quellen committen. **GOV-01**: widersprüchliche Lizenzhinweise an KiCad-Generatoren niemals stillschweigend umlizenzieren.
6. Ergebnis mit exakt geprüften Commits, Tests, PASS/FAIL/SKIP/NICHT GELAUFEN, Einschränkungen und erforderlichen HiL-Arbeiten dokumentieren.

Beiträge: [CONTRIBUTING.md](CONTRIBUTING.md), [PR-Vorlage](.github/pull_request_template.md), [Gate-Matrix](docs/entwicklung/tests-freigaben.md). Keine autonome Freigabe sicherheitskritischer Fertigung.
