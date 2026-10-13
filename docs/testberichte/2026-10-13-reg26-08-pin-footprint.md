# Prüfbericht: Pin-/Footprint-Abgleich (REG26-08)

- **Prüfbericht-ID:** REG-2026-10-13-REG26-08
- **Prüfdatum (UTC):** 13.10.2026
- **Befund:** `REG26-08` (Regelwerk H-06 Nr. 4: Pin-/Footprint-Abgleichbericht vor dem Layout)
- **Ausgangs-SHA:** `ecce931` (main, Schaltplan vollständig)
- **Artefakt:** `hardware/kicad/werkzeug/pin_footprint.py` (neu, in `pruefen.sh`), erzeugter Bericht `hardware/kicad/pin_footprint.md`; Generator `hauptplatine.py` (Footprints U401, U501, U502, Q501, D501 eingetragen; D401 gedreht), `erc_erwartet.json` (U401)
- **Änderungsklasse:** D2 (Footprint-Zuordnung, Polung D401, Prüfwerkzeug); keine D3-Inhalte
- **Teststufe:** T0 (Datenblätter TI BQ25185, TMP390, TPS709, TPS61240, TPS22917, TPD4E05U06, ESDS304, TLV9001; AVIA HX711), T3 (KiCad 10.0.6 lokal). Kein T4.

## Abnahmekriterien

| Test-ID | Szenario | Erwartet |
|---|---|---|
| PF-1 | Footprint je Bauteil | Datei in der KiCad-Bibliothek; fehlend nur aus der begründeten Liste `OFFEN` |
| PF-2 | Pins/Pads | Symbol-Pinnummern = Footprint-Padnummern |
| PF-3 | Datenblatt | jeder Pin eines aktiven Bauteils mit Datenblattname und erwartetem Symbolnamen; Abweichung = Fehler |
| PF-4 | Gegenprobe | vertauschte Pins 2/3 beim TPS61240 und ein fehlender Footprint werden erkannt |
| PF-5 | Integration | `pruefen.sh` läuft durch; ERC nur erwartete Meldungen; Netzprüfung unverändert 178/178 |

## Ergebnisse

| Test-ID | Ergebnis |
|---|---|
| PF-1 | 158 von 161 Footprints vorhanden; offen U201 (BQ25185 DLH), U401 (Ra-01SH), SW304 (Reedkontakt) |
| PF-2 | 0 Abweichungen |
| PF-3 | 0 Abweichungen; Quellen: 9 Bauteiltypen [V] in dieser Prüfung gelesen, 4 [V*] aus früherer Sitzung, Rest [A]/[P] |
| PF-4 | beide Fehler erkannt, Exitcode 1 |
| PF-5 | bestanden; ERC Hauptplatine 2 erwartete Meldungen (Footprints U201, U401) |

## Funde und Änderungen

1. **Fehlende Footprint-Zuordnung** bei U401, U501, U502, Q501, D501 (Feld leer, weil der Generator `fp=""` übergab). Eingetragen: U501 WSON-6 2 × 2 (TI DRV), U502 SOIC-16 3,9 × 9,9 mm (HX711-Datenblatt: SOP-16L, Körper 3,90–4,10 mm, Raster 1,27 mm [V]), Q501 SOT-23, D501 USON-10 2,5 × 1,0 mm, U401 `Bienen:Ai-Thinker_Ra-01SH` (noch anzulegen).
2. **Polung TVS D401:** Pad 1 lag an GND. Mit einer unidirektionalen TVS (Kathode = Pad 1 bei SOD-523) wäre die 3,3-V-Schiene über die Diode kurzgeschlossen gewesen. Jetzt Pad 1 an +3V3; mit bidirektionaler TVS ohne Bedeutung. Teilwahl weiter offen [P].
3. SMAJ12A (D204) nutzt ein KiCad-Symbol mit Pins A1/A2; Pad 1 liegt an VIN_LADER = Kathodenseite der unidirektionalen SMAJ12A [A: Konvention D_SMA]. Richtig gepolt.

## Grenzen

- Datenblatt nicht gelesen (Download gescheitert oder Teil offen): USBLC6-2SC6, SPI-Flash, AO3400A, S8550 (C397181), Quarz Y301, LED D301, TVS D401 – im Bericht [A]/[P].
- [V*]-Einträge (HY2111, FS8205, RT9080, Ra-01SH) beim Anlegen der Footprints erneut gegen das Datenblatt prüfen.
- Die Prüfung vergleicht Nummern und Namen, nicht Padgeometrie; Gehäusezeichnung und Footprint werden beim Anlegen der eigenen Footprints verglichen.
