#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Baut das Übergabepaket für den Layouter (hardware/layout-auftrag/PFLICHTENHEFT.md, Abschnitt 2.1).

Ergebnis: build/layout-auftrag-PCB-MAIN-0.1-<git-sha>.zip (build/ ist in .gitignore) mit KiCad-Projekt, Bibliotheken,
PDF, Netzliste, aktueller Stückliste (CSV, aus dem Generator), Pin/Footprint-Abgleich, den Blockdokumenten und dem
Pflichtenheft. Vorher `bash hardware/kicad/pruefen.sh` laufen lassen, damit PDF und Netzliste zum Schaltplan passen.
Aufruf: python3 hardware/layout-auftrag/paket_bauen.py
"""
import csv
import io
import os
import subprocess
import sys
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HIER)
REPO = os.path.dirname(HW)
KICAD = os.path.join(HW, "kicad")
sys.path.insert(0, KICAD)

KICAD_DATEIEN = ["bienen.kicad_sym", "pin_footprint.md", "pdf/logger.pdf", "netzliste/logger.net"]
KICAD_ORDNER = ["hauptplatine", "Bienen.pretty"]
DOKU = ["LASTENHEFT.md", "anschluesse.md", "mcu-funk.md", "versorgung.md", "waage.md", "mikrofon.md", "sicherheit-akku.md"]
AUSLASSEN = (".kicad_prl", "-backups", "fp-info-cache", ".lck")


def git_sha():
    try:
        sha = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                             check=True).stdout.strip()
        sauber = subprocess.run(["git", "-C", REPO, "status", "--porcelain"], capture_output=True, text=True).stdout == ""
        return sha if sauber else sha + "-geaendert"
    except (OSError, subprocess.CalledProcessError):
        return "ohne-git"


def stueckliste_csv():
    import hauptplatine
    zeilen = [z for z in hauptplatine.baue().stueckliste() if not z[0].startswith("#")]
    puffer = io.StringIO()
    w = csv.writer(puffer, lineterminator="\n")
    w.writerow(["Designator", "Value", "Symbol", "Footprint", "LCSC", "Sheet", "Note"])
    for ref, wert, sym, fp, lcsc, blatt, hinweis in zeilen:
        w.writerow([ref, wert, sym, fp, lcsc, blatt, hinweis])
    return puffer.getvalue(), len(zeilen), sum(1 for z in zeilen if z[4])


def main():
    sha = git_sha()
    ziel_ordner = os.path.join(REPO, "build")
    os.makedirs(ziel_ordner, exist_ok=True)
    ziel = os.path.join(ziel_ordner, "layout-auftrag-PCB-MAIN-0.1-%s.zip" % sha)
    bom, anzahl, mit_lcsc = stueckliste_csv()
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(HIER, "PFLICHTENHEFT.md"), "PFLICHTENHEFT.md")
        z.writestr("bom_aktuell.csv", bom)
        for d in KICAD_DATEIEN:
            z.write(os.path.join(KICAD, d), "kicad/" + d)
        for ordner in KICAD_ORDNER:
            for wurzel, _dirs, dateien in os.walk(os.path.join(KICAD, ordner)):
                for name in sorted(dateien):
                    if name.endswith(AUSLASSEN) or any(a in wurzel for a in AUSLASSEN):
                        continue
                    pfad = os.path.join(wurzel, name)
                    z.write(pfad, "kicad/" + os.path.relpath(pfad, KICAD).replace(os.sep, "/"))
        for d in DOKU:
            z.write(os.path.join(HW, d), "doku/" + d)
        z.writestr("STAND.txt", "Repository impyer/bienen-lora-logger, Stand %s\nStückliste: %d Teile, %d mit LCSC-Nummer\n"
                   % (sha, anzahl, mit_lcsc))
    print("Paket:", os.path.relpath(ziel, REPO), "| Teile %d, mit LCSC %d" % (anzahl, mit_lcsc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
