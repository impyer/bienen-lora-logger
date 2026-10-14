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
        # Seiten der QFN bleiben frei, damit die Signale ausbrechen können (Routing 13.10.2026: eine Kondensatorreihe
        # parallel zur Kante blockierte 18 Pins). Abblockkondensatoren daher an den Ecken, nahe ihrem VDD/VSS-Paar.
        "C301": (-3.9, -6.0, 0),       # 100 nF an Pin 48/47 (NW-Ecke)
        "C308": (-6.3, -3.9, 90),      # 100 nF an VBAT (Pin 1), oberhalb der LED-Leitung von Pin 2
        "R301": (-0.75, -6.9, 90),     # BOOT0-Pull-down an Pin 44, außerhalb des Ausbruchbereichs
        "C302": (5.6, -4.6, 90),       # 100 nF an Pin 36/35 (NO-Ecke)
        "C303": (5.4, 4.6, 90),        # 100 nF an Pin 24/23 (SO-Ecke)
        "C307": (2.9, 7.3, 0),         # VCAP 4,7 µF an Pin 22
        "C304": (7.3, 6.0, 90),        # 10 µF Sammelkondensator
        "R302": (-2.4, 8.2, 90),       # BOOT1-Pull-down an Pin 20
        # Westseite (Pins 1–12): LSE 3/4, HSE 5/6, NRST 7, VSSA 8, VDDA 9 – Quarze mit Lastkondensatoren außen
        "Y302": (-9.6, -3.6, 90),      # 32,768 kHz
        "C312": (-12.3, -4.85, 0),
        "C313": (-12.3, -2.35, 0),
        "Y301": (-8.4, 1.6, 270),      # 25 MHz: Pad 1 (IN) oben links, Pad 3 (OUT) unten rechts
        "C310": (-12.0, 0.4, 0),       # an HSE_IN (Pad 1)
        "C311": (-12.0, 2.8, 0),       # an HSE_OUT
        "C305": (-5.2, 5.2, 270),       # 100 nF an VDDA (Pin 9) / VSSA (Pin 8), SW-Ecke
        "C306": (-7.2, 5.6, 90),       # 1 µF an VDDA
        "FB301": (-7.2, 8.8, 90),      # Ferrit +3V3 → VDDA
        "C309": (-9.4, 5.6, 90),       # NRST 100 nF
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

# Vorverlegte Leiterbahnen an fein geteilten ICs (Routing 13.10.2026: der Autorouter kann 0,4-mm-Versorgungsbahnen
# nicht an 0,2-mm-Pads im 0,4-/0,65-mm-Raster anschließen). (Ref, Pad, Ziel, Breite); Ziel = (Ref, Pad) oder
# (dx, dy) relativ zum Pad. Am Stichende schließt der Autorouter die breite Bahn an.
VORVERLEGT = [
    # TPS61240: Schleife VIN/L/VOUT direkt (TI-Layoutempfehlung), Pins 2+3 = VOUT
    ("U501", "2", [("U501", "3")], 0.25),
    ("U501", "3", [("C502", "1")], 0.3),
    ("U501", "5", [(0.75, 0.0), ("L501", "2")], 0.3),   # erst gerade heraus, dann an Pin 4 (EN) vorbei
    ("U501", "6", [("C501", "1")], 0.3),
    ("C501", "1", [("L501", "1")], 0.3),
    # STM32: kurze, kritische Netze von Hand (AN2867: Quarzleitungen kurz, ohne Fremdsignale; VCAP/VDDA direkt)
    ("U301", "22", [("C307", "1")], 0.25),                              # VCAP
    ("U301", "9", [(-1.16, 0.0), (-1.76, 0.6), ("C305", "1")], 0.25),  # VDDA
    ("U301", "3", [(-4.16, 0.0), (-4.16, -3.1), ("Y302", "1")], 0.2),  # LSE_IN, oberhalb um Pad 2 herum
    ("U301", "4", [(-5.16, 0.0), ("Y302", "2")], 0.2),                 # LSE_OUT
    ("Y302", "1", [("C312", "2")], 0.2),
    ("Y302", "2", [("C313", "2")], 0.2),
    ("U301", "5", [(-5.81, 0.0), ("Y301", "1")], 0.2),                 # HSE_IN über dem Quarz
    ("U301", "6", [(-2.06, 0.0), (-3.16, 2.95), ("Y301", "3")], 0.2),  # HSE_OUT rechts am Quarz vorbei
    ("Y301", "1", [("C310", "2")], 0.2),
    # BQ25185 (WSON-10, Raster 0,4 mm): alle Pins gerade aus dem Raster heraus, Enden gestaffelt – der Autorouter
    # schloss die Pins sonst nicht an (Routing 13.10.2026). Pin 5 (GND) geht in platine_fanout.py auf das EP.
    ("U201", "1", [(-0.6, 0.0), (-1.0, -0.7)], 0.2),        # SYS nach links oben
    ("U201", "2", [(-1.3, 0.0)], 0.2),                      # VBAT gerade nach links
    ("U201", "3", [(-0.7, 0.0), (-1.1, 0.5)], 0.15),        # STAT2
    ("U201", "4", [(-0.55, 0.0), (-0.55, 1.0)], 0.15),      # CE nach unten
    ("U201", "10", [(0.6, 0.0), (1.0, -0.7)], 0.2),         # VIN_LADER nach rechts oben
    ("U201", "9", [(1.3, 0.0)], 0.15),                      # STAT1 gerade nach rechts
    ("U201", "8", [(0.95, 0.0), (1.35, 0.5)], 0.15),        # ISET (über das Ende von ILIM hinaus)
    ("U201", "7", [(0.7, 0.0), (0.7, 1.0)], 0.15),          # ILIM nach unten
    ("U201", "6", [(0.3, 0.0), (0.3, 0.8)], 0.15),          # NTC nach unten
]

# Masse-Vias in Thermal-Pads: Bezug -> Liste (dx, dy); Via 0,6/0,3 mm (Entwurfsregel), Netz GND
VIAS = {
    "U201": [(0.0, -0.4), (0.0, 0.4)],                                    # TI DLH0010A: 2 Vias
    "U301": [(x, y) for x in (-1.4, 0.0, 1.4) for y in (-1.4, 0.0, 1.4)],  # EP 5,6 × 5,6 mm
    "U501": [(0.0, -0.4), (0.0, 0.4)],                                    # EP 1,0 × 1,6 mm
}
VIA_D, VIA_BOHR = 0.6, 0.3


def mm(x):
    return pcbnew.FromMM(x)


def veraltete_stiche_entfernen(board, f):
    """Leiterbahnen, die an einem Pad von f beginnen oder enden, samt der Fanout-Via am anderen Ende entfernen
    (das Bauteil wird verschoben; platine_fanout.py legt danach neue Stiche an)."""
    formen = [(p.GetNetCode(), p.GetEffectiveShape(pcbnew.F_Cu)) for p in f.Pads()]
    weg, enden = set(), set()
    for t in board.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        for net, form in formen:
            if t.GetNetCode() != net:
                continue
            a, b = form.Collide(t.GetStart(), 0), form.Collide(t.GetEnd(), 0)
            if a or b:
                weg.add(t.m_Uuid.AsString())
                e = t.GetEnd() if a else t.GetStart()
                enden.add((e.x, e.y))
                break
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA" and (t.GetPosition().x, t.GetPosition().y) in enden:
            weg.add(t.m_Uuid.AsString())
    for t in [t for t in board.GetTracks() if t.m_Uuid.AsString() in weg]:
        board.Delete(t)


def vorverlegen(board, fp):
    """VORVERLEGT als Leiterbahnen auf F.Cu anlegen; Wegpunkte (dx, dy) relativ zum Startpad oder (Ref, Pad).
    Vorhandene identische Bahnen werden nicht doppelt angelegt."""
    vorhanden = {(t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)
                 for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"}
    for ref, pad, wege, breite in VORVERLEGT:
        p = next(q for q in fp[ref].Pads() if q.GetNumber() == pad)
        a = p.GetPosition()
        punkte = [a]
        for w in wege:
            if isinstance(w[0], str):
                punkte.append(next(q for q in fp[w[0]].Pads() if q.GetNumber() == w[1]).GetPosition())
            else:
                punkte.append(pcbnew.VECTOR2I(a.x + mm(w[0]), a.y + mm(w[1])))
        for s_, e in zip(punkte, punkte[1:]):
            if (s_.x, s_.y, e.x, e.y) in vorhanden:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(s_)
            t.SetEnd(e)
            t.SetWidth(mm(breite))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(p.GetNet())
            board.Add(t)


AUSBRUCH = {"U301": 0.86}   # QFN: Signalpins mit 0,86 mm langem Stich gerade nach außen (über das Padende hinaus)


def ausbruch(board, fp):
    """Gerade Ausbruchstiche an Signalpins der QFN (Routing 13.10.2026: Freerouting fand an mehreren STM32-Pins keinen
    Eingang). Pins mit vorhandener Bahn und GND/+3V3 bleiben unberührt."""
    for ref, laenge in AUSBRUCH.items():
        f = fp[ref]
        cx, cy = f.GetPosition().x, f.GetPosition().y
        for p in f.Pads():
            n = p.GetNetname()
            if not p.GetNumber().isdigit() or n in ("GND", "+3V3", "") or n.startswith("unconnected"):
                continue
            form = p.GetEffectiveShape(pcbnew.F_Cu)
            if any(t.GetClass() == "PCB_TRACK" and (form.Collide(t.GetStart(), 0) or form.Collide(t.GetEnd(), 0))
                   for t in board.GetTracks()):
                continue
            a = p.GetPosition()
            dx, dy = a.x - cx, a.y - cy
            if abs(dx) > abs(dy):
                e = pcbnew.VECTOR2I(a.x + (mm(laenge) if dx > 0 else -mm(laenge)), a.y)
            else:
                e = pcbnew.VECTOR2I(a.x, a.y + (mm(laenge) if dy > 0 else -mm(laenge)))
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(a)
            t.SetEnd(e)
            t.SetWidth(mm(0.15))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(p.GetNet())
            board.Add(t)


def ausweichen(board, fp, gesetzt):
    """Bauteile der Grobplatzierung, deren Courtyard ein fein gesetztes Bauteil überdeckt, neu ablegen (nächster freier
    Platz um ihre bisherige Lage, Verfahren aus platine_bestuecken.py). Gibt die verschobenen Referenzen zurück."""
    import platine_bestuecken as pb
    kaesten = {r: pb.kasten(f) for r, f in fp.items()}
    fest = [kaesten[r] for r in gesetzt]
    verschoben = []
    for r, f in sorted(fp.items()):
        if r in gesetzt or r.startswith("H"):
            continue
        k = kaesten[r]
        if any(k[0] < b[2] and b[0] < k[2] and k[1] < b[3] and b[1] < k[3] for b in fest):
            andere = [kaesten[o] for o in fp if o != r]
            ziel = (pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y))
            veraltete_stiche_entfernen(board, f)
            kaesten[r] = pb.ablegen(f, ziel, andere, None, 0.5)
            verschoben.append(r)
    return verschoben


def main():
    board = pcbnew.LoadBoard(PCB)
    fp = {f.GetReference(): f for f in board.GetFootprints()}
    for bezug, teile in FEIN.items():
        bx, by = (pcbnew.ToMM(v) for v in fp[bezug].GetPosition())
        for ref, (dx, dy, rot) in teile.items():
            f = fp[ref]
            ziel = pcbnew.VECTOR2I(mm(bx + dx), mm(by + dy))
            if f.GetPosition() != ziel or abs(f.GetOrientationDegrees() - rot) > 0.01:
                veraltete_stiche_entfernen(board, f)
            f.SetOrientationDegrees(rot)
            f.SetPosition(pcbnew.VECTOR2I(mm(bx + dx), mm(by + dy)))
            f.Reference().SetPosition(f.GetPosition())          # Referenz in die Bauteilmitte (dicht gepackt)
            f.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
            f.Reference().SetTextThickness(mm(0.12))
    weg = ausweichen(board, fp, {r for t in FEIN.values() for r in t} | set(FEIN))
    if weg:
        print("ausgewichen:", ", ".join(weg))
    vorverlegen(board, fp)
    ausbruch(board, fp)
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
