#!/usr/bin/env python3
"""I²C-Leitung zum BME280: Buskapazität, Anstiegszeit, Pull-up-Wahl.

Status je Wert: V = Datenblatt gelesen, A = Annahme, P = am Muster prüfen.
Aufruf: python3 hardware/i2c_leitung.py
"""

VDD = 3.3            # V, geschaltete Sensorschiene                         V
LAENGE_M = 1.0       # m, Festlegung Philipp 09.10.2026                      V
# Kabelvarianten: SDA gegen alle anderen Adern (+ Schirm), pF/m (min, max)
KABEL = {
    # Lapp LiYCY: ca. 120 pF/m Ader/Ader, 160 pF/m Ader/Schirm (V); Summe gegen alles (A)
    "LiYCY 4 x 0,14 geschirmt": (250, 400),
    # Netzwerkkabel Cat 5e/6: Paar ca. 50 pF/m (A, übliche Norm-Obergrenze 5,6 nF/100 m),
    # Paare SDA/GND, SCL/GND, 3V3/GND; Kopplung zu den anderen Paaren dazu (A)
    "Outdoor-Netzwerkkabel, verdrillte Paare (gewählt)": (70, 100),
}
# Platine, Stecker, ESDS304 (2,3 pF), STM32-Pin, BME280-Modul (EEPROM entfällt) A
PLATINE_PF = 35
CB_MAX_PF = 400      # I²C-Spezifikation und BME280-Datenblatt (Cb max)     V
CB_ZIEL_PF = 340     # 400 pF minus 15 % Reserve (HW26-09)                   A
TR_MAX_NS = 1000     # Standard-Mode-Anstiegszeit (30 % -> 70 %)            V
IOL_MAX_MA = 3.0     # BME280: VOL <= 0,2 x VDDIO bei 3 mA                  V
VOL = 0.4            # V, Rechenwert für den Low-Pegel                       A
PULLUPS = (1500, 1800, 2200, 3300, 4700)


def anstieg_ns(r_ohm, c_pf):
    # 30 % -> 70 %: t = R * C * ln(0,7/0,3) = 0,8473 * R * C
    return 0.8473 * r_ohm * c_pf * 1e-3


def tabelle(c_lo, c_hi):
    print(" R_pullup | I_low   | t_r bei c_lo | t_r bei c_hi | Bewertung")
    for r in PULLUPS:
        i_ma = (VDD - VOL) / r * 1000
        t_lo, t_hi = anstieg_ns(r, c_lo), anstieg_ns(r, c_hi)
        ok = i_ma <= IOL_MAX_MA and t_hi <= TR_MAX_NS
        reserve = (1 - t_hi / TR_MAX_NS) * 100
        print(f" {r:6d} Ω | {i_ma:4.2f} mA | {t_lo:7.0f} ns   | {t_hi:7.0f} ns   | "
              f"{'ok' if ok else 'nein'}, Reserve {reserve:3.0f} %")


def main():
    print(f"R_min aus {IOL_MAX_MA} mA: {(VDD - VOL) / IOL_MAX_MA * 1000:.0f} Ohm; "
          f"Ziel Buskapazität <= {CB_ZIEL_PF} pF (Grenze {CB_MAX_PF} pF)")
    fehler = 0
    for name, (lo, hi) in KABEL.items():
        c_lo = lo * LAENGE_M + PLATINE_PF
        c_hi = hi * LAENGE_M + PLATINE_PF
        ziel = "eingehalten" if c_hi <= CB_ZIEL_PF else "NICHT eingehalten"
        print(f"\n{name}, {LAENGE_M:.1f} m: {c_lo:.0f} ... {c_hi:.0f} pF -> Ziel {ziel}")
        tabelle(c_lo, c_hi)
        if "gewählt" in name and (c_hi > CB_ZIEL_PF or anstieg_ns(1800, c_hi) > TR_MAX_NS):
            fehler = 1
    return fehler


if __name__ == "__main__":
    raise SystemExit(main())
