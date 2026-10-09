#!/usr/bin/env python3
"""Projektsymbole (bienen.kicad_sym) für Bauteile, die in den KiCad-9-Bibliotheken fehlen.

Jede Pinbelegung ist mit der Datenblattquelle vermerkt. Aufruf:
  python3 hardware/kicad/werkzeug/symbole.py   → schreibt hardware/kicad/bienen.kicad_sym
Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from kicad_gen import S, Sym, dump, _txt  # noqa: E402

RASTER = 2.54


def ic(name, ref, links, rechts, unten=(), oben=(), fp="", ds="", info="", breite=None):
    """Rechteck-IC. Pin-Listen: (nummer, name, typ). Typ: power_in, power_out, input, output,
    bidirectional, passive, open_collector, no_connect."""
    n = max(len(links), len(rechts), 1)
    lmax = max([len(p[1]) for p in links] + [0])
    rmax = max([len(p[1]) for p in rechts] + [0])
    if breite is None:
        breite = max(10.16, (lmax + rmax) * 1.1 + 5)
        breite = max(breite, (max(len(unten), len(oben)) + 1) * RASTER)
    vert = max([len(p[1]) for p in list(unten) + list(oben)] + [0]) * 1.1 + 1
    import math
    schub = math.ceil(vert / RASTER) * RASTER
    hoehe = (n + 1) * RASTER + (schub if unten else 0) + (schub if oben else 0)
    hb, hh = breite / 2, hoehe / 2
    hb = math.ceil(hb / RASTER - 1e-9) * RASTER
    hh = math.ceil(hh / RASTER - 1e-9) * RASTER
    pins = []

    def pin(nr, pname, typ, x, y, w):
        p = S("pin", Sym(typ), Sym("line"), S("at", x, y, w), S("length", RASTER),
              S("name", pname, _txt(None)), S("number", str(nr), _txt(None)))
        pins.append(p)

    y0 = hh - (schub if oben else 0)
    for i, (nr, pn, t) in enumerate(links):
        pin(nr, pn, t, -hb - RASTER, y0 - RASTER * (i + 1), 0)
    for i, (nr, pn, t) in enumerate(rechts):
        pin(nr, pn, t, hb + RASTER, y0 - RASTER * (i + 1), 180)
    for i, (nr, pn, t) in enumerate(unten):
        x = -((len(unten) - 1) * RASTER) / 2 + i * RASTER
        pin(nr, pn, t, round(x / 1.27) * 1.27, -hh - RASTER, 90)
    for i, (nr, pn, t) in enumerate(oben):
        x = -((len(oben) - 1) * RASTER) / 2 + i * RASTER
        pin(nr, pn, t, round(x / 1.27) * 1.27, hh + RASTER, 270)

    sym = S("symbol", name, S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")), S("on_board", Sym("yes")),
            S("property", "Reference", ref, S("at", -hb, hh + (RASTER + 2.54 if oben else 0) + 1.27, 0), _txt(None, justify=["left"])),
            S("property", "Value", name, S("at", -hb, -hh - (RASTER + 2.54 if unten else 0) - 1.27, 0), _txt(None, justify=["left"])),
            S("property", "Footprint", fp, S("at", 0, 0, 0), _txt(None, verbergen=True)),
            S("property", "Datasheet", ds, S("at", 0, 0, 0), _txt(None, verbergen=True)),
            S("property", "Description", info, S("at", 0, 0, 0), _txt(None, verbergen=True)),
            S("symbol", name + "_0_1",
              S("rectangle", S("start", -hb, hh), S("end", hb, -hh),
                S("stroke", S("width", 0.254), S("type", Sym("default"))), S("fill", S("type", Sym("background"))))),
            [Sym("symbol"), name + "_1_1"] + pins,
            S("embedded_fonts", Sym("no")))
    return sym


SYMBOLE = [
    # TI BQ25185, WSON-10 (DLH) + Thermal-Pad. Quelle: TI SLUSF65B, Tabelle 4-1 Pin Functions [V]
    ic("BQ25185", "U",
       links=[("10", "IN", "power_in"), ("4", "~{CE}", "input"), ("6", "TS/~{MR}", "bidirectional"),
              ("8", "ISET", "passive"), ("7", "ILIM/VSET", "passive")],
       rechts=[("1", "SYS", "power_out"), ("2", "BAT", "power_in"), ("9", "STAT1", "open_collector"),
               ("3", "STAT2", "open_collector")],
       unten=[("5", "GND", "power_in"), ("11", "EP", "passive")],
       fp="Package_SON:WSON-10-1EP_2x2mm_P0.4mm_EP0.84x1.6mm",
       ds="https://www.ti.com/lit/ds/symlink/bq25185.pdf",
       info="1-Zellen-Linearlader 1 A, Power-Path, Eingang 3–18 V (25 V abs.), CE aktiv low, TS/MR: NTC + Reset (lang low = Werksmodus)"),
    # TI TMP390, SOT-563 (DRL). Quelle: TI SBOS904A, Pin Functions [V]
    ic("TMP390", "U",
       links=[("5", "VDD", "power_in"), ("1", "SETA", "passive"), ("2", "SETB", "passive")],
       rechts=[("6", "~{OUTA}", "open_collector"), ("4", "~{OUTB}", "open_collector")],
       unten=[("3", "GND", "power_in")],
       fp="Package_TO_SOT_SMD:SOT-563",
       ds="https://www.ti.com/lit/ds/symlink/tmp390.pdf",
       info="Temperaturschalter, 2 Schwellen per Widerstand (Tab. 7-1/7-2), Open-Drain aktiv low, 0,5 µA"),
    # HYCON HY2111-GB, SOT-23-6. Quelle: HYCON-Datenblatt (LCSC C82747), Abschnitt 7 Pinbelegung [V]
    ic("HY2111-GB", "U",
       links=[("5", "VDD", "power_in"), ("2", "CS", "input"), ("4", "NC", "no_connect")],
       rechts=[("1", "OD", "output"), ("3", "OC", "output")],
       unten=[("6", "VSS", "power_in")],
       fp="Package_TO_SOT_SMD:SOT-23-6",
       ds="https://www.lcsc.com/datasheet/C82747.pdf",
       info="Li-Ion-Schutz 1 Zelle: 4,28 V / 2,90 V, Freigabe nach Tiefentladung nur durch Laden"),
    # Fortune FS8205, SOT-23-6: 1 S1, 2 D12, 3 S2, 4 G2, 5 D12, 6 G1. Quelle: FS8205 Datenblatt (LCSC C32254), Abschnitt 4 [V]
    ic("FS8205", "Q",
       links=[("6", "G1", "input"), ("1", "S1", "passive")],
       rechts=[("4", "G2", "input"), ("3", "S2", "passive")],
       oben=[("2", "D12", "passive"), ("5", "D12", "passive")],
       fp="Package_TO_SOT_SMD:SOT-23-6",
       ds="https://www.lcsc.com/datasheet/C32254.pdf",
       info="Doppel-N-MOSFET mit gemeinsamem Drain, 20 V, ca. 30 mΩ"),
    # Richtek RT9080-33GJ5, TSOT-23-5: 1 VIN, 2 GND, 3 EN, 4 NC, 5 VOUT. Quelle: Richtek DS9080 (LCSC C841192) [V]
    ic("RT9080-33GJ5", "U",
       links=[("1", "VIN", "power_in"), ("3", "EN", "input")],
       rechts=[("5", "VOUT", "power_out"), ("4", "NC", "no_connect")],
       unten=[("2", "GND", "power_in")],
       fp="Package_TO_SOT_SMD:TSOT-23-5",
       ds="https://www.richtek.com/assets/product_file/RT9080/DS9080-03.pdf",
       info="LDO 3,3 V 600 mA, 2 µA Ruhestrom, EN nicht offen lassen"),
]


def main():
    ziel = os.path.join(os.path.dirname(__file__), "..", "bienen.kicad_sym")
    lib = [Sym("kicad_symbol_lib"), S("version", Sym("20251024")), S("generator", "bienen_symbole"),
           S("generator_version", "10.0")] + SYMBOLE
    with open(ziel, "w", encoding="utf-8") as f:
        f.write(dump(lib) + "\n")
    import shutil
    import subprocess
    if shutil.which("kicad-cli"):
        subprocess.run(["kicad-cli", "sym", "upgrade", "--force", ziel], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("geschrieben:", os.path.normpath(ziel), len(SYMBOLE), "Symbole")


if __name__ == "__main__":
    main()
