# Aktuelles Befundregister

**Baseline:** GitHub-`main` bei [`428d101`](https://github.com/impyer/bienen-lora-logger/commit/428d1014305b27c4daf7c3f72946ea86e6d04735). **Lokaler, nicht gepushter Claude-Arbeitsstand ist ausdrücklich nicht enthalten.** Dieses Dokument ist eine **arbeitsbezogene Momentaufnahme**; vor jeder Prüfung an neuem SHA aktualisieren. Historische [Berichte](README.md) nicht nachträglich überschreiben.

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
| **SCH26-01** | **P0** | **ANALYSIERT – mögliche Lade-Recovery-Blockade**, nicht T4-getestet. Laut [Claude-Review](2026-10-09-regelwerk-review.md) lokal behoben, **noch nicht auf `main`** | G2 nur nach geprüftem sicherem Laborplan; G3/G4 bis T4-Lade-Recovery und unabhängiger Sicherheitsbewertung blockiert |
| SCH26-02 | P1 | ANALYSIERT – Gate-/CE-Leckstrom der 10-MΩ-Kette | G3/G4: Grenz-/Temperatur-/HiL-Prüfung |
| SCH26-03 | P1 | ANALYSIERT – einzelfehlerbedingte Lade-Übertemperatur | G3/G4: Sicherheits-/Fault-Nachweis |
| SCH26-04 | P1 | **TEILWEISE IM ENTWURF BEHOBEN (T3)** – KiCad-CI nun grün, finale Footprints/Warnungsinventar offen | G4/Fertigung: vollständige Footprints + Warnungsabnahme; [CI](https://github.com/impyer/bienen-lora-logger/actions/runs/37880579725) |
| SCH26-05 | P2 | ANALYSIERT – R208 Pull-down von Sollwert abweichend | G3/G4 abhängig von Off-State-HiL |
| SCH26-06 | P2 | ANALYSIERT – JST-Batteriekabel nur logisch geprüft | G4: Kabelplan und Durchgangstest |
| SCH26-07 | P2 | ANALYSIERT – fehlende MCU-/Funk-/Sensorblätter | G4: vollständiger Schaltplan, ERC/DRC |
| SCH26-08 | P2 | ANALYSIERT – PV/Surge/Derating offen | G4: Datenblatt- und Eingangstests |

**Fundstellen und Tests:** [Review Schaltplan V0.1](2026-10-09-schaltplan-v01-review.md). Andere `HW26-*`, `FW26-*`, `SRV26-*`, `CI26-*` stehen noch in historischen Berichten: sie sind **nicht automatisch geschlossen**, nur weil sie hier nicht einzeln stehen.

## Aktualisierung bei Agent-Übergabe

1. Tatsächlichen Zielbranch/SHA abgleichen und lokale Fremdänderungen erst nach Commit/Push übernehmen.
2. Befund-ID mit Quellenstand, Status, erreichter **T-Stufe**, blockiertem **G-Gate** und Link zum Fix/Prüfprotokoll aktualisieren.
3. Nach Commit/CI höchstens **IM ENTWURF BEHOBEN** eintragen; Labor/Feld erst **NACHGEWIESEN**, wenn real durchgeführt.
4. Gate-Owner-Entscheid für **GESCHLOSSEN** dokumentieren. **Historische Testberichte bleiben unverändert**.
