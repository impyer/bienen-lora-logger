#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Prüft sicherheitsrelevante Netze in den von KiCad exportierten Netzlisten (nicht in den
Generator-Daten): Ladesperre, Zellschutz, Kabel Akku-Platine ↔ Hauptplatine, Widerstandswerte.
Seit SCH26-09 zusätzlich: Pinbelegung der Stecker laut hardware/anschluesse.md (Spalte „Pins“)
gegen die Netzliste, mit Gegenprobe (vertauschter Pin muss auffallen).
Aufruf (nach pruefen.sh): python3 werkzeug/netz_tests.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from kicad_gen import parse, finde, eins  # noqa: E402

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANSCHLUESSE = os.path.join(os.path.dirname(HIER), "anschluesse.md")
ANZ = FEHL = 0

# Stecker, deren Pinbelegung in anschluesse.md steht und schon auf einem Schaltplanblatt liegt:
# Nr. im Dokument → (Referenz auf der Hauptplatine, Bezeichnung im Dokument → Netzname im Schaltplan)
STECKER_DOKU = {
    "J1": ("J201", {"GND": "GND", "+PV": "PV1"}),
    "J2": ("J202", {"GND": "GND", "+PV": "PV2"}),
    "J3": ("J203", {"P−": "GND", "NTC": "NTC", "CE_FREI": "CE_LADEN", "TMP_VCC": "TMP_VCC", "P+": "VBAT"}),
    "J10": ("J302", {"3V3": "+3V3", "SWDIO": "SWDIO", "SWCLK": "SWCLK", "NRST": "NRST", "GND": "GND",
                     "TX1": "DBG_TX", "RX1": "DBG_RX"}),
}


def lade(name):
    with open(os.path.join(HIER, "netzliste", name), encoding="utf-8") as f:
        baum = parse(f.read())
    netze, pin_netz, werte = {}, {}, {}
    for comp in finde(eins(baum, "components"), "comp"):
        werte[eins(comp, "ref")[1]] = eins(comp, "value")[1]
        fp = eins(comp, "footprint")
        werte[eins(comp, "ref")[1] + ":footprint"] = fp[1] if fp else ""
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


def doku_pins(nr):
    """Pinbelegung eines Steckers aus der Übersichtstabelle in anschluesse.md: {Pin: Bezeichnung}.
    Erwartet in Spalte 1 „Jn (Platine: Jxxx)“ und in Spalte 4 „1 Name, 2 Name, …“; Klammerzusätze entfallen."""
    with open(ANSCHLUESSE, encoding="utf-8") as f:
        for zeile in f:
            spalten = [t.strip() for t in zeile.strip().strip("|").split("|")]
            if len(spalten) >= 4 and re.fullmatch(r"%s \(Platine: J\d+\)" % nr, spalten[0]):
                pins = {}
                for eintrag in spalten[3].split(","):
                    m = re.fullmatch(r"(\d+)\s+(\S+)(?:\s*\(.*\))?", re.sub(r"\*", "", eintrag).strip())
                    if m:
                        pins[m.group(1)] = m.group(2)
                return spalten[0], pins
    return None, {}


def stecker_abweichungen(pin_netz, ref, soll):
    """Liste der Pins, deren Netz in der Netzliste nicht dem Soll entspricht (leer = in Ordnung)."""
    return sorted((pin, netz, pin_netz.get((ref, pin))) for pin, netz in soll.items() if pin_netz.get((ref, pin)) != netz)


def stecker_gegen_doku(pin_netz):
    """SCH26-09: Dokument (Kabelplan) und Schaltplan müssen dieselbe Pinbelegung haben."""
    for nr, (ref, namen) in STECKER_DOKU.items():
        kopf, pins = doku_pins(nr)
        pruefe("anschluesse.md: Zeile %s (Platine: %s) gefunden" % (nr, ref), bool(pins), kopf)
        if not pins:
            continue
        unbekannt = sorted(set(pins.values()) - set(namen))
        pruefe("%s: alle Pinbezeichnungen zuordenbar" % nr, not unbekannt, unbekannt)
        soll = {pin: namen.get(name) for pin, name in pins.items()}
        anzahl = len({p for (r, p) in pin_netz if r == ref})
        pruefe("%s/%s: Pinzahl Doku %d = Schaltplan %d" % (nr, ref, len(soll), anzahl), len(soll) == anzahl)
        pruefe("%s/%s: Pinbelegung Doku = Netzliste %s" % (nr, ref, ", ".join("%s %s" % kv for kv in sorted(soll.items()))),
               not stecker_abweichungen(pin_netz, ref, soll), stecker_abweichungen(pin_netz, ref, soll))
    # Gegenprobe: Ein vertauschter Pin (Fall SCH26-09: Pin 5 = TX statt GND) muss als Abweichung erkannt werden.
    ref, namen = STECKER_DOKU["J10"]
    _k, pins = doku_pins("J10")
    soll = {pin: namen.get(name) for pin, name in pins.items()}
    falsch = {(ref, pin): netz for pin, netz in soll.items()}   # unabhängig vom gezeichneten Stand
    falsch[(ref, "5")], falsch[(ref, "7")] = "DBG_TX", "GND"
    pruefe("Gegenprobe: J302 mit TX an Pin 5 und GND an Pin 7 wird erkannt", len(stecker_abweichungen(falsch, ref, soll)) == 2)


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

    # --- Debug-Stecker J302 (SCH26-09): je Pin ---
    for pin, netz in (("1", "+3V3"), ("2", "SWDIO"), ("3", "SWCLK"), ("4", "NRST"), ("5", "GND"), ("6", "DBG_TX"), ("7", "DBG_RX")):
        pruefe("J302 Pin %s = %s" % (pin, netz), h_pin.get(("J302", pin)) == netz, h_pin.get(("J302", pin)))
    genau(h, "DBG_TX", {("J302", "6"), ("U301", "30")})   # PA9
    genau(h, "DBG_RX", {("J302", "7"), ("U301", "31")})   # PA10
    # --- Ra-01SH TXEN/RXEN (SCH26-11): TXEN ist im Modul DIO2 → Lötbrücken offen, nur über Brücke an PB14/PB15 ---
    for jp, mod, mcu_netz, pin in (("JP401", "TXEN_MOD", "LORA_TXEN", "5"), ("JP402", "RXEN_MOD", "LORA_RXEN", "11")):
        pruefe("%s ist offene Lötbrücke" % jp, "_Open_" in h_wert.get(jp + ":footprint", ""), h_wert.get(jp + ":footprint"))
        genau(h, mod, {("U401", pin), (jp, "1")})
    pruefe("Ra-01SH DIO2 ohne Verbindung", h_pin.get(("U401", "7"), "unconnected").startswith("unconnected"), h_pin.get(("U401", "7")))
    # --- Stecker: anschluesse.md ↔ Netzliste ---
    stecker_gegen_doku(h_pin)

    # --- Kabel J1 (Akku) ↔ J203 (Haupt), 1:1 ---
    zuordnung = {"GND": "GND", "NTC": "NTC", "CE_FREI": "CE_LADEN", "TMP_VCC": "TMP_VCC", "P+": "VBAT"}
    for pin in "12345":
        na, nh = a_pin.get(("J1", pin)), h_pin.get(("J203", pin))
        pruefe("Kabel Pin %s: Akku %s ↔ Haupt %s" % (pin, na, nh), zuordnung.get(na) == nh)

    print("%d von %d Netzprüfungen bestanden" % (ANZ - FEHL, ANZ))
    return 1 if FEHL else 0


if __name__ == "__main__":
    sys.exit(main())
