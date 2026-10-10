#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Modell des HF-Schalters im Ra-01SH und Funkstrecke zum Gateway (SCH26-11). Teststufe T2 (Rechenmodell).

Teil 1 – Schaltlogik nach dem Herstellerschaltbild (Ai-Thinker Ra-01SH Specification V1.1, Kap. 5, S. 12):
  DIO2 ─ R8 0 Ω ─ TX_EN (= Modulpin 5 „TXEN“)
  TX_EN ─ R6 10 kΩ ─ CTRL (U2 Pin 4)
  TX_EN ─ R5 1 kΩ ─ Basis Q1 (NPN); Kollektor = /CTRL (U2 Pin 6), R7 1 MΩ nach 3,3 V
  RX_EN (= Modulpin 11) ─ R1 „NC/10K“ ─ /CTRL      (Grundbestückung: R1 nicht bestückt)
  Hinweis im Schaltbild: DIO2 = 1 → RFC an RF1 (Senden); DIO2 = 0 → RFC an RF2 (Empfang).
  Unser Schaltplan: TXEN über JP401 an PB14, RXEN über JP402 an PB15, beide Brücken offen (mcu-funk.md 2.1).

Teil 2 – Funkstrecke (Friis) mit und ohne falsch stehenden HF-Schalter. Annahmen sind mit [A] markiert.

Aufruf: python3 hardware/funk_modell.py   (Exit 1, wenn die Soll-Konfiguration nicht funktioniert)
"""
import math
import sys

VDD = 3.3
# --- Annahmen für Treiberwiderstände (nur Größenordnung, [A]) -------------------------------------------
R_MCU = 50.0     # STM32 GPIO: VOL 0,4 V bei 8 mA → ca. 50 Ω [A, aus ST-Datenblatt-Größenordnung]
R_DIO = 100.0    # SX126x DIO-Ausgang, nicht im Ai-Thinker-Blatt angegeben [A]
I_GPIO_MAX = 8.0  # mA, Auslegungsgrenze eines Standard-GPIO [A]


def schalter(dio2, jp401, pb14, jp402, pb15, r1_bestueckt=False):
    """Ein Betriebszustand. dio2: 0, 1 oder 'Z' (vom Funkchip nicht getrieben).
    pb14/pb15: 'ein' (Eingang/hochohmig), 0 oder 1 (Ausgang). Ergebnis: (Schalterstellung, Konfliktstrom mA, Hinweis)."""
    konflikt = 0.0
    hinweis = []
    # Knoten TX_EN: DIO2 über 0 Ω, PB14 über JP401
    treiber = []
    if dio2 in (0, 1):
        treiber.append(("DIO2", dio2, R_DIO))
    if jp401 and pb14 in (0, 1):
        treiber.append(("PB14", pb14, R_MCU))
    pegel = {t[1] for t in treiber}
    if len(pegel) > 1:
        konflikt = VDD / sum(t[2] for t in treiber) * 1000
        hinweis.append("DIO2 und PB14 treiben gegeneinander")
        tx_en = None                       # Zwischenpegel, undefiniert
    elif pegel:
        tx_en = pegel.pop()
    else:
        tx_en = None
        hinweis.append("TX_EN offen (kein Treiber)")
    ctrl = tx_en                           # über R6 10 kΩ an einen hochohmigen Steuereingang
    # /CTRL: Q1 leitet, wenn TX_EN high; sonst R7 1 MΩ nach 3,3 V; R1 (falls bestückt) von RX_EN
    if tx_en == 1:
        nctrl = 0
    elif r1_bestueckt and jp402 and pb15 == 0:
        nctrl = 0                          # 10 kΩ gegen 1 MΩ zieht /CTRL nach unten
        hinweis.append("PB15 low zieht /CTRL über R1 herunter")
    elif tx_en == 0:
        nctrl = 1
    else:
        nctrl = None
    if (ctrl, nctrl) == (1, 0):
        stellung = "Senden (RF1)"
    elif (ctrl, nctrl) == (0, 1):
        stellung = "Empfangen (RF2)"
    else:
        stellung = "undefiniert"
    return stellung, konflikt, "; ".join(hinweis)


# Konfigurationen: (Name, Bestückung/Firmware, Funktion: Phase → Eingänge)
def dio2_rf(phase):          # setDio2AsRfSwitch(true): DIO2 high nur beim Senden
    return 1 if phase == "TX" else 0


KONFIG = [
    ("K1 Soll: JP401/JP402 offen, setDio2AsRfSwitch(true)",
     lambda ph: dict(dio2=dio2_rf(ph), jp401=False, pb14="ein", jp402=False, pb15="ein"), True),
    ("K2 DIO2-Schalter in der Firmware vergessen (DIO2 bleibt low [A])",
     lambda ph: dict(dio2=0, jp401=False, pb14="ein", jp402=False, pb15="ein"), False),
    ("K3 JP401 zu, PB14 nur Eingang (Sendeanzeige mitlesen)",
     lambda ph: dict(dio2=dio2_rf(ph), jp401=True, pb14="ein", jp402=False, pb15="ein"), True),
    ("K4 JP401 zu, PB14 als Ausgang low (z. B. unbenutzter Pin)",
     lambda ph: dict(dio2=dio2_rf(ph), jp401=True, pb14=0, jp402=False, pb15="ein"), False),
    ("K5 JP401/JP402 zu, setRfSwitchPins(PB15, PB14) und DIO2-Schalter",
     lambda ph: dict(dio2=dio2_rf(ph), jp401=True, pb14=1 if ph == "TX" else 0, jp402=True,
                     pb15=0 if ph == "TX" else 1), None),
    ("K6 Modul mit R1 = 10 kΩ, JP402 zu, PB15 low im Empfang",
     lambda ph: dict(dio2=dio2_rf(ph), jp401=False, pb14="ein", jp402=True, pb15=0, r1_bestueckt=True), False),
]
SOLL = {"Schlaf": "Empfangen (RF2)", "RX": "Empfangen (RF2)", "TX": "Senden (RF1)"}


def teil1():
    print("Teil 1 – HF-Schalter Ra-01SH nach Herstellerschaltbild (V1.1, S. 12)")
    print("  Grundlast im Senden: DIO2 speist die Basis von Q1 über 1 kΩ ≈ %.1f mA [Vbe 0,75 V A]; im Schlaf 0 mA"
          % ((VDD - 0.75) / 1.0))
    ok_soll = True
    for name, eingaenge, erwartet_ok in KONFIG:
        print("  " + name)
        alles_ok, max_konflikt = True, 0.0
        for phase in ("Schlaf", "RX", "TX"):
            st, i, h = schalter(**eingaenge(phase))
            richtig = st == SOLL[phase]
            alles_ok &= richtig and i == 0.0
            max_konflikt = max(max_konflikt, i)
            print("     %-6s → %-16s %s%s" % (phase, st, "" if richtig else "FALSCH ",
                                            ("Konflikt ≈ %.0f mA [A] " % i if i else "") + h))
        if name.startswith("K5"):
            print("     Dauerzustände gleich; an den Umschaltflanken treiben DIO2 und PB14 kurz gegeneinander "
                  "(Reihenfolge in RadioLib/Funkchip nicht belegt) [A] → vermeiden")
        if max_konflikt > I_GPIO_MAX:
            print("     ⚠ Konfliktstrom über %.0f mA: Gefahr für DIO2/PB14" % I_GPIO_MAX)
        if erwartet_ok is True and not alles_ok:
            ok_soll = False
        print("     Ergebnis: %s" % ("in Ordnung" if alles_ok else "NICHT in Ordnung"))
    return ok_soll


# --- Teil 2: Funkstrecke ------------------------------------------------------------------------------
F_HZ = 868.1e6
P_TX = 14.0                  # dBm, EU868-Grenze 25 mW ERP
G_TX = 1.8                   # dBi FPC-Antenne Taoglas FXP280 (mcu-funk.md 2.3) [V]
G_GW = 2.0                   # dBi Gateway-Antenne RAK7268V2 innen [A]
L_KABEL = 1.0                # dB IPEX/Kabel [A]
L_WEG = (10.0, 25.0)         # dB Hauswand/Dach/Bewuchs zum Gateway, Spanne [A]
L_DECKEL = (0.0, 10.0)       # dB Blechdeckel der Beute 3–10 dB (Antenova, mcu-funk.md 2.3) [V], 0 = ohne
EMPF_SF7 = -125.0            # dBm Gateway-Empfindlichkeit SF7/125 kHz, Größenordnung [A]
ISOLATION = (20.0, 35.0)     # dB Isolation eines SPDT-Schalters in falscher Stellung [A, Typ unbekannt]
SATT = -30.0                 # dBm: darüber RSSI-Werte am Gateway nicht mehr verlässlich (Übersteuerung) [A]


def fspl(d_m):
    return 20 * math.log10(d_m) + 20 * math.log10(F_HZ) - 147.55


def rssi(d_m, p_tx, verlust):
    return p_tx + G_TX + G_GW - L_KABEL - fspl(d_m) - verlust


def teil2():
    print("\nTeil 2 – Funkstrecke Logger → Gateway (Friis, 868,1 MHz)")
    print("  Freiraumdämpfung: 5 m %.1f dB, 8 m %.1f dB" % (fspl(5), fspl(8)))
    print("  %-44s %8s %18s %14s" % ("Fall", "Abstand", "RSSI [dBm]", "Reserve [dB]"))
    zeilen = []
    for p_tx, ptext in ((14.0, "+14 dBm"), (-9.0, "−9 dBm (SX1262-Minimum)")):
        for d in (5, 8):
            for falsch in (False, True):
                v_min = L_WEG[0] + L_DECKEL[0] + (ISOLATION[0] if falsch else 0)
                v_max = L_WEG[1] + L_DECKEL[1] + (ISOLATION[1] if falsch else 0)
                r_hi, r_lo = rssi(d, p_tx, v_min), rssi(d, p_tx, v_max)
                fall = "%s, Schalter %s" % (ptext, "falsch" if falsch else "richtig")
                zeilen.append((fall, d, r_lo, r_hi))
                print("  %-44s %6d m %8.0f … %5.0f %7.0f … %4.0f" % (fall, d, r_lo, r_hi, r_lo - EMPF_SF7, r_hi - EMPF_SF7))
    schlecht = [z for z in zeilen if "+14" in z[0] and "falsch" in z[0]]
    print("  Folgerung:")
    if all(z[2] > EMPF_SF7 for z in schlecht):
        print("   - Selbst mit falsch stehendem HF-Schalter bleibt bei +14 dBm Reserve. „Verbindung geht“ beweist")
        print("     am Stand also NICHT, dass der Schalter richtig steht.")
    if any(z[3] > SATT for z in zeilen if "+14" in z[0]):
        print("   - Bei +14 dBm kann der Gateway-Empfänger in die Sättigung kommen; RSSI-Vergleiche dann verfälscht.")
    print("   - Prüfung daher mit kleiner Sendeleistung (z. B. −9 dBm) und RSSI-Vergleich zum RFM95-Musterlogger")
    print("     am selben Platz, dazu die direkte Pegelmessung an DIO2/TXEN (Prüfplan F-3).")


def main():
    ok = teil1()
    teil2()
    print("\nSoll-Konfiguration K1 %s" % ("funktioniert im Modell" if ok else "FUNKTIONIERT NICHT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
