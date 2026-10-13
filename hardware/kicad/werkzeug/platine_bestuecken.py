#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Bauteile aus der Netzliste auf hardware/kicad/hauptplatine/logger.kicad_pcb bringen (erste Grobplatzierung).

Entspricht „Platine aus Schaltplan aktualisieren“ in KiCad, aber reproduzierbar:
- liest netzliste/logger.net (von pruefen.sh erzeugt),
- lädt jeden Footprint (Bienen.pretty bzw. KiCad-Standardbibliothek), setzt Referenz, Wert, LCSC, Netze an den Pads
  und die Verknüpfung zum Schaltplansymbol (Pfad aus Blatt- und Symbol-UUID). Ein späteres „Platine aus Schaltplan
  aktualisieren“ in KiCad erkennt die Bauteile daran wieder und legt sie nicht doppelt an.
- platziert nach den Regeln aus anschluesse.md 4, mcu-funk.md 2.3/3.3 und Lastenheft A3/M5 (siehe PLATZ und BEREICH);
  übrige Bauteile werden neben das Bauteil gelegt, mit dem sie die meisten Signalnetze teilen (Abblockkondensatoren
  neben das IC ihres Blatts).

Das ist eine **Grobplatzierung als Startpunkt** für die Handarbeit in KiCad, kein fertiges Layout: keine Leiterbahnen,
keine Masseflächen, Lage und Drehung der Kleinteile von Hand nachziehen. Bereits vorhandene Referenzen bleibt
unangetastet (das Skript ergänzt nur fehlende Bauteile).

Aufruf: python3 hardware/kicad/werkzeug/platine_bestuecken.py
"""
import collections
import os
import re
import sys

import pcbnew

HIER = os.path.dirname(os.path.abspath(__file__))
KICAD = os.path.dirname(HIER)
PCB = os.path.join(KICAD, "hauptplatine", "logger.kicad_pcb")
NETZ = os.path.join(KICAD, "netzliste", "logger.net")
STD_FP = os.environ.get("KICAD10_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
EIGENE = {"Bienen": os.path.join(KICAD, "Bienen.pretty")}

# Platinenrand (platine_start.py): Mitte (100, 100), 121 × 121 mm
X0, X1, Y0, Y1 = 39.5, 160.5, 39.5, 160.5
RAND = 0.5                                   # Abstand Bauteil-Courtyard zum Rand (Lötstopp, Fräsen)
LOCH_SPERRE = [(x, y, 3.5) for x in (44.9, 155.1) for y in (44.9, 155.1)]   # Ø 7 mm um die Befestigungslöcher

VERSORGUNGSNETZE = {"GND", "+3V3", "3V3_SW", "SYS", "VBUS", "/Versorgung/VIN_LADER", "/Versorgung/VBAT",
                    "/Mikrofon/3V3_ANA", "/Waage/HX_AVDD", "/Waage/5V_WAAGE", "/Waage/VSUP_HX", "/MCU/VDDA"}

# --- Feste Plätze (x, y, Drehung in Grad) -------------------------------------------------------------------
PLATZ = {}

# Klemmenkante unten (anschluesse.md 4 / M5), von links: Solar – BME280 – DS18B20 – Mikrofon – Wägezelle.
# Footprint-Ursprung = Pin 1, Körper von −1,2 bis +8,0 mm in y (Stecköffnung zur Kante) → Pinreihe 8 mm über der Kante.
KLEMMEN = [("J201", 2), ("J202", 2), ("J703", 6), ("J701", 3), ("J702", 3), ("J601", 4), ("J501", 5)]
KLEMMEN_LUECKE = 0.6                         # Abstand der Courtyards (0,4 mm Rand je Seite) → Körperabstand 1,4 mm
KLEMMEN_Y = Y1 - 8.4 - RAND                  # Courtyard (+8,4 mm) mit Randabstand; Stecköffnung 0,9 mm innen
_x = 44.9 + 3.5 + 0.3 + 2.55                 # rechts neben der Lochsperre links unten
for ref, n in KLEMMEN:
    PLATZ[ref] = (_x, KLEMMEN_Y, 0)
    _x += 3.5 * (n - 1) + 5.1 + KLEMMEN_LUECKE
KLEMMEN_ENDE = _x - KLEMMEN_LUECKE - 2.55     # rechte Körperkante der letzten Klemme (zur Kontrolle)


def klemmen_mitte(ref):
    n = dict(KLEMMEN)[ref]
    return PLATZ[ref][0] + 3.5 * (n - 1) / 2


# ESD-Schutz direkt hinter der Klemme (anschluesse.md 4), vor allen anderen Bauteilen
ESD_Y = KLEMMEN_Y - 1.6 - 2.5
PLATZ["D701"] = ((klemmen_mitte("J701") + klemmen_mitte("J702")) / 2, ESD_Y, 0)   # ONEWIRE beider Klemmen
PLATZ["D702"] = (klemmen_mitte("J703"), ESD_Y, 0)
PLATZ["D601"] = (klemmen_mitte("J601"), ESD_Y, 0)
PLATZ["D501"] = (klemmen_mitte("J501"), ESD_Y, 0)
PLATZ["D204"] = ((klemmen_mitte("J201") + klemmen_mitte("J202")) / 2, ESD_Y - 0.5, 0)   # SMAJ12A am Solareingang

# Funkkante oben: Ra-01SH mittig, Pin-1-Seite (ANT, IPEX [A]) zur Kante; keine Leiterbahn an ANT (mcu-funk.md 2.3)
PLATZ["U401"] = (100.0, Y0 + RAND + 8.95, 0)

# Seitenkante links: Lichtleiter-LED und Reedkontakt (mcu-funk.md 3.3), 10–20 mm auseinander
PLATZ["D301"] = (X0 + RAND + 0.75, 92.0, 90)       # Lichtaustritt (−y im Footprint) nach links zur Kante [A]
PLATZ["SW304"] = (X0 + RAND + 1.5, 108.0, 90)      # Schaltachse parallel zur Kante

# Innen, gut erreichbar (anschluesse.md 4): USB-C an der rechten Kante, Akkustecker links innen
PLATZ["J301"] = (X1 - 4.3, 80.0, 90)        # Buchsenfront bündig mit der Kante
PLATZ["J203"] = (62.0, 112.0, 0)

# Stiftleisten: Debug neben der MCU, Erweiterung im freien Drittel links oben (M5, F9)
PLATZ["J302"] = (135.0, 92.0, 0)
PLATZ["J704"] = (52.0, 58.0, 0)

# Taster neben der USB-Buchse (Aufspielen am Tisch: BOOT + Reset)
PLATZ["SW301"] = (146.0, 96.0, 0)
PLATZ["SW302"] = (146.0, 104.0, 0)
PLATZ["SW303"] = (146.0, 64.0, 0)

# Haupt-ICs je Block
PLATZ["U301"] = (105.0, 88.0, 0)                   # STM32 in der Mitte
PLATZ["U402"] = (124.0, 52.0, 90)                  # SPI-Flash neben dem Funkmodul
PLATZ["U201"] = (62.0, 132.0, 0)                   # Laderegler über den Solarklemmen
PLATZ["U502"] = (147.0, 130.0, 90)                 # HX711 neben der Wägezellenklemme
PLATZ["U501"] = (149.0, 113.0, 0)                  # 5-V-Wandler: rechts, weit weg vom Mikrofonzweig (A3)
PLATZ["U601"] = (122.0, 136.0, 0)                  # OPV/Filter über der Mikrofonklemme, zur MCU (PA1) hin

# --- Bereiche je Schaltplanblatt (x0, y0, x1, y1): dort werden die übrigen Bauteile abgelegt -------------------
BEREICH = {
    "Funk + Flash": (78, 40, 135, 66),
    "MCU": (84, 66, 160, 112),
    "Versorgung": (40, 104, 92, 150),
    "Anschlüsse": (64, 126, 110, 150),
    "Mikrofon": (108, 116, 138, 150),
    "Waage": (136, 104, 160, 150),
}
ANKER = {"Funk + Flash": "U401", "MCU": "U301", "Versorgung": "U201", "Anschlüsse": "J701",
         "Mikrofon": "U601", "Waage": "U502"}
# Seitenkante links (LED, Reed): eigener Bereich für deren Kleinteile
KANTE_LINKS = (40, 84, 62, 118)
# Bauteile, die trotz Netzverwandtschaft an ein bestimmtes Bauteil gehören
ZUORDNUNG = {"C401": "U401", "C402": "U401", "C403": "U401", "D401": "U401", "C404": "U402",
             "U202": "U201", "U203": "U201", "U204": "U201", "L501": "U501", "C501": "U501", "C502": "U501",
             "Q501": "U501", "R306": "D301", "R305": "SW304", "U302": "J301", "R303": "J301", "R304": "J301",
             "Y301": "U301", "Y302": "U301", "C310": "Y301", "C311": "Y301", "C312": "Y302", "C313": "Y302",
             "R701": "J701", "R702": "J703", "R703": "J703", "D201": "J201", "D202": "J202", "D203": "U201",
             "C201": "U201"}


# --- Netzliste lesen ------------------------------------------------------------------------------------------
def parse(text):
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    st = [[]]
    for x in tok:
        if x == "(":
            st.append([])
        elif x == ")":
            liste = st.pop()
            st[-1].append(liste)
        else:
            st[-1].append(x[1:-1].replace('\\"', '"') if x.startswith('"') else x)
    return st[0][0]


def find(liste, k):
    return [e for e in liste if isinstance(e, list) and e and e[0] == k]


def val(liste, k):
    f = find(liste, k)
    return f[0][1] if f and len(f[0]) > 1 else None


def netzliste():
    d = parse(open(NETZ, encoding="utf-8").read())
    teile = []
    for k in find(find(d, "components")[0], "comp"):
        props = {val(p, "name"): val(p, "value") for p in find(k, "property")}
        felder = {f[1][1]: (f[2] if len(f) > 2 else "") for f in find(find(k, "fields")[0], "field")} if find(k, "fields") else {}
        sp = find(k, "sheetpath")[0]
        teile.append({"ref": val(k, "ref"), "wert": val(k, "value"), "fp": val(k, "footprint"),
                      "blatt": props.get("Sheetname", ""), "datei": props.get("Sheetfile", ""),
                      "lcsc": props.get("LCSC"), "dnp": "dnp" in props, "bom": "exclude_from_bom" not in props,
                      "info": felder.get("Description", ""),
                      "pfad": val(sp, "tstamps") + val(k, "tstamps")})
    pads = collections.defaultdict(dict)       # ref -> pad -> netz
    for n in find(find(d, "nets")[0], "net"):
        name = val(n, "name")
        for node in find(n, "node"):
            pads[val(node, "ref")][val(node, "pin")] = name
    return teile, pads


# --- Platzierung ----------------------------------------------------------------------------------------------
def mm(x):
    return pcbnew.FromMM(x)


def kasten(fp):
    """Courtyard-Rechteck in mm (x0, y0, x1, y1); ersatzweise Umriss ohne Texte."""
    fp.BuildCourtyardCaches()
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    if cy.OutlineCount():
        b = cy.BBox()
    else:
        b = fp.GetBoundingBox(False)
    return (pcbnew.ToMM(b.GetX()), pcbnew.ToMM(b.GetY()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom()))


def frei(k, belegt, bereich=None):
    x0, y0, x1, y1 = k
    if x0 < X0 + RAND or y0 < Y0 + RAND or x1 > X1 - RAND or y1 > Y1 - RAND:
        return False
    if bereich and (x0 < bereich[0] or y0 < bereich[1] or x1 > bereich[2] or y1 > bereich[3]):
        return False
    for (lx, ly, r) in LOCH_SPERRE:
        nx, ny = min(max(lx, x0), x1), min(max(ly, y0), y1)
        if (nx - lx) ** 2 + (ny - ly) ** 2 < r * r:
            return False
    for b in belegt:
        if x0 < b[2] and b[0] < x1 and y0 < b[3] and b[1] < y1:
            return False
    return True


def setze(fp, x, y, rot=0):
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))


def ablegen(fp, ziel, belegt, bereich, abstand=0.3):
    """Spiralförmig um das Ziel-Bauteil suchen, bis der Courtyard (mit Abstand) frei ist."""
    zx, zy = ziel
    for r in [i * 0.5 for i in range(0, 120)]:
        schritte = max(1, int(r * 8))
        for i in range(schritte):
            import math
            a = 2 * math.pi * i / schritte
            for rot in (0, 90):
                setze(fp, zx + r * math.cos(a), zy + r * math.sin(a), rot)
                k = kasten(fp)
                kk = (k[0] - abstand, k[1] - abstand, k[2] + abstand, k[3] + abstand)
                if frei(kk, belegt, bereich):
                    return k
    raise RuntimeError("kein Platz für %s" % fp.GetReference())


def main():
    board = pcbnew.LoadBoard(PCB)
    vorhanden = {f.GetReference() for f in board.GetFootprints()}
    for f in board.GetFootprints():
        if f.GetReference().startswith("H"):
            f.SetBoardOnly(True)                 # Befestigungslöcher haben kein Schaltplansymbol
    teile, pads = netzliste()
    netze = {}
    for n in sorted({n for p in pads.values() for n in p.values()}):
        ni = board.FindNet(n)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(board, n)
            board.Add(ni)
        netze[n] = ni

    neu = {}
    for t in teile:
        if t["ref"] in vorhanden or not t["fp"]:
            continue
        lib, name = t["fp"].split(":", 1)
        pfad = EIGENE.get(lib, os.path.join(STD_FP, lib + ".pretty"))
        fp = pcbnew.FootprintLoad(pfad, name)
        if fp is None:
            raise SystemExit("Footprint fehlt: %s" % t["fp"])
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(t["ref"])
        fp.SetValue(t["wert"])
        fp.SetPath(pcbnew.KIID_PATH(t["pfad"].rstrip("/")))
        fp.SetSheetname(t["blatt"])
        fp.SetSheetfile(t["datei"])
        if t["lcsc"]:
            fp.SetField("LCSC", t["lcsc"])
            fp.GetField("LCSC").SetVisible(False)
        if t["info"]:
            fp.SetField("Description", t["info"])
        fp.SetDNP(t["dnp"])
        fp.SetExcludedFromBOM(not t["bom"])
        fp.Value().SetVisible(False)
        for pad in fp.Pads():
            n = pads[t["ref"]].get(pad.GetNumber())
            if n:
                pad.SetNet(netze[n])
        board.Add(fp)
        neu[t["ref"]] = (fp, t)

    belegt = [kasten(f) for f in board.GetFootprints() if f.GetReference() not in neu]
    # 1. feste Plätze
    for ref, (x, y, rot) in PLATZ.items():
        if ref in neu:
            setze(neu[ref][0], x, y, rot)
            belegt.append(kasten(neu[ref][0]))
    # 2. übrige: neben das Bauteil mit den meisten gemeinsamen Signalnetzen (im Bereich des Blatts)
    def signalnetze(ref):
        return {n for n in pads[ref].values() if n not in VERSORGUNGSNETZE and not n.startswith("unconnected")}
    platziert = set(PLATZ) | vorhanden
    rest = [r for r in neu if r not in PLATZ]
    rest.sort(key=lambda r: (r not in ZUORDNUNG, neu[r][1]["blatt"], int(re.sub(r"\D", "", r) or 0)))
    for ref in rest:
        fp, t = neu[ref]
        partner = ZUORDNUNG.get(ref)
        if partner is None:
            eigene = signalnetze(ref)
            wertung = collections.Counter()
            for p in sorted(platziert):          # feste Reihenfolge → gleiche Platzierung bei jedem Lauf
                if p in pads and neu.get(p, (None, {"blatt": None}))[1]["blatt"] == t["blatt"]:
                    wertung[p] = len(eigene & signalnetze(p))
            beste = wertung.most_common(1)
            partner = beste[0][0] if beste and beste[0][1] > 0 else ANKER[t["blatt"]]
        pf = neu[partner][0] if partner in neu else None
        ziel = (pcbnew.ToMM(pf.GetPosition().x), pcbnew.ToMM(pf.GetPosition().y)) if pf else (100, 100)
        bereich = KANTE_LINKS if partner in ("D301", "SW304") else BEREICH.get(t["blatt"])
        belegt.append(ablegen(fp, ziel, belegt, bereich))
        platziert.add(ref)

    # Referenztext, der über den Platinenrand ragt, in die Bauteilmitte legen
    for ref, (fp, t) in neu.items():
        b = fp.Reference().GetBoundingBox()
        if (pcbnew.ToMM(b.GetX()) < X0 + 0.3 or pcbnew.ToMM(b.GetRight()) > X1 - 0.3 or
                pcbnew.ToMM(b.GetY()) < Y0 + 0.3 or pcbnew.ToMM(b.GetBottom()) > Y1 - 0.3):
            fp.Reference().SetPosition(fp.GetPosition())
    board.Save(PCB)
    print("Bauteile ergänzt: %d, schon vorhanden: %d; Klemmenreihe bis x = %.2f mm (Lochsperre rechts ab %.2f mm)"
          % (len(neu), len(vorhanden), KLEMMEN_ENDE, 155.1 - 3.5))
    return 0


if __name__ == "__main__":
    sys.exit(main())
