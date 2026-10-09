# Regeln für Coding-Agents

**Verbindlicher Projektstandard:** [Entwicklungsregelwerk 1.1](docs/entwicklung/README.md) · [CLAUDE.md](CLAUDE.md) · [Entscheidungsregister](docs/entwicklung/entscheidungen.md).

1. **Übergabe:** zuerst `git pull`, Ausgangs-SHA nennen; am Ende committen und pushen bzw. dem Maintainer zum Commit übergeben, bevor ein anderer Beteiligter arbeitet (R-06 Nr. 2). Nie auf einem Stand aufbauen, von dem lokale, nicht eingecheckte Änderungen bekannt sind.
2. Relevante Regeln, Anforderungs-IDs (`LH-…`, `REQ-…`), das [Befundregister](docs/testberichte/befunde.md) und die [Prüfberichte](docs/testberichte/README.md) vor jeder Änderung prüfen. **Befundstände nur im Register pflegen.**
3. Änderungsklasse D0–D3, erforderliche T0–T6-Nachweise und betroffenes G0–G4-Gate benennen.
4. **Kein HiL/Feldtest behaupten ohne echte Messung.** Bei Lithium-Akku, Lade-/Tiefentladeschutz und anderem D3-Gefahrenpotenzial: G2 nur mit Gefährdungsanalyse und sicherem Versuchsplan; G3/G4 nur mit T4-Messungen und unabhängigem fachkundigem Review (R-09).
5. Führende Quellen bearbeiten: generierte KiCad-V0.1-Dateien über `hardware/kicad/*.py`, eigener Server über `server/eigen_anpassen.py`, TTN-Formatter über `formatter/formatter.js`.
6. Keine Schlüssel, Tokens, privaten Standorte oder unberechtigt übernommene fremde Quellen committen. Lizenz nach **GOV-01**: neue `*.py`/`*.sh` mit `SPDX-License-Identifier: GPL-3.0-or-later`; Schaltplan-/Symbol-/Footprint-Daten sind CERN-OHL-S-2.0.
7. Ergebnis mit exakt geprüften Commits, Tests, PASS/FAIL/SKIP/NICHT GELAUFEN, Einschränkungen und erforderlichen HiL-Arbeiten dokumentieren.

Beiträge: [CONTRIBUTING.md](CONTRIBUTING.md), [PR-Vorlage](.github/pull_request_template.md), [Gate-Matrix](docs/entwicklung/tests-freigaben.md). Keine autonome Freigabe sicherheitskritischer Fertigung.
