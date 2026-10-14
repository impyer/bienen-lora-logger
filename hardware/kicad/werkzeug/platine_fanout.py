#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Fanout: jedes SMD-Pad an GND oder +3V3 bekommt eine kurze Leiterbahn zu einer eigenen Durchkontaktierung zur
Fläche auf L2 (GND_L2) bzw. L3 (P3V3_L3). Teil des Routings der Hauptplatine (Lastenheft M8).

Regeln:
- nur SMD-Pads (Durchsteckpads hängen schon über die Bohrung an den Innenlagen);
- +3V3 nur, wenn das Pad über der +3V3-Fläche P3V3_L3 liegt (sonst bleibt es fürs Routing);
- Pads, in denen schon ein Via desselben Netzes sitzt (Thermal-Pads), werden übersprungen;
- Via 0,6/0,3 mm, Stich 0,3 mm breit, 0,8–2,4 mm vom Padmittelpunkt, bevorzugt vom Bauteil weg;
- Abstand zu fremden Pads, Leiterbahnen und Vias mindestens 0,2 mm (Regel 0,15 mm), zwischen Vias 0,8 mm Mittenabstand;
  kein Via in fremden Courtyards, in den Sperrflächen der Befestigungslöcher oder näher als 0,8 mm am Rand.

Wiederholbar: ein Pad mit vorhandenem Stich (Leiterbahn desselben Netzes, die am Pad beginnt) wird übersprungen.
Danach werden alle Zonen neu gefüllt. Aufruf: python3 hardware/kicad/werkzeug/platine_fanout.py
"""
import math
import os
import sys

import pcbnew

HIER = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HIER), "hauptplatine", "logger.kicad_pcb")

VIA_D, VIA_BOHR, STICH = 0.6, 0.3, 0.3
ABSTAND = 0.2
VIA_VIA = 0.8
RAND = (39.5 + 0.8, 160.5 - 0.8)
LOECHER = [(x, y) for x in (44.9, 155.1) for y in (44.9, 155.1)]
LOCH_R = 3.5 + VIA_D / 2
# (Bauteil, Pin, Endpunkt dx/dy relativ zum Bauteil, Breite): GND-Pin → Thermal-Pad
EP_STICH = [("U201", "5", -0.3, 0.8, 0.2),      # BQ25185: Pin 5 liegt neben dem EP (±0,45 × ±0,75)
            ("U301", "35", 2.6, -2.25, 0.25),   # STM32: Pin 35 innen auf das EP (Kante 2,8 mm)
            ("U301", "8", -2.6, 0.75, 0.25),    # STM32: VSSA innen auf das EP (außen liegen Quarz-/VDDA-Leitungen)
            ("U301", "23", 2.25, 2.6, 0.25)]    # STM32: VSS innen auf das EP (außen VCAP-Leitung)


def mm(x):
    return pcbnew.FromMM(x)


def tomm(v):
    return pcbnew.ToMM(v.x), pcbnew.ToMM(v.y)


def main():
    board = pcbnew.LoadBoard(PCB)
    gnd = board.FindNet("GND")
    p3v3 = board.FindNet("+3V3")
    p3_zone = next(z for z in board.Zones() if z.GetZoneName() == "P3V3_L3")
    footprints = list(board.GetFootprints())
    for f in footprints:
        f.BuildCourtyardCaches()
    alle_pads = [(p, f) for f in footprints for p in f.Pads()]
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    bahnen = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]

    def frei_via(pos, netcode, eigen_fp):
        x, y = tomm(pos)
        if not (RAND[0] < x < RAND[1] and RAND[0] < y < RAND[1]):
            return False
        if any(math.hypot(x - lx, y - ly) < LOCH_R for lx, ly in LOECHER):
            return False
        r = mm(VIA_D / 2 + ABSTAND)
        for p, f in alle_pads:
            if p.GetNetCode() != netcode and p.GetEffectiveShape(pcbnew.F_Cu).Collide(pos, r):
                return False
        for v in vias:
            d = math.hypot(*(a - b for a, b in zip(tomm(v.GetPosition()), (x, y))))
            if d < (VIA_VIA if v.GetNetCode() == netcode else VIA_D + ABSTAND):
                return False
        for t in bahnen:
            if t.GetNetCode() != netcode and t.GetEffectiveShape().Collide(pos, r):
                return False
        for f in footprints:
            if f is eigen_fp:
                continue
            cy = f.GetCourtyard(pcbnew.F_CrtYd)
            if cy.OutlineCount() and cy.Contains(pos):
                return False
        return True

    def frei_stich(a, b, netcode, eigen_pad):
        seg = pcbnew.SEG(a, b)
        r = mm(STICH / 2 + ABSTAND)
        for p, f in alle_pads:
            if p.GetNetCode() != netcode and p.GetEffectiveShape(pcbnew.F_Cu).Collide(seg, r):
                return False
        for t in bahnen:
            if t.GetNetCode() != netcode and t.GetEffectiveShape().Collide(seg, r):
                return False
        for v in vias:
            if v.GetNetCode() != netcode and v.GetEffectiveShape(pcbnew.F_Cu).Collide(seg, r):
                return False
        return True

    neu, ohne = 0, []
    for p, f in sorted(alle_pads, key=lambda pf: (pf[1].GetReference(), pf[0].GetNumber())):
        net = p.GetNetCode()
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or net not in (gnd.GetNetCode(), p3v3.GetNetCode()):
            continue
        if net == p3v3.GetNetCode() and not p3_zone.Outline().Contains(p.GetPosition()):
            continue
        shape = p.GetEffectiveShape(pcbnew.F_Cu)
        if any(v.GetNetCode() == net and shape.Collide(v.GetPosition(), 0) for v in vias):
            continue
        if any(t.GetNetCode() == net and (shape.Collide(t.GetStart(), 0) or shape.Collide(t.GetEnd(), 0)) for t in bahnen):
            continue
        px, py = tomm(p.GetPosition())
        fx, fy = tomm(f.GetPosition())
        aussen = math.atan2(py - fy, px - fx) if (px, py) != (fx, fy) else 0.0
        kandidaten = []
        for d in (0.8, 1.0, 1.2, 1.5, 1.8, 2.1, 2.4):
            for k in range(24):
                w = 2 * math.pi * k / 24
                abw = abs((w - aussen + math.pi) % (2 * math.pi) - math.pi)
                kandidaten.append((d + 0.6 * abw, d, w))
        kandidaten.sort()
        for _, d, w in kandidaten:
            pos = pcbnew.VECTOR2I(mm(px + d * math.cos(w)), mm(py + d * math.sin(w)))
            if frei_via(pos, net, f) and frei_stich(p.GetPosition(), pos, net, p):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pos)
                v.SetWidth(mm(VIA_D))
                v.SetDrill(mm(VIA_BOHR))
                v.SetNet(p.GetNet())
                board.Add(v)
                vias.append(v)
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(p.GetPosition())
                t.SetEnd(pos)
                t.SetWidth(mm(STICH))
                t.SetLayer(pcbnew.F_Cu)
                t.SetNet(p.GetNet())
                board.Add(t)
                bahnen.append(t)
                neu += 1
                break
        else:
            ohne.append("%s.%s" % (f.GetReference(), p.GetNumber()))
    # Sonderfälle: GND-Pins direkt neben dem Thermal-Pad mit einer kurzen Leiterbahn auf das Pad (das Vias trägt)
    for ref, pin, dx, dy, breite in EP_STICH:
        f = next(f for f in footprints if f.GetReference() == ref)
        p = next(q for q in f.Pads() if q.GetNumber() == pin)
        fx, fy = tomm(f.GetPosition())
        ende = pcbnew.VECTOR2I(mm(fx + dx), mm(fy + dy))
        if any(t.GetNetCode() == p.GetNetCode() and t.GetStart() == p.GetPosition() and t.GetEnd() == ende for t in bahnen):
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(p.GetPosition())
        t.SetEnd(ende)
        t.SetWidth(mm(breite))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(p.GetNet())
        board.Add(t)
        bahnen.append(t)
        ohne = [o for o in ohne if o != "%s.%s" % (ref, pin)]
        neu += 1
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print("Fanout: %d Stiche neu (Via oder Thermal-Pad); ohne Platz: %s" % (neu, ", ".join(ohne) or "keine"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
