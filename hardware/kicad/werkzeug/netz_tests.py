#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Prüft sicherheitsrelevante Netze in den von KiCad exportierten Netzlisten (nicht in den
Generator-Daten): Ladesperre, Zellschutz, Kabel Akku-Platine ↔ Hauptplatine, Widerstandswerte.
Aufruf (nach pruefen.sh): python3 werkzeug/netz_tests.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from kicad_gen import parse, finde, eins  # noqa: E402

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANZ = FEHL = 0


def lade(name):
    with open(os.path.join(HIER, "netzliste", name), encoding="utf-8") as f:
        baum = parse(f.read())
    netze, pin_netz, werte = {}, {}, {}
    for comp in finde(eins(baum, "components"), "comp"):
        werte[eins(comp, "ref")[1]] = eins(comp, "value")[1]
    for n in finde(eins(baum, "nets"), "net"):
        name = eins(n, "name")[1].split("/")[-1]
        knoten = {(eins(k, "ref")[1], eins(k, "pin")[1]) for k in finde(n, "node")}
        netze[name] = {k for k in knoten if not k[0].startswith("#")}
        for k in knoten:
            pin_netz[k] = name
    return netze, pin_netz, werte


def pruefe(text, ok, detail=""):
    global ANZ, FEHL
    ANZ += 1
    if not ok:
        FEHL += 1
    print(("ok   - " if ok else "FEHL - ") + text + ("" if ok else "  " + str(detail)))


def genau(netze, netz, soll):
    ist = netze.get(netz, set())
    pruefe("Netz %s = %s" % (netz, sorted(soll)), ist == set(soll), sorted(ist))


def enthaelt(netze, netz, soll):
    ist = netze.get(netz, set())
    pruefe("Netz %s enthält %s" % (netz, sorted(soll)), set(soll) <= ist, sorted(ist))


def modell_netze(modul):
    """Netze laut Generator-Beschreibung (Quelle der Wahrheit) als {Name: {(Ref, Pin)}}."""
    sys.path.insert(0, HIER)
    m = __import__(modul)
    pr = m.baue()
    netze = {}
    for b in [pr.wurzel] + pr.blaetter:
        for netz, knoten in b.netze().items():
            if netz in (None, "NC"):
                continue
            netze.setdefault(netz, set()).update(k for k in knoten if not k[0].startswith("#"))
    return {n: k for n, k in netze.items() if k}


def vollstaendig(modul, ist, datei):
    """Jedes Netz der KiCad-Netzliste muss exakt einem Netz des Modells entsprechen (Name und Pins).
    Fängt Zeichenfehler im Verdrahtungsmodus ab: falsch angeschlossene, offene oder kurzgeschlossene Pins."""
    soll = modell_netze(modul)
    ist = {n: k for n, k in ist.items() if k and not n.startswith("unconnected")}
    fehlt = sorted(set(soll) - set(ist))
    extra = sorted(set(ist) - set(soll))
    falsch = sorted(n for n in set(soll) & set(ist) if soll[n] != ist[n])
    pruefe("%s: alle %d Netze des Modells in KiCad vorhanden" % (datei, len(soll)), not fehlt, fehlt)
    pruefe("%s: keine zusätzlichen Netze in KiCad" % datei, not extra, {n: sorted(ist[n]) for n in extra})
    pruefe("%s: alle Netze mit genau den Pins des Modells" % datei, not falsch,
           {n: {"fehlt": sorted(soll[n] - ist[n]), "zuviel": sorted(ist[n] - soll[n])} for n in falsch})


def main():
    a, a_pin, a_wert = lade("akku.net")
    h, h_pin, h_wert = lade("logger.net")

    # --- Vollständiger Vergleich Modell ↔ gezeichneter Schaltplan ---
    vollstaendig("akku_platine", a, "akku.net")
    vollstaendig("hauptplatine", h, "logger.net")

    # --- Akku-Platine: Zellschutz ---
    genau(a, "B-", {("BT1", "2"), ("U1", "6"), ("C1", "2"), ("Q1", "1")})
    genau(a, "B+", {("BT1", "1"), ("JP1", "1"), ("J2", "1"), ("R1", "1")})
    genau(a, "D12", {("Q1", "2"), ("Q1", "5")})
    enthaelt(a, "GND", {("Q1", "3"), ("R2", "2"), ("J1", "1"), ("U2", "3"), ("U3", "3"), ("Q2", "2"), ("Q3", "2")})
    # SCH26-01: Ladesperre nur an TMP_VCC/GND (P−), keine Verbindung zu B+/B−
    genau(a, "TMP_VCC", {("J1", "4"), ("U2", "5"), ("U3", "5"), ("C2", "1"), ("C3", "1"), ("R5", "1"), ("R8", "1")})
    for ref in ("U2", "U3", "Q2", "Q3", "R5", "R8"):
        netze_ref = {n for (r, _), n in a_pin.items() if r == ref}
        pruefe("%s ohne Verbindung zu B+/B−/P+ (SCH26-01)" % ref, not (netze_ref & {"B+", "B-", "P+"}), netze_ref)
    # Stufe 1: TMP390 U2 → Q2 → CE_FREI
    genau(a, "GATE_CE", {("U2", "6"), ("U2", "4"), ("R5", "2"), ("Q2", "1")})
    genau(a, "CE_FREI", {("Q2", "3"), ("J1", "3")})
    # Stufe 2: TMP390 U3 → Q3 im NTC-Fuß
    genau(a, "GATE_NTC", {("U3", "6"), ("R8", "2"), ("Q3", "1")})
    genau(a, "NTC", {("J1", "2"), ("TH1", "1")})
    genau(a, "NTC_FUSS", {("TH1", "2"), ("Q3", "3")})
    pruefe("U3 OUTB offen", ("U3", "4") not in a_pin or a_pin[("U3", "4")].startswith("unconnected"), a_pin.get(("U3", "4")))
    for ref, soll in (("R3", "2,49k 1%"), ("R4", "18,7k 1%"), ("R6", "2,49k 1%"), ("R7", "18,7k 1%"), ("R2", "2k"), ("R1", "100")):
        pruefe("Wert %s = %s" % (ref, soll), a_wert.get(ref) == soll, a_wert.get(ref))

    # --- Hauptplatine: Lader ---
    genau(h, "CE_LADEN", {("U201", "4"), ("R205", "2"), ("C206", "1"), ("J203", "3")})
    genau(h, "TMP_VCC", {("U204", "5"), ("C212", "1"), ("J203", "4")})
    genau(h, "NTC", {("U201", "6"), ("J203", "2")})
    enthaelt(h, "VBAT", {("U201", "2"), ("J203", "5"), ("C205", "1"), ("R206", "1")})
    pruefe("U204 IN an VIN_LADER", h_pin.get(("U204", "1")) == "VIN_LADER", h_pin.get(("U204", "1")))
    pruefe("R205 (CE-Pull-up) an SYS", h_pin.get(("R205", "1")) == "SYS", h_pin.get(("R205", "1")))
    for ref, soll in (("R203", "2,0k 1%"), ("R204", "130k 1%"), ("R205", "100k"), ("R208", "100k"), ("R201", "3,3M"), ("R202", "470k")):
        pruefe("Wert %s = %s" % (ref, soll), h_wert.get(ref) == soll, h_wert.get(ref))
    genau(h, "SENSOR_EIN", {("U203", "3"), ("R208", "1"), ("U301", "41")})  # PB5
    pruefe("TPS22917 CT-Kondensator nach VIN (+3V3)", h_pin.get(("C210", "2")) == "+3V3" and h_pin.get(("C210", "1")) == "SW_CT")

    # --- Kabel J1 (Akku) ↔ J203 (Haupt), 1:1 ---
    zuordnung = {"GND": "GND", "NTC": "NTC", "CE_FREI": "CE_LADEN", "TMP_VCC": "TMP_VCC", "P+": "VBAT"}
    for pin in "12345":
        na, nh = a_pin.get(("J1", pin)), h_pin.get(("J203", pin))
        pruefe("Kabel Pin %s: Akku %s ↔ Haupt %s" % (pin, na, nh), zuordnung.get(na) == nh)

    print("%d von %d Netzprüfungen bestanden" % (ANZ - FEHL, ANZ))
    return 1 if FEHL else 0


if __name__ == "__main__":
    sys.exit(main())
