#!/usr/bin/env python3
"""Frequenzgang des Mikrofon-Eingangsfilters (hardware/mikrofon.md).
Hochpass (Koppel-C an Vorspannung) → Sallen-Key-Tiefpass 2. Ordnung (Verstärkung 1) → RC-Tiefpass am ADC.
Aufruf: python3 hardware/mikrofon_filter.py
Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"""
import cmath, math

# Bauteile (Normreihe E24 bzw. E12)
C_HP, R_HP = 220e-9, 33e3        # Koppel-C und Vorspannungs-Widerstand (Thevenin der 2 × 66k-Teilung ≈ 33k)
R1 = R2 = 9.1e3                  # Sallen-Key
C1, C2 = 22e-9, 10e-9            # C1 = Rückkopplung (am Ausgang), C2 = nach Masse
R_ADC, C_ADC = 3.3e3, 10e-9      # RC vor PA1
# Kabel 2 m LiYCY (Lapp: ca. 120 pF/m Ader/Ader, 160 pF/m Ader/Schirm) → Ader OUT gegen alles ca. 0,4 nF/m
R_ISO = 1.0e3                    # Trennwiderstand direkt am Modulausgang (MAX4466 nur bis 100 pF stabil)
C_KABEL = 2 * 0.4e-9             # 2 m
R_EIN = 100.0                    # Schutzwiderstand an der Klemme

def h(f):
    s = 2j * math.pi * f
    # Trennwiderstand + Kabelkapazität: Tiefpass weit über dem Nutzband
    kabel = 1 / (1 + s * R_ISO * C_KABEL)
    # Hochpass mit Quellwiderstand (R_ISO + R_EIN) in Reihe zum Koppel-C, Last R_HP gegen VREF
    z_c = 1 / (s * C_HP)
    hp = R_HP / (R_ISO + R_EIN + z_c + R_HP)
    sk = 1 / (s * s * R1 * R2 * C1 * C2 + s * C2 * (R1 + R2) + 1)
    rc = 1 / (1 + s * R_ADC * C_ADC)
    return kabel * hp * sk * rc

def db(x):
    return 20 * math.log10(abs(x))

fc_sk = 1 / (2 * math.pi * math.sqrt(R1 * R2 * C1 * C2))
q = math.sqrt(R1 * R2 * C1 * C2) / (C2 * (R1 + R2))
print(f"Hochpass fc = {1/(2*math.pi*(R_HP+R_ISO+R_EIN)*C_HP):.1f} Hz")
print(f"Trennwiderstand + Kabel: fc = {1/(2*math.pi*R_ISO*C_KABEL)/1e3:.0f} kHz")
print(f"Sallen-Key fc = {fc_sk:.0f} Hz, Q = {q:.3f}")
print(f"RC fc = {1/(2*math.pi*R_ADC*C_ADC):.0f} Hz")
print()
print("   f [Hz]   Dämpfung [dB]   Bedeutung")
for f, was in ((20, "Rumpeln"), (50, "Netzbrummen"), (60, "untere Bandgrenze"), (140, ""), (250, "Summen"),
               (440, ""), (560, ""), (900, "obere Bandgrenze"), (1025, "Grenze FIR"),
               (4096, "Nyquist bei 8192 Hz"), (7168, "erste Spiegelung ins Nutzband (8192 − 1024)"),
               (8192 - 900, "spiegelt auf 900 Hz"), (8192 - 60, "spiegelt auf 60 Hz"),
               (15360, "erste Spiegelung bei 16384 Hz Abtastung")):
    print(f"{f:9.0f}   {db(h(f)):8.1f}        {was}")
# Welligkeit im Nutzband (für die Korrektur in der Firmware)
werte = [db(h(f)) for f in range(60, 901, 4)]
print(f"\nNutzband 60–900 Hz: {min(werte):.2f} … {max(werte):.2f} dB (in der Firmware korrigierbar, Frequenzgang bekannt)")
