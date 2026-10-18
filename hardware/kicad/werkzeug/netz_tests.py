#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Prüft sicherheitsrelevante Netze in den von KiCad exportierten Netzlisten (nicht in den
Generator-Daten): Ladesperre, Zellschutz (Blatt Akku, seit HW-06 auf der Hauptplatine), Widerstandswerte.
Seit SCH26-09 zusätzlich: Pinbelegung der Stecker laut hardware/anschluesse.md (Spalte „Pins“)
gegen die Netzliste, mit Gegenprobe (vertauschter Pin muss auffallen).
Seit SCH26-07 (Blatt Waage): Wandler-Ansteuerung, HX711-Versorgung, AVDD aus dem Teiler, Zellenleitungen.
Seit HW-09 (18.10.2026): BLE-Modul RN4871 (Lastschalter an PB13, USART6, Pull-ups nur an BLE_VCC, J704 Pin 9–11),
USB-C-Buchse entfällt, Laden über zwei Pads J301 (kein USBLC6, kein VBUS-Teiler).
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

OFFEN = "(offen)"         # Pin ohne Verbindung (KiCad-Netz „unconnected-…“)

# Stecker, deren Pinbelegung in anschluesse.md steht und schon auf einem Schaltplanblatt liegt:
# Nr. im Dokument → (Referenz auf der Hauptplatine, Bezeichnung im Dokument → Netzname im Schaltplan)
STECKER_DOKU = {
    "J1": ("J201", {"GND": "GND", "+PV": "PV1"}),
    "J2": ("J202", {"GND": "GND", "+PV": "PV2"}),
    "J10": ("J302", {"3V3": "+3V3", "SWDIO": "SWDIO", "SWCLK": "SWCLK", "NRST": "NRST", "GND": "GND",
                     "TX1": "DBG_TX", "RX1": "DBG_RX"}),
    "J4": ("J501", {"Schirm": "GND", "E−": "GND", "S−": "ZELLE_SN", "S+": "ZELLE_SP", "E+": "ZELLE_EP"}),
    "J5": ("J601", {"GND": "GND", "VDD": "3V3_MEMS", "CLK": "PDM_CLK", "DATA": "PDM_DATA_K",
                    "MIC+": "MIC_P", "MIC−": "MIC_N", "MIC3+": "MIC3_P", "MIC3−": "MIC3_N", "Schirm": "GND"}),
    "J6": ("J701", {"GND": "GND", "DQ": "ONEWIRE", "3V3_SW": "3V3_SW"}),
    "J7": ("J702", {"GND": "GND", "DQ": "ONEWIRE", "3V3_SW": "3V3_SW"}),
    "J8": ("J703", {"Schirm": "GND", "GND": "GND", "SDA": "I2C_SDA", "SCL": "I2C_SCL", "3V3_SW": "3V3_SW", "frei": OFFEN}),
    "J9": ("J301", {"GND": "GND", "+5V": "VBUS"}),
    "J11": ("J704", {"3V3": "+3V3", "3V3_SW": "3V3_SW", "GND": "GND", "SDA": "I2C_SDA", "SCL": "I2C_SCL", "TX1": "DBG_TX",
                     "RX1": "DBG_RX", "BLE_RXD": "BLE_RXD", "BLE_TXD": "BLE_TXD", "BLE_MODE": "BLE_MODE"}),
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
    Erwartet in Spalte 1 „Jn (Platine: Jxxx)“ und in Spalte 4 „1 Name, 2 Name, …“ (Schirmpin „SH Name“);
    Klammerzusätze entfallen."""
    with open(ANSCHLUESSE, encoding="utf-8") as f:
        for zeile in f:
            spalten = [t.strip() for t in zeile.strip().strip("|").split("|")]
            if len(spalten) >= 4 and re.fullmatch(r"%s \(Platine: J\d+\)" % nr, spalten[0]):
                pins = {}
                for eintrag in spalten[3].split(","):
                    m = re.fullmatch(r"(\d+|SH)\s+(\S+)(?:\s*\(.*\))?", re.sub(r"\*", "", eintrag).strip())   # SH = Schirmpin (RJ45)
                    if m:
                        pins[m.group(1)] = m.group(2)
                return spalten[0], pins
    return None, {}


def stecker_abweichungen(pin_netz, ref, soll):
    """Liste der Pins, deren Netz in der Netzliste nicht dem Soll entspricht (leer = in Ordnung)."""
    def passt(ist, netz):
        return ist == netz or (netz == OFFEN and (ist is None or ist.startswith("unconnected")))
    return sorted((pin, netz, pin_netz.get((ref, pin))) for pin, netz in soll.items() if not passt(pin_netz.get((ref, pin)), netz))


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


def mikrofon(h, h_pin, h_wert):
    """HW-07: Blatt Mikrofon gegen mikrofon.md 2 und Lastenheft A1–A7 (Audio-ADC TLV320ADC3101, Elektret + PDM-MEMS)."""
    # Versorgung
    pruefe("FB601 zwischen 3V3_SW und MIC_FB", {h_pin.get(("FB601", "1")), h_pin.get(("FB601", "2"))} == {"3V3_SW", "MIC_FB"})
    pruefe("R602 10 Ω zwischen MIC_FB und 3V3_ANA",
           {h_pin.get(("R602", "1")), h_pin.get(("R602", "2"))} == {"MIC_FB", "3V3_ANA"} and h_wert.get("R602") == "10")
    genau(h, "3V3_ANA", {("R602", "2"), ("C601", "1"), ("C602", "1"), ("C612", "1"), ("C613", "1"), ("U601", "10")})
    genau(h, "1V8_ADC", {("U602", "5"), ("C610", "1"), ("C614", "1"), ("C615", "1"), ("U601", "22")})
    pruefe("U602 ist TPS70918 (DVDD 1,65–1,95 V)", h_wert.get("U602", "").startswith("TPS70918"), h_wert.get("U602"))
    pruefe("U602 IN und EN an 3V3_SW", h_pin.get(("U602", "1")) == h_pin.get(("U602", "3")) == "3V3_SW",
           (h_pin.get(("U602", "1")), h_pin.get(("U602", "3"))))
    pruefe("IOVDD (Pin 21) an 3V3_SW wie die I²C-Pull-ups", h_pin.get(("U601", "21")) == "3V3_SW", h_pin.get(("U601", "21")))
    genau(h, "3V3_MEMS", {("FB602", "2"), ("C611", "1"), ("J601", "4")})
    for pin in ("9", "23", "25", "15", "16", "24"):
        pruefe("U601 Pin %s an GND (AVSS, DVSS, EP, I2C_ADR0/1 → 0x18, MCLK unbenutzt)" % pin,
               h_pin.get(("U601", pin)) == "GND", h_pin.get(("U601", pin)))
    pruefe("U601 ist TLV320ADC3101 (3100 hat keinen Digitalmikrofon-Eingang)",
           h_wert.get("U601", "").startswith("TLV320ADC3101"), h_wert.get("U601"))
    # I²S und I²C zum STM32
    genau(h, "I2S_CK", {("U601", "1"), ("U301", "25")})    # PB12 = I2S3_CK
    genau(h, "I2S_WS", {("U601", "2"), ("U301", "38")})    # PA15 = I2S3_WS
    genau(h, "I2S_SD", {("U601", "3"), ("U301", "41")})    # PB5 = I2S3_SD
    genau(h, "ADC_RESET", {("U601", "4"), ("R609", "2"), ("C618", "1")})
    pruefe("Reset-Pull-up R609 an 3V3_SW", h_pin.get(("R609", "1")) == "3V3_SW", h_pin.get(("R609", "1")))
    # Elektret, pseudo-differenziell
    genau(h, "MICBIAS", {("U601", "5"), ("R610", "1"), ("C621", "1")})
    genau(h, "MIC_P", {("R610", "2"), ("C619", "1"), ("C622", "1"), ("J601", "7"), ("D601", "4")})
    genau(h, "MIC_N", {("R611", "1"), ("C620", "1"), ("C623", "1"), ("J601", "8"), ("D601", "5")})
    genau(h, "MIC_INP", {("C619", "2"), ("U601", "7")})     # IN2L(P)
    genau(h, "MIC_INN", {("C620", "2"), ("U601", "6")})     # IN3L(M)
    pruefe("R611 nach GND, R610 = R611 (symmetrisch)",
           h_pin.get(("R611", "2")) == "GND" and h_wert.get("R610") == h_wert.get("R611"), (h_wert.get("R610"), h_wert.get("R611")))
    # HW-10: Mikrofon 3 am rechten Analogeingang, gleiche Beschaltung, an J601 Pin 5/6 (Philipp) mit ESD D602
    genau(h, "MICBIAS2", {("U601", "14"), ("R614", "1"), ("C629", "1")})
    genau(h, "MIC3_P", {("R614", "2"), ("C625", "1"), ("C627", "1"), ("J601", "5"), ("D602", "3")})
    genau(h, "MIC3_N", {("R615", "1"), ("C626", "1"), ("C628", "1"), ("J601", "6"), ("D602", "1")})
    genau(h, "MIC3_INP", {("C625", "2"), ("U601", "12")})     # IN2R(P)
    genau(h, "MIC3_INN", {("C626", "2"), ("U601", "13")})     # IN3R(M)
    pruefe("R615 nach GND, R614 = R615 = R610 (alle Kapseln gleich vorgespannt)",
           h_pin.get(("R615", "2")) == "GND" and h_wert.get("R614") == h_wert.get("R615") == h_wert.get("R610"),
           (h_wert.get("R614"), h_wert.get("R615")))
    pruefe("Koppel-C Elektret 2 = Elektret 1 (gleicher Hochpass)", h_wert.get("C625") == h_wert.get("C619") and h_wert.get("C626") == h_wert.get("C620"),
           (h_wert.get("C625"), h_wert.get("C626")))
    pruefe("U601 IN1L/IN1R offen (nur IN2/IN3 je Kanal belegt)",
           all(h_pin.get(("U601", p), "unconnected").startswith("unconnected") for p in ("8", "11")), (h_pin.get(("U601", "8")), h_pin.get(("U601", "11"))))
    pruefe("ESD D602 ist ESDS304, GND an Pin 2, schützt MIC3−/MIC3+", h_wert.get("D602", "").startswith("ESDS304") and h_pin.get(("D602", "2")) == "GND"
           and {h_pin.get(("D602", "1")), h_pin.get(("D602", "3"))} == {"MIC3_N", "MIC3_P"}, (h_wert.get("D602"), h_pin.get(("D602", "2"))))
    pruefe("J601 Pin 5 = MIC3+ (Paarpartner VDD), Pin 6 = MIC3− (Paarpartner DATA)",
           h_pin.get(("J601", "5")) == "MIC3_P" and h_pin.get(("J601", "6")) == "MIC3_N", (h_pin.get(("J601", "5")), h_pin.get(("J601", "6"))))
    falsch = dict(h_pin)
    falsch[("J601", "5")], falsch[("J601", "6")] = "MIC3_N", "MIC3_P"
    pruefe("Gegenprobe: vertauschte MIC3+/MIC3− an J601 werden erkannt",
           stecker_abweichungen(falsch, "J601", {"5": "MIC3_P", "6": "MIC3_N"}) != [])
    fh = 1 / (2 * math.pi * 35e3 * farad(h_wert.get("C619", "1n")))
    pruefe(("Hochpass Koppel-C mit 35 kΩ Eingang = %.1f Hz (≤ 20 Hz, Nutzband ab 60 Hz)" % fh).replace(".", ","), fh <= 20)
    # PDM-Mikrofon
    genau(h, "PDM_CLK_ADC", {("U601", "20"), ("U603", "2")})
    genau(h, "PDM_CLK_BUF", {("U603", "4"), ("R612", "2")})
    genau(h, "PDM_CLK", {("R612", "1"), ("J601", "2"), ("D601", "1")})
    genau(h, "PDM_DATA_K", {("J601", "3"), ("D601", "3"), ("R613", "1")})
    genau(h, "PDM_DATA", {("R613", "2"), ("U601", "19")})
    pruefe("Takttreiber U603 an 3V3_SW", h_pin.get(("U603", "5")) == "3V3_SW", h_pin.get(("U603", "5")))
    # Klemme und ESD
    pruefe("ESD D601 ist ESDS304, GND an Pin 2", h_wert.get("D601", "").startswith("ESDS304") and
           h_pin.get(("D601", "2")) == "GND", (h_wert.get("D601"), h_pin.get(("D601", "2"))))
    for pin in ("1", "SH"):
        pruefe("J601 Pin %s an GND (Paarpartner CLK/Schirm)" % pin, h_pin.get(("J601", pin)) == "GND", h_pin.get(("J601", pin)))
    pruefe("J601 ist RJ45 geschirmt (T568B-Paare 1/2, 3/6, 4/5, 7/8)", h_wert.get("J601:footprint", "").startswith("Connector_RJ:RJ45"),
           h_wert.get("J601:footprint"))
    falsch = dict(h_pin)
    falsch[("J601", "2")], falsch[("J601", "3")] = "PDM_DATA_K", "PDM_CLK"
    pruefe("Gegenprobe: vertauschte CLK/DATA an J601 werden erkannt",
           stecker_abweichungen(falsch, "J601", {"2": "PDM_CLK", "3": "PDM_DATA_K"}) != [])


def anschluesse(h, h_pin, h_wert):
    """SCH26-07: Blatt Anschlüsse gegen anschluesse.md 1–3 und HW26-04 (Pull-ups nur an 3V3_SW)."""
    genau(h, "ONEWIRE", {("U301", "29"), ("R701", "2"), ("J701", "2"), ("J702", "2"), ("D701", "1")})   # PA8
    genau(h, "I2C_SDA", {("U301", "43"), ("R702", "1"), ("J703", "3"), ("D702", "1"), ("J704", "5"), ("U601", "18")})   # PB7
    genau(h, "I2C_SCL", {("U301", "42"), ("R703", "2"), ("J703", "4"), ("D702", "3"), ("J704", "6"), ("U601", "17")})   # PB6
    def pullup_ok(pin_netz, wert, ref, soll):
        andere = {n for (r, _), n in pin_netz.items() if r == ref} - {"ONEWIRE", "I2C_SDA", "I2C_SCL"}
        return andere == {"3V3_SW"} and wert.get(ref) == soll
    for ref, soll in (("R701", "4,7k"), ("R702", "1,8k"), ("R703", "1,8k")):
        pruefe("Pull-up %s = %s an 3V3_SW (HW26-04)" % (ref, soll), pullup_ok(h_pin, h_wert, ref, soll),
               ({n for (r, _), n in h_pin.items() if r == ref}, h_wert.get(ref)))
    falsch = dict(h_pin)
    falsch[("R701", "1")] = "+3V3"
    pruefe("Gegenprobe: Pull-up R701 an +3V3 statt 3V3_SW wird erkannt", not pullup_ok(falsch, h_wert, "R701", "4,7k"))
    for ref in ("D701", "D702"):
        pruefe("ESD %s ist ESDS304, GND an Pin 2" % ref,
               h_wert.get(ref, "").startswith("ESDS304") and h_pin.get((ref, "2")) == "GND", (h_wert.get(ref), h_pin.get((ref, "2"))))
    pruefe("ESD D702 schützt SDA, SCL und 3V3_SW an J703",
           {h_pin.get(("D702", p)) for p in ("1", "3", "4")} == {"I2C_SDA", "I2C_SCL", "3V3_SW"})
    pruefe("ESD D701 schützt DQ und 3V3_SW an J701/J702", {h_pin.get(("D701", p)) for p in ("1", "3")} == {"ONEWIRE", "3V3_SW"})
    pruefe("J703 Pin 6 frei (Verwechslungsschutz)", h_pin.get(("J703", "6"), "unconnected").startswith("unconnected"),
           h_pin.get(("J703", "6")))
    pol = {ref: len({p for (r, p) in h_pin if r == ref}) for ref in ("J201", "J701", "J601", "J501", "J703")}
    pruefe("Sensoranschlüsse mit eigener Polzahl/Bauform (Solar 2, DS18B20 3, Wägezelle 5, BME280 6, Mikrofone 1–3 RJ45 8 + Schirm)",
           pol == {"J201": 2, "J701": 3, "J601": 9, "J501": 5, "J703": 6}, pol)
    for ref in ("J501", "J601", "J701", "J702", "J703", "J201", "J202"):
        pruefe("%s: Pin 1 an GND (Masse/Schirm an Pin 1)" % ref, h_pin.get((ref, "1")) == "GND", h_pin.get((ref, "1")))
    for nr, netz in (("9", "BLE_RXD"), ("10", "BLE_TXD"), ("11", "BLE_MODE")):
        pruefe("J704 Pin %s = %s (HW-09: BLE-Modul; vorher frei)" % (nr, netz), h_pin.get(("J704", nr)) == netz, h_pin.get(("J704", nr)))
    pruefe("J704 Pin 12 = GND neben Pin 11 (Testmodus-Brücke)", h_pin.get(("J704", "12")) == "GND", h_pin.get(("J704", "12")))


def ble(h, h_pin, h_wert):
    """HW-09: BLE-Modul RN4871 an USART6, Versorgung über Q301 (PB13), Modul-UART und Modus an J704 Pin 9–11;
    USB-C-Buchse entfällt (Ladepads J301). Regeln: kein Pull-up des abgeschalteten Moduls an +3V3 (Rückspeisung), Reihenwiderstände
    im UART, Lastschalter aus bei hochohmigem PB13."""
    genau(h, "BLE_EIN", {("U301", "26"), ("Q301", "1"), ("R309", "2")})                 # PB13 → Gate
    pruefe("R309 (Gate-Pull-up) an +3V3, 100k: Modul aus bei hochohmigem PB13",
           h_pin.get(("R309", "1")) == "+3V3" and h_wert.get("R309") == "100k", (h_pin.get(("R309", "1")), h_wert.get("R309")))
    pruefe("Q301 ist AO3401A (P-Kanal), Source an +3V3", h_wert.get("Q301", "").startswith("AO3401") and h_pin.get(("Q301", "2")) == "+3V3",
           (h_wert.get("Q301"), h_pin.get(("Q301", "2"))))
    genau(h, "BLE_VCC", {("Q301", "3"), ("U303", "14"), ("C314", "1"), ("C315", "1"), ("R312", "1"), ("R313", "1"), ("JP301", "1")})
    pruefe("R313 (Entladung BLE_VCC) 100k nach GND", h_pin.get(("R313", "2")) == "GND" and h_wert.get("R313") == "100k", (h_pin.get(("R313", "2")), h_wert.get("R313")))
    pruefe("JP301 (BLE dauernd) ist offene Lötbrücke", "_Open_" in h_wert.get("JP301:footprint", ""), h_wert.get("JP301:footprint"))
    pruefe("U303 ist RN4871", h_wert.get("U303", "").startswith("RN4871"), h_wert.get("U303"))
    genau(h, "USART6_TX", {("U301", "32"), ("R310", "1")})                              # PA11 (AF8)
    genau(h, "USART6_RX", {("U301", "33"), ("R311", "1")})                              # PA12 (AF8)
    genau(h, "BLE_RXD", {("R310", "2"), ("U303", "7"), ("J704", "9")})
    genau(h, "BLE_TXD", {("R311", "2"), ("U303", "8"), ("J704", "10")})
    genau(h, "BLE_MODE", {("R312", "2"), ("U303", "16"), ("J704", "11")})
    genau(h, "BLE_RST", {("U303", "10"), ("C316", "1")})
    for ref, soll in (("R310", "1k"), ("R311", "1k"), ("R312", "10k")):
        pruefe("Wert %s = %s" % (ref, soll), h_wert.get(ref) == soll, h_wert.get(ref))
    for pin in ("2", "13"):
        pruefe("U303 Pin %s an GND" % pin, h_pin.get(("U303", pin)) == "GND", h_pin.get(("U303", pin)))
    for pin in ("1", "3", "4", "5", "6", "9", "11", "12", "15"):
        pruefe("U303 Pin %s offen (intern hochgezogen)" % pin, h_pin.get(("U303", pin), "unconnected").startswith("unconnected"),
               h_pin.get(("U303", pin)))
    def nur_ble_vcc(pin_netz):
        """Alle Pull-ups am Modul hängen an BLE_VCC, keiner an +3V3 (sonst Rückspeisung ins abgeschaltete Modul)."""
        return all(pin_netz.get((r, "1")) == "BLE_VCC" for r in ("R312",))
    pruefe("Pull-up R312 an BLE_VCC, nicht +3V3 (keine Rückspeisung ins abgeschaltete Modul)", nur_ble_vcc(h_pin), h_pin.get(("R312", "1")))
    falsch = dict(h_pin)
    falsch[("R312", "1")] = "+3V3"
    pruefe("Gegenprobe: R312 an +3V3 wird erkannt", not nur_ble_vcc(falsch))
    # Ladepads statt USB-C (HW-09, Philipp): J301 nur GND und VBUS → D203; kein USBLC6, kein VBUS-Teiler, keine CC-Widerstände
    genau(h, "VBUS", {("J301", "2"), ("D203", "2")})
    pruefe("J301 Pin 1 = GND (Masse an Pin 1)", h_pin.get(("J301", "1")) == "GND", h_pin.get(("J301", "1")))
    pruefe("J301 ist 1 × 2 (nur zwei Pads)", len({p for (r, p) in h_pin if r == "J301"}) == 2)
    pruefe("kein USB mehr: U302, R303, R304, R307, R308 entfallen", not any(r in h_wert for r in ("U302", "R303", "R304", "R307", "R308")))


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
    h, h_pin, h_wert = lade("logger.net")

    # --- Vollständiger Vergleich Modell ↔ gezeichneter Schaltplan ---
    vollstaendig("hauptplatine", h, "logger.net")

    # --- Blatt Akku (HW-06; bis 14.10.2026 eigene Akku-Platine): Zellschutz im Minuspfad ---
    genau(h, "B-", {("BT801", "2"), ("U801", "6"), ("C801", "2"), ("Q801", "1")})
    genau(h, "B+", {("BT801", "1"), ("JP801", "1"), ("J801", "1"), ("R801", "1")})
    genau(h, "D12", {("Q801", "2"), ("Q801", "5")})
    enthaelt(h, "GND", {("Q801", "3"), ("R802", "2"), ("U802", "3"), ("U803", "3"), ("Q802", "2"), ("Q803", "2")})
    pruefe("Zelle B− ist nicht GND (Schutz-FET Q801 im Minuspfad, B− nur als Insel)",
           h_pin.get(("BT801", "2")) == "B-" and ("BT801", "2") not in h.get("GND", set()))
    # SCH26-01: Ladesperre nur an TMP_VCC/GND (P−), keine Verbindung zu B+/B−/VBAT
    genau(h, "TMP_VCC", {("U204", "5"), ("C212", "1"), ("U802", "5"), ("U803", "5"), ("C802", "1"), ("C803", "1"),
                         ("R805", "1"), ("R808", "1")})
    for ref in ("U802", "U803", "Q802", "Q803", "R805", "R808"):
        netze_ref = {n for (r, _), n in h_pin.items() if r == ref}
        pruefe("%s ohne Verbindung zu B+/B−/VBAT (SCH26-01)" % ref, not (netze_ref & {"B+", "B-", "VBAT"}), netze_ref)
    # Stufe 1: TMP390 U802 → Q802 → CE des BQ25185
    genau(h, "GATE_CE", {("U802", "6"), ("U802", "4"), ("R805", "2"), ("Q802", "1")})
    genau(h, "CE_LADEN", {("U201", "4"), ("R205", "2"), ("C206", "1"), ("Q802", "3")})
    # Stufe 2: TMP390 U803 → Q803 im NTC-Fuß → TS des BQ25185
    genau(h, "GATE_NTC", {("U803", "6"), ("R808", "2"), ("Q803", "1")})
    genau(h, "NTC", {("U201", "6"), ("TH801", "1")})
    genau(h, "NTC_FUSS", {("TH801", "2"), ("Q803", "3")})
    pruefe("U803 OUTB offen", ("U803", "4") not in h_pin or h_pin[("U803", "4")].startswith("unconnected"), h_pin.get(("U803", "4")))
    for ref, soll in (("R803", "2,49k 1%"), ("R804", "18,7k 1%"), ("R806", "2,49k 1%"), ("R807", "18,7k 1%"),
                      ("R802", "2k"), ("R801", "100")):
        pruefe("Wert %s = %s" % (ref, soll), h_wert.get(ref) == soll, h_wert.get(ref))
    enthaelt(h, "VBAT", {("U201", "2"), ("JP801", "2"), ("J801", "2"), ("C205", "1"), ("R206", "1")})
    # --- HW-09: BLE-Modul RN4871 (mcu-funk.md 1.6) -----------------------------------------------
    ble(h, h_pin, h_wert)

    # --- Hauptplatine: Lader ---
    pruefe("U204 IN an VIN_LADER", h_pin.get(("U204", "1")) == "VIN_LADER", h_pin.get(("U204", "1")))
    pruefe("R205 (CE-Pull-up) an SYS", h_pin.get(("R205", "1")) == "SYS", h_pin.get(("R205", "1")))
    for ref, soll in (("R203", "2,0k 1%"), ("R204", "130k 1%"), ("R205", "100k"), ("R208", "100k"), ("R201", "3,3M"), ("R202", "470k")):
        pruefe("Wert %s = %s" % (ref, soll), h_wert.get(ref) == soll, h_wert.get(ref))
    genau(h, "SENSOR_EIN", {("U203", "3"), ("R208", "1"), ("U301", "11")})  # PA1 (HW-07, vorher PB5)
    pruefe("TPS22917 CT-Kondensator nach VIN (+3V3)", h_pin.get(("C210", "2")) == "+3V3" and h_pin.get(("C210", "1")) == "SW_CT")

    # --- Debug-Stecker J302 (SCH26-09): je Pin ---
    for pin, netz in (("1", "+3V3"), ("2", "SWDIO"), ("3", "SWCLK"), ("4", "NRST"), ("5", "GND"), ("6", "DBG_TX"), ("7", "DBG_RX")):
        pruefe("J302 Pin %s = %s" % (pin, netz), h_pin.get(("J302", pin)) == netz, h_pin.get(("J302", pin)))
    genau(h, "DBG_TX", {("J302", "6"), ("J704", "7"), ("U301", "30")})   # PA9, auch an J11
    genau(h, "DBG_RX", {("J302", "7"), ("J704", "8"), ("U301", "31")})   # PA10, auch an J11
    # --- Ra-01SH TXEN/RXEN (SCH26-11): TXEN ist im Modul DIO2 → Lötbrücken offen, nur über Brücke an PB14/PB15 ---
    for jp, mod, mcu_netz, pin in (("JP401", "TXEN_MOD", "LORA_TXEN", "5"), ("JP402", "RXEN_MOD", "LORA_RXEN", "11")):
        pruefe("%s ist offene Lötbrücke" % jp, "_Open_" in h_wert.get(jp + ":footprint", ""), h_wert.get(jp + ":footprint"))
        genau(h, mod, {("U401", pin), (jp, "1")})
    pruefe("Ra-01SH DIO2 ohne Verbindung", h_pin.get(("U401", "7"), "unconnected").startswith("unconnected"), h_pin.get(("U401", "7")))
    # --- Waage (SCH26-07) ---
    waage(h, h_pin, h_wert)
    # --- Mikrofon (SCH26-07, seit HW-07 Audio-ADC) ---
    mikrofon(h, h_pin, h_wert)
    # --- Anschlüsse (SCH26-07) ---
    anschluesse(h, h_pin, h_wert)
    # --- Stecker: anschluesse.md ↔ Netzliste ---
    stecker_gegen_doku(h_pin)

    print("%d von %d Netzprüfungen bestanden" % (ANZ - FEHL, ANZ))
    return 1 if FEHL else 0


if __name__ == "__main__":
    sys.exit(main())
