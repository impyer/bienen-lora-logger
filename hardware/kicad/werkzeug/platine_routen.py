#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Restliche Verbindungen der Hauptplatine mit Freerouting legen (Autorouter, Specctra DSN/SES).

Ablauf:
1. Sperrfläche „Sperre_U401“ auf L1 unter dem Funkmodul (keine Leiterbahnen/Vias zwischen den Pads, mcu-funk.md 2.3:
   unter dem Modul durchgehende Masse) – einmalig.
2. Export nach Specctra DSN, ohne die Flächen (sonst blockieren sie in Freerouting alle Vias). Die Innenlagen
   In1.Cu (GND_L2) und In2.Cu (P3V3_L3/GND_L3) werden als Flächenlagen („power“) gekennzeichnet: Freerouting legt Signale nur auf L1 (F.Cu) und L4 (B.Cu), die Flächen bleiben ganz.
3. Freerouting im Kommandozeilenmodus mit den Regeln aus logger.kicad_pro (derzeit Netzklasse Default: Bahn 0,2 mm,
   Abstand 0,2 mm; platine_start.py legt die Projektdatei neu an). Weil die Flächen fehlen, verbindet Freerouting
   auch GND zusätzlich über Bahnen; diese überflüssigen GND-Bahnen entfernt platine_aufraeumen.py.
   Stromtragfähigkeit 0,2 mm (35 µm außen): ca. 0,6 A bei 10 K Erwärmung [A, IPC-2221-Näherung]; größter Strom auf
   SYS/VBUS/VIN_LADER unter 0,3 A (Ladestrom 150 mA, versorgung.md) – ausreichend.
4. Import der SES-Datei, Zonen neu füllen, speichern.

Freerouting ist nicht Teil des Repos. Pfad zur JAR über die Umgebungsvariable FREEROUTING_JAR. Getestet mit
Freerouting 1.9.0 (Java 21; ohne Anzeige über xvfb-run). Freerouting 2.1.0 lieferte mit dieser Platine fast keine
Verbindungen („maze search algorithm could not be created“) und wird nicht verwendet. Das Ergebnis eines Autorouters ist ein Entwurf: kritische Netze (Quarze, USB, SPI,
Analogzweig) danach von Hand prüfen und bei Bedarf neu legen.

Aufruf: FREEROUTING_JAR=/pfad/freerouting-2.1.0.jar python3 hardware/kicad/werkzeug/platine_routen.py [Durchgänge]
"""
import os
import re
import subprocess
import sys
import tempfile

import pcbnew

HIER = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(os.path.dirname(HIER), "hauptplatine", "logger.kicad_pcb")
SPERRE_U401 = (-6.4, -8.0, 6.4, 8.0)        # relativ zu U401; Innenkante der Pads bei ±6,91 mm


def mm(x):
    return pcbnew.FromMM(x)


def sperre_funkmodul(board):
    if any(z.GetZoneName() == "Sperre_U401" for z in board.Zones()):
        return False
    u = board.FindFootprintByReference("U401")
    cx, cy = (pcbnew.ToMM(v) for v in u.GetPosition())
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName("Sperre_U401")
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowFootprints(False)
    z.SetLayer(pcbnew.F_Cu)
    o = z.Outline()
    o.NewOutline()
    x0, y0, x1, y1 = SPERRE_U401
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(mm(cx + x), mm(cy + y))
    board.Add(z)
    return True


def ohne_flaechen(text):
    """Alle (plane …)-Ausdrücke aus dem DSN-Text entfernen (Klammern zählen)."""
    while True:
        i = text.find("(plane ")
        if i < 0:
            return text
        tiefe = 0
        for j in range(i, len(text)):
            if text[j] == "(":
                tiefe += 1
            elif text[j] == ")":
                tiefe -= 1
                if tiefe == 0:
                    break
        text = text[:i] + text[j + 1:]


def main():
    jar = os.environ.get("FREEROUTING_JAR")
    if not jar or not os.path.exists(jar):
        raise SystemExit("FREEROUTING_JAR setzen (Pfad zur Freerouting-JAR)")
    durchgaenge = sys.argv[1] if len(sys.argv) > 1 else "100"
    board = pcbnew.LoadBoard(PCB)
    sperre_funkmodul(board)
    board.Save(PCB)
    board = pcbnew.LoadBoard(PCB)
    with tempfile.TemporaryDirectory() as tmp:
        dsn, ses = os.path.join(tmp, "logger.dsn"), os.path.join(tmp, "logger.ses")
        if not pcbnew.ExportSpecctraDSN(board, dsn):
            raise SystemExit("DSN-Export fehlgeschlagen")
        text = open(dsn, encoding="utf-8").read()
        # Flächen nicht exportieren: Freerouting behandelt sie als festes Kupfer, das Vias fremder Netze blockiert.
        # Nach dem Import werden die Zonen ohnehin neu gefüllt.
        text = ohne_flaechen(text)
        for lage in ("In1.Cu", "In2.Cu"):
            text = re.sub(r"\(layer %s\s*\(type signal\)" % re.escape(lage), "(layer %s\n      (type power)" % lage, text)
        open(dsn, "w", encoding="utf-8").write(text)
        befehl = ["java", "-jar", jar, "-de", dsn, "-do", ses, "-mp", durchgaenge]
        if not os.environ.get("DISPLAY"):
            befehl = ["xvfb-run", "-a"] + befehl          # Freerouting 1.9 öffnet ein Fenster; ohne Anzeige virtuell
        r = subprocess.run(befehl, capture_output=True, text=True, timeout=7200, cwd=tmp)   # Logdatei nicht ins Repo
        log = (r.stdout or "") + (r.stderr or "")
        for zeile in log.splitlines():
            if any(k in zeile for k in ("unrouted", "completed", "Saving", "pass")):
                print(zeile[-160:])
        if not os.path.exists(ses):
            raise SystemExit("Freerouting hat keine SES-Datei geschrieben")
        if not pcbnew.ImportSpecctraSES(board, ses):
            raise SystemExit("SES-Import fehlgeschlagen")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    print("Routing importiert und Zonen gefüllt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
