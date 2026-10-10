#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Schaltplan der Hauptplatine (KiCad-Projekt hardware/kicad/hauptplatine/), Blätter je Block.

Stand: Blatt „Versorgung“. Weitere Blätter (MCU, Funk + Flash, Waage, Mikrofon, Anschlüsse)
folgen; Netze zu diesen Blättern sind als Schnittstellen (globale Labels) angelegt.

Quellen der Werte: hardware/versorgung.md (3.1–3.8), LASTENHEFT.md V1–V7.
Aufruf: python3 hardware/kicad/hauptplatine.py
Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "werkzeug"))
from kicad_gen import Projekt  # noqa: E402

BIB = os.path.join(HIER, "bienen.kicad_sym")
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
KLEMME = "Connector_Phoenix_MC:PhoenixContact_MC_1,5_%d-G-3.5_1x0%d_P3.50mm_Horizontal"

# Netze, die zu anderen (noch folgenden) Blättern gehen
SCHNITTSTELLEN = {
    "VBUS",        # USB-C (Blatt MCU) → Diode → Ladereingang
    "ADC_SOLAR",   # PB1
    "ADC_AKKU",    # Akkuteiler → ADC (Pin auf Blatt MCU)
    "SENSOR_EIN",  # PB5 → ON des TPS22917
    "3V3_SW",      # geschaltete Sensorschiene
    "SYS",         # 5-V-Wandler der Waage hängt an SYS
}


def zeichne_versorgung(b, T):
    """Platzierung und Leitungen nach Stromfluss (A3 quer, mm).
    Obere Reihe: Panels/USB → Schottky → VIN_LADER → Laderegler → SYS. Mitte: Akku-Stecker J203 mit
    VBAT, CE, NTC und TMP_VCC (TPS70933 aus VIN_LADER). Untere Reihe: SYS → 3,3 V → Sensorschiene.
    netz_tests.py prüft jede gezeichnete Verbindung gegen die Netzbeschreibung."""
    S, D, L = b.setze, b.draht, b.label
    yv = 76.2                        # obere Schiene VIN_LADER / SYS
    y3 = 180.34                      # untere Schiene SYS / +3V3 / 3V3_SW

    b.text("1  Solar und USB → Schottky-Dioden → VIN_LADER (TVS, Messung der Eingangsspannung)", 30.48, 55.88, 2.0)
    b.text("2  Laderegler BQ25185: 4,1 V, 150 mA; CE und TS kommen von der Ladesperre der Akku-Platine", 152.4, 63.5, 2.0)
    b.text("3  Akku-Stecker J203, TMP_VCC", 175.26, 124.46, 2.0)
    b.text("4  SYS → 3,3 V (RT9080) → geschaltete Sensorschiene 3V3_SW (TPS22917, Ein/Aus von der MCU)", 152.4, 215.9, 2.0)
    b.text("Regeln: Pull-ups nur an 3V3_SW; TS/MR nie aktiv auf Masse (Werksmodus); Laderegler nicht neben der Zelle; "
           "SPI-Flash an +3V3 (dauernd).", 30.48, 233.68, 1.5)
    b.text("J203: Kabel 1:1 zur Akku-Platine J1 (anschluesse.md). TMP_VCC aus dem TPS70933 am Ladereingang gibt es nur bei "
           "Sonne/USB; ohne TMP_VCC sperrt die Ladesperre (sicherheit-akku.md).", 30.48, 240.03, 1.5)

    # Teile, auf die mehrere Abschnitte zeigen, zuerst setzen
    S(T["U201"], 205.74, 83.82, text="oben")
    S(T["J203"], 302.26, 134.62, text="oben")
    S(T["U204"], 215.9, 152.4, text="oben")
    S(T["U202"], 228.6, 185.42, text="oben")
    S(T["U203"], 299.72, 182.88, text="oben")

    # --- 1 Quellen und VIN_LADER --------------------------------------------
    S(T["J201"], 35.56, 78.74, rot=180, text="oben")
    S(T["J202"], 35.56, 99.06, rot=180, text="oben")
    S(T["D201"], 55.88, yv, rot=180, text="oben")
    S(T["D202"], 55.88, 96.52, rot=180, text="oben")
    S(T["D203"], 55.88, 116.84, rot=180, text="oben")
    D(T["J201"].p("2"), T["D201"].p("A"))
    D(T["J202"].p("2"), T["D202"].p("A"))
    D((40.64, 116.84), T["D203"].p("A"))
    D(T["D201"].p("K"), T["U201"].p("IN"))
    D(T["D202"].p("K"), (66.04, 96.52), (66.04, yv))
    D(T["D203"].p("K"), (66.04, 116.84), (66.04, 96.52))
    L("PV1", 43.18, yv)
    L("PV2", 43.18, 96.52)
    L("VBUS", 40.64, 116.84, 180)
    L("VIN_LADER", 152.4, yv)
    S(T["D204"], 78.74, 83.82, rot=270, text="rechts")
    S(T["C201"], 99.06, 83.82)
    S(T["C202"], 116.84, 83.82)
    S(T["R201"], 132.08, 83.82)
    S(T["R202"], 132.08, 99.06, text="links")
    S(T["C203"], 142.24, 99.06)
    for r in ("D204", "C201", "C202", "R201"):
        D(T[r].p("1"), (T[r].p("1")[0], yv))
    D(T["R201"].p("2"), T["R202"].p("1"))
    D(T["C203"].p("1"), (142.24, 91.44), (132.08, 91.44))
    D((142.24, 91.44), (147.32, 91.44))
    L("ADC_SOLAR", 147.32, 91.44)
    S(T["#FLG201"], 71.12, yv)
    S(T["#FLG202"], 30.48, 132.08)

    # --- 2 Laderegler -------------------------------------------------------
    S(T["R203"], 177.8, 87.63, text="links")
    S(T["R204"], 185.42, 90.17)
    D(T["U201"].p("ISET"), (177.8, 83.82))
    D(T["U201"].p("ILIM/VSET"), (185.42, 86.36))
    L("ISET", 180.34, 83.82)
    L("ILIM", 186.69, 86.36)
    x_ce, x_ts = 167.64, 170.18
    D(T["U201"].p("~{CE}"), (x_ce, 78.74), (x_ce, 134.62), T["J203"].p("3"))
    D(T["U201"].p("TS/~{MR}"), (x_ts, 81.28), (x_ts, 132.08), T["J203"].p("2"))
    L("CE_LADEN", 246.38, 134.62)
    L("NTC", 246.38, 132.08)
    S(T["R205"], 157.48, 109.22, text="links")
    S(T["C206"], 162.56, 127.0, text="links")
    D(T["R205"].p("1"), (157.48, 101.6))
    D(T["R205"].p("2"), (157.48, 116.84), (x_ce, 116.84))
    D(T["C206"].p("1"), (162.56, 121.92), (x_ce, 121.92))
    L("SYS", 157.48, 101.6, 90)
    S(T["TP201"], 243.84, 81.28, rot=270)
    S(T["TP202"], 243.84, 91.44, rot=270)
    D(T["U201"].p("STAT1"), T["TP201"].p("1"))
    D(T["U201"].p("STAT2"), (236.22, 83.82), (236.22, 91.44), T["TP202"].p("1"))
    L("LADE_STAT1", 226.06, 81.28)
    L("LADE_STAT2", 226.06, 83.82)

    # --- 3 Akku-Stecker: VBAT, Akkuteiler, TMP_VCC --------------------------
    x_vbat = 317.5
    D(T["U201"].p("BAT"), (x_vbat, 78.74), (x_vbat, 142.24), (297.18, 142.24), T["J203"].p("5"))
    L("VBAT", 302.26, 78.74)
    S(T["C205"], 264.16, 82.55)
    
    S(T["R206"], 279.4, 82.55, text="links")
    S(T["R207"], 279.4, 97.79, text="links")
    S(T["C207"], 289.56, 97.79)
    D(T["R206"].p("2"), T["R207"].p("1"))
    D(T["C207"].p("1"), (289.56, 90.17), (279.4, 90.17))
    D((289.56, 90.17), (294.64, 90.17))
    L("ADC_AKKU", 294.64, 90.17)
    S(T["#FLG203"], 309.88, 78.74)
    D((73.66, yv), (73.66, 147.32), T["U204"].p("IN"))
    S(T["C212"], 236.22, 151.13)
    D(T["U204"].p("OUT"), (292.1, 147.32), (292.1, 137.16), T["J203"].p("4"))
    L("TMP_VCC", 243.84, 147.32)

    # --- 4 SYS → 3,3 V → 3V3_SW ---------------------------------------------
    D(T["U201"].p("SYS"), (355.6, yv), (355.6, 167.64), (177.8, 167.64), (177.8, y3), T["U202"].p("VIN"))
    L("SYS", 236.22, yv)
    D(T["U202"].p("EN"), (215.9, 182.88), (215.9, y3))
    S(T["C204"], 185.42, 184.15)
    S(T["C208"], 203.2, 184.15)
    D(T["U202"].p("VOUT"), T["U203"].p("VIN"))
    S(T["C209"], 254.0, 184.15)
    b.versorgung("+3V3", 264.16, y3, "oben")
    S(T["C210"], 281.94, 182.88, rot=270, text="unten")
    D(T["C210"].p("1"), T["U203"].p("CT"))
    D(T["C210"].p("2"), (278.13, 182.88), (278.13, y3))
    L("SW_CT", 285.75, 182.88)
    S(T["R208"], 271.78, 199.39, text="links")
    D(T["U203"].p("ON"), (287.02, 185.42), (287.02, 195.58), (264.16, 195.58))
    L("SENSOR_EIN", 264.16, 195.58, 180)
    S(T["R209"], 317.5, 189.23)
    D(T["U203"].p("QOD"), T["R209"].p("1"))
    D(T["R209"].p("2"), (322.58, 193.04), (322.58, y3))
    L("SW_QOD", 309.88, 185.42)
    S(T["C211"], 332.74, 184.15)
    D(T["U203"].p("VOUT"), (342.9, y3))
    L("3V3_SW", 342.9, y3)
    for r in ("C204", "C208", "C209", "C211", "C205", "R206", "C212"):
        D(T[r].p("1"), (T[r].p("1")[0], {"C205": 78.74, "R206": 78.74, "C212": 147.32}.get(r, y3)))


def versorgung(p):
    b = p.blatt("Versorgung", "versorgung.kicad_sch", titel="Versorgung: Solar, Lader, 3,3 V, Sensorschiene")

    eingang = [
        b.teil("Connector_Generic:Conn_01x02", "J201", "Solar 1", fp=KLEMME % (2, 2),
               netze={"1": "GND", "2": "PV1"}, info="DEGSON 15EDGRHC-3.5 (Platzhalter-Footprint Phoenix MC 3,5 mm) [P]"),
        b.teil("Connector_Generic:Conn_01x02", "J202", "Solar 2", fp=KLEMME % (2, 2),
               netze={"1": "GND", "2": "PV2"}, info="wie J201"),
        b.teil("Diode:SS34", "D201", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "PV1", "K": "VIN_LADER"}, info="je Panel eine Schottky"),
        b.teil("Diode:SS34", "D202", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "PV2", "K": "VIN_LADER"}),
        b.teil("Diode:SS34", "D203", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "VBUS", "K": "VIN_LADER"}, info="USB lädt, speist nie ins Panel"),
        b.teil("Diode:SMAJ12A", "D204", "SMAJ12A", fp="Diode_SMD:D_SMA", netze={"1": "VIN_LADER", "2": "GND"},  # Pin 1 = Kathode
               info="TVS 12 V, begrenzt Störungen unter 25 V (BQ25185 abs.)"),
        b.teil("Device:C", "C201", "4,7µ 50V X7R", fp=C1206, netze={"1": "VIN_LADER", "2": "GND"}, info="≥ 1 µF an IN; 50 V wegen 25 V abs. am Eingang und DC-Bias (SCH26-08)"),
        b.teil("Device:C", "C202", "100n 50V", fp=C0603, netze={"1": "VIN_LADER", "2": "GND"}),
        b.teil("Device:R", "R201", "3,3M", fp=R0603, netze={"1": "VIN_LADER", "2": "ADC_SOLAR"}, info="HW26-08: 25 V → 3,12 V"),
        b.teil("Device:R", "R202", "470k", fp=R0603, netze={"1": "ADC_SOLAR", "2": "GND"}),
        b.teil("Device:C", "C203", "100n", fp=C0603, netze={"1": "ADC_SOLAR", "2": "GND"}, info="Ladung für die ADC-Abtastung"),
        b.teil("power:PWR_FLAG", "#FLG201", "PWR_FLAG", netze={"1": "VIN_LADER"}, info="Quellen: Panels an J201/J202 und VBUS über D201–D203; Klemmen sind für den ERC passive Pins"),
        b.teil("power:PWR_FLAG", "#FLG202", "PWR_FLAG", netze={"1": "GND"}, info="Bezug über die Klemmen J201/J202 und den Akku-Stecker J203 (passive Pins)"),
    ]

    lader = [
        b.teil("Bienen:BQ25185", "U201", "BQ25185DLHR", fp="Bienen:WSON-10-1EP_2.2x2mm_DLH0010A",
               netze={"IN": "VIN_LADER", "SYS": "SYS", "BAT": "VBAT", "~{CE}": "CE_LADEN", "TS/~{MR}": "NTC",
                      "ISET": "ISET", "ILIM/VSET": "ILIM", "STAT1": "LADE_STAT1", "STAT2": "LADE_STAT2",
                      "GND": "GND", "EP": "GND"},
               info="Footprint DLH 2,2 × 2 mm selbst anlegen [P]; Thermal-Pad mit 6–9 Vias auf L2"),
        b.teil("Device:R", "R203", "2,0k 1%", fp=R0603, netze={"1": "ISET", "2": "GND"}, info="ICHG = 300 AΩ / 2 kΩ = 150 mA (HW26-11)"),
        b.teil("Device:R", "R204", "130k 1%", fp=R0603, netze={"1": "ILIM", "2": "GND"}, info="Tab. 6-1: VBATREG 4,1 V, ILIM 500 mA"),
        b.teil("Device:C", "C204", "22µ 25V X5R", fp=C1206, netze={"1": "SYS", "2": "GND"},
               info="≥ 10 µF an SYS wirksam bei 4,5 V; 10 µF/0805 fiele durch DC-Bias darunter (REG26-11, versorgung.md 3.9)"),
        b.teil("Device:C", "C205", "4,7µ", fp=C0805, netze={"1": "VBAT", "2": "GND"}, info="≥ 1 µF an BAT"),
        b.teil("Device:R", "R205", "100k", fp=R0603, netze={"1": "SYS", "2": "CE_LADEN"},
               info="CE-Pull-up: Leitungsbruch CE_FREI → Laden gesperrt. Strom nur bei Sonne (Q2 an TMP_VCC); SCH26-02"),
        b.teil("Device:C", "C206", "10n", fp=C0603, netze={"1": "CE_LADEN", "2": "GND"}, info="Störschutz an CE (RC 1 ms)"),
        b.teil("Bienen:TPS70933DBV", "U204", "TPS70933DBV", fp="Package_TO_SOT_SMD:SOT-23-5",
               netze={"IN": "VIN_LADER", "EN": "NC", "OUT": "TMP_VCC", "GND": "GND"},
               info="TMP_VCC für die Ladesperre auf der Akku-Platine, nur bei Sonne/USB (SCH26-01); EN offen = ein (max. 6,5 V)"),
        b.teil("Device:C", "C212", "4,7µ 16V X7R", fp=C0805, netze={"1": "TMP_VCC", "2": "GND"},
               info="Datenblatt verlangt ≥ 2,2 µF am Ausgang; 4,7 µF/0805 hält das bei 3,3 V trotz DC-Bias (REG26-11)"),
        b.teil("Connector:TestPoint", "TP201", "STAT1", fp="TestPoint:TestPoint_Pad_D1.0mm", netze={"1": "LADE_STAT1"}),
        b.teil("Connector:TestPoint", "TP202", "STAT2", fp="TestPoint:TestPoint_Pad_D1.0mm", netze={"1": "LADE_STAT2"}),
        b.teil("Connector_Generic:Conn_01x05", "J203", "Akku (JST PH 5)", fp="Connector_JST:JST_PH_B5B-PH-K_1x05_P2.00mm_Vertical",
               netze={"1": "GND", "2": "NTC", "3": "CE_LADEN", "4": "TMP_VCC", "5": "VBAT"},
               info="Kabel 1:1 zur Akku-Platine J1: 1 P−, 2 NTC, 3 CE_FREI, 4 TMP_VCC, 5 P+"),
        b.teil("power:PWR_FLAG", "#FLG203", "PWR_FLAG", netze={"1": "VBAT"}, info="Quelle: Akku-Platine über J203 Pin 5 (P+), anderes KiCad-Projekt"),
        b.teil("Device:R", "R206", "2,2M", fp=R0603, netze={"1": "VBAT", "2": "ADC_AKKU"}, info="Akkuteiler 1:2, 0,9 µA"),
        b.teil("Device:R", "R207", "2,2M", fp=R0603, netze={"1": "ADC_AKKU", "2": "GND"}),
        b.teil("Device:C", "C207", "100n", fp=C0603, netze={"1": "ADC_AKKU", "2": "GND"}),
    ]

    regler = [
        b.teil("Bienen:RT9080-33GJ5", "U202", "RT9080-33GJ5", fp="Package_TO_SOT_SMD:TSOT-23-5", lcsc="C841192",
               netze={"VIN": "SYS", "EN": "SYS", "VOUT": "+3V3", "GND": "GND"}, info="EN an VIN (nicht offen lassen)"),
        b.teil("Device:C", "C208", "2,2µ 16V X7R", fp=C0603, netze={"1": "SYS", "2": "GND"}, info="≥ 1 µF wirksam bei 4,5 V (REG26-11)"),
        b.teil("Device:C", "C209", "2,2µ 16V X7R", fp=C0603, netze={"1": "+3V3", "2": "GND"},
               info="≥ 1 µF wirksam bei 3,3 V (REG26-11); dazu 100 µF + 10 µF am Funkmodul (Blatt Funk)"),
        b.teil("Power_Management:TPS22917DBV", "U203", "TPS22917DBV", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C2681320",
               netze={"VIN": "+3V3", "VOUT": "3V3_SW", "ON": "SENSOR_EIN", "CT": "SW_CT", "QOD": "SW_QOD", "GND": "GND"},
               info="QOD über R209 an VOUT: aktive Entladung; CT nach VIN (Datenblatt Tab. 6-1)"),
        b.teil("Device:R", "R209", "0", fp=R0603, netze={"1": "SW_QOD", "2": "3V3_SW"},
               info="QOD-Widerstand (Datenblatt: extern oder direkt); 0 Ω = interner Wert, bei Bedarf erhöhen"),
        b.teil("Device:C", "C210", "1n", fp=C0603, netze={"1": "SW_CT", "2": "+3V3"}, info="CT 1 nF → Anstieg ca. 1,7 ms bei 3,3 V"),
        b.teil("Device:R", "R208", "100k", fp=R0603, netze={"1": "SENSOR_EIN", "2": "GND"}, info="ON nie offen (Standby: GPIO hochohmig); 100 kΩ wie versorgung.md 3.7 (SCH26-05)"),
        b.teil("Device:C", "C211", "1µ", fp=C0603, netze={"1": "3V3_SW", "2": "GND"}),
    ]

    zeichne_versorgung(b, {t.ref: t for t in b.teile})
    return b


def baue():
    p = Projekt("logger", os.path.join(HIER, "hauptplatine"), firma="Bienenlogger – Philipp Schnabel",
                rev="0.1 Entwurf", datum="2026-10-09", eigene_bibs={"Bienen": BIB},
                kommentare=["Board-Kennung PCB-MAIN-0.1 (REG26-10)",
                            "Umgebung [A]: Gehäuse −20 … +60 °C, Betauung möglich; VIN ≤ 12 V dauernd, 25 V absolut"])
    p.schnittstellen = set(SCHNITTSTELLEN)
    w = p.blatt("Bienenlogger Hauptplatine", "logger.kicad_sch", titel="Bienenlogger Hauptplatine 121 × 121 mm, 4 Lagen")
    w.text("Blätter: Versorgung (fertig). Folgen: MCU, Funk + Flash, Waage, Mikrofon, Anschlüsse.", 30, 25, 2.0)
    versorgung(p)
    return p


if __name__ == "__main__":
    pr = baue()
    g = pr.schreibe()
    print("geschrieben:", pr.ordner, "| globale Netze:", ", ".join(sorted(g)))
