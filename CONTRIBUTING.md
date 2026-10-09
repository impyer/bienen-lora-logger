# Mitwirken am Bienen-logger

Das Projekt verbindet quelloffene **Firmware, TTN-Formatter, Server und eigene Hardware/Mechanik**. Neue Mitwirkende sind willkommen – besonders unabhängige technische Gegenprüfungen und reproduzierbare Testfälle.

**Vor dem ersten PR bitte lesen:**
- [Entwicklungsregeln – Einstieg](docs/entwicklung/README.md) (**Version 1.0: seit 09.10.2026 angenommen und für neue Änderungen verbindlich**)
- [Projektregelwerk](docs/entwicklung/regelwerk.md)
- [Teststrategie/Freigabestufen](docs/entwicklung/tests-freigaben.md)
- [Lizenzübersicht](LICENSE.md) und [Testberichte/offene Befunde](docs/testberichte/README.md)
- [Sicherheitshinweise](SECURITY.md)

## So reichst du eine Änderung ein

1. Prüfe den aktuellen `main`-Commit und ob es bereits einen Befund oder eine Projektentscheidung zum Thema gibt.
2. Beschreibe die Änderung und nenne bei Fehlerbehebungen die **Befund-ID**; bei neuen Funktionen ein nachvollziehbares Soll und einen Testfall.
3. Halte den Patch klein und verwende die **führende Quelle**: Firmware/Formatter wie dokumentiert, abgeleiteten Server aus dem Generator, KiCad-V0.1-Schaltung aus den Python-Generatoren. **Keine Handänderung nur in generierten Dateien.**
4. Ergänze Tests/Negativtests und dokumentiere klar, ob es Host-/SiL-/Build-/HiL- oder Feldnachweise sind. Das tatsächliche Git-SHA gehört zu Ergebnissen.
5. Führe die relevanten Tests aus und hänge den Nachweis an den PR. Typische Befehle:

   ```bash
   bash tests/alle_tests_linux.sh
   python3 hardware/energiebilanz.py
   python3 hardware/mikrofon_filter.py
   python3 hardware/i2c_leitung.py
   # Falls KiCad 10 installiert:
   bash hardware/kicad/pruefen.sh
   git diff -- hardware/kicad/
   ```

6. Fülle die [PR-Vorlage](.github/pull_request_template.md) aus. „Nicht ausgeführt“ ist eine zulässige **ehrliche** Angabe, kein bestandenes Ergebnis.
7. Besondere Anforderungen: keine sensiblen Daten; ursprüngliche Urheber-/Lizenzhinweise erhalten; keine fremden nichtoffenen PCB-Dateien kopieren.

## Ein-Personen- und KI-Beiträge

Auch beim Einzelentwickler hilft der PR als nachvollziehbares Reviewprotokoll. Claude und andere Coding-Agents sollen dieselben Test- und Sicherheitsregeln anwenden, keine tatsächlichen Messwerte erfinden und sicherheitsrelevante Entscheidungen nicht eigenständig freigeben.

**Wichtig:** Bei Arbeiten an Akku-/Ladeschaltungen sind Datenblatt- und sicherheitsgerichtete Messungen vor der Fertigungsfreigabe zwingender als eine grüne allgemeine CI.
