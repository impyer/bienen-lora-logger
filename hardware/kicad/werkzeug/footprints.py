#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Projektfootprints (hardware/kicad/Bienen.pretty) für Bauteile, die in der KiCad-Bibliothek fehlen.

Jeder Footprint nennt seine Maßquelle. Maße in mm, Ursprung = Bauteilmitte, Draufsicht.
Aufruf: python3 hardware/kicad/werkzeug/footprints.py   → schreibt hardware/kicad/Bienen.pretty/*.kicad_mod
Die Footprints selbst stehen unter CERN-OHL-S-2.0 (wie Schaltpläne und Symbole).
"""
import os

ZIEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Bienen.pretty")


def f(x):
    """Zahl ohne überflüssige Nullen (stabile, reproduzierbare Ausgabe)."""
    s = ("%.4f" % x).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Fp:
    def __init__(self, name, beschreibung, tags, attr="smd"):
        self.name, self.beschreibung, self.tags, self.attr = name, beschreibung, tags, attr
        self.teile = []

    def pad_smd(self, nr, x, y, w, h, form="roundrect", paste=True, rratio=0.25, extra=""):
        lagen = '"F.Cu" "F.Mask"' + (' "F.Paste"' if paste else "")
        rr = " (roundrect_rratio %s)" % f(rratio) if form == "roundrect" else ""
        self.teile.append('\t(pad "%s" smd %s (at %s %s) (size %s %s) (layers %s)%s%s)'
                          % (nr, form, f(x), f(y), f(w), f(h), lagen, rr, extra))

    def paste(self, x, y, w, h):
        """Nur Pastenöffnung (ohne Kupfer), z. B. verkleinerte Paste auf dem Thermal-Pad."""
        self.teile.append('\t(pad "" smd roundrect (at %s %s) (size %s %s) (layers "F.Paste") (roundrect_rratio 0.25))'
                          % (f(x), f(y), f(w), f(h)))

    def linie(self, lage, x1, y1, x2, y2, breite):
        self.teile.append('\t(fp_line (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "%s"))'
                          % (f(x1), f(y1), f(x2), f(y2), f(breite), lage))

    def rechteck(self, lage, x1, y1, x2, y2, breite):
        self.teile.append('\t(fp_rect (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (fill no) (layer "%s"))'
                          % (f(x1), f(y1), f(x2), f(y2), f(breite), lage))

    def kreis(self, lage, x, y, r, breite, fuellen=False):
        self.teile.append('\t(fp_circle (center %s %s) (end %s %s) (stroke (width %s) (type solid)) (fill %s) (layer "%s"))'
                          % (f(x), f(y), f(x + r), f(y), f(breite), "yes" if fuellen else "no", lage))

    def text(self, art, wert, x, y, lage):
        self.teile.append('\t(property "%s" "%s" (at %s %s 0) (layer "%s") (effects (font (size 1 1) (thickness 0.15))))'
                          % (art, wert, f(x), f(y), lage))

    def schreibe(self, ref_y, wert_y):
        kopf = ['(footprint "%s"' % self.name, "\t(version 20260206)", '\t(generator "bienen_footprints")',
                '\t(layer "F.Cu")', '\t(descr "%s")' % self.beschreibung, '\t(tags "%s")' % self.tags]
        kopf.append('\t(property "Reference" "REF**" (at 0 %s 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))' % f(ref_y))
        kopf.append('\t(property "Value" "%s" (at 0 %s 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % (self.name, f(wert_y)))
        kopf.append('\t(attr %s)' % self.attr)
        os.makedirs(ZIEL, exist_ok=True)
        with open(os.path.join(ZIEL, self.name + ".kicad_mod"), "w", encoding="utf-8") as d:
            d.write("\n".join(kopf + self.teile) + "\n)\n")


def bq25185_dlh():
    """TI DLH0010A (WSON-10, 2,2 × 2,0 mm, 0,4 mm Raster). Quelle: TI SLUSF65, Package Outline und
    Example Board Layout 4226298/A [V]: Padreihen 2,1 mm Mittenabstand, Pads 0,5 × 0,2 mm, Thermal-Pad 0,9 × 1,5 mm,
    Pastenöffnung Thermal-Pad 0,85 × 1,38 mm (88 %). NSMD-Pads (Lötstopp 0,05 mm). Durchkontaktierungen im
    Thermal-Pad (TI: 2 × Ø 0,2 mm bei y = ±0,5, verfüllt oder abgedeckt) setzt das Layout."""
    fp = Fp("WSON-10-1EP_2.2x2mm_DLH0010A",
            "TI DLH0010A WSON-10 2.2x2.0mm P0.4mm EP0.9x1.5mm (TI SLUSF65, 4226298/A)", "WSON DLH BQ25185")
    for i in range(5):
        y = -0.8 + 0.4 * i
        fp.pad_smd(str(1 + i), -1.05, y, 0.5, 0.2)          # 1–5 links, von oben nach unten
        fp.pad_smd(str(10 - i), 1.05, y, 0.5, 0.2)          # 10–6 rechts, von oben nach unten
    fp.pad_smd("11", 0, 0, 0.9, 1.5, form="roundrect", paste=False, rratio=0.05)
    fp.paste(0, 0, 0.85, 1.38)
    fp.rechteck("F.Fab", -1.1, -1.0, 1.1, 1.0, 0.1)
    fp.kreis("F.Fab", -0.7, -0.6, 0.15, 0.1)
    fp.linie("F.SilkS", -0.6, -1.11, 0.6, -1.11, 0.12)
    fp.linie("F.SilkS", -0.6, 1.11, 0.6, 1.11, 0.12)
    fp.kreis("F.SilkS", -1.55, -1.05, 0.1, 0.12, fuellen=True)    # Pin-1-Punkt
    fp.rechteck("F.CrtYd", -1.55, -1.25, 1.55, 1.25, 0.05)
    fp.schreibe(-2.0, 2.0)


def ra01sh():
    """Ai-Thinker Ra-01SH, 16 Stempellöcher, Modul 16 × 17 mm. Quelle: Ra-01SH Specification V1.1 (2020-08-18),
    S. 10 Abmessungen und S. 13 „Recommended module package design size“ [V]: Raster 2,0 mm, erstes Pad 1,0 mm
    unter der Oberkante, Pads 1,536 × 1,0 mm, Innenkantenabstand 13,828 mm, Pin 1 2,262 mm breit (nach außen
    verlängert), Umriss 16,06 × 17,0 mm. Pin 1 oben links, 1–8 links nach unten, 9–16 rechts nach oben."""
    fp = Fp("Ai-Thinker_Ra-01SH", "Ai-Thinker Ra-01SH LoRa module 16x17mm, 16 castellated pads P2.0mm "
            "(Ra-01SH Specification V1.1 p.10/13)", "LoRa SX1262 Ra-01SH Ai-Thinker")
    innen = 13.8284 / 2
    for i in range(8):
        y = -7.0 + 2.0 * i
        if i == 0:
            fp.pad_smd("1", -(innen + 2.262 / 2), y, 2.262, 1.0, form="rect")
        else:
            fp.pad_smd(str(1 + i), -(innen + 1.5358 / 2), y, 1.5358, 1.0, form="rect")
        fp.pad_smd(str(16 - i), innen + 1.5358 / 2, y, 1.5358, 1.0, form="rect")
    bx, by = 16.0625 / 2, 8.5
    fp.rechteck("F.Fab", -bx, -by, bx, by, 0.1)
    fp.linie("F.SilkS", -bx - 0.12, -by - 0.12, bx + 0.12, -by - 0.12, 0.12)
    fp.linie("F.SilkS", -bx - 0.12, by + 0.12, bx + 0.12, by + 0.12, 0.12)
    fp.kreis("F.SilkS", -9.8, -7.0, 0.2, 0.12, fuellen=True)      # Pin-1-Punkt außerhalb des Pads
    fp.rechteck("F.CrtYd", -10.25, -8.95, 10.25, 8.95, 0.05)
    fp.schreibe(-9.8, 9.8)


def main():
    bq25185_dlh()
    ra01sh()
    import shutil
    import subprocess
    if shutil.which("kicad-cli"):        # in KiCads eigenes Format bringen (prüft zugleich die Syntax)
        subprocess.run(["kicad-cli", "fp", "upgrade", "--force", ZIEL], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # KiCad vergibt dabei zufällige UUIDs → durch feste ersetzen, damit die Ausgabe reproduzierbar bleibt
        import re
        import uuid
        for datei in sorted(os.listdir(ZIEL)):
            pfad = os.path.join(ZIEL, datei)
            with open(pfad, encoding="utf-8") as d:
                inhalt = d.read()
            zaehler = iter(range(100000))
            inhalt = re.sub(r'\(uuid "[0-9a-f-]+"\)',
                            lambda m: '(uuid "%s")' % uuid.uuid5(uuid.NAMESPACE_URL, "bienen/%s/%d" % (datei, next(zaehler))),
                            inhalt)
            with open(pfad, "w", encoding="utf-8") as d:
                d.write(inhalt)
    print("geschrieben:", os.path.normpath(ZIEL))


if __name__ == "__main__":
    main()
