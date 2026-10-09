# Audit: bisherige Arbeitsergebnisse gegen das Entwicklungsregelwerk (09.10.2026)

- **Prüfbericht-ID:** AUD-2026-10-09-01
- **Prüfdatum (UTC):** 2026-10-09, ca. 03:50
- **Maßstab:** Regelwerk 1.1 in der vom Maintainer entschiedenen Fassung (ADR-0002). Auf `main` liegt noch 1.0; wo das einen Unterschied macht, steht es dabei.
- **Geprüfte Stände:**
  - `main` = `428d101` („Regelwerk“, Vorgänger `8fc2aa4`). Ermittelt aus Reflog und Git-Objekten des lokalen Klons; das lokale Arbeitsverzeichnis entsprach diesem Stand.
  - Arbeitskopie von Claude mit der Behebung SCH26 und den Zusammenführungsdateien (siehe REG26-01).
- **Teststufe:** T0 (statisches Review von Dokumenten, Commits und Quellen). Ergänzend T3: `hardware/kicad/pruefen.sh` und die Rechenskripte in der Arbeitskopie.
- **Person / zweiter Prüfweg:** Claude (Agent). Ein zweiter Prüfweg steht aus.
- **Nicht geprüft:**
  - GitHub-Actions-Ergebnis zu `428d101` (kein Zugriff)
  - Firmware-Quelltext im Detail (nur Stichprobe der Toolchain-Doku)
  - `SECURITY.md`

## 1. Ergebnis

Die Arbeitsergebnisse folgen in den Grundsätzen dem Regelwerk:
- Generatoren sind die führende Quelle.
- Kein erfundener HiL-Nachweis.
- Annahmen sind gekennzeichnet (V/A/P).
- Tests hängen nicht von der Uhrzeit ab.
- Keine Geheimnisse im Repository.
- Keine kopierten Datenblätter.

**Es gibt aber einen schwerwiegenden Prozessbefund (REG26-01):**
- Die Behebung des P0-Befunds SCH26-01 ist am 09.10.2026 um 05:25 Ortszeit durch ein „reset: moving to HEAD“ vor dem `git pull` aus dem Arbeitsverzeichnis verschwunden.
- `main` enthält deshalb den Akku-Entwurf **mit** dem bestätigten Fehler.
- Der neue CI-Job prüft diesen alten Stand.

## 2. Befunde

| ID | Prio / gesperrtes Gate | Regel | Befund | Maßnahme |
|---|---|---|---|---|
| **REG26-01** | **P0 / G1 für Akku-Schaltung, G2** | R-06 Nr. 2 (Übergabe), R-02 Nr. 2 | Die nicht eingecheckte Behebung SCH26 (Akku-Platine mit TMP_VCC, zweite Stufe, J3 5-polig; `versorgung.md` 3.3; Kabelplan; `erc_erwartet.json`, `erc_pruefen.py`, `netz_tests.py`; Bericht) wurde lokal verworfen (Reflog `6377feb … reset: moving to HEAD`, danach Pull auf `8fc2aa4`). Auf `main` liegt der Stand `fcd18fe`: TMP390 an P+/P−, CE-Pull-up 10 MΩ, J3 4-polig. Das ist genau der in SCH26-01 bestätigte Stillstand nach Tiefentladung. | Wiederherstellung aus Claudes Arbeitskopie ins Arbeitsverzeichnis, **sofort committen und pushen**. Ursache: Übergabe ohne Commit (Claude kann nicht committen; der Stand lag nur im Arbeitsverzeichnis). Künftig nach jeder Claude-Lieferung sofort committen. |
| **REG26-02** | P1 / G1 | R-07, ADR-Pflicht | Regelwerk 1.1 (ADR-0002, Befundregister, Statusmodell, GOV-01-Umsetzung, EX-01) liegt nur im Ordner `bienen-lora-logger_merge`; `main` führt 1.0. Die Entscheidungen des Maintainers sind damit formal nicht in Kraft. | Mit der Wiederherstellung einchecken. |
| **REG26-03** | P1 / G1 | T-01 (Beweisgrenze), H-06 Nr. 3 | Der CI-Job `kicad-schaltplan` auf `main` läuft mit dem alten `pruefen.sh`: ERC nur mit `--severity-error`, keine Netzprüfungen, alter Entwurf. Ein grüner Lauf würde fälschlich Sicherheit vermitteln. | Mit der Wiederherstellung erledigt (neues `pruefen.sh`, `netz_tests.py`, `erc_erwartet.json`). |
| **REG26-04** | P2 / – | R-06 Nr. 7 | Commit-Nachrichten ohne Warum/Was/IDs/Tests: „Regelwerk“, „Befunde behoben“, „neue Version“, „Fehlerfix“, „Schaltplan erstellt V0.1“. | Historie nicht umschreiben. Ab jetzt Nachrichten nach Muster: `SCH26-01..08: … (Tests: pruefen.sh 42/42, ERC OK)`. Claude liefert künftig die Commit-Nachricht mit. |
| **REG26-05** | P2 / – | T-03 (exakter SHA) | Behebungsberichte ohne SHA („Commit-ID beim Einchecken nachtragen“). | Nachgetragen: SRV26 → `3f2f9d6`, HW26/CI26 → `cc6ba60` (aus Reflog und Dateizeiten zugeordnet). SCH26 nach dem Wiederherstellungs-Commit nachtragen. |
| **REG26-06** | **P1 / G2 (D3)** | R-09, T-05 G2, H-02 | Für die Akku-/Ladeschaltung fehlen eine eigenständige **Gefährdungs- und Fehleranalyse** und der **sichere Versuchsplan** (Zell-Emulator, Strombegrenzung, Abbruchkriterien). `versorgung.md` 3.3 enthält eine Fehlertabelle, das reicht für G2 nicht. | Dokument `hardware/sicherheit-akku.md` mit Gefährdungsliste, Einzelfehlern (Q2/Q3/U2/U3/NTC/Leitungen/Stecker), Versuchsplan SCH-T01 … T08 mit Aufbau, Grenzwerten und Abbruchkriterien; Gegenlesen durch zweiten Prüfweg. |
| **REG26-07** | P1 / G2 (D3) | T-06 | Keine Rückverfolgbarkeitsmatrix für die D3-Funktionen (`LH-V1`/`LH-V2`/`LH-V3` ↔ Schaltungsteil ↔ Test-ID ↔ Status). | Teil von `sicherheit-akku.md`. |
| **REG26-08** | P2 / Layout | H-06 Nr. 4 | Pinbelegungen der eigenen Symbole sind mit Datenblattquelle im Code vermerkt; ein **Pin-/Footprint-Abgleichbericht** fehlt. Footprints BQ25185 (DLH), Keystone 1043, Klemmen sind Platzhalter (bekannt, SCH26-04). | Vor dem Layout: Abgleichbericht je Custom-Symbol und Footprint. |
| **REG26-09** | P2 / – | H-06 Nr. 3 | 9 `PWR_FLAG`-Symbole ohne dokumentierte Begründung (Akku: B+, B−, P+, GND, TMP_VCC, HY_VDD; Haupt: VIN_LADER, GND, VBAT). Alle markieren echte Quellen (Zelle, Stecker, R1-gespeistes HY_VDD), das steht aber nirgends. | Begründung als Kommentar je Flag im Generator und Tabelle im KiCad-README. |
| **REG26-10** | P2 / G2 | H-01 | Board-ID/Revision und Umgebungsbedingungen je Platine sind nicht festgelegt; im Titelblock steht nur „0.1 Entwurf“. | Kennungen `PCB-AKKU-0.1`, `PCB-MAIN-0.1` (O-05) in Titelblock und Lastenheft; Betriebsbereich (z. B. −20 … +60 °C Gehäuse) eintragen. |
| **REG26-11** | P2 / G2 | H-03 | Kondensatoren ohne wirksame Kapazität bei Betriebsspannung (DC-Bias), keine Schienentabelle (Toleranz, Welligkeit, Start-/Abschaltreihenfolge) für SYS, +3V3, 3V3_SW, TMP_VCC. | Tabelle in `versorgung.md` ergänzen; MLCC-Typen mit Derating auswählen. |
| **REG26-12** | P1 / Fertigung | H-02 Nr. 1, GOV-04 | Zellmodell und Datenblatt der gekauften Zelle unbekannt. | Philipp: Aufdruck der Zelle; danach Grenzwerte (GOV-04). |

## 3. Konform

| Regel | Beleg |
|---|---|
| R-02 Nr. 2 Quellcode vor Klickzustand | KiCad nur aus `hardware/kicad/*.py`; Server aus `eigen_anpassen.py` (CI-Diff) |
| R-02 Nr. 3, T-01 keine Schein-HiL | alle Berichte nennen „kein Muster, keine Messung“ |
| R-06 Nr. 4 Regressionstest bei Fehlerbehebung | CI26-01 mit Gegenprobe; SCH26-01 mit Gegenprobe (Netzprüfung) |
| S-04 Uhrzeit-unabhängige Tests | `SERVER_UHR` mit libfaketime, CI 05:00/14:00 |
| S-05 Nr. 3 keine Erfolgsbehauptung nach Dateigröße | `le_speicherung_erkannt()` |
| H-02 Nr. 3/4 keine Scheinredundanz, Wiederanlauf | im Entwurf umgesetzt (SCH26-01/03), **auf `main` erst nach REG26-01** |
| H-02 Nr. 6 keine Versuche an echten Zellen | in allen Testplänen so vorgegeben |
| H-06 Nr. 1/2 Generator, Reproduzierbarkeit | `pruefen.sh`: zweimal erzeugt, identisch (Arbeitskopie) |
| O-02 Datenblätter verlinken | keine Hersteller-PDFs im Repository |
| O-06 Geheimnisse | nur `Config_Geraet.beispiel.h`; Stichprobe ohne Schlüsselmuster |
| S-01 Toolchain | `firmware/README.md` nennt Core- und Bibliotheksversionen |

## 4. Reihenfolge

1. **REG26-01/02/03:** Wiederherstellung einchecken und pushen (Dateien liegen im Arbeitsverzeichnis).
2. REG26-05: SHA für SCH26 nachtragen.
3. REG26-06/07: `hardware/sicherheit-akku.md` (Voraussetzung für G2 des Akku-Teils).
4. REG26-08 … 11 vor dem Layout; REG26-12 sobald der Zellaufdruck bekannt ist.
