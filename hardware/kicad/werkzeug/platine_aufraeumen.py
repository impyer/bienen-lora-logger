#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Aufräumen nach dem Routing der Hauptplatine.

0. Überflüssige GND-Bahnen/Vias des Autorouters entfernen (GND liegt auf L2/L3, Anschluss über die Fanout-Vias).
1. Lose Leiterbahnenden entfernen: Stücke, deren eines Ende weder an einem Pad noch an einer anderen Bahn oder Via
   desselben Netzes hängt (Reste der vorverlegten Stiche, die der Autorouter anders angeschlossen hat). Wiederholt,
   bis nichts mehr lose ist. Bahnen von Netzen, die noch nicht vollständig verbunden sind, bleiben als Hilfe stehen.
2. Bestückungsdruck: Referenzen der Kleinteile auf die Bestückungszeichnung (F.Fab) verschieben; auf dem Druck bleiben
   Stecker, Klemmen, Taster, Testpunkte, Lötbrücken, LED, Reedkontakt, ICs und Quarze.
3. Klemmenbeschriftung (Lastenheft M4: Aufdruck an jeder Klemme): Wert der Klemme (z. B. „Solar 1“, „BME280“) über
   der Klemme. Pin 1 (Masse) ist am eckigen Pad zu erkennen.

Wiederholbar. Aufruf: python3 hardware/kicad/werkzeug/platine_aufraeumen.py [noch offene Netze …]
"""
import json
import os
import subprocess
import sys
import tempfile

import pcbnew

HIER = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HIER), "hauptplatine", "logger.kicad_pcb")
AUF_DRUCK = ("J", "SW", "TP", "JP", "U", "Y", "D301")
KLEMMEN = ("J201", "J202", "J703", "J701", "J702", "J601", "J501")


def mm(x):
    return pcbnew.FromMM(x)


def lose_enden(board, unfertig):
    entfernt = 0
    while True:
        punkte = {}
        for t in board.GetTracks():
            if t.GetClass() == "PCB_TRACK":
                for e in (t.GetStart(), t.GetEnd()):
                    punkte.setdefault((t.GetNetCode(), e.x, e.y), []).append(t)
        pads = [p for f in board.GetFootprints() for p in f.Pads()]
        vias = {(v.GetNetCode(), v.GetPosition().x, v.GetPosition().y) for v in board.GetTracks() if v.GetClass() == "PCB_VIA"}
        weg = []
        for t in board.GetTracks():
            if t.GetClass() != "PCB_TRACK" or t.GetNetname() in unfertig:
                continue
            for e in (t.GetStart(), t.GetEnd()):
                k = (t.GetNetCode(), e.x, e.y)
                if len(punkte.get(k, [])) > 1 or k in vias:
                    continue
                if any(p.GetNetCode() == t.GetNetCode() and p.GetEffectiveShape(t.GetLayer()).Collide(e, 0) for p in pads):
                    continue
                # Ende liegt auf einer anderen Bahn (T-Abzweig)?
                if any(o.GetNetCode() == t.GetNetCode() and o is not t and o.GetLayer() == t.GetLayer()
                       and o.GetEffectiveShape().Collide(e, 0) for o in board.GetTracks() if o.GetClass() == "PCB_TRACK"
                       and o.m_Uuid.AsString() != t.m_Uuid.AsString()):
                    continue
                weg.append(t.m_Uuid.AsString())
                break
        if not weg:
            return entfernt
        for t in [t for t in board.GetTracks() if t.m_Uuid.AsString() in weg]:
            board.Delete(t)
        entfernt += len(weg)


def drc_lose_enden(unfertig):
    """Von der KiCad-DRC als „track_dangling“ gemeldete Stücke entfernen (auch überlappende Reste, die die eigene
    Prüfung als T-Abzweig ansieht). Netze in `unfertig` bleiben unberührt. Wiederholt bis nichts mehr gemeldet wird."""
    gesamt = 0
    while True:
        with tempfile.TemporaryDirectory() as tmp:
            j = os.path.join(tmp, "drc.json")
            subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "-o", j, PCB],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            d = json.load(open(j))
        uuids = {i["uuid"] for v in d["violations"] if v["type"] == "track_dangling" for i in v["items"]
                 if not any("[%s]" % n in i["description"] for n in unfertig)}
        if not uuids:
            return gesamt
        board = pcbnew.LoadBoard(PCB)
        weg = [t for t in board.GetTracks() if t.m_Uuid.AsString() in uuids]
        for t in weg:
            board.Delete(t)
        board.Save(PCB)
        gesamt += len(weg)
        if not weg:
            return gesamt


def gnd_bahnen_entfernen(board):
    """Überflüssige GND-Bahnen und -Vias des Autorouters entfernen (GND hängt über Fanout-Vias an L2/L3). Bleiben:
    Fanout-Stiche (0,3 mm) mit ihren Vias und alles, was an den Thermal-Pads von U201/U301/U501 hängt."""
    ep = [p for f in board.GetFootprints() if f.GetReference() in ("U201", "U301", "U501") for p in f.Pads()
          if p.GetNetname() == "GND"]
    stich_enden = set()
    for t in board.GetTracks():
        if t.GetNetname() == "GND" and t.GetClass() == "PCB_TRACK" and abs(pcbnew.ToMM(t.GetWidth()) - 0.3) < 1e-6:
            stich_enden |= {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)}
    weg = []
    for t in board.GetTracks():
        if t.GetNetname() != "GND":
            continue
        if t.GetClass() == "PCB_TRACK":
            if abs(pcbnew.ToMM(t.GetWidth()) - 0.3) > 1e-6 and not any(
                    p.GetEffectiveShape(pcbnew.F_Cu).Collide(e, 0) for p in ep for e in (t.GetStart(), t.GetEnd())):
                weg.append(t.m_Uuid.AsString())
        elif (t.GetPosition().x, t.GetPosition().y) not in stich_enden and not any(
                p.GetEffectiveShape(pcbnew.F_Cu).Collide(t.GetPosition(), 0) for p in ep):
            weg.append(t.m_Uuid.AsString())
    for t in [t for t in board.GetTracks() if t.m_Uuid.AsString() in weg]:
        board.Delete(t)
    return len(weg)


def main():
    board = pcbnew.LoadBoard(PCB)
    unfertig = set(a for a in (sys.argv[1:] or []))
    g = gnd_bahnen_entfernen(board)
    n = lose_enden(board, unfertig)
    fab = 0
    for f in board.GetFootprints():
        r = f.GetReference()
        ref = f.Reference()
        if r.startswith(AUF_DRUCK):
            ref.SetLayer(pcbnew.F_SilkS)
        else:
            ref.SetLayer(pcbnew.F_Fab)
            fab += 1
    vorhanden = {(t.GetText(), t.GetPosition().x, t.GetPosition().y) for t in board.GetDrawings() if t.GetClass() == "PCB_TEXT"}
    for r in KLEMMEN:
        f = board.FindFootprintByReference(r)
        p1 = next(p for p in f.Pads() if p.GetNumber() == "1")
        mitte_x = sum(p.GetPosition().x for p in f.Pads()) // len(f.Pads())
        for inhalt, x, groesse in ((f.GetValue(), mitte_x, 0.9),):
            pos = pcbnew.VECTOR2I(x, p1.GetPosition().y - mm(2.1))
            if (inhalt, pos.x, pos.y) in vorhanden:
                continue
            t = pcbnew.PCB_TEXT(board)
            t.SetText(inhalt)
            t.SetPosition(pos)
            t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(mm(groesse), mm(groesse)))
            t.SetTextThickness(mm(0.15))
            board.Add(t)
    board.Save(PCB)
    n += drc_lose_enden(unfertig)
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print("Aufräumen: %d überflüssige GND-Bahnen/Vias, %d lose Bahnstücke entfernt, %d Referenzen auf F.Fab"
          % (g, n, fab))
    return 0


if __name__ == "__main__":
    sys.exit(main())
