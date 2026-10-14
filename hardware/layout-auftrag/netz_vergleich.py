#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Abnahme des Layouts (PFLICHTENHEFT.md Abschnitt 9): vergleicht die IPC-D-356-Netzliste der gelieferten Platine
mit der KiCad-Netzliste des Schaltplans (hardware/kicad/netzliste/logger.net).

Verglichen wird die **Verbindung der Pins** (welche Pins liegen gemeinsam in einem Netz), nicht der Netzname: Andere
Layout-Werkzeuge kürzen oder ändern Netznamen (IPC-D-356 erlaubt 14 Zeichen, lange Namen über NNAME-Aliase).
Gemeldet werden: Pins nur auf einer Seite, getrennte Netze (ein Schaltplan-Netz auf mehrere Platinen-Netze verteilt)
und verbundene Netze (mehrere Schaltplan-Netze in einem Platinen-Netz). Pins ohne Netz (KiCad „unconnected-…“, auf der
Platine Ein-Pin-Netze) zählen nicht. Geprüft am 14.10.2026 mit einer echten KiCad-10-IPC-D-356-Ausgabe (Testplatine mit
allen Footprints und Netzen): gleich; Netznamen dort auf 14 Zeichen gekürzt, was der Pin-Vergleich verträgt.

Aufruf:
  python3 hardware/layout-auftrag/netz_vergleich.py platine.ipc            → Exitcode 0 = gleich, 1 = Abweichung
  python3 hardware/layout-auftrag/netz_vergleich.py --selbsttest           → Rundlauf und Gegenprobe mit logger.net
"""
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
NETZLISTE = os.path.join(os.path.dirname(HIER), "kicad", "netzliste", "logger.net")
sys.path.insert(0, os.path.join(os.path.dirname(HIER), "kicad", "werkzeug"))


def kicad_netze(pfad=NETZLISTE):
    """{Netzname: {(Ref, Pin)}} aus der KiCad-Netzliste; ohne unbeschaltete Pins und ohne #-Symbole."""
    from kicad_gen import parse, finde, eins
    with open(pfad, encoding="utf-8") as f:
        baum = parse(f.read())
    netze = {}
    for n in finde(eins(baum, "nets"), "net"):
        name = eins(n, "name")[1]
        if name.startswith("unconnected-"):
            continue
        pins = {(eins(k, "ref")[1], eins(k, "pin")[1]) for k in finde(n, "node")}
        pins = {p for p in pins if not p[0].startswith("#")}
        if pins:
            netze[name] = pins
    return netze


def ipc356_netze(text):
    """{Netzname: {(Ref, Pin)}} aus IPC-D-356 (Datensätze 317/327, Festspalten; Aliase „P  NNAMEx …“)."""
    alias = {}
    netze = {}
    for zeile in text.splitlines():
        if zeile.startswith("P  NNAME"):
            teile = zeile[3:].split(None, 1)
            if len(teile) == 2:
                alias[teile[0]] = teile[1].strip()
            continue
        if not (zeile.startswith("317") or zeile.startswith("327")):
            continue
        netz = zeile[3:17].strip()
        ref = zeile[20:26].strip()
        pin = zeile[27:31].strip()
        if not netz or netz.startswith("N/C") or ref in ("VIA", ""):
            continue
        netz = alias.get(netz, netz)
        netze.setdefault(netz, set()).add((ref, pin))
    return netze


def vergleiche(soll, ist):
    """Liste von Abweichungstexten (leer = gleich)."""
    zu_soll = {p: n for n, ps in soll.items() for p in ps}
    # Unbeschaltete Pads: Werkzeuge geben ihnen eigene Ein-Pin-Netze (KiCad: gekürztes „unconnected-…“) → nicht werten
    ist = {n: ps for n, ps in ist.items() if not (len(ps) == 1 and next(iter(ps)) not in zu_soll)}
    zu_ist = {p: n for n, ps in ist.items() for p in ps}
    fehler = []
    nur_soll = sorted(set(zu_soll) - set(zu_ist))
    nur_ist = sorted(set(zu_ist) - set(zu_soll))
    if nur_soll:
        fehler.append("Pins nur im Schaltplan (fehlen auf der Platine): " + ", ".join("%s.%s" % p for p in nur_soll[:40]))
    if nur_ist:
        fehler.append("Pins nur auf der Platine: " + ", ".join("%s.%s" % p for p in nur_ist[:40]))
    for name, pins in sorted(soll.items()):
        teile = {zu_ist[p] for p in pins if p in zu_ist}
        if len(teile) > 1:
            fehler.append("Schaltplan-Netz %s auf der Platine getrennt in: %s" % (name, ", ".join(sorted(teile))))
    for name, pins in sorted(ist.items()):
        teile = {zu_soll[p] for p in pins if p in zu_soll}
        if len(teile) > 1:
            fehler.append("Platinen-Netz %s verbindet Schaltplan-Netze: %s" % (name, ", ".join(sorted(teile))))
    return fehler


def als_ipc356(netze):
    """Minimale IPC-D-356-Darstellung (für den Selbsttest), lange Netznamen über NNAME-Aliase."""
    zeilen = ["C  Selbsttest netz_vergleich.py", "P  UNITS CUST 0"]
    kurz = {}
    for i, name in enumerate(sorted(netze)):
        if len(name) > 14:
            kurz[name] = "NNAME%d" % (i + 1)
            zeilen.append("P  %s %s" % (kurz[name], name))
    for name, pins in sorted(netze.items()):
        for ref, pin in sorted(pins):
            zeilen.append("327%-14s   %-6s-%-4s" % (kurz.get(name, name), ref, pin))
    zeilen.append("999")
    return "\n".join(zeilen) + "\n"


def selbsttest():
    soll = kicad_netze()
    ok = True
    fehler = vergleiche(soll, ipc356_netze(als_ipc356(soll)))
    print(("ok   " if not fehler else "FEHL ") + "Rundlauf logger.net → IPC-D-356 → Vergleich: %d Netze, %d Pins"
          % (len(soll), sum(len(p) for p in soll.values())))
    ok &= not fehler
    # Gegenprobe 1: zwei Netze verbunden (MIC_P und MIC_N kurzgeschlossen)
    kaputt = {n: set(p) for n, p in soll.items()}
    p = [n for n in kaputt if n.endswith("MIC_P")][0]
    m = [n for n in kaputt if n.endswith("MIC_N")][0]
    kaputt[p] |= kaputt.pop(m)
    erkannt = any("verbindet" in f for f in vergleiche(soll, ipc356_netze(als_ipc356(kaputt))))
    print(("ok   " if erkannt else "FEHL ") + "Gegenprobe: Kurzschluss MIC_P/MIC_N wird erkannt")
    ok &= erkannt
    # Gegenprobe 2: ein Netz getrennt (B− in zwei Teile)
    kaputt = {n: set(p) for n, p in soll.items()}
    b = [n for n in kaputt if n.endswith("/B-")][0]
    pins = sorted(kaputt[b])
    kaputt[b] = set(pins[:1])
    kaputt[b + "_2"] = set(pins[1:])
    erkannt = any("getrennt" in f for f in vergleiche(soll, ipc356_netze(als_ipc356(kaputt))))
    print(("ok   " if erkannt else "FEHL ") + "Gegenprobe: getrenntes Netz B− wird erkannt")
    ok &= erkannt
    # Gegenprobe 3: B− mit GND verbunden (Schutz-FET überbrückt)
    kaputt = {n: set(p) for n, p in soll.items()}
    kaputt["GND"] |= kaputt.pop(b)
    erkannt = any("verbindet" in f and "B-" in f for f in vergleiche(soll, ipc356_netze(als_ipc356(kaputt))))
    print(("ok   " if erkannt else "FEHL ") + "Gegenprobe: B− an GND wird erkannt")
    ok &= erkannt
    return 0 if ok else 1


def main(argv):
    if len(argv) == 2 and argv[1] == "--selbsttest":
        return selbsttest()
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8", errors="replace") as f:
        ist = ipc356_netze(f.read())
    soll = kicad_netze()
    fehler = vergleiche(soll, ist)
    for f_ in fehler:
        print("FEHL " + f_)
    print("Schaltplan: %d Netze, Platine: %d Netze – %s" % (len(soll), len(ist), "gleich" if not fehler else
                                                         "%d Abweichung(en)" % len(fehler)))
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
