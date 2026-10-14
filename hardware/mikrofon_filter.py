#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Rechnung zum Block Mikrofon seit HW-07 (hardware/mikrofon.md, Lastenheft A1–A7).

Zwei Mikrofone am Audio-ADC TI TLV320ADC3101: Elektret analog (linker Kanal), MEMS Infineon IM69D127 als PDM
(rechter Kanal). Das Skript prüft den Taktplan gegen die Datenblattgrenzen, rechnet den Hochpass der
Koppelkondensatoren, die Vorspannung der Elektretkapsel, die Last am PDM-Ausgang über das Cat7-Kabel und den
Dezimationsschritt im STM32. Bis 14.10.2026 rechnete es das Analogfilter des GY-MAX4466-Zweigs (Sallen-Key
1179 Hz + RC 4,8 kHz); diese Schaltung ist durch HW-07 ersetzt (Stand davor im Git-Verlauf).

Kennzeichnung: [V] Datenblatt, [A] Annahme/Rechnung, [P] am Muster prüfen. Exitcode 1, wenn eine Grenze verletzt ist.
Aufruf: python3 hardware/mikrofon_filter.py
Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"""
import math
import sys

FEHLER = []


def pruefe(text, ok):
    print(("ok   " if ok else "FEHL ") + text)
    if not ok:
        FEHLER.append(text)


# --- 1 Taktplan -------------------------------------------------------------------------------------------
FS = 24576.0                 # Hz, Abtastrate des ADC (3 × 8192 Hz)
AOSR = 128                   # Überabtastung; Filter A mit AOSR = 64 oder 128 [V, TI SLAS553B Tab. „ADC Digital Filter“]
SLOT_BITS = 32               # I²S-Rahmen 2 × 32 Bit → BCLK = 64 · fS
P, J, D, R = 1, 32, 0, 2     # PLL des ADC, Eingang BCLK
NADC, MADC = 8, 4

bclk = 2 * SLOT_BITS * FS
pll = bclk / P * (J + D / 1e4) * R
adc_clkin = NADC * MADC * AOSR * FS
mod_clk = AOSR * FS          # = DMCLK für das PDM-Mikrofon [V, Abschnitt 10.3.12.6]
print("Taktplan: fS %.0f Hz, BCLK %.6f MHz, PLL %.3f MHz, ADC_CLKIN %.3f MHz, DMCLK %.4f MHz"
      % (FS, bclk / 1e6, pll / 1e6, adc_clkin / 1e6, mod_clk / 1e6))
pruefe("PLL-Eingang BCLK/P = %.3f MHz im Bereich 0,512–20 MHz (D = 0) [V 10.3.7]" % (bclk / P / 1e6),
       0.512e6 <= bclk / P <= 20e6)
pruefe("PLL-Ausgang %.2f MHz im Bereich 80–110 MHz [V 10.3.7]" % (pll / 1e6), 80e6 <= pll <= 110e6)
pruefe("J = %d im Bereich 4–55 (D = 0) [V 10.3.7]" % J, 4 <= J <= 55 and D == 0)
pruefe("PLL = NADC · MADC · AOSR · fS (fS genau aus BCLK abgeleitet)", abs(pll - adc_clkin) < 1)
pruefe("AOSR · fS = %.3f MHz im Bereich 2,8–6,2 MHz [V 11.2.2.1, Gl. 6]" % (mod_clk / 1e6), 2.8e6 < mod_clk < 6.2e6)
pruefe("DMCLK %.3f MHz im IM69D127-Band 2,9–3,3 MHz (Zwischenwerte nicht erlaubt) [V Infineon]" % (mod_clk / 1e6),
       2.9e6 <= mod_clk <= 3.3e6)
pruefe("ADC_CLK = MADC · AOSR · fS = %d · fS ≥ Befehlszahl PRB_R1 (188) · fS [V 10.3.7, Tab. 6]" % (MADC * AOSR),
       MADC * AOSR >= 188)
print("Hinweis: 11.2.2.1 Gl. 8 verweist für die Ressourcenklasse auf Tab. 5, die diese Spalte nicht enthält – "
      "Wert am Muster bzw. bei TI klären [P]")

# STM32F411 als I²S-Master: I2SCLK aus PLLI2S (HSE 25 MHz, M = 25 → 1 MHz), fS = I2SCLK / (64 · (2·DIV + ODD))
N_I2S, R_I2S, DIV, ODD = 302, 2, 48, 0
i2sclk = 1e6 * N_I2S / R_I2S
fs_stm = i2sclk / (64 * (2 * DIV + ODD))
pruefe("STM32 PLLI2S: VCO %d MHz (100–432), I2SCLK %.1f MHz → fS %.1f Hz, Abweichung %.4f %% [A, RM0383 prüfen]"
       % (N_I2S, i2sclk / 1e6, fs_stm, (fs_stm / FS - 1) * 100),
       100 <= N_I2S <= 432 and abs(fs_stm / FS - 1) < 1e-3)

# --- 2 Elektret: Vorspannung und Hochpass -----------------------------------------------------------------------
MICBIAS = 2.5                # V, einstellbar 2,0/2,5 V oder AVDD [V 10.3.11]
R_BIAS = 1e3                 # R610 und R611
I_KAPSEL = (0.1e-3, 0.5e-3)  # A, üblicher Bereich für Elektretkapseln [A]; Kapsel noch wählen [P]
for i in I_KAPSEL:
    u = MICBIAS - 2 * R_BIAS * i
    pruefe("Kapselspannung bei %.1f mA: %.2f V (≥ 1,5 V) [A]" % (i * 1e3, u), u >= 1.5)
pruefe("MICBIAS-Strom ≤ 4 mA [V]", max(I_KAPSEL) <= 4e-3)
C_KOPPEL, R_EIN = 1e-6, 35e3  # Eingangswiderstand bei 0 dB [V 10.3.10]
fh = 1 / (2 * math.pi * C_KOPPEL * R_EIN)
pruefe("Hochpass Koppel-C: %.1f Hz (deutlich unter 60 Hz)" % fh, fh < 20)

# --- 3 PDM über das Kabel --------------------------------------------------------------------------------------------
C_ESD = 2.3e-12              # ESDS304 je Kanal [V]
C_PIN = 5e-12                # DMDIN-Pin [A]
C_M = 110e-12                # Cat7: Ader gegen Paarpartner + Paarschirm, grob [A] (Betriebskapazität ≤ 56 pF/m [V])
for laenge in (0.5, 1.0):
    c = laenge * C_M + C_ESD + C_PIN
    pruefe("DATA-Last bei %.1f m Cat7: %.0f pF ≤ 200 pF [V Infineon; A Kabelwert]" % (laenge, c * 1e12), c <= 200e-12)
c2 = 2.0 * C_M + C_ESD + C_PIN
print("Hinweis: bei 2 m wären es ca. %.0f pF > 200 pF – über 1 m nur mit Treiber im Mikrofonkopf (Lastenheft A4) [A]"
      % (c2 * 1e12))
# Takt: Puffer 74LVC1G17 (Ausgangswiderstand ca. 15 Ω bei 3,3 V [A]) + 33 Ω in Reihe
R_TREIB = 15 + 33
for laenge in (0.5, 1.0):
    c = laenge * C_M + C_ESD + 5e-12
    t_an = 2.2 * R_TREIB * c
    pruefe("Taktflanke am Mikrofon bei %.1f m: ca. %.1f ns ≤ 13 ns [V Infineon; A Rechnung, T4 messen]"
           % (laenge, t_an * 1e9), t_an <= 13e-9)

# --- 4 Dezimation im STM32 --------------------------------------------------------------------------------------------
FS_FFT = 2048.0
faktor = FS / FS_FFT
pruefe("Dezimation %.0f Hz → %.0f Hz mit ganzzahligem Faktor %.0f" % (FS, FS_FFT, faktor), faktor == int(faktor))
print("Nutzband 60–900 Hz; das FIR vor der Dezimation muss ab %.0f Hz sperren (nach der Dezimation spiegelt "
      "alles über 1024 Hz) [A]." % (FS_FFT - 900))

print()
if FEHLER:
    print("%d Grenze(n) verletzt" % len(FEHLER))
    sys.exit(1)
print("alle Grenzen eingehalten")
