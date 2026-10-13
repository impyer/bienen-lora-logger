#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Einmaliger Start der Platinendatei hardware/kicad/hauptplatine/logger.kicad_pcb (Layout-Grundgerüst).

Legt an: 4 Kupferlagen, 1,6 mm; Umriss 121 × 121 mm (Lastenheft M1, Camdenboss CBHUB_02 Rev. N Blatt 5);
4 Befestigungslöcher Ø 3,4 mm auf 110,2 × 110,2 mm (nicht durchkontaktiert) mit Kupfersperrfläche Ø 7 mm;
Entwurfsregeln nach JLCPCB-Standardfertigung (konservativ); Hinweise zu Klemmenkante, Funkkante und Bauhöhe (HW-03).
Danach wird logger.kicad_pcb **von Hand in KiCad** weiterbearbeitet (Bauteile über „Platine aus Schaltplan
aktualisieren“). Das Skript überschreibt eine vorhandene Platinendatei nicht.

Aufruf: python3 hardware/kicad/werkzeug/platine_start.py
"""
import os
import sys

import pcbnew

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(os.path.dirname(HIER), "hauptplatine", "logger.kicad_pcb")

MITTE = (100.0, 100.0)        # Platinenmitte im KiCad-Blatt (mm)
SEITE = 121.0                 # Lastenheft M1
ECKRADIUS = 3.0               # [A] Ecken gerundet (M1 nennt keinen Wert)
LOCHABSTAND = 110.2           # CBHUB_02 Blatt 5
LOCH = 3.4                    # Ø Bohrung in der Platine, Blatt 5
SPERRE = 7.0                  # Ø Kupfersperrfläche: Hülse Außen-Ø ≤ 6 mm + Rand (HW-03) [A]


def mm(x):
    return pcbnew.FromMM(x)


def punkt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def linie(board, lage, x1, y1, x2, y2, breite=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(punkt(x1, y1))
    s.SetEnd(punkt(x2, y2))
    s.SetLayer(lage)
    s.SetWidth(mm(breite))
    board.Add(s)


def bogen(board, lage, cx, cy, sx, sy, winkel, breite=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(punkt(cx, cy))
    s.SetStart(punkt(sx, sy))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(winkel, pcbnew.DEGREES_T))
    s.SetLayer(lage)
    s.SetWidth(mm(breite))
    board.Add(s)


def text(board, lage, inhalt, x, y, groesse=1.5):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(inhalt)
    t.SetPosition(punkt(x, y))
    t.SetLayer(lage)
    t.SetTextSize(pcbnew.VECTOR2I(mm(groesse), mm(groesse)))
    t.SetTextThickness(mm(groesse * 0.15))
    board.Add(t)


def befestigungsloch(board, nr, x, y):
    fp = pcbnew.FootprintLoad(os.path.join(os.path.dirname(HIER), "Bienen.pretty"), "Befestigung_3.4mm_Huelse")
    fp.SetFPID(pcbnew.LIB_ID("Bienen", "Befestigung_3.4mm_Huelse"))
    fp.SetReference("H%d" % nr)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.SetBoardOnly(True)                        # kein Schaltplansymbol (Abgleich Platine ↔ Schaltplan)
    fp.SetPosition(punkt(x, y))
    board.Add(fp)
    # Kupfersperrfläche auf allen Lagen (Schraubenkopf/Hülse, kein Kupfer)
    zone = pcbnew.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowZoneFills(True)
    zone.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for lg in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(lg)
    zone.SetLayerSet(ls)
    umriss = zone.Outline()
    umriss.NewOutline()
    import math
    for i in range(24):
        a = 2 * math.pi * i / 24
        umriss.Append(mm(x + SPERRE / 2 * math.cos(a)), mm(y + SPERRE / 2 * math.sin(a)))
    zone.SetZoneName("Sperre_H%d" % nr)
    board.Add(zone)


def main():
    if os.path.exists(ZIEL):
        print("vorhanden, nicht überschrieben:", ZIEL)
        return 0
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    # JLCPCB Standard (4 Lagen): konservativ gewählt [A, vor Bestellung mit den aktuellen JLCPCB-Fähigkeiten vergleichen]
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_MinClearance = mm(0.15)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_HoleClearance = mm(0.25)

    cx, cy = MITTE
    h = SEITE / 2
    r = ECKRADIUS
    E = pcbnew.Edge_Cuts
    linie(board, E, cx - h + r, cy - h, cx + h - r, cy - h)
    linie(board, E, cx + h, cy - h + r, cx + h, cy + h - r)
    linie(board, E, cx + h - r, cy + h, cx - h + r, cy + h)
    linie(board, E, cx - h, cy + h - r, cx - h, cy - h + r)
    bogen(board, E, cx + h - r, cy - h + r, cx + h - r, cy - h, 90)
    bogen(board, E, cx + h - r, cy + h - r, cx + h, cy + h - r, 90)
    bogen(board, E, cx - h + r, cy + h - r, cx - h + r, cy + h, 90)
    bogen(board, E, cx - h + r, cy - h + r, cx - h, cy - h + r, 90)

    d = LOCHABSTAND / 2
    for nr, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1)), start=1):
        befestigungsloch(board, nr, cx + sx * d, cy + sy * d)

    U = pcbnew.User_1
    text(board, U, "Klemmenkante (anschluesse.md 4), von links:", cx, cy + h - 16, 1.2)
    text(board, U, "J201/J202 Solar - J703 BME280 - J701/J702 DS18B20 - J601 Mikrofon - J501 Waage", cx, cy + h - 13, 1.2)
    text(board, U, "Funkkante: Ra-01SH mit IPEX gegenüber den Klemmen", cx, cy - h + 6, 1.2)
    text(board, U, "Bauhöhe über der Platine <= 40 mm; Platine auf 10-mm-Hülsen (HW-03); Unterseite ohne Bauteile (M2)",
         cx, cy, 1.2)
    text(board, pcbnew.F_SilkS, "PCB-MAIN-0.1", cx, cy + h - 3, 1.0)

    board.Save(ZIEL)
    print("angelegt:", ZIEL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
