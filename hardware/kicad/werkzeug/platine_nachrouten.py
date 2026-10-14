#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Restliche offene Verbindungen nach dem Autorouter mit einem einfachen Gitter-Router schließen (A*, L1/L4, Vias).

Für jede offene Verbindung aus der KiCad-DRC (kicad-cli, „unconnected_items“):
- Suchfenster um beide Enden (+4 mm), Raster 0,05 mm;
- gesperrt ist jede Zelle, deren Abstand zu Kupfer eines fremden Netzes kleiner als halbe Bahnbreite + Abstand ist
  (Bahn 0,15 mm, Abstand 0,2 mm, also 0,05 mm Reserve auf die Regel 0,15 mm); für Vias (0,6 mm) auf beiden Lagen
  0,3 + 0,2 mm; Sperrflächen (Funkmodul, Befestigungslöcher) und 0,5 mm Randabstand ebenso;
- Bewegung in 8 Richtungen, Lagenwechsel über Via (Kosten 25 Zellen), Bahnen werden zu geraden Stücken zusammengefasst.

Es entstehen nur Bahnen, die die Regeln mit Reserve einhalten; danach prüft die DRC. Verbindungen ohne Weg bleiben
offen und werden gemeldet. Aufruf: python3 hardware/kicad/werkzeug/platine_nachrouten.py
"""
import heapq
import json
import math
import os
import subprocess
import sys
import tempfile

import pcbnew

HIER = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HIER), "hauptplatine", "logger.kicad_pcb")
RASTER = 0.05
BAHN, ABSTAND = 0.15, 0.2
VIA_D, VIA_BOHR = 0.6, 0.3
RAND = 0.5
FENSTER = 4.0
LAGEN = (pcbnew.F_Cu, pcbnew.B_Cu)
X0, X1, Y0, Y1 = 39.5, 160.5, 39.5, 160.5


def mm(x):
    return pcbnew.FromMM(x)


def offene(board_pfad):
    with tempfile.TemporaryDirectory() as tmp:
        j = os.path.join(tmp, "drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "-o", j, board_pfad],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return json.load(open(j))["unconnected_items"]


def objekte(board):
    alle = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            alle[p.m_Uuid.AsString()] = p
    for t in board.GetTracks():
        alle[t.m_Uuid.AsString()] = t
    return alle


def lagen_von(obj):
    if obj.GetClass() == "PAD":
        return [l for l in LAGEN if obj.IsOnLayer(l)]
    if obj.GetClass() == "PCB_VIA":
        return list(LAGEN)
    return [obj.GetLayer()] if obj.GetLayer() in LAGEN else []


def form(obj, lage):
    if obj.GetClass() in ("PAD", "PCB_VIA"):
        return obj.GetEffectiveShape(lage)
    return obj.GetEffectiveShape()


def route(board, a, b, net):
    ax, ay = (pcbnew.ToMM(v) for v in a.GetPosition()) if a.GetClass() != "PCB_TRACK" else (None, None)
    pa = [a.GetStart(), a.GetEnd()] if a.GetClass() == "PCB_TRACK" else [a.GetPosition()]
    pb = [b.GetStart(), b.GetEnd()] if b.GetClass() == "PCB_TRACK" else [b.GetPosition()]
    xs = [pcbnew.ToMM(p.x) for p in pa + pb]
    ys = [pcbnew.ToMM(p.y) for p in pa + pb]
    fx0, fx1 = max(X0, min(xs) - FENSTER), min(X1, max(xs) + FENSTER)
    fy0, fy1 = max(Y0, min(ys) - FENSTER), min(Y1, max(ys) + FENSTER)
    nx, ny = int((fx1 - fx0) / RASTER) + 1, int((fy1 - fy0) / RASTER) + 1

    def zelle(x, y):
        return int(round((x - fx0) / RASTER)), int(round((y - fy0) / RASTER))

    def punkt(i, j):
        return pcbnew.VECTOR2I(mm(fx0 + i * RASTER), mm(fy0 + j * RASTER))

    r_bahn, r_via = BAHN / 2 + ABSTAND, VIA_D / 2 + ABSTAND
    sperre = {l: bytearray(nx * ny) for l in LAGEN}
    sperre_via = bytearray(nx * ny)
    hindernisse = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() != net:
                hindernisse.append(p)
    for t in board.GetTracks():
        if t.GetNetCode() != net:
            hindernisse.append(t)
    regeln = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]
    for h in hindernisse:
        bb = h.GetBoundingBox()
        bx0, by0 = pcbnew.ToMM(bb.GetX()) - r_via, pcbnew.ToMM(bb.GetY()) - r_via
        bx1, by1 = pcbnew.ToMM(bb.GetRight()) + r_via, pcbnew.ToMM(bb.GetBottom()) + r_via
        if bx1 < fx0 or bx0 > fx1 or by1 < fy0 or by0 > fy1:
            continue
        i0, j0 = zelle(max(bx0, fx0), max(by0, fy0))
        i1, j1 = zelle(min(bx1, fx1), min(by1, fy1))
        hl = lagen_von(h)
        if h.GetClass() == "PAD" and h.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            hl = list(LAGEN)
        formen = {l: form(h, l) for l in hl}
        for i in range(max(0, i0), min(nx, i1 + 1)):
            for j in range(max(0, j0), min(ny, j1 + 1)):
                p = punkt(i, j)
                for l, fo in formen.items():
                    if fo.Collide(p, mm(r_bahn)):
                        sperre[l][j * nx + i] = 1
                    if fo.Collide(p, mm(r_via)):
                        sperre_via[j * nx + i] = 1
    for i in range(nx):
        for j in range(ny):
            x, y = fx0 + i * RASTER, fy0 + j * RASTER
            if x < X0 + RAND or x > X1 - RAND or y < Y0 + RAND or y > Y1 - RAND:
                sperre[pcbnew.F_Cu][j * nx + i] = sperre[pcbnew.B_Cu][j * nx + i] = sperre_via[j * nx + i] = 1
                continue
            p = punkt(i, j)
            for z in regeln:
                if z.GetLayerSet().Contains(pcbnew.F_Cu) and z.Outline().Collide(p, mm(r_via)):
                    sperre_via[j * nx + i] = 1
                    if z.Outline().Collide(p, mm(r_bahn)):
                        sperre[pcbnew.F_Cu][j * nx + i] = 1

    def zellen_von(obj):
        out = []
        for l in lagen_von(obj) or list(LAGEN):
            fo = form(obj, l)
            bb = obj.GetBoundingBox()
            i0, j0 = zelle(pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()))
            i1, j1 = zelle(pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
            for i in range(max(0, i0), min(nx, i1 + 1)):
                for j in range(max(0, j0), min(ny, j1 + 1)):
                    if fo.Collide(punkt(i, j), 0):
                        out.append((l, i, j))
        return out

    # nur Zellen, an denen eine Bahn den Abstand zu fremdem Kupfer einhält
    start = [k for k in zellen_von(a) if not sperre[k[0]][k[2] * nx + k[1]]]
    ziel = {k for k in zellen_von(b) if not sperre[k[0]][k[2] * nx + k[1]]}
    if not start or not ziel:
        if os.environ.get("NACHROUTEN_DEBUG"):
            print("  keine freien Start-/Zielzellen: Start %d, Ziel %d" % (len(start), len(ziel)))
        return None
    tx = sum(i for _, i, _ in ziel) / len(ziel)
    ty = sum(j for _, _, j in ziel) / len(ziel)
    offen_ = [(math.hypot(i - tx, j - ty), 0.0, (l, i, j), None) for l, i, j in start]
    heapq.heapify(offen_)
    herkunft, kosten = {}, {}
    schritte = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    gefunden = None
    while offen_:
        _, g, k, vor = heapq.heappop(offen_)
        if k in herkunft:
            continue
        herkunft[k] = vor
        if k in ziel:
            gefunden = k
            break
        l, i, j = k
        nachbarn = []
        for di, dj, c in schritte:
            ii, jj = i + di, j + dj
            if 0 <= ii < nx and 0 <= jj < ny and not sperre[l][jj * nx + ii]:
                nachbarn.append(((l, ii, jj), c))
        if not sperre_via[j * nx + i]:
            andere = pcbnew.B_Cu if l == pcbnew.F_Cu else pcbnew.F_Cu
            nachbarn.append(((andere, i, j), 25))
        for nk, c in nachbarn:
            ng = g + c
            if nk not in herkunft and ng < kosten.get(nk, 1e18):
                kosten[nk] = ng
                heapq.heappush(offen_, (ng + math.hypot(nk[1] - tx, nk[2] - ty), ng, nk, k))
        if len(herkunft) > 4000000:
            break
    if os.environ.get("NACHROUTEN_DEBUG"):
        print("  Fenster %dx%d, Start %d, Ziel %d, untersucht %d, gefunden %s" % (nx, ny, len(start), len(ziel),
                                                                              len(herkunft), bool(gefunden)))
    if not gefunden:
        return None
    weg = []
    k = gefunden
    while k is not None:
        weg.append(k)
        k = herkunft[k]
    weg.reverse()
    return weg, punkt


def anlegen(board, weg, punkt, netinfo):
    """Weg (Liste von (Lage, i, j)) als Bahnen und Vias anlegen; gerade Läufe werden zu einem Stück."""
    gruppen, akt = [], [weg[0]]
    for k in weg[1:]:
        if k[0] == akt[-1][0]:
            akt.append(k)
        else:
            gruppen.append(akt)
            akt = [k]
    gruppen.append(akt)
    for g, nachste in zip(gruppen, gruppen[1:] + [None]):
        ecken = [g[0]]
        for vor, k, nach in zip(g, g[1:], g[2:]):
            if (k[1] - vor[1], k[2] - vor[2]) != (nach[1] - k[1], nach[2] - k[2]):
                ecken.append(k)
        if len(g) > 1:
            ecken.append(g[-1])
        for s_, e in zip(ecken, ecken[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(punkt(s_[1], s_[2]))
            t.SetEnd(punkt(e[1], e[2]))
            t.SetWidth(mm(BAHN))
            t.SetLayer(s_[0])
            t.SetNet(netinfo)
            board.Add(t)
        if nachste is not None:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(punkt(g[-1][1], g[-1][2]))
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_BOHR))
            v.SetNet(netinfo)
            board.Add(v)


def main():
    ergebnis = []
    for _ in range(3):                      # nach jedem Durchgang neu prüfen (Verbindungen hängen zusammen)
        liste = offene(PCB)
        if not liste:
            break
        board = pcbnew.LoadBoard(PCB)
        obj = objekte(board)
        geschafft = 0
        for u in liste:
            a, b = (obj.get(i["uuid"]) for i in u["items"])
            if a is None or b is None:
                continue
            r = route(board, a, b, a.GetNetCode())
            if r:
                anlegen(board, r[0], r[1], a.GetNet())
                geschafft += 1
            ergebnis.append((a.GetNetname(), bool(r)))
        board.Save(PCB)
        if not geschafft:
            break
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    rest = offene(PCB)
    print("Nachrouten: %d Versuche, offen danach: %d %s" % (len(ergebnis), len(rest),
          sorted({i["items"][0]["description"].split("[")[1].split("]")[0] for i in rest if "[" in i["items"][0]["description"]})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
