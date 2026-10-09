#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""ERC mit allen Schweregraden; vergleicht die Meldungen mit erc_erwartet.json (SCH26-04).
Endet mit Fehlercode bei jedem Fehler und jeder nicht erwarteten Warnung.
Aufruf: python3 werkzeug/erc_pruefen.py   (im Ordner hardware/kicad)
"""
import json
import os
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    with open(os.path.join(HIER, "erc_erwartet.json"), encoding="utf-8") as f:
        erwartet = json.load(f)
    fehler = 0
    for sch, liste in erwartet.items():
        if sch.startswith("_"):
            continue
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "erc.json")
            subprocess.run(["kicad-cli", "sch", "erc", "--severity-all", "--format", "json", "-o", out,
                            os.path.join(HIER, sch)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(out, encoding="utf-8") as f:
                d = json.load(f)
        offen = [dict(e) for e in liste]
        n = 0
        for blatt in d.get("sheets", []):
            for v in blatt.get("violations", []):
                n += 1
                items = [i.get("description", "") for i in v.get("items", [])]
                treffer = next((e for e in offen if e["type"] == v["type"] and any(e["item"] in i for i in items)), None)
                if treffer and v["severity"] != "error":
                    offen.remove(treffer)
                    print("  erwartet  %-24s %s (%s)" % (v["type"], treffer["item"], treffer["grund"]))
                else:
                    fehler += 1
                    print("  NEU       %-8s %-24s %s %s" % (v["severity"], v["type"], v["description"], items))
        for e in offen:
            print("  Hinweis: erwartete Meldung nicht mehr vorhanden (Liste bereinigen): %s %s" % (e["type"], e["item"]))
        print("ERC %s: %d Meldungen" % (sch, n))
    print("ERC-Ergebnis:", "OK" if fehler == 0 else "%d unerwartete Meldungen" % fehler)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
