# ADR-0001 – Entwicklungsregelwerk 1.0 verbindlich einführen

**Status:** ANGENOMMEN  
**Datum:** 09.10.2026  
**Entscheidend:** Projektverantwortliche/Projektleitung, ausdrückliche Zustimmung in der Projektunterhaltung  
**Geltungsbereich:** `impyer/bienen-lora-logger`, Hardware, Mechanik, Firmware, LoRaWAN, Server, Formatter, Dokumentation und Tests  
**Vorgänger:** [Entwurf 0.1 bei `72e4f79`](https://github.com/impyer/bienen-lora-logger/commit/72e4f79f54d093623d2506007ef05dcbadc267c6)  
**Wirksamkeit:** ab dem Commit der Annahme von Regelwerk 1.0, für **künftige Änderungen und neu beanspruchte Freigaben**.

## Anlass

Bienen-logger umfasst eine 18650-Akku-/Ladeschaltung, eine eigene KiCad-Platine, STM32-/LoRaWAN-Firmware und Backend-Software. Ein erfolgreicher Kompiliervorgang, ein grüner ERC, ein analytischer SiL-Test und ein sicherer Feldbetrieb sind unterschiedliche Evidenzstufen. Menschliche und automatisierte Beiträge brauchen dieselben nachvollziehbaren Regeln.

## Beschluss

1. [Regelwerk 1.0](../regelwerk.md), [Hardware](../hardware.md), [Software](../software.md), [Tests und Freigaben](../tests-freigaben.md) sowie [Open Source](../open-source-releases.md) sind der **verbindliche Projektstandard**.
2. Risiken werden nach D0–D3, Nachweise T0–T6 und Freigaben G0–G4 dokumentiert. Alle Ergebnisangaben beziehen sich auf einen konkreten SHA/Zielstand und nennen ausgeführte und ausstehende Tests.
3. G0/G1 verantwortet der Projekt-Maintainer. Für **D3-Schutzfunktionen** dürfen G2–G4 nicht ohne unabhängig fachkundig geprüfte Sicherheitsanalyse und erforderliche reale bzw. gleichwertige Labor-Nachweise freigegeben werden. Coding-Agents und allgemeine CI können nicht allein freigeben.
4. Unvollständige KiCad-Entwürfe dürfen nur ausdrücklich **experimentell/nicht fertigungsreif** veröffentlicht werden. Für einen Fertigungsrelease sind editierbare Originalquellen, dokumentierte Exporte, Montageinformationen und die zugehörigen Prüfberichte nötig.
5. **GOV-01** (Lizenzfrage der KiCad-Python-Generatoren) und **GOV-04** (tatsächliche Zell-/Bauteil-Grenzwerte) bleiben offen und sind im [Entscheidungsregister](../entscheidungen.md) verzeichnet. Lizenzhinweise oder Rechte werden durch diese Entscheidung nicht verändert.
6. Alte Projektentscheidungen und historische Testergebnisse bleiben erhalten. Das Regelwerk erklärt keine früheren Geräte nachträglich als geprüft.

## Umsetzung und Einschränkungen

Die Projektleitung prüft die Anwendung durch nachvollziehbare Commits/PRs und Testberichte. Die vorhandene GitHub-CI deckt Teilbereiche ab; **eine technische Durchsetzung via Branch-Protection oder mandatory Reviewer ist durch diese ADR nicht eingerichtet** und darf nicht behauptet werden.

Der offene P0-Schaltplanbefund `SCH26-01` bleibt auch nach dieser Regelwerksannahme offen; keine Akkuschutz-/PCB-/Feldfreigabe wird dadurch ausgesprochen. Abweichungen erfolgen gemäß R-08; Änderungen an Sicherheits-/Freigabeprinzipien erfordern eine neue ADR.

**Überprüfung:** spätestens vor erster PCB-Bestellung und vor jedem Feldrelease.
