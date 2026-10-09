#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Energiebilanz der eigenen Logger-Platine (Lastenheft 0.4, Abschnitt 3).

Aufruf:  python3 hardware/energiebilanz.py
Alle Werte stehen in den Tabellen unten, jeweils mit Quelle und Status:
  V = aus Datenblatt gelesen, A = Annahme/Rechnung, M = gemessen (noch keine).
Sobald Messwerte vom Steckbrett-Aufbau vorliegen, die Zahlen hier ersetzen und den Status auf M setzen.
Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"""

ZYKLEN_PRO_TAG = 96          # Messintervall 15 min
KAPAZITAET_MAH = 3350        # BAK N18650CP-34E, Händlerangabe typ. (V, nkon.nl)

# ---------------------------------------------------------------------------
# 1. Ruhestrom (alles, was dauernd an der Zelle hängt), µA bei 25 °C
# ---------------------------------------------------------------------------
RUHE = [
    # (Teil, µA, Status, Quelle)
    ("Laderegler BQ25185, ohne Eingang (IQ_BAT)", 4.0, "V", "TI BQ25185 Datenblatt, Tab. 5.5, IQ_BAT typ. 4 µA"),
    ("Zellschutz HY2111-GB, Normalbetrieb", 3.0, "V", "HYCON HY2111, S. 8, typ. 3,0 µA bei 3,9 V"),
    ("LDO RT9080-33, ohne Last", 2.0, "V", "Richtek DS9080, Electrical Characteristics, typ. 2 µA"),
    ("STM32F411 Standby, LSE + RTC an", 2.6, "A", "ST DocID026289 Rev 6, Tab. 29/30: 2,4 µA (1,7 V) / 2,8 µA (3,6 V), 3,3 V interpoliert"),
    ("SX1262 Sleep (warm start)", 0.6, "V", "Semtech SX1261/2 Rev 1.1, Tab. 3-5"),
    ("Spannungsteiler Akku 2 × 2,2 MΩ bei 3,9 V", 0.9, "A", "U/R"),
    ("Lastschalter AO3401A gesperrt, Leckstrom", 0.1, "A", "AOS AO3401A IDSS ≤ 1 µA bei 30 V; bei 3,3 V deutlich weniger"),
    ("5-V-Wandler TPS61240 aus (EN low)", 1.5, "V", "TI TPS61240 Datenblatt S. 5, Shutdown typ. 1,5 µA"),
    ("SPI-Flash 64 Mbit im Deep Power-down (dauernd versorgt)", 1.0, "A", "W25Q-Familie: 1 µA laut LCSC-Angabe (V); andere Hersteller bis 3 µA typ. (V, Zetta) – Typ bei Bestellung"),
    # Ladesperre (2 × TMP390, Pull-ups, LDO TPS70933) hängt an TMP_VCC aus dem Ladereingang:
    # nachts 0 µA aus der Zelle (SCH26-01, versorgung.md 3.3)
]

# ---------------------------------------------------------------------------
# 2. Ladung je Messzyklus: (Teil, Strom mA, Dauer s, Status, Quelle)
#    Szenario A: Ablauf wie die heutige ZS-Firmware (MCU durchgehend 96 MHz, wartet in den RX-Fenstern aktiv)
#    Szenario B: neue Firmware (MCU 16 MHz beim Warten, 96 MHz nur für Abtastung/FFT, Stop-Modus in den RX-Pausen)
# ---------------------------------------------------------------------------
GEMEINSAM = [
    # Waage (waage.md): 5-V-Wandler TPS61240 → 1 × HX711 (Entscheidung 09.10.2026), AVDD 4,3 V, Bosche H40A (404 Ω, V: Bosche-Datenblatt).
    # Last am 5-V-Ausgang: 4,3 V / 404 Ω = 10,6 mA Brücke + 1,5 mA HX711 = 12,1 mA (A: Brückenstrom fließt über den PNP aus 5 V).
    # Strom aus SYS bei 3,7 V und 85 % Wirkungsgrad: 12,1 mA × 5 V / 3,7 V / 0,85 = 19,3 mA (A).
    ("Waage: 5-V-Wandler + 1 × HX711 + H40A-Brücke (404 Ω, AVDD 4,3 V)", 19.3, 1.8, "A",
     "Bosche H40A RLC 404 Ω (V); HX711 Tab. 2: 1,4 + 0,1 mA (V); Wandler-Wirkungsgrad 85 % (A); "
     "Dauer: Anlauf + 400 ms Einschwingen + 10 Werte bei 10 SPS (V/A)"),
    ("DS18B20 × 2, Wandlung parallel", 2 * 1.0, 0.75, "V", "ADI DS18B20: IDD typ. 1 mA, tCONV 750 ms (12 Bit)"),
    ("Mikrofonmodul GY-MAX4466 (Verstärker + Elektret-Vorstrom)", 0.3, 1.4, "A", "MAX4466 ICC 24 µA (V); Elektret-Vorstrom geschätzt 0,2–0,3 mA"),
    ("Sensorschiene sonst (Pull-ups, BME280)", 0.2, 8.0, "A", "BME280 < 1 mA für ~10 ms (V); Pull-ups 1,8 kΩ teilweise low"),
    ("Sitzung in den SPI-Flash schreiben (HW26-10, 2 × 256 Byte)", 15.0, 0.003, "A", "NOR Page Program typ. 0,7 ms bei ca. 15 mA je Seite (W25Q-Familie, A)"),
    ("SX1262 RX1 (SF7) + RX2 (SF9), ohne Downlink, LDO-Modus", 8.8, 0.045, "A",
     "RX 8,8 mA LDO-Modus (V, Tab. 3-5); Fensterlänge ~8 Symbole + Reserve (A)"),
]
SZENARIEN = {
    "A (Ablauf wie ZS-Firmware heute)": GEMEINSAM + [
        ("MCU aktiv 96 MHz, Peripherie an", 19.5, 8.0, "A", "ST Tab. 23: 84 MHz 16,8 mA / 100 MHz 20,7 mA bei 3,6 V, interpoliert"),
        ("SX1262 TX +14 dBm, Standard-PA-Einstellung, SF7 (118 ms)", 90.0, 0.118, "V", "Semtech Tab. 3-6; Airtime nach Semtech-Formel (A)"),
        ("SX1262 Standby XOSC zwischen TX und RX2", 0.8, 2.0, "V", "Semtech Tab. 3-5"),
    ],
    "B (neue Firmware, sparsam)": GEMEINSAM + [
        ("MCU 16 MHz beim Warten auf Sensoren", 3.0, 6.0, "V", "ST Tab. 23: 16 MHz HSI, Peripherie an, 3,0 mA"),
        ("MCU 96 MHz für Abtastung und FFT", 19.5, 1.5, "A", "wie oben"),
        ("SX1262 TX +14 dBm, optimale PA-Einstellung, SF7", 45.0, 0.118, "V", "Semtech Tab. 3-6 (optimale Einstellung)"),
        ("MCU + Funk im Stop zwischen TX und RX2", 0.015, 2.0, "V", "ST Tab. 28: Stop, Low-Power-Regler, 14 µA"),
    ],
}

# Ungünstiger Fall zusätzlich: schlechte Funkverbindung, SF12 (2,79 s Airtime) mit +14 dBm Standard-PA
SF12_ZUSATZ_MAS = 90.0 * (2.794 - 0.118)

# ---------------------------------------------------------------------------
# 3. Selbstentladung und nutzbare Kapazität
# ---------------------------------------------------------------------------
SELBSTENTLADUNG_PROZENT_MONAT = (2.0, 5.0)   # A: Spanne; Battery University BU-802b nennt höhere Werte bei Vollladung/25 °C
LADESCHLUSS_FAKTOR = 0.90    # A: Ladeschluss 4,1 V statt 4,2 V kostet grob 10 % Kapazität
ENTLADEFENSTER = 0.95        # A: unterhalb 3,3 V (Firmware stellt Senden ein) bleiben nur wenige Prozent
KAELTE_FAKTOR = 0.80         # A: Kapazität bei −10 °C und kleiner Last; nicht belegt, Messung offen

# ---------------------------------------------------------------------------
# 4. Solarertrag im Winter
# ---------------------------------------------------------------------------
EINSTRAHLUNG_DEZ_HORIZONTAL = 0.55   # kWh/m²/Tag, DWD-Deutschlandmittel Dez. (V, solarserver.de 12.01.2023)
NEIGUNGS_FAKTOR_65_GRAD = 1.5        # A: Gewinn bei 65° Süd gegenüber horizontal im Dezember (1,5–2)
PANEL_FLAECHE_M2 = 2 * 0.0100        # A: zwei Panels je ca. 100 cm² — Maße noch messen!
GESAMTWIRKUNGSGRAD = 0.10            # A: Panel ~12–15 %, Laderegler ohne MPPT (Panel wird auf ~4,4 V gezogen)
AKKU_SPANNUNG = 3.8                  # V, mittlere Zellspannung für mAh → Wh


def mas_zu_mah(mas):
    return mas / 3600.0


def main():
    print("=" * 78)
    print("Energiebilanz Logger-Platine (Werte mit Status V/A/M, siehe Quelltext)")
    print("=" * 78)

    ruhe_ua = sum(r[1] for r in RUHE)
    print("\n1. Ruhestrom bei 25 °C")
    for teil, ua, st, _ in RUHE:
        print(f"   {ua:5.1f} µA  [{st}]  {teil}")
    print(f"   {ruhe_ua:5.1f} µA  Summe  →  {ruhe_ua * 24 / 1000:.2f} mAh/Tag")
    print("   Bei 70 °C im Gehäuse: STM32 Standby bis 14 µA max. (ST Tab. 30), Summe dann grob 25 µA.")

    selbst_min = KAPAZITAET_MAH * SELBSTENTLADUNG_PROZENT_MONAT[0] / 100 / 30
    selbst_max = KAPAZITAET_MAH * SELBSTENTLADUNG_PROZENT_MONAT[1] / 100 / 30
    nutzbar = KAPAZITAET_MAH * LADESCHLUSS_FAKTOR * ENTLADEFENSTER * KAELTE_FAKTOR

    for name, posten in SZENARIEN.items():
        mas = sum(i * t for _, i, t, _, _ in posten)
        print(f"\n2. Messzyklus, Szenario {name}")
        for teil, i, t, st, _ in sorted(posten, key=lambda p: -p[1] * p[2]):
            print(f"   {i * t:7.1f} mAs  [{st}]  {teil}")
        zyklus_mah_tag = mas_zu_mah(mas) * ZYKLEN_PRO_TAG
        last = zyklus_mah_tag + ruhe_ua * 24 / 1000
        print(f"   {mas:7.1f} mAs je Zyklus  →  {zyklus_mah_tag:.2f} mAh/Tag bei {ZYKLEN_PRO_TAG} Zyklen")
        print(f"   Last gesamt (Zyklen + Ruhe): {last:.2f} mAh/Tag")
        for se, wort in ((selbst_min, "2 %/Monat"), (selbst_max, "5 %/Monat")):
            tag = last + se
            print(f"   + Selbstentladung {wort} ({se:.1f} mAh/Tag) = {tag:.1f} mAh/Tag"
                  f"  →  {nutzbar / tag:.0f} Tage ohne Laden")
        tag_sf12 = last + selbst_max + mas_zu_mah(SF12_ZUSATZ_MAS) * ZYKLEN_PRO_TAG
        print(f"   Ungünstig (SF12 jedes Mal, 5 %/Monat): {tag_sf12:.1f} mAh/Tag  →  {nutzbar / tag_sf12:.0f} Tage")

    print(f"\n3. Nutzbare Kapazität: {KAPAZITAET_MAH} mAh × {LADESCHLUSS_FAKTOR} (4,1 V) × {ENTLADEFENSTER}"
          f" (bis 3,3 V) × {KAELTE_FAKTOR} (Kälte) = {nutzbar:.0f} mAh")

    ertrag_wh = EINSTRAHLUNG_DEZ_HORIZONTAL * NEIGUNGS_FAKTOR_65_GRAD * PANEL_FLAECHE_M2 * GESAMTWIRKUNGSGRAD * 1000
    ertrag_mah = ertrag_wh / AKKU_SPANNUNG * 1000
    print(f"\n4. Solarertrag Dezember (Mittel): {ertrag_wh:.2f} Wh/Tag ≈ {ertrag_mah:.0f} mAh/Tag"
          f"  (Fläche {PANEL_FLAECHE_M2 * 1e4:.0f} cm², angenommen)")
    print("   Verhältnis Ertrag / Bedarf (Szenario A, 5 %/Monat):",
          f"{ertrag_mah / (mas_zu_mah(sum(i * t for _, i, t, _, _ in SZENARIEN['A (Ablauf wie ZS-Firmware heute)'])) * ZYKLEN_PRO_TAG + ruhe_ua * 0.024 + selbst_max):.0f} : 1")
    print("   Achtung: Unter +5 °C Zelltemperatur sperrt der TMP390 das Laden (HW26-07). Dann zählt nur die Reichweite aus Abschnitt 2.")


if __name__ == "__main__":
    main()
