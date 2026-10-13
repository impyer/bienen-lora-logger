#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Versorgungslage L3 (In2.Cu) der Hauptplatine anlegen (Lastenheft M8).

Aufbau nach M8: L1 Signal/Bauteile, L2 durchgehende Masse (GND_L2, platine_fein.py), **L3 Versorgung mit
Masse-Füllung**, L4 Signal. Dieses Skript legt auf L3 an:

1. „P3V3_L3“: Fläche +3V3 (Priorität 1) über dem oberen Teil der Platine – Mikrocontroller, Funkmodul, Flash,
   USB/Taster, Debug- und Erweiterungsleiste, LED/Reed an der linken Kante – mit einem Arm zu den Reglern
   U202 (RT9080, Ausgang +3V3) und U203 (Lastschalter, Eingang +3V3) im Versorgungsblock.
2. „GND_L3“: Masse-Füllung (Priorität 0) über die ganze Platine. Sie füllt alles außerhalb der +3V3-Fläche,
   also auch unter dem Mikrofonzweig und den Klemmen (zweite Massefläche unter dem Analogteil, A3).

SYS, 3V3_SW, 5 V der Waage und 3V3_ANA bekommen beim Routing breite Leiterbahnen (auf L3 durch die Masse-Füllung
oder auf L4), keine eigenen Flächen: Ihre Verbraucher liegen verteilt, eigene Flächen würden L3 zerstückeln.

Wiederholbar: Zonen werden nur angelegt, wenn es sie mit diesem Namen noch nicht gibt; danach werden alle Zonen
neu gefüllt. Aufruf: python3 hardware/kicad/werkzeug/platine_lagen.py
"""
import os
import sys

import pcbnew

HIER = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HIER), "hauptplatine", "logger.kicad_pcb")

# Platinenkoordinaten in mm (Umriss 39,5 … 160,5)
P3V3_UMRISS = [(40.0, 40.0), (160.0, 40.0), (160.0, 108.0), (76.0, 108.0), (76.0, 138.0),
               (52.0, 138.0), (52.0, 118.0), (40.0, 118.0)]
GANZ = [(40.0, 40.0), (160.0, 40.0), (160.0, 160.0), (40.0, 160.0)]


def mm(x):
    return pcbnew.FromMM(x)


def zone(board, name, netz, umriss, prio):
    for z in board.Zones():
        if z.GetZoneName() == name:
            return False
    z = pcbnew.ZONE(board)
    z.SetZoneName(name)
    z.SetLayer(pcbnew.In2_Cu)
    z.SetNet(board.FindNet(netz))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(0.2))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    o = z.Outline()
    o.NewOutline()
    for x, y in umriss:
        o.Append(mm(x), mm(y))
    board.Add(z)
    return True


def main():
    board = pcbnew.LoadBoard(PCB)
    neu = [n for n, args in (("P3V3_L3", ("+3V3", P3V3_UMRISS, 1)), ("GND_L3", ("GND", GANZ, 0)))
           if zone(board, n, *args)]
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print("L3: neu angelegt %s; alle Zonen gefüllt" % (", ".join(neu) or "nichts"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
