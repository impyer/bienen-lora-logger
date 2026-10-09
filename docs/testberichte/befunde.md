# Aktuelles Befundregister

**Baseline:** GitHub-`main` bei [`6dbba8d`](https://github.com/impyer/bienen-lora-logger/commit/6dbba8d6bd5d255b94fc4c396584508698f3100d). Das ist eine **arbeitsbezogene Momentaufnahme**. Claude hat generierte KiCad-Schaltungen und Hilfsprüfungen committed, **die führenden Python-Generatoren aber nicht angepasst**. [GitHub-CI 37881512633](https://github.com/impyer/bienen-lora-logger/actions/runs/37881512633) meldet deshalb **6/7 Jobs erfolgreich, KiCad-Diff fehlgeschlagen**. Technische Status erst nach synchronisiertem Generatorstand aktualisieren. Historische [Berichte](README.md) nicht nachträglich überschreiben.

## Befundstatus nach Nachweis

| Status | Erforderliche Begründung |
|---|---|
| **OFFEN** | Sachverhalt/Fehler noch nicht hinreichend eingegrenzt |
| **ANALYSIERT – bestätigt / Hypothese / verworfen** | Konkrete statische, analytische oder Testevidenz; Unsicherheit klar benennen |
| **IM ENTWURF BEHOBEN (T0–T3)** | Fix auf **referenziertem Git-SHA**, Code-/Netzprüfung und geeignete Host-/KiCad-Tests vorhanden; **kein** T4-Nachweis |
| **NACHGEWIESEN (T4/T5)** | Tatsächlich bestandene Labor-/Feldprüfung mit Prüfling, Setup, Messwerten und Test-ID |
| **GESCHLOSSEN** | Gate-Owner dokumentiert nachvollziehbare Schlussentscheidung auf Basis der erforderlichen Belege |

**Zusätzlich pro Befund:** P0–P3, blockiertes Gate G0–G4, Hardware-/Firmwarerevision, zuständige Person und nächster Prüfschritt. **Geschlossen** ist nicht gleich **im Entwurf korrigiert**. Eine widerlegte Hypothese darf mit Nachweis geschlossen werden; nicht nur umbenennen.

## Offene Schaltplanpunkte auf der genannten GitHub-Baseline

| ID | Prio | Status auf Baseline | Sperre / erforderlicher Nachweis |
|---|---|---|---|
| **SCH26-01** | **P0** | **ANALYSIERT – bestätigter Entwurfsfehler, Fix nur im generierten KiCad-Schaltplan auf `6dbba8d`**. FÜHRENDE PYTHON-QUELLEN UNVERÄNDERT; T3-Reproduktion **FAIL**. Keine Hardwaremessung. | G1 der betroffenen D3-Schaltplanänderung und ungesicherter G2-Aufbau gesperrt. Nach konsistenten Quellen und sicherem Plan gezieltes G2-Labor; G3/G4 bis T4 und unabhängiger Sicherheitsprüfung blockiert. [Issue #2](https://github.com/impyer/bienen-lora-logger/issues/2) |
| SCH26-02 | P1 | **Korrektur nur im generierten KiCad: 100 kΩ**; Python-Quelle enthält weiterhin 10 MΩ, T3 FAIL | G1 für Entwurfskonsistenz; G3/G4 bis Strom-/Temperatur-/HiL-Prüfung. [Issue #2](https://github.com/impyer/bienen-lora-logger/issues/2) |
| SCH26-03 | P1 | **Zweiter TMP390 nur im generierten Schaltplan**, nicht im Python-Generator; T3 FAIL | G1 für Entwurfskonsistenz; G3/G4 bis T4-Fault-Injection und unabhängigen Safety-Nachweis. [Issue #2](https://github.com/impyer/bienen-lora-logger/issues/2) |
| SCH26-04 | P1 | **REGRESSION:** KiCad-CI bei `6dbba8d` ROT; `pruefen.sh` ist alt, neue ERC-/Netzprüfer liegen separat, werden nicht aufgerufen | G1: [CI-Fehler](https://github.com/impyer/bienen-lora-logger/actions/runs/37881512633), [Issue #2](https://github.com/impyer/bienen-lora-logger/issues/2). G4 weiterhin gesperrt wegen fehlender Footprints |
| SCH26-05 | P2 | **100 kΩ nur im generierten Schaltplan**, Python-Generator noch 1 MΩ | G1 Quellkonsistenz; G3/G4 abhängig von Off-State-HiL |
| SCH26-06 | P2 | ANALYSIERT – JST-Batteriekabel nur logisch geprüft | G4: Kabelplan und Durchgangstest |
| SCH26-07 | P2 | ANALYSIERT – fehlende MCU-/Funk-/Sensorblätter | G4: vollständiger Schaltplan, ERC/DRC |
| SCH26-08 | P2 | ANALYSIERT – PV/Surge/Derating offen | G4: Datenblatt- und Eingangstests |
| **REG26-13** | **P0 – G1/G2 für Akku-Schaltplan** | **BESTÄTIGT: führende Generatoren und `pruefen.sh` unverändert, generierte `.kicad_sch` geändert**; CI-Schritt `git diff` FAIL. Das ist kein reiner Layout-Diff, sondern betrifft die Laderegel-/Sicherheitslogik. | [Issue #2 – konkrete Behebung und Akzeptanztests](https://github.com/impyer/bienen-lora-logger/issues/2), [Review-Regression 6dbba8d](2026-10-09-sch26-generator-regression.md) |


**Fundstellen und Tests:** [Review Schaltplan V0.1](2026-10-09-schaltplan-v01-review.md) und [neuer Regressionstest 6dbba8d](2026-10-09-sch26-generator-regression.md). Andere `HW26-*`, `FW26-*`, `SRV26-*`, `CI26-*` stehen noch in historischen Berichten: sie sind **nicht automatisch geschlossen**, nur weil sie hier nicht einzeln stehen.

## Aktualisierung bei Agent-Übergabe

1. Tatsächlichen Zielbranch/SHA abgleichen und lokale Fremdänderungen erst nach Commit/Push übernehmen.
2. Befund-ID mit Quellenstand, Status, erreichter **T-Stufe**, blockiertem **G-Gate** und Link zum Fix/Prüfprotokoll aktualisieren.
3. Nach Commit/CI höchstens **IM ENTWURF BEHOBEN** eintragen; Labor/Feld erst **NACHGEWIESEN**, wenn real durchgeführt.
4. Gate-Owner-Entscheid für **GESCHLOSSEN** dokumentieren. **Historische Testberichte bleiben unverändert**.
