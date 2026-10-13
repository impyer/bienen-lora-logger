#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Prüft sicherheitsrelevante Netze in den von KiCad exportierten Netzlisten (nicht in den
Generator-Daten): Ladesperre, Zellschutz, Kabel Akku-Platine ↔ Hauptplatine, Widerstandswerte.
Seit SCH26-09 zusätzlich: Pinbelegung der Stecker laut hardware/anschluesse.md (Spalte „Pins“)
gegen die Netzliste, mit Gegenprobe (vertauschter Pin muss auffallen).
Seit SCH26-07 (Blatt Waage): Wandler-Ansteuerung, HX711-Versorgung, AVDD aus dem Teiler, Zellenleitungen.
Aufruf (nach pruefen.sh): python3 werkzeug/netz_tests.py
"""
import math
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
    "J4": ("J501", {"Schirm": "GND", "E−": "GND", "S−": "ZELLE_SN", "S+": "ZELLE_SP", "E+": "ZELLE_EP"}),
    "J5": ("J601", {"Schirm": "GND", "GND": "GND", "OUT": "MIC_OUT_K", "VCC": "3V3_ANA"}),
}
VBG_HX711 = 1.25        # V, Bandgap-Referenz des AVDD-Reglers (HX711-Datenblatt, waage.md 3)
VSUP_MIN = 4.9          # V, TPS61240 5,0 V −2 % (waage.md 2)


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


def ohm(wert):
    """Widerstandswert aus dem Wertfeld, z. B. „8,2k 1%“ → 8200.0."""
    zahl = wert.split()[0].replace(",", ".")
    faktor = {"k": 1e3, "M": 1e6}.get(zahl[-1], 1.0)
    return float(zahl.rstrip("kM")) * faktor


def avdd(r_oben, r_unten):
    """AVDD des HX711 aus dem Teiler an VFB: 1,25 V × (1 + R_oben / R_unten)."""
    return VBG_HX711 * (1 + r_oben / r_unten)


def avdd_ok(u):
    """AVDD im Zielbereich 4,2–4,4 V und mindestens 0,1 V unter VSUP (HX711-Datenblatt)."""
    return 4.2 <= u <= 4.4 and VSUP_MIN - u >= 0.1


def waage(h, h_pin, h_wert):
    """SCH26-07: Blatt Waage gegen waage.md 2–4 und die Regeln in waage.md 7."""
    genau(h, "WAAGE_EIN", {("U301", "21"), ("U501", "4"), ("R501", "1")})          # PB10 → EN, Pull-down
    pruefe("R501 (EN-Pull-down) an GND, 100k", h_pin.get(("R501", "2")) == "GND" and h_wert.get("R501") == "100k",
           (h_pin.get(("R501", "2")), h_wert.get("R501")))
    pruefe("TPS61240 VIN an SYS, nicht an 3,3 V (Regel 3)", h_pin.get(("U501", "6")) == "SYS", h_pin.get(("U501", "6")))
    pruefe("TPS61240 FB direkt an VOUT", h_pin.get(("U501", "3")) == h_pin.get(("U501", "2")) == "5V_WAAGE",
           (h_pin.get(("U501", "2")), h_pin.get(("U501", "3"))))
    pruefe("TPS61240 Thermal-Pad an GND", h_pin.get(("U501", "7")) == "GND", h_pin.get(("U501", "7")))
    genau(h, "L_5V", {("L501", "2"), ("U501", "5")})
    pruefe("Ferrit FB501 zwischen 5V_WAAGE und VSUP_HX",
           {h_pin.get(("FB501", "1")), h_pin.get(("FB501", "2"))} == {"5V_WAAGE", "VSUP_HX"})
    enthaelt(h, "VSUP_HX", {("U502", "1"), ("Q501", "2")})                          # VSUP und Emitter
    pruefe("HX711 DVDD an 3V3_SW (Regel 4)", h_pin.get(("U502", "16")) == "3V3_SW", h_pin.get(("U502", "16")))
    genau(h, "HX_BASE", {("U502", "2"), ("Q501", "1")})
    enthaelt(h, "HX_AVDD", {("U502", "3"), ("Q501", "3"), ("R503", "1"), ("FB502", "1")})
    genau(h, "HX_VFB", {("U502", "4"), ("R503", "2"), ("R504", "1")})
    pruefe("R504 (unterer Teilerwiderstand) an GND", h_pin.get(("R504", "2")) == "GND", h_pin.get(("R504", "2")))
    u = avdd(ohm(h_wert.get("R503", "0")), ohm(h_wert.get("R504", "1")))
    pruefe(("AVDD aus R503/R504 = %.2f V: 4,2–4,4 V und ≥ 0,1 V unter VSUP %.1f V" % (u, VSUP_MIN)).replace(".", ","), avdd_ok(u))
    pruefe(("Gegenprobe: Teiler 20k/6,8k (AVDD %.2f V) wird als falsch erkannt" % avdd(20e3, 6.8e3)).replace(".", ","),
           not avdd_ok(avdd(20e3, 6.8e3)))
    for pin, netz in (("15", "GND"), ("14", "GND")):                                    # RATE, XI
        pruefe("HX711 Pin %s an %s (10 Werte/s, interner Takt)" % (pin, netz), h_pin.get(("U502", pin)) == netz)
    pruefe("HX711 XO offen", h_pin.get(("U502", "13"), "unconnected").startswith("unconnected"), h_pin.get(("U502", "13")))
    genau(h, "HX_DOUT", {("U301", "45"), ("R509", "2")})                           # PB8
    genau(h, "HX_SCK", {("U301", "46"), ("R508", "2")})                            # PB9
    genau(h, "HX_DOUT_IC", {("U502", "12"), ("R509", "1")})
    genau(h, "HX_PD_SCK", {("U502", "11"), ("R508", "1")})
    for ref in ("R508", "R509"):
        pruefe("Wert %s = 1k (Reihenwiderstand)" % ref, h_wert.get(ref) == "1k", h_wert.get(ref))
    # Zellenleitungen: nur Klemme, ESD mit kleinem Leckstrom und Reihenwiderstand (Regel 6)
    genau(h, "ZELLE_EP", {("J501", "5"), ("D501", "1"), ("FB502", "2")})
    genau(h, "ZELLE_SP", {("J501", "4"), ("D501", "2"), ("R505", "1")})
    genau(h, "ZELLE_SN", {("J501", "3"), ("D501", "4"), ("R506", "1")})
    genau(h, "HX_INP", {("U502", "8"), ("R505", "2"), ("C510", "1"), ("C511", "1")})
    genau(h, "HX_INN", {("U502", "7"), ("R506", "2"), ("C510", "2"), ("C512", "1"), ("R507", "1")})
    genau(h, "HX_INB", {("U502", "9"), ("U502", "10"), ("R507", "2")})
    pruefe("ESD D501 ist TPD4E05U06 (≤ 10 nA)", h_wert.get("D501", "").startswith("TPD4E05U06"), h_wert.get("D501"))


def farad(wert):
    """Kapazität aus dem Wertfeld, z. B. „22n C0G“ → 22e-9."""
    zahl = wert.split()[0].replace(",", ".").replace("µ", "u")
    return float(zahl[:-1]) * {"p": 1e-12, "n": 1e-9, "u": 1e-6}[zahl[-1]]


def sallen_key(r1, r2, c_rueck, c_masse):
    """Tiefpass 2. Ordnung, Verstärkung 1: Grenzfrequenz f0 und Güte Q (C_rück vom Mittelknoten zum Ausgang)."""
    f0 = 1 / (2 * math.pi * math.sqrt(r1 * r2 * c_rueck * c_masse))
    q = math.sqrt(r1 * r2 * c_rueck * c_masse) / (c_masse * (r1 + r2))
    return f0, q


def sk_ok(f0, q):
    """Soll aus mikrofon.md 2.1: 1179 Hz ± 5 %, Q 0,6–0,9 (nahe Butterworth 0,707)."""
    return abs(f0 - 1179) <= 0.05 * 1179 and 0.6 <= q <= 0.9


def mikrofon(h, h_pin, h_wert):
    """SCH26-07: Blatt Mikrofon gegen mikrofon.md 2 und Lastenheft A1–A2."""
    # Versorgung: 3V3_SW → Ferrit → 47 Ω → 3V3_ANA (A1)
    pruefe("FB601 zwischen 3V3_SW und MIC_FB", {h_pin.get(("FB601", "1")), h_pin.get(("FB601", "2"))} == {"3V3_SW", "MIC_FB"})
    pruefe("R602 47 Ω zwischen MIC_FB und 3V3_ANA",
           {h_pin.get(("R602", "1")), h_pin.get(("R602", "2"))} == {"MIC_FB", "3V3_ANA"} and h_wert.get("R602") == "47")
    enthaelt(h, "3V3_ANA", {("C601", "1"), ("U601", "5"), ("R603", "1"), ("J601", "4"), ("D601", "3")})
    # Vorspannung 1,65 V
    genau(h, "MIC_VREF", {("R603", "2"), ("R604", "1"), ("C603", "1"), ("R605", "1")})
    pruefe("VREF-Teiler symmetrisch (R603 = R604)", h_wert.get("R603") == h_wert.get("R604"), (h_wert.get("R603"), h_wert.get("R604")))
    # Eingang: ESD direkt an der Klemme, dann 100 Ω, Hochpass
    genau(h, "MIC_OUT_K", {("J601", "3"), ("D601", "1"), ("R601", "1")})
    genau(h, "MIC_IN", {("R601", "2"), ("C604", "1")})
    genau(h, "MIC_HP", {("C604", "2"), ("R605", "2"), ("R606", "1")})
    fh = 1 / (2 * math.pi * ohm(h_wert.get("R605", "1")) * farad(h_wert.get("C604", "1n")))
    pruefe(("Hochpass R605/C604 = %.1f Hz (Lastenheft A2: 20–25 Hz)" % fh).replace(".", ","), 20 <= fh <= 25)
    pruefe("ESD D601 ist ESDS304 (3,6 V reicht für 3,3 V)", h_wert.get("D601", "").startswith("ESDS304"), h_wert.get("D601"))
    pruefe("ESD D601 GND an Pin 2", h_pin.get(("D601", "2")) == "GND", h_pin.get(("D601", "2")))
    # Sallen-Key mit Spannungsfolger
    genau(h, "MIC_SK1", {("R606", "2"), ("R607", "1"), ("C605", "2")})
    genau(h, "MIC_SK2", {("R607", "2"), ("C606", "1"), ("U601", "3")})
    genau(h, "MIC_OP", {("U601", "1"), ("U601", "4"), ("C605", "1"), ("R608", "1")})
    pruefe("C606 nach GND", h_pin.get(("C606", "2")) == "GND", h_pin.get(("C606", "2")))
    pruefe("OPV V− an GND", h_pin.get(("U601", "2")) == "GND", h_pin.get(("U601", "2")))
    pruefe("OPV ist TLV9001IDBVR (nicht TLV9001U: andere Pinfolge)", h_wert.get("U601") == "TLV9001IDBVR", h_wert.get("U601"))
    f0, q = sallen_key(ohm(h_wert.get("R606", "1")), ohm(h_wert.get("R607", "1")),
                       farad(h_wert.get("C605", "1n")), farad(h_wert.get("C606", "1n")))
    pruefe(("Sallen-Key f0 = %.0f Hz, Q = %.2f (Soll 1179 Hz ± 5 %%, Q 0,6–0,9)" % (f0, q)).replace(".", ","), sk_ok(f0, q))
    f0g, qg = sallen_key(9.1e3, 9.1e3, 10e-9, 22e-9)
    pruefe(("Gegenprobe: vertauschte Kondensatoren (Q = %.2f) werden erkannt" % qg).replace(".", ","), not sk_ok(f0g, qg))
    # RC vor dem ADC
    genau(h, "MIC_ADC", {("R608", "2"), ("C608", "1"), ("U301", "11")})   # PA1
    frc = 1 / (2 * math.pi * ohm(h_wert.get("R608", "1")) * farad(h_wert.get("C608", "1n")))
    pruefe(("RC vor PA1 = %.1f kHz (mikrofon.md: 4,8 kHz)" % (frc / 1000)).replace(".", ","), 4.0e3 <= frc <= 5.5e3)


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
    # --- Waage (SCH26-07) ---
    waage(h, h_pin, h_wert)
    # --- Mikrofon (SCH26-07) ---
    mikrofon(h, h_pin, h_wert)
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
