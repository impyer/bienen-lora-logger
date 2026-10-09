# Entwicklungsregeln – Einstieg

**Version:** 1.1 · **Status:** ANGENOMMEN; für neue Änderungen verbindlich · **Beschlussdatum:** 09.10.2026 · **Wirksam ab:** dem Annahme-Commit · **Maintainer:** Philipp Schnabel (`impyer`)

Für das Projekt Bienen-logger gelten dieselben Grundsätze für Menschen und Coding-Agents: Änderungen müssen **nachvollziehbar**, **reproduzierbar**, **risikogerecht geprüft** und **lizenzrechtlich sauber** sein. Die folgenden Texte sind der **verabschiedete Projektstandard für Menschen und Coding-Agents**. Er gilt für neue Änderungen und neu beanspruchte Freigaben. Bestehende Entscheidungen und historische Prüfergebnisse werden **nicht** rückwirkend überschrieben. [Beschluss ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md).

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
| [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md) | Beschluss, Geltungsbereich, Einschränkungen |
| [ADR-0002](entscheidungen/ADR-0002-regelwerk-1-1.md) | Fassung 1.1 nach Review: Befundregister, Statusmodell, D3-Gates, Übergabe, Lizenz |
| [Governance- und Ausnahmeregister](entscheidungen.md) | GOV-01 bis GOV-04, Ausnahmen EX-… |
| [Befundregister](../testberichte/befunde.md) | **einzige Stelle** für den aktuellen Stand aller Befunde (Statusmodell R-05a) |

## Projektstufen und Freigaben

| Stufe | Bedeutung | Was ein grünes Ergebnis **nicht** bedeutet |
|---|---|---|
| **ENTWICKLUNG** | Quellstand und Host-/CI-Tests sind nachvollziehbar | keine Aussage zu echten elektrischen Messwerten |
| **LABORMUSTER** | Prüfling mit eindeutigem PCB-/Firmwarestand, sicherer HiL-Plan und erfüllten Sicherheitsvorbedingungen | keine Freigabe für unbeaufsichtigten Außenbetrieb |
| **FELDTEST** | definierter, beaufsichtigter/überwachter Einsatz mit Mess-/Rollbackplan | keine allgemeine Serien-/Produktzulassung |
| **RELEASE** | eingefrorene, reproduzierbare Hardware-/Softwareartefakte und abgeschlossene Gate-Nachweise | keine automatische CE-/RED-/EMV-Konformitätsaussage |

Freigaben und deren Mindestkriterien sind mit der Annahme in [tests-freigaben.md](tests-freigaben.md) verbindlich geregelt. **Ein „bestanden“ aus einer Stufe gilt niemals stillschweigend auch für die nächste.**

## Aktuelle Ausgangslage

Der Stand aller Befunde steht im [Befundregister](../testberichte/befunde.md), die Prüfberichte in [`docs/testberichte/`](../testberichte/README.md). Dieses Dokument nennt bewusst keine einzelnen Befundstände (R-05a).

## Beschluss und verbliebene Entscheidungen

**Beschlossen:** [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md) (1.0) und [ADR-0002](entscheidungen/ADR-0002-regelwerk-1-1.md) (1.1). Der Maintainer verantwortet G0–G2. Für D3-Gefahren darf G3/G4 **nicht** allein aus Selbstreview, KI-Review oder CI freigegeben werden; T4-Messungen und ein unabhängiges fachkundiges Review sind nachzuweisen.

[**Governance-Register**](entscheidungen.md): **GOV-01 ENTSCHIEDEN** (Skripte GPL, Hardwaredaten CERN-OHL-S), **GOV-02 ANGENOMMEN** (Gate-Zuständigkeit, D3-Gates), **GOV-03 ANGENOMMEN** (Open-Hardware-Fertigungspaket), **GOV-04 OFFEN** (Grenzwerte der beschafften Bauteile). Ausnahme **EX-01** (beelogger-Passwort im GET).

**Praktische Durchsetzung:** im PR/Commit mit Test- und Reviewnachweis; Übergabe zwischen Beteiligten nur über gepushte Stände (R-06 Nr. 2). GitHub-Branch-Protection ist durch den Beschluss **nicht** automatisch aktiviert. Änderungen an Sicherheits-/Freigabegrundsätzen werden via neue ADR beschlossen; historische Testberichte bleiben unverändert.
