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


def degson_15edgrc(n):
    """DEGSON 15EDGRC-3.5-0nP-14-00A(H): steckbare Leiterplattenklemme, einreihig, geschlossen, gewinkelt, Raster 3,5 mm.
    Quelle: EasyEDA/LCSC-Footprint zu C7603438 (4-polig) [A]: Bohrung 1,4 mm, Pad Ø 2,0 mm, Körper 2,15 mm über die
    äußeren Pins, y −1,2 … +8,0 mm (Stecköffnung zur Seite +y, also zur Platinenkante). DEGSON-Zeichnung prüfen [P].
    Ursprung Pin 1 (wie die KiCad-Footprints der Phoenix-MC-Bauform)."""
    fp = Fp("DEGSON_15EDGRC-3.5-%02dP" % n, "DEGSON 15EDGRC-3.5 pluggable terminal block header 1x%02d P3.50mm right angle "
            "closed, drill 1.4mm (EasyEDA C7603438 geometry)" % n, "terminal block pluggable DEGSON 15EDGRC 3.5mm",
            attr="through_hole")
    for i in range(n):
        form = "rect" if i == 0 else "circle"
        fp.teile.append('\t(pad "%d" thru_hole %s (at %s 0) (size 2 2) (drill 1.4) (layers "*.Cu" "*.Mask"))'
                        % (i + 1, form, f(3.5 * i)))
    x1, x2 = -2.15, 3.5 * (n - 1) + 2.15
    fp.rechteck("F.Fab", x1, -1.2, x2, 8.0, 0.1)
    fp.linie("F.Fab", x1, 6.0, x2, 6.0, 0.1)                       # Stecköffnung (Steckerseite)
    fp.rechteck("F.SilkS", x1 - 0.12, -1.32, x2 + 0.12, 8.12, 0.12)
    fp.rechteck("F.CrtYd", x1 - 0.4, -1.6, x2 + 0.4, 8.4, 0.05)
    fp.schreibe(-2.6, 9.4)


def mrs03_j():
    """MiRelay MRS03-x-3: vergossener Reedkontakt mit J-Anschlüssen, Körper 8,5 × 2,1 × 2,4 mm. Quelle: MiRelay-Datenblatt
    MRS03 (LCSC C41432613), Abschnitt 4 „J型引脚“ [V]: Gesamtlänge 9,6 ± 0,2 mm, Innenabstand der Anschlüsse 6,8 mm,
    Anschlussbreite 0,6 mm. Kein Pad-Vorschlag im Datenblatt → Pads 2,0 × 1,2 mm bei x = ±4,1 mm (überdecken die
    Anschlüsse von 3,4 bis 4,8 mm mit Rand) [A]; EasyEDA (MK17-B-3-Footprint): 2,3 × 1,3 mm bei ±4,05 mm. Schaltachse
    = Längsachse: Magnet parallel zur Platinenkante führen."""
    fp = Fp("MiRelay_MRS03_J-Lead_8.5x2.1mm", "MiRelay MRS03 molded reed switch, J-lead, 8.5x2.1x2.4mm (MiRelay MRS03 datasheet)",
            "reed switch MRS03 MiRelay")
    fp.pad_smd("1", -4.1, 0, 2.0, 1.2)
    fp.pad_smd("2", 4.1, 0, 2.0, 1.2)
    fp.rechteck("F.Fab", -4.25, -1.05, 4.25, 1.05, 0.1)
    fp.linie("F.Fab", -2.5, 0, 2.5, 0, 0.1)                       # Glasröhrchen/Schaltachse
    fp.linie("F.SilkS", -2.9, -1.2, 2.9, -1.2, 0.12)
    fp.linie("F.SilkS", -2.9, 1.2, 2.9, 1.2, 0.12)
    fp.rechteck("F.CrtYd", -5.35, -1.5, 5.35, 1.5, 0.05)
    fp.schreibe(-2.4, 2.4)


def ltst_s220():
    """Lite-On LTST-S220 (seitlich abstrahlende Chip-LED, 2,15 × 1,0 mm). Quelle: Lite-On DS22-2000-075 Rev. D [V]:
    „Suggest Soldering Pad Dimensions“ 2 Pads 1,0 × 1,5 mm, Abstand 1,0 mm, gesamt 4,0 mm; Kathode an der Seite mit
    „Cathode Mask“ = Pad 1. Lichtaustritt seitlich: hier zur Seite −y (an die Platinenkante legen)."""
    fp = Fp("LED_Lite-On_LTST-S220_SideView", "Lite-On LTST-S220 side looking chip LED 2.15x1.0mm, pad 1 = cathode "
            "(Lite-On DS22-2000-075)", "LED side view LTST-S220")
    fp.pad_smd("1", -1.25, 0, 1.5, 1.0)
    fp.pad_smd("2", 1.25, 0, 1.5, 1.0)
    fp.rechteck("F.Fab", -1.075, -0.5, 1.075, 0.5, 0.1)
    fp.linie("F.Fab", -0.85, -0.5, -0.85, -0.85, 0.1)              # Linse (Lichtaustritt −y)
    fp.linie("F.Fab", -0.85, -0.85, 0.85, -0.85, 0.1)
    fp.linie("F.Fab", 0.85, -0.85, 0.85, -0.5, 0.1)
    fp.linie("F.SilkS", -0.35, 0.75, 0.35, 0.75, 0.12)
    fp.kreis("F.SilkS", -2.35, 0.75, 0.1, 0.12, fuellen=True)       # Kathodenpunkt
    fp.rechteck("F.CrtYd", -2.25, -1.1, 2.25, 0.85, 0.05)
    fp.schreibe(-2.0, 2.0)


def befestigung():
    """Befestigungsloch Ø 3,4 mm (nicht durchkontaktiert) für die Gehäusedome CBHUB-02 (Blatt 5) mit 10-mm-Distanzhülse
    (HW-03). Courtyard Ø 7 mm = Hülse Außen-Ø ≤ 6 mm plus Rand; Kupfer-Sperrfläche setzt die Platine."""
    fp = Fp("Befestigung_3.4mm_Huelse", "Mounting hole 3.4mm NPTH for CBHUB-02 boss with 10mm spacer sleeve (HW-03)",
            "mounting hole NPTH 3.4", attr="exclude_from_pos_files exclude_from_bom")
    fp.teile.append('\t(pad "" np_thru_hole circle (at 0 0) (size 3.4 3.4) (drill 3.4) (layers "*.Cu" "*.Mask"))')
    fp.kreis("F.Fab", 0, 0, 3.0, 0.1)
    fp.kreis("F.CrtYd", 0, 0, 3.5, 0.05)
    fp.schreibe(-4.5, 4.5)


def main():
    befestigung()
    mrs03_j()
    ltst_s220()
    bq25185_dlh()
    ra01sh()
    for n in (2, 3, 4, 5, 6):
        degson_15edgrc(n)
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
