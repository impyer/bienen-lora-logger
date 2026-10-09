# Entwicklungsregeln – Einstieg

**Version:** 0.1 · **Status:** Diskussionsentwurf, noch nicht formal verabschiedet · **Stand:** 09.10.2026

Für das Projekt Bienen-logger gelten dieselben Grundsätze für Menschen und Coding-Agents: Änderungen müssen **nachvollziehbar**, **reproduzierbar**, **risikogerecht geprüft** und **lizenzrechtlich sauber** sein. Die folgenden Texte sind ein Vorschlag für den gemeinsamen Projektstandard. Bestehende Projektentscheidungen werden dadurch **nicht** rückwirkend überschrieben. Sobald das Regelwerk beschlossen ist, wird dieser Status zusammen mit dem Beschluss-Commit aktualisiert.

## Wo steht was?

| Dokument | Zweck |
|---|---|
| [Regelwerk und Zusammenarbeit](regelwerk.md) | Begriffe, Verbindlichkeit, Änderungsprozess, Rollen, Ausnahmen und Entscheidungskompetenz |
| [Hardware und Mechanik](hardware.md) | Schaltplan, Akku/Solar, PCB/PCBA, Sensor-/RF-Schnittstellen, Stückliste und sichere Muster |
| [Firmware, Formatter und Server](software.md) | Architektur, Codequalität, Zeit/Daten, Energie, Funk, Sicherheit, Konfiguration, APIs |
| [Prüfstrategie und Freigaben](tests-freigaben.md) | Teststufen, Nachweise, Entwicklungs-/HiL-/Feld-/Release-Gates, Rückverfolgbarkeit |
| [Open Source und Veröffentlichungen](open-source-releases.md) | Herkunft, Lizenzen, Beiträge, Sicherheit, reproduzierbare Releasepakete |
| [Beitragen](../../CONTRIBUTING.md) | Konkreter GitHub-Ablauf |
| [Änderungs-/PR-Checkliste](../../.github/pull_request_template.md) | Minimalnachweis direkt beim Review |
| [Entscheidungsvorlage](vorlagen/entscheidung.md) | Architecture Decision Record (ADR), auch für Sicherheitsanforderungen |
| [Prüfberichtsvorlage](vorlagen/pruefbericht.md) | Gleichförmige, commitbezogene Testergebnisse |

## Projektstufen und Freigaben

| Stufe | Bedeutung | Was ein grünes Ergebnis **nicht** bedeutet |
|---|---|---|
| **ENTWICKLUNG** | Quellstand und Host-/CI-Tests sind nachvollziehbar | keine Aussage zu echten elektrischen Messwerten |
| **LABORMUSTER** | Prüfling mit eindeutigem PCB-/Firmwarestand, sicherer HiL-Plan und erfüllten Sicherheitsvorbedingungen | keine Freigabe für unbeaufsichtigten Außenbetrieb |
| **FELDTEST** | definierter, beaufsichtigter/überwachter Einsatz mit Mess-/Rollbackplan | keine allgemeine Serien-/Produktzulassung |
| **RELEASE** | eingefrorene, reproduzierbare Hardware-/Softwareartefakte und abgeschlossene Gate-Nachweise | keine automatische CE-/RED-/EMV-Konformitätsaussage |

Freigaben und deren Mindestkriterien stehen verbindlich erst nach gemeinsamer Abnahme in [tests-freigaben.md](tests-freigaben.md). **Ein „bestanden“ aus einer Stufe gilt niemals stillschweigend auch für die nächste.**

## Aktuelle Ausgangslage (nur Kontext, kein neue Abnahme)

Die letzte Schaltplanprüfung betrifft [KiCad V0.1 bei `fcd18fe`](../testberichte/2026-10-09-schaltplan-v01-review.md). Es existieren bisher eine Akku-Platine und das Versorgungsblatt der Hauptplatine, keine vollständige MCU-/SX1262-/Sensor-Schaltung. Das **mögliche** Lade-Recovery-Problem `SCH26-01` ist als P0 für einen späteren Hardwareaufbau dokumentiert, nicht am Muster bestätigt. Das Regelwerk definiert den Umgang mit solchen Befunden; es erklärt sie nicht für erledigt.

## Offene Entscheidungen für eine Version 1.0

- **GOV-01:** Lizenzzuordnung von Python-Generatoren in `hardware/kicad/` klären; `LICENSE.md` ordnet `hardware/` CERN-OHL-S-2.0 zu, einige Python-Dateien deklarieren GPL-3.0-or-later. Eine Änderung der Lizenzhinweise benötigt eine Prüfung der Rechte und Zustimmung der jeweiligen Rechteinhaber.
- **GOV-02:** Wer gibt bei einem Ein-Personen-Projekt sicherheitskritische Änderungen verbindlich frei? Vorschlag: dokumentierter Selbstreview plus unabhängiger Fach-/Labornachweis, bei P0 keine Freigabe allein auf Basis eines KI-Reviews.
- **GOV-03:** Genauen Umfang der ersten öffentlichen Hardware-Fertigungsfreigabe festlegen (nur Dateien veröffentlichen oder vollständiges Open-Hardware-Rebuildpaket mit Bestückungs- und Prüfplan?).
- **GOV-04:** Schwellenwerte für Akku-/Energie-/RF-/Messgenauigkeit je tatsächlicher Zell-, Board- und Bauteilrevision in einer Testanforderung festschreiben. Das Regelwerk erfindet keine Grenzwerte.

**Änderungsvorschläge:** Issues oder Pull Requests mit Befund-/Entscheidungs-ID, Begründung und Auswirkung auf bestehende Releases einreichen. Für den finalen Beschluss `Status: angenommen`, Version und Beschluss-Commit eintragen.
