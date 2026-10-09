# Entwicklungsregeln – Einstieg

**Regelwerk 1.0:** ANGENOMMEN (09.10.2026) und derzeit auf `main` verbindlich. **Ergänzung 1.1:** Vorschlag [ADR-0002](entscheidungen/ADR-0002-regelwerk-review.md) nach [Claude E1–E12](../testberichte/2026-10-09-regelwerk-review.md), erst nach Merge verbindlich.

Für das Projekt Bienen-logger gelten dieselben Grundsätze für Menschen und Coding-Agents: Änderungen müssen **nachvollziehbar**, **reproduzierbar**, **risikogerecht geprüft** und **lizenzrechtlich sauber** sein. Die folgenden Texte sind der **verabschiedete Projektstandard für Menschen und Coding-Agents**. Er gilt für neue Änderungen und neu beanspruchte Freigaben. Bestehende Entscheidungen und historische Prüfergebnisse werden **nicht** rückwirkend überschrieben. [Beschluss ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md).

## Wo steht was?

| Dokument | Zweck |
|---|---|
| **[Pflichtteil auf einer Seite](PFLICHTTEIL.md)** | Zehn handhabbare Regeln für Menschen und Agents |
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
| [Governance-Register](entscheidungen.md) | GOV-01 bis GOV-04: erledigte und offene Entscheidungen |
| [Aktuelles Befundregister](../testberichte/befunde.md) | Git-SHA, Evidenzstatus, Gate-Sperren und nächste Prüfungen |
| [Ausnahmenregister](ausnahmen.md) | Legacy-API EX-01 mit Sicherheitsauflagen |
| [ADR-0002](entscheidungen/ADR-0002-regelwerk-review.md) | Übernahme von E1–E12 als eigener Änderungsvorschlag |

## Projektstufen und Freigaben

| Stufe | Bedeutung | Was ein grünes Ergebnis **nicht** bedeutet |
|---|---|---|
| **ENTWICKLUNG** | Quellstand und Host-/CI-Tests sind nachvollziehbar | keine Aussage zu echten elektrischen Messwerten |
| **LABORMUSTER** | Prüfling mit eindeutigem PCB-/Firmwarestand, sicherer HiL-Plan und erfüllten Sicherheitsvorbedingungen | keine Freigabe für unbeaufsichtigten Außenbetrieb |
| **FELDTEST** | definierter, beaufsichtigter/überwachter Einsatz mit Mess-/Rollbackplan | keine allgemeine Serien-/Produktzulassung |
| **RELEASE** | eingefrorene, reproduzierbare Hardware-/Softwareartefakte und abgeschlossene Gate-Nachweise | keine automatische CE-/RED-/EMV-Konformitätsaussage |

Freigaben und deren Mindestkriterien sind mit der Annahme in [tests-freigaben.md](tests-freigaben.md) verbindlich geregelt. **Ein „bestanden“ aus einer Stufe gilt niemals stillschweigend auch für die nächste.**

## Veränderlicher Projektstand

**Aktuelle** P0/P1-Punkte, tatsächlich eingecheckte Schaltungen und deren Teststatus stehen im [Befundregister](../testberichte/befunde.md), stets bezogen auf einen Git-SHA. Die hier geltenden Regeln sollen keine veralteten Befundstände für neue Agents festschreiben.

## Beschluss und verbliebene Entscheidungen

**Beschlossen:** [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md). Die Projektleitung verantwortet G0/G1. **G2 D3:** sicherer Laborzugang mit Risiko-/Versuchsplan, T3-Checks, Zell-Emulator/Strombegrenzung und unabhängiger Gegenprüfung des Plans. **T4 entsteht erst im Labor**; **G3/G4 D3** verlangen bestandene T4-Messungen und unabhängige fachkundige Safety-Bewertung. Kein Ki-/CI-Alleinentscheid.

[**Governance-Register**](entscheidungen.md): **GOV-01 OFFEN** (Lizenzierung der KiCad-Generatoren), **GOV-02 ANGENOMMEN** (vorläufige Gate-Zuständigkeit und D3-Sicherheit), **GOV-03 ANGENOMMEN** (vollständiges Open-Hardware-Fertigungspaket), **GOV-04 OFFEN** (konkrete Mess-/Sicherheitsgrenzen für beschaffte Komponenten).

**Praktische Durchsetzung:** im PR/Commit mit Test- und Reviewnachweis. GitHub-Branch-Protection ist durch den Beschluss **nicht** automatisch aktiviert. Änderungen an Sicherheits-/Freigabegrundsätzen werden via neue ADR beschlossen; historische Testberichte bleiben unverändert.
