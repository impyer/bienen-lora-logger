# Regeln für Coding-Agents

**Auf `main` gilt Regelwerk 1.0.** Die Ergänzung 1.1 ist ein separater Draft-PR. Einstieg: [Pflichtteil](docs/entwicklung/PFLICHTTEIL.md) · [Regelwerk](docs/entwicklung/README.md) · [aktuelles Befundregister](docs/testberichte/befunde.md) · [CLAUDE.md](CLAUDE.md).

1. **Vor Übergabe zwischen Mensch, Claude und ChatGPT** den lokalen Stand committen/pushen oder klar als ungepusht kennzeichnen. **Vor eigener Arbeit** Zielbranch/SHA, andere offene/ungepushte Änderungen, Regeln, IDs, [Befundregister](docs/testberichte/befunde.md) und [historische Testberichte](docs/testberichte/README.md) prüfen.
2. Änderungsklasse D0–D3, erforderliche T0–T6-Nachweise und betroffenes G0–G4-Gate benennen.
3. **Kein HiL/Feldtest behaupten ohne echte Messung.** **G2 bei D3:** sicherer Laboraufbau mit T0-/T3-Gefahren-/Designprüfung, strombegrenztem Zell-Emulator, dokumentiertem Versuchsplan und unabhängiger Prüfung des Plans. **G3/G4 bei D3:** einschlägige bestandene T4-Messungen plus vom Entwerfer unabhängige fachkundige Sicherheitsbewertung. **Keine festen Befund-Statuswerte in Agent-Regeln; maßgeblich ist das [Register](docs/testberichte/befunde.md).**
4. Führende Quellen bearbeiten: generierte KiCad-V0.1-Dateien über `hardware/kicad/*.py`, eigener Server über `server/eigen_anpassen.py`, TTN-Formatter über `formatter/formatter.js`.
5. Keine Schlüssel, Tokens, privaten Standorte oder unberechtigt übernommene fremde Quellen committen. **GOV-01**: widersprüchliche Lizenzhinweise an KiCad-Generatoren niemals stillschweigend umlizenzieren.
6. Ergebnis mit Baseline-/Ergebnis-SHA, Tests, PASS/FAIL/SKIP/NICHT GELAUFEN, Evidenzstufe, Sperr-Gate und erforderlichen HiL-Arbeiten dokumentieren. **Bei fremden uncommitted Änderungen kein Direktcommit auf `main`**; Branch/PR für Übergabe. `CLAUDE.md`/`CHANGELOG.md` zusammenführen, nicht überschreiben.

Beiträge: [CONTRIBUTING.md](CONTRIBUTING.md), [PR-Vorlage](.github/pull_request_template.md), [Gate-Matrix](docs/entwicklung/tests-freigaben.md). Keine autonome Freigabe sicherheitskritischer Fertigung.
