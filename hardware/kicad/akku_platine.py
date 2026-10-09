#!/usr/bin/env python3
"""Schaltplan der Akku-Platine (eigenes KiCad-Projekt hardware/kicad/akku-platine/).

Inhalt (versorgung.md 3.3/3.4, LASTENHEFT V1/V2/V3):
- Zelle 18650 im Halter
- Zellschutz HY2111-GB + Doppel-FET FS8205 (2,90 V aus / 4,28 V)
- Strommessbrücke in B+ (Lötbrücke geschlossen, Stiftleiste für das Amperemeter)
- NTC 10 k für den TS-Pin des BQ25185 (Stufe 2 der Ladesperre)
- TMP390 + N-FET: Ladesperre Stufe 1, +5 … 42 °C, Leitung CE_FREI (Leitungsbruch → gesperrt)
- Stecker J1 JST PH 4-polig: 1 P−, 2 NTC, 3 CE_FREI, 4 P+

Aufruf: python3 hardware/kicad/akku_platine.py
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


def baue():
    p = Projekt("akku", os.path.join(HIER, "akku-platine"), firma="Bienenlogger – Philipp Schnabel",
                rev="0.1 Entwurf", datum="2026-10-09", eigene_bibs={"Bienen": BIB})
    b = p.blatt("Akku-Platine", "akku.kicad_sch", titel="Akku-Platine: Zellschutz, Ladesperre")

    # --- Zelle, Messbrücke, Stecker ---
    zelle = [
        b.teil("Device:Battery_Cell", "BT1", "18650 3,6 V", fp="Battery:BatteryHolder_Keystone_1042_1x18650",
               netze={"+": "B+", "-": "B-"},
               info="Halter Keystone 1043 (SMD) vorgesehen; Footprint 1042 nur Platzhalter [P]"),
        b.teil("Jumper:SolderJumper_2_Bridged", "JP1", "Messbrücke B+", fp="Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
               netze={"A": "B+", "B": "P+"}, info="Zum Strommessen auftrennen, Amperemeter an J2"),
        b.teil("Connector_Generic:Conn_01x02", "J2", "Strommessung", fp="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
               netze={"1": "B+", "2": "P+"}, dnp=True, info="nur bei Bedarf bestücken"),
        b.teil("Connector_Generic:Conn_01x04", "J1", "JST PH 4-polig", fp="Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal",
               netze={"1": "GND", "2": "NTC", "3": "CE_FREI", "4": "P+"},
               info="Kabel zur Hauptplatine J3: 1 P−(GND), 2 NTC, 3 CE_FREI, 4 P+"),
        b.teil("power:PWR_FLAG", "#FLG101", "PWR_FLAG", netze={"1": "B+"}),
        b.teil("power:PWR_FLAG", "#FLG102", "PWR_FLAG", netze={"1": "B-"}),
        b.teil("power:PWR_FLAG", "#FLG103", "PWR_FLAG", netze={"1": "P+"}),
        b.teil("power:PWR_FLAG", "#FLG104", "PWR_FLAG", netze={"1": "GND"}),
    ]
    b.gruppe("Zelle, Messbrücke, Stecker zur Hauptplatine", zelle, 20, 30, breite=380)

    # --- Zellschutz (HYCON-Anwendungsschaltung: R1 100 Ω, C1 100 nF, R2 2 kΩ) ---
    schutz = [
        b.teil("Bienen:HY2111-GB", "U1", "HY2111-GB", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C82747",
               netze={"VDD": "HY_VDD", "VSS": "B-", "CS": "HY_CS", "OD": "GATE_ENTL", "OC": "GATE_LADE"}),
        b.teil("Device:R", "R1", "100", fp=R0603, netze={"1": "B+", "2": "HY_VDD"}, info="HYCON-Anwendungsschaltung R1"),
        b.teil("Device:C", "C1", "100n", fp=C0603, netze={"1": "HY_VDD", "2": "B-"}, info="HYCON C1"),
        b.teil("power:PWR_FLAG", "#FLG105", "PWR_FLAG", netze={"1": "HY_VDD"}),
        b.teil("Device:R", "R2", "2k", fp=R0603, netze={"1": "HY_CS", "2": "GND"}, info="HYCON R2 (CS an P−)"),
        b.teil("Bienen:FS8205", "Q1", "FS8205", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C32254",
               netze={"G1": "GATE_ENTL", "S1": "B-", "G2": "GATE_LADE", "S2": "GND", "D12": "D12"},
               info="M1 Entladen (G1, S1 an B−), M2 Laden (G2, S2 an P−)"),
    ]
    b.gruppe("Zellschutz: HY2111-GB + FS8205 (2,90 V aus, Freigabe durch Laden)", schutz, 20, 95, breite=380)

    # --- Ladesperre Stufe 1 und NTC ---
    sperre = [
        b.teil("Bienen:TMP390", "U2", "TMP390A2DRL", fp="Package_TO_SOT_SMD:SOT-563",
               netze={"VDD": "P+", "GND": "GND", "SETA": "SETA", "SETB": "SETB", "~{OUTA}": "GATE_CE", "~{OUTB}": "GATE_CE"},
               info="OUTA heiß 42 °C, OUTB kalt +5 °C, Hysterese 5 °C; Ausgänge verbunden (wired-OR)"),
        b.teil("Device:C", "C2", "100n", fp=C0603, netze={"1": "P+", "2": "GND"}),
        b.teil("Device:R", "R3", "2,49k 1%", fp=R0603, netze={"1": "SETA", "2": "GND"}, info="TMP390 Tab. 7-1: 42 °C"),
        b.teil("Device:R", "R4", "18,7k 1%", fp=R0603, netze={"1": "SETB", "2": "GND"}, info="TMP390 Tab. 7-2: +5 °C, Hysterese 5 °C"),
        b.teil("Device:R", "R5", "10M", fp=R0603, netze={"1": "P+", "2": "GATE_CE"}, info="Gate-Pull-up; Strom nur bei gesperrtem Laden"),
        b.teil("Transistor_FET:AO3400A", "Q2", "AO3400A", fp="Package_TO_SOT_SMD:SOT-23",
               netze={"G": "GATE_CE", "S": "GND", "D": "CE_FREI"}, info="leitet → CE low → Laden erlaubt"),
        b.teil("Device:Thermistor_NTC", "TH1", "10k B3435", fp="Resistor_SMD:R_0603_1608Metric",
               netze={"1": "NTC", "2": "GND"}, info="unter der Zelle, Wärmeleitpad; B = 3435 K (BQ25185-Schwellen)"),
    ]
    b.gruppe("Ladesperre: TMP390 (Stufe 1, +5 … 42 °C) und NTC für BQ25185 (Stufe 2)", sperre, 20, 160, breite=380)

    b.text("TMP390 und NTC direkt unter der Zelle anordnen (Wärmekopplung). Leitungsbruch an CE_FREI: Pull-up auf der Hauptplatine → CE high → Laden gesperrt.", 20, 255)
    b.text("Quellen: HYCON HY2111 (LCSC C82747) Abschnitt 7/10; FS8205 (LCSC C32254); TI TMP390 SBOS904A Tab. 7-1/7-2; versorgung.md 3.3/3.4.", 20, 262)
    return p


if __name__ == "__main__":
    pr = baue()
    pr.schreibe()
    print("geschrieben:", pr.ordner)
