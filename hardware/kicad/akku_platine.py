#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Schaltplan der Akku-Platine (eigenes KiCad-Projekt hardware/kicad/akku-platine/).

Inhalt (versorgung.md 3.3/3.4, LASTENHEFT V1/V2/V3):
- Zelle 18650 im Halter
- Zellschutz HY2111-GB + Doppel-FET FS8205 (2,90 V aus / 4,28 V)
- Strommessbrücke in B+ (Lötbrücke geschlossen, Stiftleiste für das Amperemeter)
- Ladesperre Stufe 1: TMP390 (U2) + N-FET Q2 → CE_FREI → CE des BQ25185, außerhalb +5 … 42 °C gesperrt
- Ladesperre Stufe 2: zweiter TMP390 (U3, 42 °C) trennt mit Q3 den NTC → TS offen → BQ25185 sperrt
  (unabhängig vom CE-Pfad, SCH26-03); NTC 10 k sperrt zusätzlich unter ca. +1,7 °C und über ca. 59,5 °C
- Beide TMP390 und alle Pull-ups hängen an TMP_VCC: 3,3 V aus dem Ladereingang (TPS70933 auf der
  Hauptplatine). Sie arbeiten damit auch, wenn der Zellschutz nach Tiefentladung getrennt hat
  (SCH26-01), und ziehen nachts keinen Strom aus der Zelle.
- Stecker J1 JST PH 5-polig: 1 P−(GND), 2 NTC, 3 CE_FREI, 4 TMP_VCC, 5 P+

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


def zeichne(b, T):
    """Platzierung und Leitungen nach Stromfluss (Verdrahtungsmodus, A3 quer, Maße in mm).
    Oben der Leistungspfad B+ → Messbrücke → P+ → Stecker, darunter der Zellschutz im Minuspfad
    B− → FS8205 → P− (GND). Unten die Ladesperre: Stufe 2 (NTC-Kreis) und Stufe 1 (CE), beide
    aus TMP_VCC vom Stecker. Jede Verbindung prüft netz_tests.py gegen die Netzbeschreibung."""
    S, D, L = b.setze, b.draht, b.label

    # --- Überschriften ------------------------------------------------------
    b.text("1  Leistungspfad: Zelle → Messbrücke JP1 → P+ zum Stecker J1", 40.64, 22.86, 2.0)
    b.text("2  Zellschutz im Minuspfad: HY2111 schaltet Q1 (M1 Entladen, M2 Laden); GND = P−", 101.6, 58.42, 2.0)
    b.text("3  Ladesperre Stufe 2 (SCH26-03): U3 öffnet über 42 °C mit Q3 den NTC-Kreis → TS offen → BQ25185 lädt nicht", 40.64, 129.54, 2.0)
    b.text("4  Ladesperre Stufe 1 (CE)", 40.64, 203.2, 2.0)
    b.text("U2 sperrt außerhalb +5 … 42 °C über Q2: CE_FREI high → BQ25185 lädt nicht", 40.64, 208.28, 1.5)
    b.text("TMP_VCC kommt von der Hauptplatine (TPS70933 am Ladereingang): nur bei Sonne/USB vorhanden. "
           "Fehlt es oder reißt eine Ader, sperren beide Stufen. Keine Verbindung der Sperre zu B+/B− (SCH26-01).",
           40.64, 276.86, 1.5)

    # --- 1 Leistungspfad ----------------------------------------------------
    yb = 45.72                       # B+/P+-Schiene
    S(T["BT1"], 50.8, 76.2, text="links")
    S(T["JP1"], 127.0, yb, text="unten")
    S(T["J2"], 124.46, 33.02, rot=90, text="links")
    S(T["J1"], 279.4, 101.6)
    D(T["BT1"].p("+"), (50.8, yb), T["JP1"].p("A"))
    D(T["J2"].p("1"), (124.46, 40.64), (119.38, 40.64), (119.38, yb))
    D(T["J2"].p("2"), (127.0, 40.64), (134.62, 40.64), (134.62, yb))
    D(T["JP1"].p("B"), (287.02, yb), (287.02, 114.3), (274.32, 114.3), T["J1"].p("5"))
    L("B+", 55.88, yb)
    L("P+", 160.02, yb)

    # --- 2 Zellschutz -------------------------------------------------------
    yminus = 99.06                   # B−-Schiene
    S(T["R1"], 76.2, 57.15, text="links")
    S(T["U1"], 116.84, 76.2)
    S(T["C1"], 86.36, 81.28, text="links")
    S(T["R2"], 99.06, 86.36)
    S(T["Q1"], 165.1, 96.52)
    D(T["R1"].p("1"), (76.2, yb))
    D(T["R1"].p("2"), (76.2, 71.12), T["U1"].p("VDD"))
    D(T["C1"].p("1"), (86.36, 71.12))
    D(T["U1"].p("CS"), (99.06, 73.66), T["R2"].p("1"))
    D(T["BT1"].p("-"), (50.8, yminus), T["Q1"].p("S1"))
    D(T["U1"].p("VSS"), (116.84, yminus))
    D(T["C1"].p("2"), (86.36, yminus))
    D(T["U1"].p("OD"), (149.86, 71.12), (149.86, 96.52), T["Q1"].p("G1"))
    D(T["U1"].p("OC"), (177.8, 73.66), (177.8, 96.52), T["Q1"].p("G2"))
    D(T["Q1"].p("2"), T["Q1"].p("5"))
    L("HY_VDD", 76.2, 69.85, 90)
    L("HY_CS", 99.06, 81.28, 90)
    L("B-", 55.88, yminus)
    L("GATE_ENTL", 129.54, 71.12)
    L("GATE_LADE", 157.48, 73.66)
    L("D12", 163.83, 86.36)

    # --- Stecker-Spalten: NTC, CE_FREI, TMP_VCC ------------------------------
    x_ntc, x_ce, x_vcc, x_li = 251.46, 254.0, 256.54, 55.88
    D((x_ntc, 99.06), T["J1"].p("2"))
    D((x_ce, 101.6), T["J1"].p("3"))
    D((x_vcc, 104.14), T["J1"].p("4"))

    # --- 3 Stufe 2 ----------------------------------------------------------
    o = 7.62
    y2 = 139.7 + o                   # TMP_VCC-Schiene Stufe 2
    S(T["C3"], 66.04, 147.32 + o, text="links")
    S(T["U3"], 106.68, 160.02 + o)
    S(T["R6"], 81.28, 177.8 + o, text="links")
    S(T["R7"], 91.44, 177.8 + o)
    S(T["R8"], 127.0, 147.32 + o)
    S(T["Q3"], 139.7, 160.02 + o)
    S(T["TH1"], 142.24, 139.7 + o)
    D((x_li, y2), (127.0, y2))
    D(T["C3"].p("1"), (66.04, y2))
    D(T["U3"].p("VDD"), (76.2, 154.94 + o), (76.2, y2))
    D(T["U3"].p("SETA"), (81.28, 157.48 + o), T["R6"].p("1"))
    D(T["U3"].p("SETB"), (91.44, 160.02 + o), T["R7"].p("1"))
    D(T["R8"].p("1"), (127.0, y2))
    D(T["U3"].p("~{OUTA}"), (132.08, 154.94 + o), (132.08, 160.02 + o), T["Q3"].p("G"))
    D(T["R8"].p("2"), (127.0, 154.94 + o))
    D(T["TH1"].p("2"), T["Q3"].p("D"))
    D(T["TH1"].p("1"), (142.24, 137.16), (x_ntc, 137.16), (x_ntc, 99.06))
    L("SETA2", 81.28, 171.45 + o, 90)
    L("SETB2", 91.44, 171.45 + o, 90)
    L("GATE_NTC", 132.08, 160.02 + o)
    L("NTC_FUSS", 142.24, 151.13 + o)
    L("NTC", 190.5, 137.16)

    # --- 4 Stufe 1 ----------------------------------------------------------
    o = 20.32
    y1 = 193.04 + o                  # TMP_VCC-Schiene Stufe 1
    S(T["C2"], 66.04, 200.66 + o, text="links")
    S(T["U2"], 106.68, 213.36 + o)
    S(T["R3"], 81.28, 231.14 + o, text="links")
    S(T["R4"], 91.44, 231.14 + o)
    S(T["R5"], 127.0, 200.66 + o)
    S(T["Q2"], 139.7, 213.36 + o)
    D((x_li, y1), (127.0, y1))
    D(T["C2"].p("1"), (66.04, y1))
    D(T["U2"].p("VDD"), (76.2, 208.28 + o), (76.2, y1))
    D(T["U2"].p("SETA"), (81.28, 210.82 + o), T["R3"].p("1"))
    D(T["U2"].p("SETB"), (91.44, 213.36 + o), T["R4"].p("1"))
    D(T["R5"].p("1"), (127.0, y1))
    D(T["U2"].p("~{OUTA}"), (121.92, 208.28 + o), (132.08, 208.28 + o), (132.08, 213.36 + o), T["Q2"].p("G"))
    D(T["U2"].p("~{OUTB}"), (121.92, 210.82 + o), (121.92, 208.28 + o))
    D(T["R5"].p("2"), (127.0, 208.28 + o))
    D(T["Q2"].p("D"), (142.24, 198.12), (x_ce, 198.12), (x_ce, 101.6))
    L("SETA1", 81.28, 224.79 + o, 90)
    L("SETB1", 91.44, 224.79 + o, 90)
    L("GATE_CE", 124.46, 208.28 + o)
    L("CE_FREI", 190.5, 198.12)

    # --- TMP_VCC: vom Stecker nach unten, links hoch zu beiden Stufen -------
    y_unten = 266.7
    D((x_vcc, 104.14), (x_vcc, y_unten), (x_li, y_unten), (x_li, y2))
    L("TMP_VCC", 190.5, y_unten)

    # --- PWR_FLAGs auf den Schienen (Begründung je Flag in der Beschreibung) --
    S(T["#FLG101"], 63.5, yb)
    S(T["#FLG102"], 63.5, yminus)
    S(T["#FLG103"], 172.72, yb)
    S(T["#FLG104"], 195.58, 101.6)
    S(T["#FLG106"], 205.74, y_unten)
    S(T["#FLG105"], 81.28, 71.12)


def baue():
    p = Projekt("akku", os.path.join(HIER, "akku-platine"), firma="Bienenlogger – Philipp Schnabel",
                rev="0.1 Entwurf", datum="2026-10-09", eigene_bibs={"Bienen": BIB},
                kommentare=["Board-Kennung PCB-AKKU-0.1 (REG26-10)",
                            "Umgebung [A]: Gehäuse −20 … +60 °C, Betauung möglich; Laden nur +5 … 42 °C (sicherheit-akku.md)"])
    b = p.blatt("Akku-Platine", "akku.kicad_sch", titel="Akku-Platine: Zellschutz, Ladesperre")

    # --- Zelle, Messbrücke, Stecker ---
    zelle = [
        b.teil("Device:Battery_Cell", "BT1", "18650 3,6 V", fp="Battery:BatteryHolder_Keystone_1042_1x18650",
               netze={"+": "B+", "-": "B-"},
               info="Keystone 1042 (SMD), Entscheidung HW-02; Pad 1 = Plus; LCSC-Nummer [P]"),
        b.teil("Jumper:SolderJumper_2_Bridged", "JP1", "Messbrücke B+", fp="Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
               netze={"A": "B+", "B": "P+"}, info="Zum Strommessen auftrennen, Amperemeter an J2"),
        b.teil("Connector_Generic:Conn_01x02", "J2", "Strommessung", fp="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
               netze={"1": "B+", "2": "P+"}, dnp=True, info="nur bei Bedarf bestücken"),
        b.teil("Connector_Generic:Conn_01x05", "J1", "JST PH 5-polig", fp="Connector_JST:JST_PH_S5B-PH-K_1x05_P2.00mm_Horizontal",
               netze={"1": "GND", "2": "NTC", "3": "CE_FREI", "4": "TMP_VCC", "5": "P+"},
               info="Kabel 1:1 zur Hauptplatine J203: 1 P−(GND), 2 NTC, 3 CE_FREI, 4 TMP_VCC, 5 P+ (Kabelplan anschluesse.md)"),
        b.teil("power:PWR_FLAG", "#FLG101", "PWR_FLAG", netze={"1": "B+"}, info="Quelle: Zelle BT1 (+); der Halter ist für den ERC nur ein passiver Pin"),
        b.teil("power:PWR_FLAG", "#FLG102", "PWR_FLAG", netze={"1": "B-"}, info="Quelle: Zelle BT1 (−)"),
        b.teil("power:PWR_FLAG", "#FLG103", "PWR_FLAG", netze={"1": "P+"}, info="Zelle über die Lötbrücke JP1 (passiv); ohne Flag sähe der ERC keinen Treiber"),
        b.teil("power:PWR_FLAG", "#FLG104", "PWR_FLAG", netze={"1": "GND"}, info="P−: Zelle über Q1 (FS8205); der ERC kennt den FET nicht als Quelle"),
        b.teil("power:PWR_FLAG", "#FLG106", "PWR_FLAG", netze={"1": "TMP_VCC"}, info="Quelle: U204 (TPS70933) auf der Hauptplatine über J1 Pin 4, anderes KiCad-Projekt"),
    ]

    # --- Zellschutz (HYCON-Anwendungsschaltung: R1 100 Ω, C1 100 nF, R2 2 kΩ) ---
    schutz = [
        b.teil("Bienen:HY2111-GB", "U1", "HY2111-GB", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C82747",
               netze={"VDD": "HY_VDD", "VSS": "B-", "CS": "HY_CS", "OD": "GATE_ENTL", "OC": "GATE_LADE"}),
        b.teil("Device:R", "R1", "100", fp=R0603, netze={"1": "B+", "2": "HY_VDD"}, info="HYCON-Anwendungsschaltung R1"),
        b.teil("Device:C", "C1", "100n", fp=C0603, netze={"1": "HY_VDD", "2": "B-"}, info="HYCON C1"),
        b.teil("power:PWR_FLAG", "#FLG105", "PWR_FLAG", netze={"1": "HY_VDD"}, info="aus B+ über R1 100 Ω (HYCON-Anwendungsschaltung); der ERC sieht den Widerstand nicht als Treiber"),
        b.teil("Device:R", "R2", "2k", fp=R0603, netze={"1": "HY_CS", "2": "GND"}, info="HYCON R2 (CS an P−)"),
        b.teil("Bienen:FS8205", "Q1", "FS8205", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C32254",
               netze={"G1": "GATE_ENTL", "S1": "B-", "G2": "GATE_LADE", "S2": "GND", "D12": "D12"},
               info="M1 Entladen (G1, S1 an B−), M2 Laden (G2, S2 an P−)"),
    ]

    # --- Ladesperre Stufe 1: TMP390 U2 → Q2 → CE ---
    stufe1 = [
        b.teil("Bienen:TMP390", "U2", "TMP390A2DRL", fp="Package_TO_SOT_SMD:SOT-563",
               netze={"VDD": "TMP_VCC", "GND": "GND", "SETA": "SETA1", "SETB": "SETB1", "~{OUTA}": "GATE_CE", "~{OUTB}": "GATE_CE"},
               info="OUTA heiß 42 °C, OUTB kalt +5 °C, Hysterese 5 °C; Ausgänge verbunden (wired-OR)"),
        b.teil("Device:C", "C2", "100n", fp=C0603, netze={"1": "TMP_VCC", "2": "GND"}),
        b.teil("Device:R", "R3", "2,49k 1%", fp=R0603, netze={"1": "SETA1", "2": "GND"}, info="TMP390 Tab. 7-1: 42 °C"),
        b.teil("Device:R", "R4", "18,7k 1%", fp=R0603, netze={"1": "SETB1", "2": "GND"}, info="TMP390 Tab. 7-2: +5 °C, Hysterese 5 °C"),
        b.teil("Device:R", "R5", "100k", fp=R0603, netze={"1": "TMP_VCC", "2": "GATE_CE"},
               info="Gate-Pull-up an TMP_VCC: Leckstrom TMP390 ±0,1 µA → 10 mV (SCH26-02)"),
        b.teil("Transistor_FET:AO3400A", "Q2", "AO3400A", fp="Package_TO_SOT_SMD:SOT-23",
               netze={"G": "GATE_CE", "S": "GND", "D": "CE_FREI"}, info="leitet → CE low → Laden erlaubt"),
    ]

    # --- Ladesperre Stufe 2: TMP390 U3 trennt den NTC ---
    stufe2 = [
        b.teil("Bienen:TMP390", "U3", "TMP390A2DRL", fp="Package_TO_SOT_SMD:SOT-563",
               netze={"VDD": "TMP_VCC", "GND": "GND", "SETA": "SETA2", "SETB": "SETB2", "~{OUTA}": "GATE_NTC", "~{OUTB}": "NC"},
               info="nur Kanal A (heiß 42 °C, Hysterese 5 °C); OUTB offen (Datenblatt: erlaubt)"),
        b.teil("Device:C", "C3", "100n", fp=C0603, netze={"1": "TMP_VCC", "2": "GND"}),
        b.teil("Device:R", "R6", "2,49k 1%", fp=R0603, netze={"1": "SETA2", "2": "GND"}, info="TMP390 Tab. 7-1: 42 °C"),
        b.teil("Device:R", "R7", "18,7k 1%", fp=R0603, netze={"1": "SETB2", "2": "GND"}, info="Hysterese 5 °C (Kanal B ungenutzt)"),
        b.teil("Device:R", "R8", "100k", fp=R0603, netze={"1": "TMP_VCC", "2": "GATE_NTC"}, info="Gate-Pull-up Q3"),
        b.teil("Transistor_FET:AO3400A", "Q3", "AO3400A", fp="Package_TO_SOT_SMD:SOT-23",
               netze={"G": "GATE_NTC", "S": "GND", "D": "NTC_FUSS"},
               info="leitet → NTC wirkt; sperrt (zu heiß oder TMP_VCC fehlt) → TS offen → BQ25185 sperrt"),
        b.teil("Device:Thermistor_NTC", "TH1", "10k B3435", fp="Resistor_SMD:R_0603_1608Metric",
               netze={"1": "NTC", "2": "NTC_FUSS"}, info="unter der Zelle, Wärmeleitpad; B = 3435 K (BQ25185-Schwellen)"),
    ]
    zeichne(b, {t.ref: t for t in b.teile})
    return p


if __name__ == "__main__":
    pr = baue()
    pr.schreibe()
    print("geschrieben:", pr.ordner)
