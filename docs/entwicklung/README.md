# Entwicklungsregeln – Einstieg

**Version:** 1.0 · **Status:** ANGENOMMEN; für neue Änderungen verbindlich · **Beschlussdatum:** 09.10.2026 · **Wirksam ab:** dem Annahme-Commit

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
| [Governance-Register](entscheidungen.md) | GOV-01 bis GOV-04: erledigte und offene Entscheidungen |

## Projektstufen und Freigaben

| Stufe | Bedeutung | Was ein grünes Ergebnis **nicht** bedeutet |
|---|---|---|
| **ENTWICKLUNG** | Quellstand und Host-/CI-Tests sind nachvollziehbar | keine Aussage zu echten elektrischen Messwerten |
| **LABORMUSTER** | Prüfling mit eindeutigem PCB-/Firmwarestand, sicherer HiL-Plan und erfüllten Sicherheitsvorbedingungen | keine Freigabe für unbeaufsichtigten Außenbetrieb |
| **FELDTEST** | definierter, beaufsichtigter/überwachter Einsatz mit Mess-/Rollbackplan | keine allgemeine Serien-/Produktzulassung |
| **RELEASE** | eingefrorene, reproduzierbare Hardware-/Softwareartefakte und abgeschlossene Gate-Nachweise | keine automatische CE-/RED-/EMV-Konformitätsaussage |

Freigaben und deren Mindestkriterien sind mit der Annahme in [tests-freigaben.md](tests-freigaben.md) verbindlich geregelt. **Ein „bestanden“ aus einer Stufe gilt niemals stillschweigend auch für die nächste.**

## Aktuelle Ausgangslage (nur Kontext, kein neue Abnahme)

Die letzte Schaltplanprüfung betrifft [KiCad V0.1 bei `fcd18fe`](../testberichte/2026-10-09-schaltplan-v01-review.md). Es existieren bisher eine Akku-Platine und das Versorgungsblatt der Hauptplatine, keine vollständige MCU-/SX1262-/Sensor-Schaltung. Das **mögliche** Lade-Recovery-Problem `SCH26-01` ist als P0 für einen späteren Hardwareaufbau dokumentiert, nicht am Muster bestätigt. Das Regelwerk definiert den Umgang mit solchen Befunden; es erklärt sie nicht für erledigt.

## Beschluss und verbliebene Entscheidungen

**Beschlossen:** [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md). Die Projektleitung verantwortet G0/G1. Für D3-Gefahren darf G2–G4 **nicht** allein aus Selbstreview, KI-Review oder CI freigegeben werden; die erforderliche fachkundige Gegenprüfung und Labor-Evidenz sind nachzuweisen.

[**Governance-Register**](entscheidungen.md): **GOV-01 OFFEN** (Lizenzierung der KiCad-Generatoren), **GOV-02 ANGENOMMEN** (vorläufige Gate-Zuständigkeit und D3-Sicherheit), **GOV-03 ANGENOMMEN** (vollständiges Open-Hardware-Fertigungspaket), **GOV-04 OFFEN** (konkrete Mess-/Sicherheitsgrenzen für beschaffte Komponenten).

**Praktische Durchsetzung:** im PR/Commit mit Test- und Reviewnachweis. GitHub-Branch-Protection ist durch den Beschluss **nicht** automatisch aktiviert. Änderungen an Sicherheits-/Freigabegrundsätzen werden via neue ADR beschlossen; historische Testberichte bleiben unverändert.
