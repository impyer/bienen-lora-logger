# Prüfbericht: Schaltplanblatt Anschlüsse (SCH26-07, Teil Anschlüsse)

- **Prüfbericht-ID:** SCH-2026-10-13-SCH26-07-ANSCHLUESSE
- **Prüfdatum (UTC):** 13.10.2026
- **Anforderung/Befund:** `SCH26-07` (Blätter fehlen; hier: letztes Blatt Anschlüsse), Lastenheft M4/M5/F10; `anschluesse.md` 1–4; HW26-04 (Pull-ups an 3V3_SW), HW26-09 (I²C-Leitung), HW26-13 (J11 2 × 6)
- **Ausgangs-SHA:** `969339de` (main, nach dem Commit des Blatts Mikrofon)
- **Ergebnis-SHA:** Commit dieses Stands auf main
- **Artefakt:** Generator `hardware/kicad/hauptplatine.py` (`anschluesse()`, `zeichne_anschluesse()`), Prüfwerkzeug `werkzeug/netz_tests.py` (`anschluesse()`, Stecker J6/J7/J8/J11, Behandlung freier Pins), `erc_erwartet.json`, `anschluesse.md` (Platinenreferenzen)
- **Änderungsklasse:** D2 (neues Schaltplanblatt, Pinbelegung J6/J7/J8/J11, Prüfwerkzeug); keine D3-Inhalte
- **Teststufe:** T0 (ESDS304-Pinfolge, TI-Datenblatt Tab. 4-2), T3 (KiCad 10.0.6, lokal in der Claude-Umgebung). **Kein T4, kein Muster.**
- **Person / zweiter Prüfweg:** Claude; Abnahme Maintainer; unabhängiges Review empfohlen

## Ziel und Abnahmekriterien

| Test-ID | Szenario | Erwartetes Ergebnis/Grenze | Begründung/Quelle |
|---|---|---|---|
| A-1 | Netzvergleich Zeichnung ↔ Netzbeschreibung | alle Netze des Modells in KiCad, keine zusätzlichen, gleiche Pins | Verdrahtungsmodus |
| A-2 | ERC Hauptplatine | nur die Footprint-Meldung U201; keine offenen globalen Labels mehr | `erc_erwartet.json` |
| A-3 | 1-Wire | ONEWIRE = PA8, R701, J701/2, J702/2, D701/1 | anschluesse.md 1 |
| A-4 | I²C | I2C_SDA/SCL = PB7/PB6, Pull-up, J703, D702, J704 | anschluesse.md 1, 3.1 |
| A-5 | Pull-ups | R701 4,7 kΩ, R702/R703 1,8 kΩ, alle nur an 3V3_SW; Gegenprobe Pull-up an +3V3 fällt durch | HW26-04, anschluesse.md 3 |
| A-6 | ESD | D701 an DQ und 3V3_SW, D702 an SDA, SCL, 3V3_SW; GND an Pin 2 | anschluesse.md 1, 2 |
| A-7 | Verwechslungsschutz | Polzahlen Solar 2, DS18B20 3, Mikrofon 4, Wägezelle 5, BME280 6; J703 Pin 6 frei; Masse an Pin 1 aller Klemmen | anschluesse.md 1 (Regeln) |
| A-8 | Stecker gegen Doku | J6/J701, J7/J702, J8/J703, J11/J704 = Netzliste | SCH26-09-Prüfung erweitert |
| A-9 | Reproduzierbarkeit | zweimal erzeugt identisch; `--gegenprobe` erkennt jedes Blatt | SCH26-12 |
| A-10 | ältere Blätter | nur `mcu.kicad_sch` ändert sich: DBG_TX/DBG_RX werden globale Labels (jetzt auch an J704) | erwartete Nebenwirkung |

## Durchführung / Reproduktion

```sh
bash hardware/kicad/pruefen.sh                 # A-1 … A-8, A-9
bash hardware/kicad/pruefen.sh --gegenprobe    # A-9
python3 hardware/i2c_leitung.py                # Buskapazität (unverändert)
```

## Entwurf (Kurzfassung)

| Block | Inhalt |
|---|---|
| DS18B20 | J701 = J6, J702 = J7 (1 GND, 2 DQ, 3 3V3_SW), gemeinsamer Bus an PA8, R701 4,7 kΩ an 3V3_SW, ESDS304 D701 für beide Klemmen |
| BME280 | J703 = J8 (1 Schirm, 2 GND, 3 SDA, 4 SCL, 5 3V3_SW, 6 frei), R702/R703 1,8 kΩ an 3V3_SW, ESDS304 D702 an SDA, SCL, 3V3_SW |
| Erweiterung | J704 = J11, 2 × 6: 1 3V3, 2 3V3_SW, 3/4/12 GND, 5 SDA, 6 SCL, 7 TX1, 8 RX1, 9 PA15, 10 PB12, 11 PB13; ohne ESD (innen) |

Prüfwerkzeug: Freie Pins („frei“ in `anschluesse.md`) werden als unverbunden erwartet (KiCad-Netz `unconnected-…`).

## Resultate

| Test-ID | Istwert | Ergebnis |
|---|---|---|
| A-1 | `logger.net`: alle Netze des Modells, keine zusätzlichen | bestanden |
| A-2 | ERC Hauptplatine 1 erwartete Meldung (vorher 7), Akku 0 | bestanden |
| A-3 | ONEWIRE = {U301/29, R701/2, J701/2, J702/2, D701/1} | bestanden |
| A-4 | I2C_SDA = {U301/43, R702/1, J703/3, D702/1, J704/5}; I2C_SCL = {U301/42, R703/2, J703/4, D702/3, J704/6} | bestanden |
| A-5 | Werte und 3V3_SW richtig; Gegenprobe erkannt | bestanden |
| A-6 | D701, D702 wie gefordert | bestanden |
| A-7 | Polzahlen {2, 3, 4, 5, 6}; J703/6 offen; Pin 1 = GND an J201, J202, J501, J601, J701, J702, J703 | bestanden |
| A-8 | 4 Stecker = Doku | bestanden |
| A-9 | reproduzierbar (9 Dateien); Gegenprobe erkennt alle Blattdateien | bestanden |
| A-10 | `mcu.kicad_sch`: nur Label-Art DBG_TX/DBG_RX geändert; andere Blätter unverändert | bestanden |
| Gesamt | `netz_tests.py` **178/178** (vorher 139) | bestanden |
| CI | GitHub Actions auf dem neuen Commit | offen |
| Muster | Buskapazität des Kabels, Anstiegszeit, 1-Wire mit zwei Fühlern | **nicht ausgeführt** (T4) |

## Einschränkungen

- LCSC-Nummer ESDS304DBVR und DEGSON-Teilenummern 3-/6-polig offen [P]; Footprints der Klemmen sind Platzhalter (Phoenix MC 3,5 mm).
- 1-Wire-Reichweite beruht auf einer Annahme (anschluesse.md 3); am Muster mit den echten Fühlerkabeln prüfen.
- Damit ist SCH26-07 im Entwurf behoben: alle Blätter vorhanden. Vor dem Layout fehlen REG26-08 (Pin-/Footprint-Bericht) und die eigenen Footprints.

## Freigabeentscheidung

- **Gate:** G1 für den Entwurf nach grüner CI; G2/G3 unverändert gesperrt
- **Entscheidung:** durch den Maintainer
