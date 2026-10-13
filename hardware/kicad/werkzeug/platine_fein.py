#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Feinplatzierung der kritischen Bauteilgruppen auf hardware/kicad/hauptplatine/logger.kicad_pcb.

Setzt Lage und Drehung der Bauteile in FEIN (relativ zum Bezugsbauteil, dessen Lage aus der Grobplatzierung
übernommen wird) und legt die Masse-Durchkontaktierungen in den Thermal-Pads an (VIAS). Gruppen:

1. STM32 U301 (mcu-funk.md 1.1/1.2): je ein 100 nF direkt an jedem VDD/VSS-Paar, VCAP 4,7 µF an Pin 22,
   VDDA-Filter an Pin 9, Quarze direkt am Gehäuse mit Lastkondensatoren außen (AN2867), BOOT0/NRST.
2. Funkmodul U401 (mcu-funk.md 2.2): 100 µF + 10 µF + 100 nF und TVS direkt an Pin 3 (VCC), ANT (Pin 1) frei.
3. 5-V-Wandler U501 (TPS61240, waage.md): kurze Schleife CIN – VIN – L – SW, COUT direkt an VOUT/GND.
4. Thermal-Pads: BQ25185 U201 2 Vias (TI-Layoutbeispiel), STM32-EP 9 Vias, TPS61240-EP 2 Vias, alle an GND (L2).
5. Lagenaufbau (Lastenheft M8): L2 = durchgehende Massefläche „GND_L2“ (einmalig angelegt, danach gefüllt).

Das Skript ist wiederholbar: Es setzt absolute Lagen und legt Vias nur an, wo noch keine liegt. Alle übrigen
Bauteile bleiben, wie sie sind (auch von Hand verschobene).

Aufruf: python3 hardware/kicad/werkzeug/platine_fein.py
"""
import os
import sys

import pcbnew

HIER = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HIER), "hauptplatine", "logger.kicad_pcb")

# Bezug -> {Ref: (dx, dy, Drehung)}; dx/dy in mm relativ zur Lage des Bezugs, Drehung absolut in Grad
FEIN = {
    "U301": {
        # Nordseite (Pins 37–48): VDD 48 / VSS 47, BOOT0 44
        "C301": (-2.5, -5.1, 0),       # 100 nF an Pin 48/47
        "R301": (0.7, -5.1, 0),        # BOOT0-Pull-down an Pin 44
        # Ostseite (Pins 25–36): VDD 36 / VSS 35
        "C302": (5.1, -3.0, 90),       # 100 nF an Pin 36/35
        # Südseite (Pins 13–24): VCAP 22, VSS 23, VDD 24, BOOT1 20
        "C307": (0.3, 5.4, 0),         # VCAP 4,7 µF an Pin 22
        "C303": (3.9, 5.1, 0),         # 100 nF an Pin 24/23
        "C304": (3.9, 7.1, 0),         # 10 µF Sammelkondensator
        "R302": (-1.9, 7.6, 0),        # BOOT1-Pull-down an Pin 20
        # Westseite (Pins 1–12): VBAT 1, LSE 3/4, HSE 5/6, NRST 7, VSSA 8, VDDA 9
        "Y302": (-6.4, -5.5, 0),       # 32,768 kHz an Pin 3/4, Lastkondensatoren nach außen
        "C312": (-7.65, -8.3, 90),
        "C313": (-5.15, -8.3, 90),
        "C308": (-5.1, -2.5, 90),      # 100 nF an VBAT (Pin 1)
        "Y301": (-8.4, 0.2, 90),       # 25 MHz an Pin 5/6
        "C310": (-12.0, 2.0, 90),
        "C311": (-12.0, -1.6, 90),
        "C305": (-5.1, 1.9, 90),       # 100 nF an VDDA (Pin 9) / VSSA (Pin 8)
        "C306": (-5.1, 5.2, 90),       # 1 µF an VDDA
        "FB301": (-7.0, 5.2, 90),      # Ferrit +3V3 → VDDA
        "C309": (-8.9, 5.2, 90),       # NRST 100 nF
    },
    "U401": {
        # links: Pin 2 GND (−7,68 / −5,0), Pin 3 VCC (−7,68 / −3,0), Pin 5 TXEN_MOD; Courtyard des Moduls bis x = −10,25
        "C403": (-11.2, -3.0, 90),     # 100 nF direkt an Pin 3
        "D401": (-11.2, -0.15, 90),    # TVS 3,3 V an Pin 3
        "C402": (-13.4, -3.0, 90),     # 10 µF
        "C401": (-16.4, -3.0, 90),     # 100 µF
        "JP401": (-14.1, 1.05, 90),    # TXEN-Lötbrücke an Pin 5
        # rechts: SPI-Pins 12 SCK (+1,0), 13 MISO (−1,0), 14 MOSI (−3,0), 15 NSS (−5,0); Reihenwiderstände auf Pinhöhe
        "R404": (12.2, -5.0, 0),
        "R403": (12.2, -3.0, 0),
        "R402": (12.2, -1.0, 0),
        "R401": (12.2, 1.0, 0),
        "R405": (15.3, -5.0, 0),       # NSS-Pull-up
        "JP402": (12.6, 3.2, 0),       # RXEN-Lötbrücke an Pin 11
    },
    "U501": {
        # Pins: 1 GND oben links, 2/3 VOUT links, 4 EN unten rechts, 5 L rechts Mitte, 6 VIN oben rechts
        "C501": (0.0, -3.0, 180),      # CIN: Pad 1 (SYS) rechts an Pin 6, Pad 2 (GND) links an Pin 1
        "L501": (2.5, 0.2, 270),       # Pad 1 (SYS) oben, Pad 2 (L) an Pin 5
        "C502": (-2.6, 0.0, 90),       # COUT: Pad 1 (5 V) unten an Pin 2/3, Pad 2 (GND) oben an Pin 1
        "R501": (2.6, 3.2, 0),         # EN-Pull-down an Pin 4
        "Q501": (-3.8, -3.6, 0),
    },
}

# Masse-Vias in Thermal-Pads: Bezug -> Liste (dx, dy); Via 0,6/0,3 mm (Entwurfsregel), Netz GND
VIAS = {
    "U201": [(0.0, -0.4), (0.0, 0.4)],                                    # TI DLH0010A: 2 Vias
    "U301": [(x, y) for x in (-1.4, 0.0, 1.4) for y in (-1.4, 0.0, 1.4)],  # EP 5,6 × 5,6 mm
    "U501": [(0.0, -0.4), (0.0, 0.4)],                                    # EP 1,0 × 1,6 mm
}
VIA_D, VIA_BOHR = 0.6, 0.3


def mm(x):
    return pcbnew.FromMM(x)


def main():
    board = pcbnew.LoadBoard(PCB)
    fp = {f.GetReference(): f for f in board.GetFootprints()}
    for bezug, teile in FEIN.items():
        bx, by = (pcbnew.ToMM(v) for v in fp[bezug].GetPosition())
        for ref, (dx, dy, rot) in teile.items():
            f = fp[ref]
            f.SetOrientationDegrees(rot)
            f.SetPosition(pcbnew.VECTOR2I(mm(bx + dx), mm(by + dy)))
            f.Reference().SetPosition(f.GetPosition())          # Referenz in die Bauteilmitte (dicht gepackt)
            f.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
            f.Reference().SetTextThickness(mm(0.12))
    gnd = board.FindNet("GND")
    vorhanden = {(t.GetPosition().x, t.GetPosition().y) for t in board.GetTracks() if t.GetClass() == "PCB_VIA"}
    neu = 0
    for bezug, liste in VIAS.items():
        bx, by = (pcbnew.ToMM(v) for v in fp[bezug].GetPosition())
        for dx, dy in liste:
            p = pcbnew.VECTOR2I(mm(bx + dx), mm(by + dy))
            if (p.x, p.y) in vorhanden:
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(p)
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_BOHR))
            v.SetNet(gnd)
            board.Add(v)
            neu += 1
    # Lagenaufbau M8: L2 (In1.Cu) durchgehende Massefläche über die ganze Platine
    if not any(z.GetZoneName() == "GND_L2" for z in board.Zones()):
        z = pcbnew.ZONE(board)
        z.SetZoneName("GND_L2")
        z.SetLayer(pcbnew.In1_Cu)
        z.SetNet(gnd)
        z.SetLocalClearance(mm(0.2))
        z.SetMinThickness(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((40.0, 40.0), (160.0, 40.0), (160.0, 160.0), (40.0, 160.0)):
            o.Append(mm(x), mm(y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print("Feinplatzierung: %d Bauteile gesetzt, %d Vias neu" % (sum(len(t) for t in FEIN.values()), neu))
    return 0


if __name__ == "__main__":
    sys.exit(main())
