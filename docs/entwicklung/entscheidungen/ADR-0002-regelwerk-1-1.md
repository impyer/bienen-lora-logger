# ADR-0002 – Regelwerk 1.1: Befundregister, Statusmodell, D3-Gates, Übergabe, Lizenz

**Status:** ANGENOMMEN
**Datum:** 09.10.2026
**Entscheidend:** Maintainer Philipp Schnabel, nach [Review des Regelwerks 1.0 durch Claude](../../testberichte/2026-10-09-regelwerk-review.md)
**Vorgänger:** [ADR-0001](ADR-0001-projektregelwerk.md), Regelwerk 1.0 bei `8fc2aa4`
**Wirksamkeit:** ab dem Commit dieser ADR, für künftige Änderungen und neu beanspruchte Freigaben

## Anlass

Das Review von Regelwerk 1.0 fand einen Zirkelschluss bei den D3-Gates (Labornachweise als Voraussetzung für das Labor), eine unbestimmte „unabhängig fachkundige“ Prüfung, veränderliche Befundstände in normativen Texten und fehlende Regeln für die Übergabe zwischen Agents. Letzteres hat am 09.10.2026 zu zwei auseinanderlaufenden Ständen geführt (Regelwerk-Commit ohne die lokal noch nicht eingecheckte SCH26-Behebung).

## Beschluss

| Review-Punkt | Entscheidung | Umgesetzt in |
|---|---|---|
| E1 D3-Gates | G2: Gefährdungsanalyse, Netz-/ERC-Prüfung, sicherer Versuchsplan (Zell-Emulator, Strombegrenzung). G3/G4: zusätzlich T4-Messungen und unabhängiges Review | regelwerk R-09, tests-freigaben T-02/T-05, GOV-02 |
| E2 Unabhängig fachkundig | ein bis zwei befreundete Hardware-Entwickler des Maintainers, nicht Entwerfer der Änderung, schriftlicher Prüfbericht; Maintainer namentlich genannt | regelwerk R-09, GOV-02 |
| E3 Befundregister | zentrales Register `docs/testberichte/befunde.md`; Regeltexte nennen keine Befundstände | regelwerk R-05a, AGENTS.md, CLAUDE.md, hardware H-02 |
| E4 Statusmodell | offen / analysiert / im Entwurf behoben / nachgewiesen / geschlossen, mit gesperrtem Gate | regelwerk R-05a |
| E5 Übergabe | vor jedem Wechsel commit + push; Ausgangs-SHA nennen; ein Beteiligter je Stand | regelwerk R-06 Nr. 2, AGENTS.md |
| E6 Anforderungs-IDs | Lastenheft-Zeilen als `LH-…`; MUSS für D2/D3, SOLL für D1 | regelwerk R-03 |
| E7 Reproduzierbarkeit | Quellen und erzeugte Quelldateien byte-gleich; zeitgestempelte Exporte ausgenommen; KiCad-Hauptversion 10 festgelegt | regelwerk R-06 Nr. 5, hardware H-06 Nr. 2 |
| E8 Lizenz (GOV-01) | Skripte GPL-3.0-or-later; Schaltpläne/Symbole/Footprints/Exporte CERN-OHL-S-2.0 | GOV-01, open-source O-01, `LICENSE.md`, SPDX |
| E9 beelogger-Passwort | dokumentierte Ausnahme EX-01 | entscheidungen.md, software S-05 |

**Nicht übernommen bzw. offen:** E10 (Pflichtfelder je Prüfstufe), E11 (einseitige Kurzfassung) – ohne Entscheidung des Maintainers, bleiben Vorschläge.

## Auswirkungen

- Laborversuche am Akku-/Ladeteil sind möglich, sobald die D3-Befunde mindestens „im Entwurf behoben“ sind und der sichere Versuchsplan vorliegt; Feldbetrieb erst nach Messung und unabhängigem Review.
- Agents und Menschen pflegen Befundstände nur noch im Register.

**Überprüfung:** spätestens vor erster PCB-Bestellung und vor jedem Feldrelease.
