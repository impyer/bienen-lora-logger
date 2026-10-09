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
        b.teil("Connector_Generic:Conn_01x05", "J1", "JST PH 5-polig", fp="Connector_JST:JST_PH_S5B-PH-K_1x05_P2.00mm_Horizontal",
               netze={"1": "GND", "2": "NTC", "3": "CE_FREI", "4": "TMP_VCC", "5": "P+"},
               info="Kabel 1:1 zur Hauptplatine J203: 1 P−(GND), 2 NTC, 3 CE_FREI, 4 TMP_VCC, 5 P+ (Kabelplan anschluesse.md)"),
        b.teil("power:PWR_FLAG", "#FLG101", "PWR_FLAG", netze={"1": "B+"}),
        b.teil("power:PWR_FLAG", "#FLG102", "PWR_FLAG", netze={"1": "B-"}),
        b.teil("power:PWR_FLAG", "#FLG103", "PWR_FLAG", netze={"1": "P+"}),
        b.teil("power:PWR_FLAG", "#FLG104", "PWR_FLAG", netze={"1": "GND"}),
        b.teil("power:PWR_FLAG", "#FLG106", "PWR_FLAG", netze={"1": "TMP_VCC"}),
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
    y = b.gruppe("Ladesperre Stufe 1: TMP390 U2 sperrt über CE außerhalb +5 … 42 °C", stufe1, 20, 160, breite=380)

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
    b.gruppe("Ladesperre Stufe 2 (SCH26-03): TMP390 U3 öffnet mit Q3 den NTC-Kreis über 42 °C → BQ25185 sperrt (TS offen)",
             stufe2, 20, y + 25, breite=380)

    b.text("U2, U3 und TH1 direkt unter der Zelle (Wärmeleitpad). Leitungsbruch CE_FREI oder TMP_VCC → Laden gesperrt. Keine Verbindung von TMP_VCC/GATE_* zu B+/B− (kein Pfad am Zellschutz vorbei, SCH26-01).", 20, 265)
    b.text("Quellen: HYCON HY2111 (LCSC C82747) Abschnitt 7/10; FS8205 (LCSC C32254); TI TMP390 SBOS904A Tab. 7-1/7-2; versorgung.md 3.3/3.4.", 20, 272)
    return p


if __name__ == "__main__":
    pr = baue()
    pr.schreibe()
    print("geschrieben:", pr.ordner)
