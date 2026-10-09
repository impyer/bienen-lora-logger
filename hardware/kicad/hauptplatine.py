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
        b.teil("power:PWR_FLAG", "#FLG201", "PWR_FLAG", netze={"1": "VIN_LADER"}),
        b.teil("power:PWR_FLAG", "#FLG202", "PWR_FLAG", netze={"1": "GND"}),
    ]
    y = b.gruppe("Solar-Eingang (versorgung.md 3.1): Schottky je Panel, TVS, Messung der Ladereingangsspannung", eingang, 20, 35, breite=370)

    lader = [
        b.teil("Bienen:BQ25185", "U201", "BQ25185DLHR", fp="Bienen:WSON-10-1EP_2.2x2mm_DLH0010A",
               netze={"IN": "VIN_LADER", "SYS": "SYS", "BAT": "VBAT", "~{CE}": "CE_LADEN", "TS/~{MR}": "NTC",
                      "ISET": "ISET", "ILIM/VSET": "ILIM", "STAT1": "LADE_STAT1", "STAT2": "LADE_STAT2",
                      "GND": "GND", "EP": "GND"},
               info="Footprint DLH 2,2 × 2 mm selbst anlegen [P]; Thermal-Pad mit 6–9 Vias auf L2"),
        b.teil("Device:R", "R203", "2,0k 1%", fp=R0603, netze={"1": "ISET", "2": "GND"}, info="ICHG = 300 AΩ / 2 kΩ = 150 mA (HW26-11)"),
        b.teil("Device:R", "R204", "130k 1%", fp=R0603, netze={"1": "ILIM", "2": "GND"}, info="Tab. 6-1: VBATREG 4,1 V, ILIM 500 mA"),
        b.teil("Device:C", "C204", "10µ", fp=C0805, netze={"1": "SYS", "2": "GND"}, info="≥ 10 µF an SYS"),
        b.teil("Device:C", "C205", "4,7µ", fp=C0805, netze={"1": "VBAT", "2": "GND"}, info="≥ 1 µF an BAT"),
        b.teil("Device:R", "R205", "100k", fp=R0603, netze={"1": "SYS", "2": "CE_LADEN"},
               info="CE-Pull-up: Leitungsbruch CE_FREI → Laden gesperrt. Strom nur bei Sonne (Q2 an TMP_VCC); SCH26-02"),
        b.teil("Device:C", "C206", "10n", fp=C0603, netze={"1": "CE_LADEN", "2": "GND"}, info="Störschutz an CE (RC 1 ms)"),
        b.teil("Bienen:TPS70933DBV", "U204", "TPS70933DBV", fp="Package_TO_SOT_SMD:SOT-23-5",
               netze={"IN": "VIN_LADER", "EN": "NC", "OUT": "TMP_VCC", "GND": "GND"},
               info="TMP_VCC für die Ladesperre auf der Akku-Platine, nur bei Sonne/USB (SCH26-01); EN offen = ein (max. 6,5 V)"),
        b.teil("Device:C", "C212", "2,2µ", fp=C0603, netze={"1": "TMP_VCC", "2": "GND"}, info="≥ 2,2 µF am Ausgang (Datenblatt)"),
        b.teil("Connector:TestPoint", "TP201", "STAT1", fp="TestPoint:TestPoint_Pad_D1.0mm", netze={"1": "LADE_STAT1"}),
        b.teil("Connector:TestPoint", "TP202", "STAT2", fp="TestPoint:TestPoint_Pad_D1.0mm", netze={"1": "LADE_STAT2"}),
        b.teil("Connector_Generic:Conn_01x05", "J203", "Akku (JST PH 5)", fp="Connector_JST:JST_PH_B5B-PH-K_1x05_P2.00mm_Vertical",
               netze={"1": "GND", "2": "NTC", "3": "CE_LADEN", "4": "TMP_VCC", "5": "VBAT"},
               info="Kabel 1:1 zur Akku-Platine J1: 1 P−, 2 NTC, 3 CE_FREI, 4 TMP_VCC, 5 P+"),
        b.teil("power:PWR_FLAG", "#FLG203", "PWR_FLAG", netze={"1": "VBAT"}),
        b.teil("Device:R", "R206", "2,2M", fp=R0603, netze={"1": "VBAT", "2": "ADC_AKKU"}, info="Akkuteiler 1:2, 0,9 µA"),
        b.teil("Device:R", "R207", "2,2M", fp=R0603, netze={"1": "ADC_AKKU", "2": "GND"}),
        b.teil("Device:C", "C207", "100n", fp=C0603, netze={"1": "ADC_AKKU", "2": "GND"}),
    ]
    y = b.gruppe("Laderegler BQ25185 (3.2/3.3): 4,1 V, 150 mA; CE und NTC von der Ladesperre der Akku-Platine; TMP_VCC nur bei Sonne",
                 lader, 20, y + 25, breite=370)

    regler = [
        b.teil("Bienen:RT9080-33GJ5", "U202", "RT9080-33GJ5", fp="Package_TO_SOT_SMD:TSOT-23-5", lcsc="C841192",
               netze={"VIN": "SYS", "EN": "SYS", "VOUT": "+3V3", "GND": "GND"}, info="EN an VIN (nicht offen lassen)"),
        b.teil("Device:C", "C208", "1µ", fp=C0603, netze={"1": "SYS", "2": "GND"}),
        b.teil("Device:C", "C209", "1µ", fp=C0603, netze={"1": "+3V3", "2": "GND"}, info="100 µF + 10 µF am Funkmodul (Blatt Funk)"),
        b.teil("Power_Management:TPS22917DBV", "U203", "TPS22917DBV", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C2681320",
               netze={"VIN": "+3V3", "VOUT": "3V3_SW", "ON": "SENSOR_EIN", "CT": "SW_CT", "QOD": "SW_QOD", "GND": "GND"},
               info="QOD über R209 an VOUT: aktive Entladung; CT nach VIN (Datenblatt Tab. 6-1)"),
        b.teil("Device:R", "R209", "0", fp=R0603, netze={"1": "SW_QOD", "2": "3V3_SW"},
               info="QOD-Widerstand (Datenblatt: extern oder direkt); 0 Ω = interner Wert, bei Bedarf erhöhen"),
        b.teil("Device:C", "C210", "1n", fp=C0603, netze={"1": "SW_CT", "2": "+3V3"}, info="CT 1 nF → Anstieg ca. 1,7 ms bei 3,3 V"),
        b.teil("Device:R", "R208", "100k", fp=R0603, netze={"1": "SENSOR_EIN", "2": "GND"}, info="ON nie offen (Standby: GPIO hochohmig); 100 kΩ wie versorgung.md 3.7 (SCH26-05)"),
        b.teil("Device:C", "C211", "1µ", fp=C0603, netze={"1": "3V3_SW", "2": "GND"}),
    ]
    b.gruppe("3,3 V (RT9080, 3.6) und geschaltete Sensorschiene 3V3_SW (TPS22917, 3.7)", regler, 20, y + 25, breite=370)

    b.text("Regeln: Pull-ups nur an 3V3_SW; TS/MR nie aktiv auf Masse (Werksmodus); Laderegler nicht neben der Zelle; "
           "SPI-Flash an +3V3 (dauernd).", 20, 270)
    return b


def baue():
    p = Projekt("logger", os.path.join(HIER, "hauptplatine"), firma="Bienenlogger – Philipp Schnabel",
                rev="0.1 Entwurf", datum="2026-10-09", eigene_bibs={"Bienen": BIB})
    p.schnittstellen = set(SCHNITTSTELLEN)
    w = p.blatt("Bienenlogger Hauptplatine", "logger.kicad_sch", titel="Bienenlogger Hauptplatine 121 × 121 mm, 4 Lagen")
    w.text("Blätter: Versorgung (fertig). Folgen: MCU, Funk + Flash, Waage, Mikrofon, Anschlüsse.", 30, 25, 2.0)
    versorgung(p)
    return p


if __name__ == "__main__":
    pr = baue()
    g = pr.schreibe()
    print("geschrieben:", pr.ordner, "| globale Netze:", ", ".join(sorted(g)))
