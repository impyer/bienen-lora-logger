#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""SPICE-Prüfung ausgewählter Analogpfade der Hauptplatine (T2, Modell – keine Messung).

Nutzt die ngspice-Bibliothek, die KiCad 10 mitbringt (Windows: ngspice.dll im KiCad-bin, Linux: libngspice.so.0 aus
dem Paket libngspice0). Jede Simulation nennt Quelle und Status der Modellwerte: [V] Datenblatt, [A] Annahme.
Ergebnis je Prüfung: ok / FEHL gegen eine Grenze; Exit 1 bei einer Abweichung, Exit 0 mit „ÜBERSPRUNGEN“, wenn keine
ngspice-Bibliothek gefunden wird (dann gilt die Prüfung als nicht gelaufen, nicht als bestanden).

Aufruf: python3 hardware/schaltplan_spice.py            (auch in der CI, Job hardware-rechnungen)
        python3 hardware/schaltplan_spice.py --zeige    (zusätzlich die Kennlinien als Tabelle)
Stand 18.10.2026: Blatt Mikrofon (Elektretpfad), Blatt Waage (AVDD-Regler), Blatt MCU (BLE-Lastschalter, RN4871-Reset),
Blatt Versorgung (ADC-Teiler, Sensorschiene), Blatt Anschlüsse (1-Wire).
"""
import ctypes
import ctypes.util
import glob
import math
import os
import sys

ZEIGE = "--zeige" in sys.argv
ANZ = FEHL = 0


# ---------------------------------------------------------------------------
# ngspice über die Shared Library (API: ngSpice_Init, ngSpice_Command, ngGet_Vec_Info)
# ---------------------------------------------------------------------------
def finde_bibliothek():
    kandidaten = []
    if sys.platform == "win32":
        kandidaten += glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Programs\KiCad\*\bin\ngspice.dll"))
        kandidaten += glob.glob(r"C:\Program Files\KiCad\*\bin\ngspice.dll")
    else:
        for name in ("ngspice", "libngspice.so.0"):
            p = ctypes.util.find_library(name)
            if p:
                kandidaten.append(p)
        kandidaten += glob.glob("/usr/lib/*/libngspice.so.0") + glob.glob("/usr/lib/libngspice.so.0")
    for k in kandidaten:
        if os.path.exists(k) or not os.path.isabs(k):
            return k
    return None


class NgSpice:
    def __init__(self, pfad):
        if sys.platform == "win32":
            os.add_dll_directory(os.path.dirname(pfad))
        self.ng = ctypes.CDLL(pfad)
        self.log = []
        SendChar = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
        SendStat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
        Exit = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
        Data = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
        Init = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
        BG = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
        self._cb = (SendChar(lambda s, i, u: self.log.append(s.decode("utf-8", "replace")) or 0),
                    SendStat(lambda s, i, u: 0), Exit(lambda a, b, c, d, u: 0), Data(lambda p, n, i, u: 0),
                    Init(lambda p, i, u: 0), BG(lambda r, i, u: 0))
        self.ng.ngSpice_Init(*self._cb, None)
        self.ng.ngSpice_Command.argtypes = [ctypes.c_char_p]

        class VecInfo(ctypes.Structure):
            _fields_ = [("v_name", ctypes.c_char_p), ("v_type", ctypes.c_int), ("v_flags", ctypes.c_short),
                        ("v_realdata", ctypes.POINTER(ctypes.c_double)), ("v_compdata", ctypes.c_void_p),
                        ("v_length", ctypes.c_int)]

        class Cx(ctypes.Structure):
            _fields_ = [("re", ctypes.c_double), ("im", ctypes.c_double)]
        self._VecInfo, self._Cx = VecInfo, Cx
        self.ng.ngGet_Vec_Info.restype = ctypes.POINTER(VecInfo)
        self.ng.ngGet_Vec_Info.argtypes = [ctypes.c_char_p]
        self.version = next((z for z in self.log if "ngspice" in z.lower()), "ngspice")

    def lauf(self, netzliste, name):
        """Netzliste als Datei schreiben, laden, rechnen. Rückgabe: Funktion vek(name)."""
        ordner = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__pycache__")
        os.makedirs(ordner, exist_ok=True)
        pfad = os.path.join(ordner, name + ".cir")
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(netzliste)
        self.log.clear()
        self.ng.ngSpice_Command(b"destroy all")
        self.ng.ngSpice_Command(("source " + pfad).encode())
        self.ng.ngSpice_Command(b"run")
        fehler = [z for z in self.log if "error" in z.lower() and "no error" not in z.lower()]
        if fehler:
            raise RuntimeError("ngspice: " + " | ".join(fehler[:3]))
        return self.vek

    def vek(self, name):
        p = self.ng.ngGet_Vec_Info(name.encode())
        if not p:
            raise KeyError("Vektor %s fehlt" % name)
        v = p.contents
        if v.v_realdata:
            return [v.v_realdata[i] for i in range(v.v_length)]
        arr = ctypes.cast(v.v_compdata, ctypes.POINTER(self._Cx))
        return [complex(arr[i].re, arr[i].im) for i in range(v.v_length)]


def pruefe(text, ok, ist):
    global ANZ, FEHL
    ANZ += 1
    FEHL += 0 if ok else 1
    print(("ok   - " if ok else "FEHL - ") + text + "  [%s]" % ist)


def bei(xs, x):
    """Index des Stützpunkts, der x am nächsten liegt."""
    return min(range(len(xs)), key=lambda i: abs((xs[i].real if isinstance(xs[i], complex) else xs[i]) - x))


def db(z):
    return 20 * math.log10(abs(z)) if abs(z) > 0 else -999.0


# ---------------------------------------------------------------------------
# S1 Elektretpfad (Blatt Mikrofon): Kapsel pseudo-differenziell über 2 × 1 kΩ an MICBIAS/GND,
#    100 pF an der Buchse, 1 µF Koppel-C, ADC-Eingang ca. 35 kΩ [V: TI SLAS553B 10.3.10, PGA-Eingangswiderstand] [A: 35 kΩ]
#    Kapsel als JFET-Quelle: Ausgangswiderstand 2,2 kΩ, Ruhestrom 0,3 mA [A]
# ---------------------------------------------------------------------------
def s1_elektret(ng):
    netz = """Elektret pseudo-differenziell (Blatt Mikrofon, Elektret 1 und 3 gleich)
Vbias micbias 0 dc 2.5
Cbias micbias 0 1u
R610 micbias micp 1k
R611 micn 0 1k
* Kapsel: Signalquelle 1 V (AC) mit 2,2 kOhm Innenwiderstand zwischen MIC+ und MIC-, parallel dazu der Ruhestrom 0,3 mA
Vsig micp sig1 dc 0 ac 1
Rsig sig1 sigc 2.2k
Cser sigc micn 1
Ibias micp micn dc 0.3m
C622 micp 0 100p
C623 micn 0 100p
C619 micp inp 1u
C620 micn inn 1u
Rinp inp 0 35k
Rinn inn 0 35k
.ac dec 20 0.1 10meg
.end
"""
    v = ng.lauf(netz, "s1_elektret")
    f = [x.real for x in v("frequency")]
    h = [a - b for a, b in zip(v("v(inp)"), v("v(inn)"))]
    g1k = db(h[bei(f, 1000)])
    f3 = next((f[i] for i in range(len(f)) if db(h[i]) >= g1k - 3), None)
    fo = next((f[i] for i in range(len(f)) if f[i] > 1000 and db(h[i]) <= g1k - 3), None)
    g3m = db(h[bei(f, 3.146e6)])
    print("S1 Elektretpfad: Durchlass %.2f dB bei 1 kHz (Kapsel 2,2 kΩ gegen 2 × 1 kΩ), untere Grenze %.1f Hz, obere Grenze %.0f kHz, "
          "bei 3,146 MHz %.1f dB gegenüber 1 kHz" % (g1k, f3, fo / 1e3, g3m - g1k))
    pruefe("S1 Hochpass ≤ 20 Hz (Nutzband ab 60 Hz)", f3 is not None and f3 <= 20, "%.1f Hz" % f3)
    pruefe("S1 obere Grenze der 100-pF-Ableitung ≥ 100 kHz (Nutzband bis 900 Hz unverzerrt, Dezimationsfilter im ADC) [A]",
           fo is not None and fo >= 100e3, "%.0f kHz" % (fo / 1e3))
    # Arbeitspunkt: Kapselspannung aus getrenntem DC-Lauf
    netz_dc = netz.replace(".ac dec 20 0.1 10meg\n", ".op\n")
    v = ng.lauf(netz_dc, "s1_elektret_dc")
    ukap = v("v(micp)")[0] - v("v(micn)")[0]
    print("   Arbeitspunkt: Kapselspannung %.2f V bei 0,3 mA (MICBIAS 2,5 V, 2 × 1 kΩ)" % ukap)
    pruefe("S1 Kapselspannung ≥ 1,5 V (übliche Elektretkapsel, mikrofon.md 7.1)", ukap >= 1.5, "%.2f V" % ukap)
    if ZEIGE:
        for fz in (1, 5, 20, 60, 1000, 10000, 3.146e6):
            print("      %10.0f Hz  %7.2f dB" % (fz, db(h[bei(f, fz)])))


# ---------------------------------------------------------------------------
# S2 HX711-AVDD-Regler (Blatt Waage): PNP S8550 als Längsregler, VFB-Teiler 20 kΩ / 8,2 kΩ, VBG 1,25 V [V: HX711 Fig. 1]
#    Regelverstärker als Behavioral-Quelle; Last: Brücke 404 Ω [V Bosche] + HX711 1,5 mA [V]
# ---------------------------------------------------------------------------
def s2_hx711(ng):
    def lauf(bf, r503, r504, vsup):
        netz = """HX711 AVDD-Regler
.model QPNP PNP(IS=1e-14 BF=%g VAF=60)
Vsup vsup 0 dc %g
Q1 avdd base vsup QPNP
Rb ctrl base 10k
* interner Regler (HX711 BASE-Pin): Basis nach unten, wenn VFB < 1,25 V; nach oben (PNP sperrt), wenn VFB > 1,25 V
Eamp ctrl 0 value={%g*0.5*(1 + tanh(2000*(v(fb) - 1.25)))}
R503 avdd fb %g
R504 fb 0 %g
Rbr avdd 0 404
Rhx avdd 0 2.87k
C505 avdd 0 10u
.nodeset v(avdd)=4.3 v(fb)=1.25 v(ctrl)=3.5
.op
.end
""" % (bf, vsup, vsup, r503, r504)
        v = ng.lauf(netz, "s2_hx711")
        return v("v(avdd)")[0], -v("vsup#branch")[0], v("v(ctrl)")[0]
    avdd, isup, ctrl = lauf(150, 20e3, 8.2e3, 5.0)
    print("S2 HX711-AVDD: %.3f V bei VSUP 5,0 V, Strom %.1f mA, Basisansteuerung %.2f V" % (avdd, isup * 1e3, ctrl))
    pruefe("S2 AVDD 4,2–4,4 V und ≥ 0,1 V unter VSUP (HX711-Datenblatt)", 4.2 <= avdd <= 4.4 and 5.0 - avdd >= 0.1, "%.3f V" % avdd)
    # Toleranzen 1 % und hFE-Spanne
    ecken = [lauf(bf, r503, r504, 5.0)[0] for bf in (80, 300) for r503 in (19.8e3, 20.2e3) for r504 in (8.118e3, 8.282e3)]
    print("   Eckwerte (hFE 80–300, Widerstände ±1 %%): %.3f … %.3f V" % (min(ecken), max(ecken)))
    pruefe("S2 AVDD-Eckwerte innerhalb 4,2–4,4 V", min(ecken) >= 4.2 and max(ecken) <= 4.4, "%.3f … %.3f V" % (min(ecken), max(ecken)))
    # Variante ohne 5-V-Wandler: VSUP = 3V3_SW → AVDD muss ≤ VSUP − 0,1 V, Teiler für 3,0 V: 14 k / 10 k [A]
    avdd3, isup3, _ = lauf(150, 14e3, 10e3, 3.3)
    print("   Variante ohne Wandler (VSUP 3,3 V, Teiler 14k/10k): AVDD %.2f V, Strom %.1f mA aus 3V3_SW" % (avdd3, isup3 * 1e3))
    empf = 2e-3 * avdd3                       # Brücke 2 mV/V [A: Bosche H40A]
    print("   Brückensignal bei Nennlast: %.2f mV (statt %.2f mV bei 4,3 V); HX711-Rauschen 50 nV eff [V] → Auflösung %.1f g bzw. %.1f g bei 200 kg" % (
        empf * 1e3, 2e-3 * avdd * 1e3, 50e-9 / empf * 200e3, 50e-9 / (2e-3 * avdd) * 200e3))


# ---------------------------------------------------------------------------
# S3 BLE-Lastschalter (Blatt MCU): Q301 AO3401A schaltet 10 µF + 100 nF an +3V3; Einschaltstromstoß und Einbruch der
#    3,3-V-Schiene (RT9080 als Quelle mit 0,2 Ω Innenwiderstand [A]; Schienenkapazität 2,2 µ + 100 µ + 10 µ + 7 × 100 n [V Generator]).
#    Fall A: Gate direkt von PB13 (Stand bis HW-11, Flanke 20 ns [A]); Fall B (Stand seit HW-11): R314 10 kΩ vor dem Gate
#    und C317 47 nF zwischen Gate und Drain (Miller-Rampe: dU/dt ≈ I_gate / C_gd).
#    AO3401A: VGS(th) −0,9 V, Rds(on) 60 mΩ bei −4,5 V, Ciss ca. 1 nF [V/A: AOS AO3401A]
# ---------------------------------------------------------------------------
def s3_ble_einschalten(ng, rg, cgd):
    netz = """BLE-Lastschalter Einschalten
.model PSW PMOS(LEVEL=1 VTO=-0.9 KP=5 LAMBDA=0.02)
Vldo ldo 0 dc 3.3
Rldo ldo v33 0.2
Crail v33 0 112.9u
Vpb13 pb13x 0 pwl(0 3.3 10u 3.3 10.02u 0)
Rg pb13x gate %g
Cgs gate v33 1n
Cgd gate blevcc %g
R309 v33 gate 100k
M1 blevcc gate v33 v33 PSW
C314 blevcc 0 10u
C315 blevcc 0 100n
R313 blevcc 0 100k
Rmod blevcc 0 330
.tran 0.05u 2m
.end
""" % (rg, cgd)
    v = ng.lauf(netz, "s3_ble_%g" % rg)
    t = v("time")
    v33 = v("v(v33)")
    i = v("vldo#branch")
    umin = min(v33)
    imax = max(abs(x) for x in i)
    return umin, imax, t, v33


def s3(ng):
    ua, ia, _, _ = s3_ble_einschalten(ng, 1, 1e-12)
    ub, ib_, _, _ = s3_ble_einschalten(ng, 10e3, 47e-9)
    print("S3 BLE einschalten: ohne Sanftanlauf (bis HW-11) +3V3-Minimum %.2f V, Spitzenstrom aus der Schiene %.0f mA; "
          "mit R314 10 kΩ + C317 47 nF (Stand): %.2f V und %.0f mA" % (ua, ia * 1e3, ub, ib_ * 1e3))
    pruefe("S3 Sanftanlauf R314/C317 begrenzt den Spitzenstrom auf ≤ 300 mA [A]", ib_ <= 0.3, "%.0f mA" % (ib_ * 1e3))
    pruefe("S3 +3V3 bleibt ≥ 3,2 V beim Einschalten des Moduls (Stand mit Sanftanlauf) [A]", ub >= 3.2, "%.2f V" % ub)


# ---------------------------------------------------------------------------
# S4 RN4871-Reset und Abschalten: interner Pull-up 34–74 kΩ [V: DS50002489D Tab. 2-2] mit C316 100 nF;
#    Entladung von BLE_VCC über R313 100 kΩ nach dem Abschalten
# ---------------------------------------------------------------------------
def s4_reset(ng):
    aus = []
    for rpu in (34e3, 48e3, 74e3):
        netz = """RN4871 RST_N Anlauf
Vcc vcc 0 pwl(0 0 1u 3.3)
Rpu vcc rst %g
C316 rst 0 100n
.tran 10u 30m
.end
""" % rpu
        v = ng.lauf(netz, "s4_reset")
        t, r = v("time"), v("v(rst)")
        t70 = next(t[i] for i in range(len(t)) if r[i] >= 0.7 * 3.3)
        aus.append(t70)
    print("S4 RN4871 RST_N erreicht 0,7·VDD nach %.1f / %.1f / %.1f ms (Pull-up 34/48/74 kΩ, C316 100 nF)" % tuple(x * 1e3 for x in aus))
    pruefe("S4 Reset-Verzögerung 1–10 ms (Versorgung stabil, vor dem 68-ms-Anlauf des Moduls) [A]", 1e-3 <= min(aus) and max(aus) <= 10e-3, "%.1f–%.1f ms" % (aus[0] * 1e3, aus[-1] * 1e3))
    netz = """BLE_VCC Entladung über R313
Vsw sw 0 pwl(0 3.3 1m 3.3 1.001m 0)
Rsw sw blevcc 1e9
Cinit blevcc 0 10.1u ic=3.3
R313 blevcc 0 100k
.tran 1m 5 uic
.end
"""
    v = ng.lauf(netz, "s4_entladung")
    t, u = v("time"), v("v(blevcc)")
    t03 = next(t[i] for i in range(len(t)) if u[i] <= 0.3)
    print("   BLE_VCC fällt nach dem Abschalten in %.1f s unter 0,3 V (R313 100 kΩ, 10,1 µF)" % t03)
    pruefe("S4 Aus-Zustand nach ≤ 5 s definiert (kurzer Aus-Ein-Zyklus als Reset) [A]", t03 <= 5, "%.1f s" % t03)


# ---------------------------------------------------------------------------
# S5 ADC-Teiler (Blatt Versorgung): Fehler durch Eingangsleckstrom des STM32 an hochohmigen Teilern
#    Akku 2 × 2,2 MΩ (R_th 1,1 MΩ), Solar 3,3 MΩ / 470 kΩ (R_th 411 kΩ); Leckstrom: typisch wenige 10 nA [A], Datenblatt-
#    Maximum ±1 µA [P: ST DS10314 Ilkg] – reine Rechnung, hier zur Einordnung
# ---------------------------------------------------------------------------
def s5_teiler():
    for name, rth, faktor in (("Akku 2,2 MΩ / 2,2 MΩ", 1.1e6, 2.0), ("Solar 3,3 MΩ / 470 kΩ", 3.3e6 * 470e3 / (3.3e6 + 470e3), 1 / 0.1247)):
        for ilkg in (50e-9, 1e-6):
            fehl = ilkg * rth * faktor
            print("S5 %s: Leckstrom %4.0f nA → Fehler an der Quelle %.2f V" % (name, ilkg * 1e9, fehl))
    fehl_typ = 50e-9 * 1.1e6 * 2
    pruefe("S5 Akkumessfehler bei 50 nA Leckstrom ≤ 0,15 V (Schwellen 3,3/3,5 V in der Firmware) [A]", fehl_typ <= 0.15, "%.2f V" % fehl_typ)
    print("   Hinweis: beim Datenblatt-Maximum 1 µA wären es 2,2 V – Teiler im Betrieb mit Referenzspannung kalibrieren oder niederohmiger geschaltet speisen (Bericht).")


# ---------------------------------------------------------------------------
# S6 Sensorschiene (Blatt Versorgung): TPS22917 mit CT 1 nF – Anstieg laut Datenblatt ca. 3,8 µs/pF bei 3,6 V [V: Tab. tON]
#    → tON ≈ 3,8 ms; Einschaltstrom in die Schienenkapazität ca. 30 µF [V Generator: C211 1 µ, C601 22 µ, C609 1 µ, C616/617, C624, C508 …]
# ---------------------------------------------------------------------------
def s6_sensorschiene():
    ton = 3.8e-6 * 1000 + 120e-6
    c = 30e-6
    i = c * 3.3 / ton
    print("S6 Sensorschiene: Anstieg ca. %.1f ms, Einschaltstrom in %.0f µF ca. %.0f mA" % (ton * 1e3, c * 1e6, i * 1e3))
    pruefe("S6 Einschaltstrom der Sensorschiene ≤ 200 mA (RT9080 600 mA, LoRa-Puffer bleibt geladen) [A]", i <= 0.2, "%.0f mA" % (i * 1e3))


# ---------------------------------------------------------------------------
# S7 1-Wire (Blatt Anschlüsse): Pull-up 4,7 kΩ an 3V3_SW, Kabel bis 10 m à 50 pF/m + 2 Sensoren 25 pF [A]; Anstieg bis 0,7·VDD
# ---------------------------------------------------------------------------
def s7_onewire(ng):
    netz = """1-Wire Anstieg
V33 v33 0 dc 3.3
R701 v33 dq 4.7k
Cbus dq 0 550p
Sdrv dq 0 ctl 0 SW
Vctl ctl 0 pwl(0 1 5u 1 5.01u 0)
.model SW SW(RON=50 ROFF=1e9 VT=0.5)
.tran 10n 30u
.end
"""
    v = ng.lauf(netz, "s7_onewire")
    t, u = v("time"), v("v(dq)")
    t0 = 5.01e-6
    t70 = next(t[i] for i in range(len(t)) if t[i] > t0 and u[i] >= 0.7 * 3.3) - t0
    print("S7 1-Wire: Anstieg auf 0,7·VDD in %.1f µs bei 550 pF Bus" % (t70 * 1e6))
    pruefe("S7 1-Wire-Anstieg ≤ 15 µs (Zeitschlitz Standard-Speed) [V: 1-Wire-Timing]", t70 <= 15e-6, "%.1f µs" % (t70 * 1e6))


def main():
    pfad = finde_bibliothek()
    if not pfad:
        print("ÜBERSPRUNGEN: keine ngspice-Bibliothek gefunden (KiCad 10 bringt sie mit: ngspice.dll bzw. libngspice0). "
              "Diese Prüfung gilt damit als NICHT GELAUFEN.")
        return 0
    ng = NgSpice(pfad)
    print("ngspice: %s  (%s)" % (pfad, ng.version.strip()))
    print("=" * 78)
    s1_elektret(ng)
    s2_hx711(ng)
    s3(ng)
    s4_reset(ng)
    s5_teiler()
    s6_sensorschiene()
    s7_onewire(ng)
    print("=" * 78)
    print("%d von %d SPICE-/Modellprüfungen bestanden (T2, keine Messung)" % (ANZ - FEHL, ANZ))
    return 1 if FEHL else 0


if __name__ == "__main__":
    sys.exit(main())
