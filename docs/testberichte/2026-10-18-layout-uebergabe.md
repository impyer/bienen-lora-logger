# Prüfbericht: Schaltplan-Freigabe für den Layout-Auftrag (Layout-Stand 18.10.2026)

- **Prüfbericht-ID:** SCH-2026-10-18-LAYOUT
- **Prüfdatum (UTC):** 18.10.2026
- **Anforderung/Befund:** Lastenheft M1–M9, Pflichtenheft `hardware/layout-auftrag/PFLICHTENHEFT.md` issue 3; HW-08 (Layout extern), HW-09 (BLE, Ladepads); Regelwerk H-06 Nr. 2–6
- **Geprüfter Git-Commit:** `4c36898` (Branch `design/hw09-layout-uebergabe`, Basis main `66a3ba2`; enthält HW-09 `7498d6b`, `3a9bea0`, `d3c2174`, `82e0614`)
- **Artefakt/Zielkonfiguration:** KiCad-10-Projekt `hardware/kicad/hauptplatine/` (7 Blätter, Rahmenplatine), Projektbibliotheken, Übergabepaket `build/layout-auftrag-PCB-MAIN-0.1-4c36898.zip` (nicht im Repo, `build/` ist ignoriert)
- **Teststufe:** T0 (Sichtprüfung, Dokumente) und T3 (KiCad 10.0.7 unter Windows). **Keine Messung, kein Muster.**
- **Person / zweiter Prüfweg:** Coding-Agent (Claude) auf Weisung des Maintainers; CI-Lauf nach dem Push als zweiter Weg

## Ziel und Abnahmekriterien

Der Schaltplan soll so eingefroren und geprüft sein, dass der beauftragte Layouter mit dem Paket arbeiten kann (Pflichtenheft 2.1): reproduzierbare Erzeugung, ERC 0, Netzprüfung gegen die Netzbeschreibung, Pin-/Footprint-Abgleich ohne Abweichung, alle Footprints vorhanden, Rahmenplatine mit DRC 0, Paket vollständig und aus sich heraus prüfbar.

| Test-ID | Szenario | Erwartetes Ergebnis/Grenze | Quelle |
|---|---|---|---|
| L-1 | `pruefen.sh` auf dem Commit | reproduzierbar, ERC 0, Netzprüfung alle, Pin/Footprint 0 Abweichungen, 0 offene Footprints | H-06 Nr. 2–4 |
| L-2 | Sichtprüfung aller 8 Blätter (PDF → PNG) | keine überlappenden Symbole/Labels, Titelblock mit Kennung, Datum und Revision | REG26-10 |
| L-3 | DRC der Rahmenplatine `logger.kicad_pcb` | 0 Verstöße | H-06 Nr. 5, Pflichtenheft 5.2 |
| L-4 | Paket bauen (`paket_bauen.py`) und entpackt prüfen: ERC des entpackten Projekts, DRC der entpackten Platine, Dateiliste | ERC 0, DRC 0, alle Dateien aus Pflichtenheft 2.1 vorhanden, `STAND.txt` mit Commit | Pflichtenheft 2.1 |
| L-5 | `netz_vergleich.py --selbsttest` mit der aktuellen Netzliste | Rundlauf und Gegenproben bestanden | HW-08, Pflichtenheft 9 |
| L-6 | Host-Tests, die unter Windows laufen | Formatter 14/14 (zweimal), S2120 12/12 | Regression |

## Durchführung / Reproduktion

```sh
export PATH="$LOCALAPPDATA/Programs/KiCad/10.0/bin:$PATH"
export KICAD9_SYMBOL_DIR="$LOCALAPPDATA/Programs/KiCad/10.0/share/kicad/symbols"
export KICAD_FOOTPRINTS="$LOCALAPPDATA/Programs/KiCad/10.0/share/kicad/footprints" PYTHONUTF8=1
bash hardware/kicad/pruefen.sh
kicad-cli pcb drc --severity-all --exit-code-violations -o drc.rpt hardware/kicad/hauptplatine/logger.kicad_pcb
python hardware/layout-auftrag/paket_bauen.py            # nach dem Commit, damit STAND.txt den sauberen SHA trägt
unzip build/layout-auftrag-PCB-MAIN-0.1-4c36898.zip -d /tmp/paket
kicad-cli sch erc --severity-all --exit-code-violations -o erc.rpt /tmp/paket/kicad/hauptplatine/logger.kicad_sch
kicad-cli pcb drc --severity-all --exit-code-violations -o drc.rpt /tmp/paket/kicad/hauptplatine/logger.kicad_pcb
python hardware/layout-auftrag/netz_vergleich.py --selbsttest
pdftoppm -r 75 -png hardware/kicad/pdf/logger.pdf blatt   # Sichtprüfung
```

## Resultate

| Test-ID | Istwert | Ergebnis | Abweichung |
|---|---|---|---|
| L-1 | 20 Dateien zweimal identisch; ERC **0**; Netzprüfung **220/220**; Pin-/Footprint-Abgleich **177 Bauteile, 0 Abweichungen, 0 offen** | bestanden | 7 Klemmen-Footprints bleiben Platzhalter nach EasyEDA-Geometrie (DEGSON-Zeichnung [P]) |
| L-2 | 8 Blätter angesehen (Wurzel, Versorgung, MCU, Funk + Flash, Waage, Mikrofon, Anschlüsse, Akku); Titelblock „0.1 Layout-Stand“, 2026-10-18, PCB-MAIN-0.1 | bestanden | Blatt Mikrofon: Fußnote reicht bis in den Titelblock (nur Optik) |
| L-3 | `** Found 0 DRC violations **`, 0 unverbundene Elemente | bestanden | Rahmen ohne Bauteile (HW-08) |
| L-4 | Paket `layout-auftrag-PCB-MAIN-0.1-4c36898.zip`: 38 Dateien (Pflichtenheft, STAND.txt, bom_aktuell.csv mit 177 Zeilen / 21 LCSC, KiCad-Projekt mit 8 Schaltplandateien, Platine, beide lib-tables, Symbolbibliothek, 11 Footprints, PDF, Netzliste, pin_footprint.md, 7 Blockdokumente); entpackt: ERC **0** (Exit 0), DRC **0** | bestanden | – |
| L-5 | 118 Netze, 549 Pins; Gegenproben MIC_P/MIC_N, B− getrennt, B− an GND erkannt | bestanden | – |
| L-6 | Formatter 14/14 und 14/14 (min), S2120 12/12 | bestanden | C++-Host-/Simulationstests und PHP-Servertests nicht lokal (kein g++/php) – CI |

## Einschränkungen, Risiken, Regressionsfolgen

- **Entwurfsstand, keine Fertigungsfreigabe:** Alle Nachweise sind T0/T3. Die D3-Gates für Akku/Laden (SCH26-01 … 03, HW26-16 … 19) sind unverändert offen; der Layouter ändert daran nichts (Pflichtenheft 2.3, 5.3 B−).
- **Offene Bauteilwahl** (Pflichtenheft 7, Vorschlag durch den Layouter, Freigabe Philipp): RJ45 J601, Ferrite, L501, TVS D401, SPI-Flash U402, DEGSON-Zeichnung; **RN4871 nur 50 Stück bei LCSC** (HW26-20), Ra-01SH-Bestand vor der Bestellung.
- **Footprint RN4871** nach Datenblattbild [V]; Gegenprüfung mit LCSC/EasyEDA C633942 vor der Bestellung (HW26-20). Antennenteil ragt nach Fig. 4-9 über die Platinenkante – Platzierungsregel 11.
- **Nicht im Paket:** STEP des Gehäuses (Herstellerdatei, auf Anfrage), Firmware. Der Firmware-Absatz zu BLE liegt in einem eigenen Branch (`claude/hw09-ble-firmware-userguide`, Commit `24c0359`) und ist für das Layout nicht relevant.
- Unter Windows erzeugt der Generator identische Dateien wie die CI (Vergleich 18.10.2026); die CI auf dem gepushten Branch ist der zweite Prüfweg.

## Nachtrag 18.10.2026 abends: HW-10 (dritter Mikrofoneingang) und Pin-Review

Nach der Freigabe kamen zwei Aufträge des Maintainers: **HW-10** (alle drei Mikrofonanschlüsse des Audio-ADC nutzen) und eine **Prüfung aller Pinfunktionen**. Beides ist eingearbeitet; der Layout-Stand wurde neu erzeugt und geprüft.

- **HW-10:** Mikrofon 3 (zweite Elektretkapsel) pseudo-differenziell an IN2R(P)/IN3R(M) mit MICBIAS2 (R614/R615, C625–C629), auf **J601 Pin 5 (MIC3+) / 6 (MIC3−)** (Philipp: ein Stecker für alle drei Mikrofone; vorher Masse-Paarpartner), ESD D602 neben D601; Blatt Mikrofon Abschnitt 6; Pflichtenheft Regel 1/2 und Netztabelle (MIC3-Paar), 185 Teile / 21 LCSC. Regel: Mikrofon 3 nur bei stehendem PDM-Takt messen.
- **Pin-Review:** eigener Bericht [2026-10-18-pinfunktionen-review](2026-10-18-pinfunktionen-review.md) – keine Abweichung; `pin_footprint.py` für STM32, AO3400A, AO3401A, HY2111, FS8205, 74LVC1G17 auf [V].
- **Nachweis (Commit `6cdc364`):** `pruefen.sh` reproduzierbar, ERC **0**, Netzprüfung **230/230**, Pin-/Footprint-Abgleich **186 Bauteile, 0 Abweichungen**; Paket **`layout-auftrag-PCB-MAIN-0.1-6cdc364.zip`** (38 Dateien, bom_aktuell.csv 186 Zeilen, 20 mit LCSC) entpackt: ERC **0**, DRC **0**. Dieses Paket ersetzt die aus `4c36898`, `23aed6e` und `bec9a04`.
- **Review-Nachtrag (externe Prüfung):** `mikrofon.md` Bauteiltabelle/Schaltbild auf J601 Pin 5/6 = MIC3+/MIC3− berichtigt; Q501 ohne LCSC-Nummer, Pflichtenheft 7 verlangt Pinfolge 1 B, 2 E, 3 C mit Pinbild; R313 100 kΩ an BLE_VCC (definierter Aus-Zustand). BLE-Musterprüfungen B-1 … B-6 und Antennenlage bleiben offen (HW26-20, Pflichtenheft 11).

## Freigabeentscheidung

- **Betroffenes Gate:** G1 (Quellstand) – **bestanden, vorbehaltlich grüner CI**; G2/G3/G4 unverändert offen
- **Entscheidung:** Schaltplan **zur Layout-Bearbeitung freigegeben** (Platzierung/Routing durch den Layouter, HW-08); keine Freigabe zur Bestellung
- **Begründung und Verantwortliche:** alle Prüfungen L-1 … L-6 bestanden; Maintainer bestätigt mit dem Merge und dem Versand des Pakets
- **Reproduzierbare Daten:** Befehle oben; Paketname mit Commit-SHA (gültig: `6cdc364`); Pin-Review [2026-10-18-pinfunktionen-review](2026-10-18-pinfunktionen-review.md); Berichte des HW-09-Stands [2026-10-18-hw09-ble-rn4871](2026-10-18-hw09-ble-rn4871.md)
