#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Schaltplan der Hauptplatine (KiCad-Projekt hardware/kicad/hauptplatine/), Blätter je Block.

Stand 18.10.2026: alle Blätter im Entwurf: „Versorgung“, „MCU“, „Funk + Flash“, „Waage“, „Mikrofon“, „Anschlüsse“, „Akku“
(HW-06: Zelle und Zellschutz auf der Hauptplatine, Akku-Platine entfällt); Netze zwischen den Blättern sind globale Labels.
HW-09 (18.10.2026): BLE-Modul RN4871 an USART6 (PA11/PA12) statt USB-Daten; USB-C-Buchse entfällt (Philipp), Laden am Tisch
über zwei Lötpads J301 (5 V → D203 → Ladereingang).

Quellen der Werte: hardware/versorgung.md (3.1–3.8), LASTENHEFT.md V1–V7, mcu-funk.md, waage.md, mikrofon.md.
Aufruf: python3 hardware/kicad/hauptplatine.py
Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "werkzeug"))
from kicad_gen import Projekt  # noqa: E402

BIB = os.path.join(HIER, "bienen.kicad_sym")
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
# Steckbare Klemmen DEGSON 15EDGRC-3.5 (einreihig, geschlossen, gewinkelt; SCH26-13): Footprint und LCSC-Nummer je Polzahl
KLEMME_LCSC = {2: "C5160225", 3: "C5160226", 4: "C7603438", 5: "C7603439", 6: "C49352918"}


def klemme(n):
    return {"fp": "Bienen:DEGSON_15EDGRC-3.5-%02dP" % n, "lcsc": KLEMME_LCSC[n]}

# Netze, die zu anderen (noch folgenden) Blättern gehen
SCHNITTSTELLEN = {
    "VBUS",        # Ladepads J301 (Blatt MCU) → Diode D203 → Ladereingang
    "BLE_RXD", "BLE_TXD", "BLE_MODE",   # HW-09: Modul-UART und Modus des RN4871 (Blatt MCU) auch an J704 Pin 9–11
    "ADC_SOLAR",   # PB1
    "ADC_AKKU",    # Akkuteiler → ADC (Pin auf Blatt MCU)
    "SENSOR_EIN",  # PA1 → ON des TPS22917 (HW-07: vorher PB5)
    "3V3_SW",      # geschaltete Sensorschiene
    "SYS",         # 5-V-Wandler der Waage hängt an SYS
    # Blatt MCU → Funk + Flash
    "SPI_SCK", "SPI_MISO", "SPI_MOSI", "LORA_NSS", "LORA_DIO1", "LORA_BUSY", "LORA_RST", "LORA_TXEN", "LORA_RXEN",
    "FLASH_CS",
    # Blatt MCU → Mikrofon, Waage, Anschlüsse
    "HX_DOUT", "HX_SCK", "WAAGE_EIN", "ONEWIRE", "I2C_SCL", "I2C_SDA",
    "I2S_CK", "I2S_WS", "I2S_SD",  # HW-07: I2S3 zum Audio-ADC (PB12 CK, PA15 WS, PB5 SD)
}


def zeichne_versorgung(b, T):
    """Platzierung und Leitungen nach Stromfluss (A3 quer, mm).
    Obere Reihe: Panels/USB → Schottky → VIN_LADER → Laderegler → SYS. Mitte: Labels zum Blatt Akku mit
    VBAT, CE, NTC und TMP_VCC (TPS70933 aus VIN_LADER) als Labels zum Blatt Akku. Untere Reihe: SYS → 3,3 V → Sensorschiene.
    netz_tests.py prüft jede gezeichnete Verbindung gegen die Netzbeschreibung."""
    S, D, L = b.setze, b.draht, b.label
    yv = 76.2                        # obere Schiene VIN_LADER / SYS
    y3 = 180.34                      # untere Schiene SYS / +3V3 / 3V3_SW

    b.text("1  Solar und Ladepads (5 V) → Schottky-Dioden → VIN_LADER (TVS, Messung der Eingangsspannung)", 30.48, 55.88, 2.0)
    b.text("2  Laderegler BQ25185: 4,1 V, 150 mA; CE und TS kommen von der Ladesperre (Blatt Akku)", 152.4, 63.5, 2.0)
    b.text("3  Zum Blatt Akku: VBAT, CE_LADEN, NTC, TMP_VCC", 175.26, 124.46, 2.0)
    b.text("4  SYS → 3,3 V (RT9080) → geschaltete Sensorschiene 3V3_SW (TPS22917, Ein/Aus von der MCU)", 152.4, 215.9, 2.0)
    b.text("Regeln: Pull-ups nur an 3V3_SW; TS/MR nie aktiv auf Masse (Werksmodus); Laderegler nicht neben der Zelle; "
           "SPI-Flash an +3V3 (dauernd).", 30.48, 233.68, 1.5)
    b.text("Zelle, Zellschutz und Ladesperre auf Blatt Akku (HW-06). TMP_VCC aus dem TPS70933 am Ladereingang gibt es nur bei "
           "Sonne/USB; ohne TMP_VCC sperrt die Ladesperre (sicherheit-akku.md).", 30.48, 240.03, 1.5)

    # Teile, auf die mehrere Abschnitte zeigen, zuerst setzen
    S(T["U201"], 205.74, 83.82, text="oben")
    S(T["U204"], 215.9, 152.4, text="oben")
    S(T["U202"], 228.6, 185.42, text="oben")
    S(T["U203"], 299.72, 182.88, text="oben")

    # --- 1 Quellen und VIN_LADER --------------------------------------------
    S(T["J201"], 35.56, 78.74, rot=180, text="oben")
    S(T["J202"], 35.56, 99.06, rot=180, text="oben")
    S(T["D201"], 55.88, yv, rot=180, text="oben")
    S(T["D202"], 55.88, 96.52, rot=180, text="oben")
    S(T["D203"], 55.88, 116.84, rot=180, text="oben")
    D(T["J201"].p("2"), T["D201"].p("A"))
    D(T["J202"].p("2"), T["D202"].p("A"))
    D((40.64, 116.84), T["D203"].p("A"))
    D(T["D201"].p("K"), T["U201"].p("IN"))
    D(T["D202"].p("K"), (66.04, 96.52), (66.04, yv))
    D(T["D203"].p("K"), (66.04, 116.84), (66.04, 96.52))
    L("PV1", 43.18, yv)
    L("PV2", 43.18, 96.52)
    L("VBUS", 40.64, 116.84, 180)
    L("VIN_LADER", 152.4, yv)
    S(T["D204"], 78.74, 83.82, rot=270, text="rechts")
    S(T["C201"], 99.06, 83.82)
    S(T["C202"], 116.84, 83.82)
    S(T["R201"], 132.08, 83.82)
    S(T["R202"], 132.08, 99.06, text="links")
    S(T["C203"], 142.24, 99.06)
    for r in ("D204", "C201", "C202", "R201"):
        D(T[r].p("1"), (T[r].p("1")[0], yv))
    D(T["R201"].p("2"), T["R202"].p("1"))
    D(T["C203"].p("1"), (142.24, 91.44), (132.08, 91.44))
    D((142.24, 91.44), (147.32, 91.44))
    L("ADC_SOLAR", 147.32, 91.44)
    S(T["#FLG201"], 71.12, yv)
    S(T["#FLG202"], 30.48, 132.08)

    # --- 2 Laderegler -------------------------------------------------------
    S(T["R203"], 177.8, 87.63, text="links")
    S(T["R204"], 185.42, 90.17)
    D(T["U201"].p("ISET"), (177.8, 83.82))
    D(T["U201"].p("ILIM/VSET"), (185.42, 86.36))
    L("ISET", 180.34, 83.82)
    L("ILIM", 186.69, 86.36)
    x_ce, x_ts = 167.64, 170.18
    D(T["U201"].p("~{CE}"), (x_ce, 78.74), (x_ce, 134.62), (246.38, 134.62))
    D(T["U201"].p("TS/~{MR}"), (x_ts, 81.28), (x_ts, 132.08), (246.38, 132.08))
    L("CE_LADEN", 246.38, 134.62)
    L("NTC", 246.38, 132.08)
    S(T["R205"], 157.48, 109.22, text="links")
    S(T["C206"], 162.56, 127.0, text="links")
    D(T["R205"].p("1"), (157.48, 101.6))
    D(T["R205"].p("2"), (157.48, 116.84), (x_ce, 116.84))
    D(T["C206"].p("1"), (162.56, 121.92), (x_ce, 121.92))
    L("SYS", 157.48, 101.6, 90)
    S(T["TP201"], 243.84, 81.28, rot=270)
    S(T["TP202"], 243.84, 91.44, rot=270)
    D(T["U201"].p("STAT1"), T["TP201"].p("1"))
    D(T["U201"].p("STAT2"), (236.22, 83.82), (236.22, 91.44), T["TP202"].p("1"))
    L("LADE_STAT1", 226.06, 81.28)
    L("LADE_STAT2", 226.06, 83.82)

    # --- 3 VBAT, Akkuteiler, TMP_VCC (zum Blatt Akku) -------------------------
    D(T["U201"].p("BAT"), (302.26, 78.74))
    L("VBAT", 302.26, 78.74)
    S(T["C205"], 264.16, 82.55)
    
    S(T["R206"], 279.4, 82.55, text="links")
    S(T["R207"], 279.4, 97.79, text="links")
    S(T["C207"], 289.56, 97.79)
    D(T["R206"].p("2"), T["R207"].p("1"))
    D(T["C207"].p("1"), (289.56, 90.17), (279.4, 90.17))
    D((289.56, 90.17), (294.64, 90.17))
    L("ADC_AKKU", 294.64, 90.17)
    S(T["#FLG203"], 297.18, 78.74)
    D((73.66, yv), (73.66, 147.32), T["U204"].p("IN"))
    S(T["C212"], 236.22, 151.13)
    D(T["U204"].p("OUT"), (243.84, 147.32))
    L("TMP_VCC", 243.84, 147.32)

    # --- 4 SYS → 3,3 V → 3V3_SW ---------------------------------------------
    D(T["U201"].p("SYS"), (355.6, yv), (355.6, 167.64), (177.8, 167.64), (177.8, y3), T["U202"].p("VIN"))
    L("SYS", 236.22, yv)
    D(T["U202"].p("EN"), (215.9, 182.88), (215.9, y3))
    S(T["C204"], 185.42, 184.15)
    S(T["C208"], 203.2, 184.15)
    D(T["U202"].p("VOUT"), T["U203"].p("VIN"))
    S(T["C209"], 254.0, 184.15)
    b.versorgung("+3V3", 264.16, y3, "oben")
    S(T["C210"], 281.94, 182.88, rot=270, text="unten")
    D(T["C210"].p("1"), T["U203"].p("CT"))
    D(T["C210"].p("2"), (278.13, 182.88), (278.13, y3))
    L("SW_CT", 285.75, 182.88)
    S(T["R208"], 271.78, 199.39, text="links")
    D(T["U203"].p("ON"), (287.02, 185.42), (287.02, 195.58), (264.16, 195.58))
    L("SENSOR_EIN", 264.16, 195.58, 180)
    S(T["R209"], 317.5, 189.23)
    D(T["U203"].p("QOD"), T["R209"].p("1"))
    D(T["R209"].p("2"), (322.58, 193.04), (322.58, y3))
    L("SW_QOD", 309.88, 185.42)
    S(T["C211"], 332.74, 184.15)
    D(T["U203"].p("VOUT"), (342.9, y3))
    L("3V3_SW", 342.9, y3)
    for r in ("C204", "C208", "C209", "C211", "C205", "R206", "C212"):
        D(T[r].p("1"), (T[r].p("1")[0], {"C205": 78.74, "R206": 78.74, "C212": 147.32}.get(r, y3)))


STM32_FP = "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm"


def mcu(p):
    """Blatt MCU (mcu-funk.md 1, 1.6, 3.3, 4): STM32F411CEU6, Takt, Reset/BOOT, Ladepads, Debug, Magnet/Taster, LED,
    BLE-Modul RN4871 (HW-09)."""
    b = p.blatt("MCU", "mcu.kicad_sch", titel="MCU: STM32F411CEU6, Takt, Ladepads, BLE RN4871, Debug, Magnet und LED")
    pins = {"VDD": "+3V3", "VBAT": "+3V3", "VDDA": "VDDA", "VSS": "GND", "VSSA": "GND", "VCAP1": "VCAP",
            "NRST": "NRST", "BOOT0": "BOOT0", "PH0": "HSE_IN", "PH1": "HSE_OUT", "PC14": "LSE_IN", "PC15": "LSE_OUT",
            "PC13": "LED", "PA0": "WAKE", "PA1": "SENSOR_EIN", "PA2": "LORA_DIO1", "PA3": "LORA_BUSY", "PA4": "LORA_NSS",
            "PA5": "SPI_SCK", "PA6": "SPI_MISO", "PA7": "SPI_MOSI", "PA8": "ONEWIRE", "PA9": "DBG_TX", "PA10": "DBG_RX",
            "PA11": "USART6_TX", "PA12": "USART6_RX", "PA13": "SWDIO", "PA14": "SWCLK", "PA15": "I2S_WS",
            "PB0": "ADC_AKKU", "PB1": "ADC_SOLAR", "PB2": "BOOT1", "PB3": "FLASH_CS", "PB4": "LORA_RST",
            "PB5": "I2S_SD", "PB6": "I2C_SCL", "PB7": "I2C_SDA", "PB8": "HX_DOUT", "PB9": "HX_SCK", "PB10": "WAAGE_EIN",
            "PB12": "I2S_CK", "PB13": "BLE_EIN", "PB14": "LORA_TXEN", "PB15": "LORA_RXEN"}
    netze = {}
    for nr, name, *_r in pins_von_lib("MCU_ST_STM32F4:STM32F411CEUx"):
        netze[nr] = pins[name]
    b.teil("MCU_ST_STM32F4:STM32F411CEUx", "U301", "STM32F411CEU6", fp=STM32_FP, netze=netze,
           info="UFQFPN-48; Pinbelegung mcu-funk.md 4; Thermal-Pad (49) an GND")
    # Versorgung
    for ref in ("C301", "C302", "C303"):
        b.teil("Device:C", ref, "100n", fp=C0603, netze={"1": "+3V3", "2": "GND"}, info="je VDD-Pin direkt am Pin (AN4488)")
    b.teil("Device:C", "C304", "10µ 10V X5R", fp=C0805, netze={"1": "+3V3", "2": "GND"}, info="Sammelkondensator VDD (ST: ≥ 4,7 µF)")
    b.teil("Device:C", "C308", "100n", fp=C0603, netze={"1": "+3V3", "2": "GND"}, info="VBAT an 3,3 V, keine Knopfzelle (V6)")
    b.teil("Device:FerriteBead_Small", "FB301", "600R@100MHz", fp="Inductor_SMD:L_0603_1608Metric",
           netze={"1": "+3V3", "2": "VDDA"}, info="VDDA für die Mikrofonmessung beruhigt [A]")
    b.teil("Device:C", "C305", "100n", fp=C0603, netze={"1": "VDDA", "2": "GND"})
    b.teil("Device:C", "C306", "1µ", fp=C0603, netze={"1": "VDDA", "2": "GND"})
    b.teil("Device:C", "C307", "4,7µ X7R", fp=C0805, netze={"1": "VCAP", "2": "GND"}, info="VCAP_1: keramisch, ESR < 1 Ω, sehr nah")
    # Reset, BOOT
    b.teil("Device:C", "C309", "100n", fp=C0603, netze={"1": "NRST", "2": "GND"})
    b.teil("Switch:SW_Push", "SW301", "Reset", fp="Button_Switch_SMD:SW_SPST_TL3342", netze={"1": "GND", "2": "NRST"})
    b.teil("Device:R", "R301", "10k", fp=R0603, netze={"1": "BOOT0", "2": "GND"})
    b.teil("Switch:SW_Push", "SW302", "BOOT", fp="Button_Switch_SMD:SW_SPST_TL3342", netze={"1": "+3V3", "2": "BOOT0"},
           info="gedrückt halten + Reset → ROM-Bootloader über USART1 an J302 (kein USB mehr, HW-09)")
    b.teil("Device:R", "R302", "10k", fp=R0603, netze={"1": "GND", "2": "BOOT1"}, info="PB2/BOOT1 nach GND")
    # Takt
    b.teil("Device:Crystal_GND24", "Y301", "25MHz 12pF", fp="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", lcsc="C9006",
           netze={"1": "HSE_IN", "3": "HSE_OUT", "2": "GND", "4": "GND"}, info="YXC X322525MOB4SI")
    b.teil("Device:C", "C310", "18p C0G", fp=C0603, netze={"1": "GND", "2": "HSE_IN"}, info="2·(CL − Cstray) [A], am Muster prüfen")
    b.teil("Device:C", "C311", "18p C0G", fp=C0603, netze={"1": "GND", "2": "HSE_OUT"})
    b.teil("Device:Crystal", "Y302", "32,768k 7pF", fp="Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", lcsc="C97604",
           netze={"1": "LSE_IN", "2": "LSE_OUT"}, info="Seiko SC-32S; AN4488: CL ≤ 7 pF")
    b.teil("Device:C", "C312", "8,2p C0G", fp=C0603, netze={"1": "GND", "2": "LSE_IN"})
    b.teil("Device:C", "C313", "8,2p C0G", fp=C0603, netze={"1": "GND", "2": "LSE_OUT"})
    # Magnet/Taster, LED
    b.teil("Switch:SW_Push", "SW303", "Service", fp="Button_Switch_SMD:SW_SPST_TL3342", netze={"1": "WAKE", "2": "+3V3"})
    b.teil("Switch:SW_Reed", "SW304", "MRS03-B-3", fp="Bienen:MiRelay_MRS03_J-Lead_8.5x2.1mm", lcsc="C41432613",
           netze={"1": "WAKE", "2": "+3V3"},
           info="MiRelay MRS03-B-3: Reed SMD 8,5 × 2,1 mm, 10–15 AT; an der Platinenkante neben der LED, Längsachse parallel zur Kante; Schaltabstand durch die Wand am Prototyp [P]")
    b.teil("Device:R", "R305", "100k", fp=R0603, netze={"1": "WAKE", "2": "GND"}, info="Pull-down WKUP1")
    b.teil("Device:R", "R306", "1k", fp=R0603, netze={"1": "+3V3", "2": "LED_A"}, info="≥ 1 kΩ (mcu-funk.md 4)")
    b.teil("Device:LED", "D301", "LTST-S220KGKT", fp="Bienen:LED_Lite-On_LTST-S220_SideView", lcsc="C160469",
           netze={"A": "LED_A", "K": "LED"},
           info="Lite-On, seitlich abstrahlend, grün (AlInGaP 574 nm), am Rand vor dem Lichtleiter; mit 1 kΩ ca. 1,3 mA – Helligkeit am Muster prüfen [P]")
    # HW-09 (Philipp, 18.10.2026): USB-C-Buchse entfällt (PA11/PA12 sind USART6 für das BLE-Modul, kein USB-Gerät mehr).
    # Laden am Tisch über zwei Lötpads J301 (Stiftleiste nicht bestückt): 5 V → D203 → Ladereingang; D203 schützt gegen
    # Verpolung, TVS und Eingangsregelung des Laders wie bei den Panels (versorgung.md 3.1). USBLC6 und VBUS-Teiler entfallen.
    b.teil("Connector_Generic:Conn_01x02", "J301", "Laden 5 V", fp="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
           dnp=True, netze={"1": "GND", "2": "VBUS"},
           info="= J9: zwei Lötpads 2,54 mm (1 GND, 2 +5 V), Stiftleiste nicht bestückt; Laden aus einem 5-V-Netzteil, Verpolung sperrt D203 (HW-09)")
    # HW-09 (18.10.2026): BLE-Modul Microchip RN4871 (mcu-funk.md 1.6): Transparent-UART an USART6 (PA11 TX, PA12 RX, AF8),
    # Versorgung über P-FET Q301 aus +3V3, geschaltet von PB13 (low = ein; im Standby hochohmig → R309 sperrt).
    b.teil("Bienen:RN4871", "U303", "RN4871-I/RM130", fp="Bienen:Microchip_RN4871", lcsc="C633942",
           netze={"VBAT": "BLE_VCC", "RST_N": "BLE_RST", "UART_RX": "BLE_RXD", "UART_TX": "BLE_TXD", "P2_0": "BLE_MODE",
                  "GND": "GND", "P1_6": "NC", "P1_2": "NC", "P1_3": "NC", "P1_7": "NC", "P3_6": "NC", "P0_0": "NC",
                  "P0_2": "NC", "P2_7": "NC", "NC": "NC"},
           info="Microchip DS50002489D: BLE 5.0, Chip-Antenne, −40 … +85 °C (-I); Modul an die Platinenkante, Antenne nach außen, "
                "Metall (Zelle!) ≥ 30 mm entfernt; unbenutzte Pins offen (intern hochgezogen); Flusskontrolle in der Modul-"
                "Einstellung aus [P]; LCSC C633942 Extended, 50 Stück am 18.10.2026, ca. 12 $ [V]")
    b.teil("Transistor_FET:AO3401A", "Q301", "AO3401A", fp="Package_TO_SOT_SMD:SOT-23", lcsc="C15127",
           netze={"G": "BLE_EIN", "S": "+3V3", "D": "BLE_VCC"},
           info="Lastschalter BLE: PB13 low = Modul ein; Gate-Pull-up R309 hält das Modul aus, solange PB13 hochohmig ist (Standby)")
    b.teil("Device:R", "R309", "100k", fp=R0603, netze={"1": "+3V3", "2": "BLE_EIN"}, info="Gate-Pull-up: Modul aus bei hochohmigem PB13")
    b.teil("Device:R", "R310", "1k", fp=R0603, netze={"1": "USART6_TX", "2": "BLE_RXD"},
           info="Reihenwiderstand: begrenzt Rückspeisung in das abgeschaltete Modul und Querstrom bei externem Adapter an J704 Pin 9")
    b.teil("Device:R", "R311", "1k", fp=R0603, netze={"1": "USART6_RX", "2": "BLE_TXD"}, info="wie R310")
    b.teil("Device:R", "R312", "10k", fp=R0603, netze={"1": "BLE_VCC", "2": "BLE_MODE"},
           info="P2_0 high = Anwendungsmodus; an BLE_VCC (nicht +3V3), damit nichts in das abgeschaltete Modul speist; "
                "Testmodus für Modul-Firmware-Update: J704 Pin 11 an GND (Pin 12)")
    b.teil("Device:C", "C314", "10µ 6,3V X5R", fp=C0805, netze={"1": "BLE_VCC", "2": "GND"}, info="Datenblatt Fig. 5-4: 10 µF X5R an VBAT")
    b.teil("Device:C", "C315", "100n", fp=C0603, netze={"1": "BLE_VCC", "2": "GND"}, info="direkt an Pin 14")
    b.teil("Device:C", "C316", "100n", fp=C0603, netze={"1": "BLE_RST", "2": "GND"},
           info="Anlaufverzögerung mit dem internen Pull-up (48 kΩ typ.) ≈ 5 ms [A]; Reset = Abschalten über Q301, kein MCU-Pin")
    b.teil("Jumper:SolderJumper_2_Open", "JP301", "BLE dauernd", bom=False, fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
           netze={"A": "BLE_VCC", "B": "+3V3"},
           info="offen lassen; geschlossen: Modul dauernd versorgt (Entwicklung, Modul-Firmware-Update über J704 ohne laufende MCU)")
    b.teil("power:PWR_FLAG", "#FLG302", "PWR_FLAG", netze={"1": "BLE_VCC"},
           info="aus +3V3 über den Lastschalter Q301 (FET ist für den ERC kein Treiber); REG26-09")
    # Debug
    # SCH26-09: Pinfolge wie anschluesse.md J10 (führend für den Kabelplan); netz_tests.py vergleicht beide.
    # GND an Pin 5: SWD-Adapter an Pin 1–5 und USB-Seriell-Adapter (GND, RX, TX) an Pin 5–7 je am Stück.
    b.teil("Connector_Generic:Conn_01x07", "J302", "Debug (SWD + Serial1)", fp="Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
           netze={"1": "+3V3", "2": "SWDIO", "3": "SWCLK", "4": "NRST", "5": "GND", "6": "DBG_TX", "7": "DBG_RX"},
           info="= J10 in anschluesse.md: 1 3V3, 2 SWDIO, 3 SWCLK, 4 NRST, 5 GND, 6 TX1 (PA9, Ausgang), 7 RX1 (PA10)")
    b.teil("power:PWR_FLAG", "#FLG301", "PWR_FLAG", netze={"1": "VDDA"}, info="VDDA aus +3V3 über FB301 (Ferrit ist für den ERC kein Treiber)")
    zeichne_mcu(b, {t.ref: t for t in b.teile})
    return b


def zeichne_mcu(b, T):
    """Platzierung und Leitungen (A3 quer, mm). Mitte der STM32; oben die 3,3-V-Versorgung mit den
    Abblockkondensatoren, links Reset/BOOT und Quarze, rechts Magnet/Taster. Leitungen zu anderen
    Blättern und zu den Gruppen Ladepads und Debug enden an Netznamen."""
    S, D, L = b.setze, b.draht, b.label
    U = S(T["U301"], 200.66, 139.7, text="unten")

    b.text("1  Versorgung: VDD je 100 nF am Pin, VDDA über Ferrit, VBAT an 3,3 V, VCAP 4,7 µF", 144.78, 48.26, 2.0)
    b.text("2  Reset, BOOT, Quarze 25 MHz und 32,768 kHz (CL ≤ 7 pF)", 30.48, 81.28, 2.0)
    b.text("3  Magnet/Taster weckt (WKUP1), LED unter dem Lichtleiter", 236.22, 60.96, 2.0)
    b.text("4  Ladepads J301 (HW-09, statt USB-C): 5 V → D203 → Lader; Verpolung sperrt D203", 279.4, 157.48, 2.0)
    b.text("5  Debug-Leiste: SWD und Serial1 (auch ROM-Bootloader über USART1)", 279.4, 101.6, 2.0)
    b.text("6  BLE-Modul RN4871 (HW-09)", 30.48, 172.72, 2.0)
    b.text("Versorgung über Q301 aus +3V3, PB13 low = ein (Ruhestrom 0); UART an USART6 PA11/PA12 (AF8) über 1 kΩ", 160.02, 189.23, 1.5)
    b.text("Modul-UART und P2_0 auch an J704 Pin 9–11 (Modul-Firmware-Update: JP301 zu, Pin 11 an GND, MCU in Reset)", 160.02, 193.04, 1.5)
    b.text("Firmware: PA11/PA12 bei abgeschaltetem Modul hochohmig, sonst Rückspeisung über die Modul-Schutzdioden", 160.02, 196.85, 1.5)
    b.text("Netznamen ohne Gegenstück auf diesem Blatt führen zu den Blättern Versorgung, Funk + Flash, Waage, "
           "Mikrofon und Anschlüsse (mcu-funk.md 4).", 30.48, 241.3, 1.5)

    # --- 1 Versorgung oben ---------------------------------------------------
    y_r = 66.04                      # +3V3-Schiene
    D((129.54, y_r), (205.74, y_r))
    b.versorgung("+3V3", 129.54, y_r, "oben")
    for pin in ("VBAT", "24", "36", "48"):
        D(U.p(pin), (U.p(pin)[0], y_r))
    for ref, x in (("C303", 134.62), ("C302", 147.32), ("C301", 160.02), ("C304", 172.72), ("C308", 185.42)):
        S(T[ref], x, 69.85)
        D(T[ref].p("1"), (x, y_r))
    S(T["FB301"], 205.74, 71.12)
    D(T["FB301"].p("1"), (205.74, y_r))
    D(T["FB301"].p("2"), (205.74, 81.28), U.p("VDDA"))
    D((205.74, 81.28), (228.6, 81.28))
    S(T["C305"], 218.44, 85.09)
    S(T["C306"], 228.6, 85.09)
    S(T["#FLG301"], 210.82, 81.28)
    L("VDDA", 207.01, 81.28)
    S(T["C307"], 175.26, 180.34, text="links")
    D(U.p("VCAP1"), (175.26, 172.72), T["C307"].p("1"))
    L("VCAP", 177.8, 172.72)

    # --- 2 Reset, BOOT, Quarze links ----------------------------------------
    y_rst = 88.9
    D(U.p("NRST"), (172.72, 104.14), (172.72, y_rst), (101.6, y_rst))
    S(T["C309"], 152.4, 92.71)
    D(T["C309"].p("1"), (152.4, y_rst))
    S(T["SW301"], 96.52, y_rst, text="oben")
    L("NRST", 157.48, y_rst)
    y_boot = 101.6
    D(U.p("BOOT0"), (170.18, 109.22), (170.18, y_boot), (101.6, y_boot))
    S(T["R301"], 116.84, 105.41, text="links")
    D(T["R301"].p("1"), (116.84, y_boot))
    S(T["SW302"], 96.52, y_boot, text="oben")
    L("BOOT0", 152.4, y_boot)
    # HSE
    S(T["Y301"], 144.78, 115.57, rot=270, text="oben")
    D(U.p("PH0"), (167.64, 114.3), (167.64, 111.76), T["Y301"].p("1"))
    D(U.p("PH1"), (170.18, 116.84), (170.18, 119.38), T["Y301"].p("3"))
    S(T["C310"], 132.08, 111.76, rot=90, text="links")
    S(T["C311"], 132.08, 119.38, rot=90, text="links")
    D(T["C310"].p("2"), T["Y301"].p("1"))
    D(T["C311"].p("2"), T["Y301"].p("3"))
    L("HSE_IN", 172.72, 114.3)
    L("HSE_OUT", 172.72, 116.84)
    # LSE
    S(T["Y302"], 144.78, 128.27, rot=270, text="unten")
    D(U.p("PC14"), T["Y302"].p("1"))
    D(U.p("PC15"), (154.94, 127.0), (154.94, 132.08), T["Y302"].p("2"))
    S(T["C312"], 132.08, 124.46, rot=90, text="links")
    S(T["C313"], 132.08, 132.08, rot=90, text="links")
    D(T["C312"].p("2"), T["Y302"].p("1"))
    D(T["C313"].p("2"), T["Y302"].p("2"))
    L("LSE_IN", 165.1, 124.46)
    L("LSE_OUT", 165.1, 127.0)
    # PB2/BOOT1 und LED: über Netznamen zu kleinen Gruppen links unten
    stub(b, U, "PB2")
    stub(b, U, "PC13")
    R2 = S(T["R302"], 86.36, 160.02, rot=180, text="rechts")
    stub(b, R2, "2", 5.08)
    S(T["R306"], 106.68, 152.4)
    S(T["D301"], 106.68, 165.1, rot=90)
    D(T["R306"].p("2"), T["D301"].p("A"))
    D(T["D301"].p("K"), (106.68, 173.99))
    L("LED", 106.68, 173.99, 270)
    L("LED_A", 106.68, 158.75)

    # --- Pins zu anderen Blättern: kurze Leitung mit Netzname ---------------
    for pin in ("PB0", "PB1", "PB3", "PB4", "PB5", "PB6", "PB7", "PB8", "PB9", "PB10", "PB12", "PB13", "PB14", "PB15",
                "PA1", "PA2", "PA3", "PA4", "PA5", "PA6", "PA7", "PA8", "PA9", "PA10", "PA11", "PA12", "PA13", "PA14",
                "PA15"):
        stub(b, U, pin)

    # --- 3 Magnet/Taster, PA0 -----------------------------------------------
    D(U.p("PA0"), (246.38, 104.14), (246.38, 78.74))
    S(T["SW304"], 256.54, 78.74, text="oben")
    S(T["SW303"], 256.54, 86.36, text="unten")
    D((246.38, 78.74), T["SW304"].p("1"))
    D((246.38, 86.36), T["SW303"].p("1"))
    S(T["R305"], 254.0, 96.52, rot=90, text="unten")
    D((246.38, 96.52), T["R305"].p("1"))
    L("WAKE", 228.6, 104.14)

    # --- 5 Debug-Leiste -----------------------------------------------------
    J = S(T["J302"], 304.8, 119.38)
    for pin in ("2", "3", "4", "6", "7"):      # Pin 1 +3V3 und Pin 5 GND als Versorgungssymbol (SCH26-09)
        stub(b, J, pin, 10.16)

    # --- 4 Ladepads (HW-09, statt USB-C) --------------------------------------
    K = S(T["J301"], 330.2, 170.18, text="rechts")
    D(K.p("2"), (309.88, K.p("2")[1]))
    L("VBUS", 309.88, K.p("2")[1], 180)
    D(K.p("1"), (317.5, K.p("1")[1]))
    b.versorgung("GND", 317.5, K.p("1")[1], "unten")

    # --- 6 BLE-Modul RN4871 (HW-09) -------------------------------------------
    # Links der Lastschalter: +3V3 → Q301 (Source oben, Drain unten) → BLE_VCC-Schiene nach rechts zum Modul;
    # JP301 überbrückt den FET; Gate mit Pull-up R309 und Netzname BLE_EIN (PB13).
    B = S(T["U303"], 129.54, 208.28, text="oben")
    Q = S(T["Q301"], 58.42, 187.96, rot=180, text="links")
    x_q = Q.p("S")[0]                                   # senkrechte Achse Source/Drain des FET
    y_o, y_v = 180.34, B.p("VBAT")[1]                   # +3V3-Schiene, BLE_VCC-Schiene (Höhe des VBAT-Pins)
    D(Q.p("S"), (x_q, y_o), (71.12, y_o))
    b.versorgung("+3V3", x_q, y_o, "oben")
    D(Q.p("D"), (x_q, y_v), B.p("VBAT"))
    D(Q.p("G"), (78.74, Q.p("G")[1]))
    L("BLE_EIN", 78.74, Q.p("G")[1])
    S(T["R309"], 71.12, 184.15, text="rechts")          # Pin 1 auf der +3V3-Schiene, Pin 2 auf der Gate-Leitung
    JP = S(T["JP301"], 38.1, 187.96, rot=90, text="links")
    D(JP.p("B"), (38.1, y_o), (x_q, y_o))
    D(JP.p("A"), (38.1, y_v), (x_q, y_v))
    for ref, x in (("C314", 63.5), ("C315", 71.12), ("R312", 78.74)):
        S(T[ref], x, y_v + 3.81, text="links" if ref == "C314" else "rechts")
    D(T["R312"].p("2"), (78.74, B.p("P2_0")[1]), B.p("P2_0"))
    L("BLE_MODE", 88.9, B.p("P2_0")[1])
    S(T["#FLG302"], 106.68, y_v)
    L("BLE_VCC", 88.9, y_v)
    for pin, netz in (("RST_N", "BLE_RST"), ("UART_RX", "BLE_RXD"), ("UART_TX", "BLE_TXD")):
        D(B.p(pin), (101.6, B.p(pin)[1]))
        L(netz, 101.6, B.p(pin)[1], 180)
    # GND-Pins des Moduls gemeinsam
    g1, g2 = B.p("2"), B.p("13")
    D(g1, (g1[0], g1[1] + 2.54), (g2[0], g2[1] + 2.54), g2)
    b.versorgung("GND", (g1[0] + g2[0]) / 2, g1[1] + 2.54, "unten")
    # Reihenwiderstände MCU ↔ Modul und Reset-Kondensator, über Netznamen
    for ref, y in (("R310", 205.74), ("R311", 213.36)):
        R = S(T[ref], 190.5, y, rot=90, text="oben" if ref == "R310" else "unten")
        stub(b, R, "1", 7.62)
        stub(b, R, "2", 7.62)
    C = S(T["C316"], 165.1, 220.98, text="rechts")
    stub(b, C, "1", 5.08)

def funk(p):
    """Blatt Funk + Flash (mcu-funk.md 2, 3.1, 3.2): Ra-01SH an SPI1, SPI-Flash 64 Mbit am selben Bus."""
    b = p.blatt("Funk + Flash", "funk.kicad_sch", titel="Funk + Flash: Ra-01SH (SX1262/LLCC68), SPI-NOR-Flash 64 Mbit")
    b.teil("Bienen:Ra-01SH", "U401", "Ra-01SH", fp="Bienen:Ai-Thinker_Ra-01SH", lcsc="C2764087",
           netze={"3.3V": "+3V3", "RESET": "LORA_RST", "NSS": "RF_NSS", "SCK": "RF_SCK", "MOSI": "RF_MOSI", "MISO": "RF_MISO",
                  "BUSY": "LORA_BUSY", "DIO1": "LORA_DIO1", "ANT": "NC", "TXEN": "TXEN_MOD", "RXEN": "RXEN_MOD",
                  "DIO2": "NC", "DIO3": "NC", "GND": "GND"},
           info="Antenne über IPEX; Pin ANT ohne Leiterbahn, liegt im Modul parallel zur IPEX (mcu-funk.md 2.3); DIO2 schaltet HF-Schalter, DIO3 offen (kein TCXO)")
    b.teil("Device:C", "C401", "100µ 6,3V X5R", fp="Capacitor_SMD:C_1210_3225Metric", netze={"1": "+3V3", "2": "GND"},
           info="Puffer für Sendestromspitzen > 200 mA (mcu-funk.md 2.2) [A]")
    b.teil("Device:C", "C402", "10µ 10V X5R", fp=C0805, netze={"1": "+3V3", "2": "GND"})
    b.teil("Device:C", "C403", "100n", fp=C0603, netze={"1": "+3V3", "2": "GND"}, info="direkt an Pin 3")
    b.teil("Device:D_TVS", "D401", "TVS 3,3V", fp="Diode_SMD:D_SOD-523", netze={"1": "+3V3", "2": "GND"},
           info="ESD-Schutz am 3,3-V-Eingang des Moduls (Datenblatt-Empfehlung); Pad 1 an +3V3, damit auch eine unidirektionale TVS (Kathode = Pad 1) richtig sitzt; Teil wählen [P]")
    for ref, mod, mcu_ in (("R401", "RF_SCK", "SPI_SCK"), ("R402", "RF_MISO", "SPI_MISO"), ("R403", "RF_MOSI", "SPI_MOSI"),
                           ("R404", "RF_NSS", "LORA_NSS")):
        b.teil("Device:R", ref, "33", fp=R0603, netze={"1": mcu_, "2": mod}, info="Reihenwiderstand 10–100 Ω laut Datenblatt")
    b.teil("Device:R", "R405", "100k", fp=R0603, netze={"1": "+3V3", "2": "LORA_NSS"}, info="NSS nicht ausgewählt, solange PA4 im Standby hochohmig ist")
    b.teil("Jumper:SolderJumper_2_Open", "JP401", "TXEN", bom=False, fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
           netze={"A": "TXEN_MOD", "B": "LORA_TXEN"}, info="offen lassen: TXEN ist im Modul DIO2 (R8 0 Ω); geschlossen PB14 nur als Eingang (SCH26-11, mcu-funk.md 2.1)")
    b.teil("Jumper:SolderJumper_2_Open", "JP402", "RXEN", bom=False, fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
           netze={"A": "RXEN_MOD", "B": "LORA_RXEN"}, info="offen lassen: RXEN im Modul über R1 (NC) nicht verbunden; PB15 nur Eingang (SCH26-11)")
    b.teil("Memory_Flash:W25Q32JVSS", "U402", "64 Mbit SOIC-8 208 mil", fp="Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
           netze={"1": "FLASH_CS", "6": "SPI_SCK", "5": "SPI_MOSI", "2": "SPI_MISO", "3": "FLASH_WP", "7": "FLASH_HOLD",
                  "8": "+3V3", "4": "GND"},
           info="Teil nach Bestand: XT25F64BSSIGU-S (C2890984) oder ZD25Q64DSIGT (C55199021); Standard-Pinbelegung 25er-Reihe")
    b.teil("Device:C", "C404", "100n", fp=C0603, netze={"1": "+3V3", "2": "GND"})
    b.teil("Device:R", "R406", "100k", fp=R0603, netze={"1": "+3V3", "2": "FLASH_CS"}, info="CS nicht ausgewählt im Standby (PB3 hochohmig)")
    b.teil("Device:R", "R407", "10k", fp=R0603, netze={"1": "+3V3", "2": "FLASH_WP"})
    b.teil("Device:R", "R408", "10k", fp=R0603, netze={"1": "+3V3", "2": "FLASH_HOLD"})
    zeichne_funk(b, {t.ref: t for t in b.teile})
    return b


def zeichne_funk(b, T):
    """Links die Leitungen vom MCU (Netznamen), in der Mitte die 33-Ω-Widerstände, rechts das Modul;
    oben die 3,3-V-Pufferung, unten der SPI-Flash mit seinen Pull-ups."""
    S, D, L = b.setze, b.draht, b.label
    M = S(T["U401"], 190.5, 127.0, text="unten")
    b.text("1  Funkmodul Ra-01SH: 3,3 V dauernd, Puffer 100 µF + 10 µF + 100 nF, TVS am Eingang", 86.36, 66.04, 2.0)
    b.text("2  SPI1 vom MCU mit 33 Ω in Reihe; NSS mit 100 kΩ Pull-up", 86.36, 93.98, 1.5)
    b.text("TXEN/RXEN über offene Lötbrücken (mcu-funk.md 2.1)", 210.82, 106.68, 1.5)
    b.text("3  SPI-NOR-Flash 64 Mbit am selben Bus, eigener CS (PB3); Sitzung + Messwerte (mcu-funk.md 3.1/3.2)", 86.36, 162.56, 2.0)
    b.text("ANT ohne Leiterbahn: Antenne über die IPEX-Buchse des Moduls.", 210.82, 132.08, 1.5)

    # --- 3,3 V mit Pufferung -------------------------------------------------
    y_r = 78.74
    D(M.p("3.3V"), (176.53, M.p("3.3V")[1]), (176.53, y_r), (109.22, y_r))
    b.versorgung("+3V3", 109.22, y_r, "oben")
    for ref, x in (("C401", 116.84), ("C402", 132.08), ("C403", 147.32), ("D401", 162.56)):
        rot = 270 if ref == "D401" else 0     # Pad 1 (Kathodenseite bei unidirektionaler TVS) an +3V3 (REG26-08)
        S(T[ref], x, 82.55, rot=rot)
        pin = "1"
        D(T[ref].p(pin), (x, y_r))
    # --- RESET, SPI, BUSY, DIO1 ---------------------------------------------
    x_l = 86.36
    D(M.p("RESET"), (172.72, M.p("RESET")[1]), (172.72, 99.06), (x_l, 99.06))
    L("LORA_RST", x_l, 99.06, 180)
    zeilen = (("R404", "NSS", 152.4), ("R401", "SCK", 134.62), ("R403", "MOSI", 152.4), ("R402", "MISO", 134.62))
    for ref, pin, x in zeilen:
        y = M.p(pin)[1]
        R = S(T[ref], x, y, rot=90, text="oben" if ref in ("R404", "R401") else "unten")
        D(R.p("2"), M.p(pin))
        D(R.p("1"), (x_l, y))
        L(T[ref].pin_netz["1"], x_l, y, 180)
        L(T[ref].pin_netz["2"], 167.64, y)
    S(T["R405"], 127.0, 113.03)
    D(T["R405"].p("2"), (127.0, M.p("NSS")[1]))
    for pin, netz in (("BUSY", "LORA_BUSY"), ("DIO1", "LORA_DIO1")):
        D(M.p(pin), (x_l, M.p(pin)[1]))
        L(netz, x_l, M.p(pin)[1], 180)
    # --- TXEN/RXEN über Lötbrücken ------------------------------------------
    for jp, pin, netz in (("JP401", "TXEN", "LORA_TXEN"), ("JP402", "RXEN", "LORA_RXEN")):
        y = M.p(pin)[1]
        J = S(T[jp], 218.44, y, text="oben" if jp == "JP401" else "unten")
        D(M.p(pin), J.p("A"))
        D(J.p("B"), (238.76, y))
        L(netz, 238.76, y)
        L(T[jp].pin_netz["1"], 203.2, y)

    # --- 3 Flash ------------------------------------------------------------
    F = S(T["U402"], 172.72, 190.5, text="rechts")
    D(F.p("8"), (172.72, 172.72), (185.42, 172.72))
    b.versorgung("+3V3", 172.72, 172.72, "oben")
    S(T["C404"], 185.42, 176.53)
    x_f = 149.86
    D(F.p("1"), (x_f, F.p("1")[1]))
    L("FLASH_CS", x_f, F.p("1")[1], 180)
    S(T["R406"], 154.94, 177.8)
    D(T["R406"].p("2"), (154.94, F.p("1")[1]))
    for pin in ("6", "5", "2"):
        D(F.p(pin), (x_f, F.p(pin)[1]))
        L(F.pin_netz[pin], x_f, F.p(pin)[1], 180)
    for ref, pin in (("R407", "3"), ("R408", "7")):
        y = F.p(pin)[1]
        R = S(T[ref], 116.84 if ref == "R407" else 104.14, y, rot=90, text="oben" if ref == "R407" else "unten")
        D(R.p("2"), F.p(pin))
        L(F.pin_netz[pin], 124.46, y)


def waage(p):
    """Blatt Waage (waage.md 2–4, anschluesse.md J4): 5-V-Wandler TPS61240 an SYS, HX711 mit AVDD 4,30 V über
    PNP, Wägezellenklemme J501 (= J4) mit ESD-Schutz und Eingangsfilter. Kennzeichnung: [V] Datenblatt, [A] Annahme,
    [P] am Muster bzw. vor der Bestellung prüfen."""
    b = p.blatt("Waage", "waage.kicad_sch", titel="Waage: 5-V-Wandler TPS61240, HX711, Wägezelle H40A")
    # --- 1 5-V-Wandler (waage.md 2) ------------------------------------------
    b.teil("Bienen:TPS61240", "U501", "TPS61240DRVR", fp="Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm", lcsc="C59567",
           netze={"VIN": "SYS", "L": "L_5V", "EN": "WAAGE_EIN", "VOUT": "5V_WAAGE", "FB": "5V_WAAGE", "GND": "GND", "EP": "GND"},
           info="fest 5,0 V ±2 %, Lasttrennung im Aus [V]; Footprint KiCad WSON-6 2×2 mit TI DRV0006A vergleichen [P]")
    b.teil("Device:C", "C501", "4,7µ 16V X5R", fp=C0805, netze={"1": "SYS", "2": "GND"},
           info="TI: mindestens 2,2 µF an VIN [V]; 4,7 µF/0805 wegen DC-Bias bei 4,5 V [A]; direkt an VIN/GND")
    b.teil("Device:L", "L501", "1µ", fp="Inductor_SMD:L_0805_2012Metric", netze={"1": "SYS", "2": "L_5V"},
           info="TI: 1,0 µH empfohlen, Schaltstrombegrenzung 500–600 mA [V]; Teil mit Isat ≥ 0,7 A wählen (TI-Liste: TOKO MDT2012-CH1R0AN) [P]")
    b.teil("Device:R", "R501", "100k", fp=R0603, netze={"1": "WAAGE_EIN", "2": "GND"},
           info="EN nie offen: PB10 ist im Standby hochohmig; Datenblatt nennt keinen internen Pull-down (waage.md 2)")
    b.teil("Device:C", "C502", "10µ 10V X5R", fp=C0805, netze={"1": "5V_WAAGE", "2": "GND"},
           info="TI: COUT 1–20 µF [V]; wirksam bei 5 V etwa die Hälfte [A]; mit C503 zusammen unter 20 µF Nennwert [A]")
    b.teil("Device:R", "R502", "100k", fp=R0603, netze={"1": "5V_WAAGE", "2": "GND"},
           info="entlädt 5 V nach dem Abschalten, damit die HX711 beim nächsten Einschalten sicher neu startet [A]")
    b.teil("Device:FerriteBead_Small", "FB501", "600R@100MHz", fp="Inductor_SMD:L_0603_1608Metric",
           netze={"1": "5V_WAAGE", "2": "VSUP_HX"}, info="trennt den 3,5-MHz-Wandler von VSUP (waage.md 2) [A]; Teil wählen [P]")
    b.teil("Device:C", "C503", "10µ 10V X5R", fp=C0805, netze={"1": "VSUP_HX", "2": "GND"})
    b.teil("Device:C", "C504", "100n", fp=C0603, netze={"1": "VSUP_HX", "2": "GND"}, info="direkt an VSUP (Pin 1)")
    b.teil("power:PWR_FLAG", "#FLG501", "PWR_FLAG", netze={"1": "VSUP_HX"}, info="VSUP aus 5V_WAAGE über FB501 (Ferrit ist für den ERC kein Treiber)")
    # --- 2 HX711 mit Analogregler (waage.md 3) --------------------------------
    b.teil("Analog_ADC:HX711", "U502", "HX711", fp="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", lcsc="C43656",
           netze={"VSUP": "VSUP_HX", "BASE": "HX_BASE", "AVDD": "HX_AVDD", "VFB": "HX_VFB", "AGND": "GND", "VBG": "HX_VBG",
                  "INA-": "HX_INN", "INA+": "HX_INP", "INB-": "HX_INB", "INB+": "HX_INB", "PD_SCK": "HX_PD_SCK",
                  "DOUT": "HX_DOUT_IC", "XO": "NC", "XI": "GND", "RATE": "GND", "DVDD": "3V3_SW"},
           info="Kanal A, Verstärkung 128; RATE an GND = 10 Werte/s; XI an GND = interner Takt [V]")
    b.teil("Transistor_BJT:SS8550", "Q501", "S8550", fp="Package_TO_SOT_SMD:SOT-23", lcsc="C397181",
           netze={"B": "HX_BASE", "E": "VSUP_HX", "C": "HX_AVDD"},
           info="PNP-Regler für AVDD nach HX711-Datenblatt Fig. 1 [V]; Ersatz C111271; Pinfolge des Lieferteils mit 1 B, 2 E, 3 C vergleichen [P]")
    b.teil("Device:R", "R503", "20k 1%", fp=R0603, netze={"1": "HX_AVDD", "2": "HX_VFB"},
           info="AVDD = 1,25 V × (1 + 20k/8,2k) = 4,30 V (waage.md 3)")
    b.teil("Device:R", "R504", "8,2k 1%", fp=R0603, netze={"1": "HX_VFB", "2": "GND"})
    b.teil("Device:C", "C505", "10µ 10V X5R", fp=C0805, netze={"1": "HX_AVDD", "2": "GND"})
    b.teil("Device:C", "C506", "100n", fp=C0603, netze={"1": "HX_AVDD", "2": "GND"}, info="direkt an AVDD (Pin 3)")
    b.teil("power:PWR_FLAG", "#FLG502", "PWR_FLAG", netze={"1": "HX_AVDD"}, info="AVDD kommt vom Kollektor Q501 (für den ERC kein Treiber)")
    b.teil("Device:C", "C507", "100n", fp=C0603, netze={"1": "HX_VBG", "2": "GND"}, info="VBG-Abblockung (Datenblatt Fig. 1)")
    b.teil("Device:C", "C508", "100n", fp=C0603, netze={"1": "3V3_SW", "2": "GND"}, info="DVDD an 3V3_SW: Pegel wie STM32 (waage.md 3)")
    b.teil("Device:R", "R507", "0", fp=R0603, netze={"1": "HX_INN", "2": "HX_INB"},
           info="Kanal B unbenutzt, auf Gleichtakt der Brücke gelegt [A]; bei Störung der Messung auslöten [P]")
    b.teil("Device:R", "R508", "1k", fp=R0603, netze={"1": "HX_PD_SCK", "2": "HX_SCK"},
           info="begrenzt den Strom, wenn PB9 high ist und 3V3_SW aus (mcu-funk.md 4)")
    b.teil("Device:R", "R509", "1k", fp=R0603, netze={"1": "HX_DOUT_IC", "2": "HX_DOUT"})
    # --- 3 Wägezelle (waage.md 4, anschluesse.md J4) ---------------------------
    b.teil("Connector_Generic:Conn_01x05", "J501", "Wägezelle", **klemme(5),
           netze={"1": "GND", "2": "GND", "3": "ZELLE_SN", "4": "ZELLE_SP", "5": "ZELLE_EP"},
           info="= J4 in anschluesse.md: 1 Schirm, 2 E−, 3 S−, 4 S+, 5 E+; DEGSON 15EDGRC-3.5-05P; Schirm nur hier an Masse")
    b.teil("Power_Protection:TPD4E05U06DQA", "D501", "TPD4E05U06DQAR", fp="Package_SON:USON-10_2.5x1.0mm_P0.5mm", lcsc="C138714",
           netze={"D1+": "ZELLE_EP", "D1-": "ZELLE_SP", "D2+": "ZELLE_SN", "D2-": "NC", "6": "NC", "7": "NC", "9": "NC",
                  "10": "NC", "GND": "GND"},
           info="5,5 V, Leckstrom 0,01 nA typ./10 nA max. (anschluesse.md 2) [V]; direkt hinter J501; 4. Kanal frei")
    b.teil("Device:FerriteBead_Small", "FB502", "Ferrit ≤ 0,1 Ω", fp="Inductor_SMD:L_0603_1608Metric",
           netze={"1": "HX_AVDD", "2": "ZELLE_EP"},
           info="E+ aus AVDD; Gleichstromwiderstand ≤ 0,1 Ω, sonst ändert sich die Brückenspeisung mit der Temperatur [A]; Teil wählen [P]")
    b.teil("Device:R", "R505", "100", fp=R0603, netze={"1": "ZELLE_SP", "2": "HX_INP"}, info="waage.md 4")
    b.teil("Device:R", "R506", "100", fp=R0603, netze={"1": "ZELLE_SN", "2": "HX_INN"})
    b.teil("Device:C", "C510", "100n", fp=C0603, netze={"1": "HX_INP", "2": "HX_INN"}, info="Differenzfilter S+/S−")
    b.teil("Device:C", "C511", "10n C0G", fp=C0603, netze={"1": "HX_INP", "2": "GND"}, info="Gleichtaktfilter; C0G für gleiche Werte S+/S− [A]")
    b.teil("Device:C", "C512", "10n C0G", fp=C0603, netze={"1": "HX_INN", "2": "GND"})
    zeichne_waage(b, {t.ref: t for t in b.teile})
    return b


def zeichne_waage(b, T):
    """Oben die 5-V-Kette von links nach rechts (SYS → TPS61240 → Ferrit → VSUP_HX → PNP → HX711), darunter
    der AVDD-Regler links vom HX711, rechts die Leitungen zum MCU. Unten links die Klemme J501 mit Filter;
    ESD-Baustein und HX711-Eingänge sind über Netznamen verbunden."""
    S, D, L = b.setze, b.draht, b.label
    yr = 119.38                       # Schiene SYS → 5 V → VSUP_HX
    yb, ya = 129.54, 137.16           # Zeilen HX_BASE und HX_AVDD
    b.text("1  5-V-Wandler an SYS, nur beim Wiegen an (WAAGE_EIN = PB10, 100 kΩ nach GND)", 30.48, 99.06, 2.0)
    b.text("2  HX711: AVDD 4,30 V über PNP, DVDD an 3V3_SW, 10 Werte/s", 198.12, 99.06, 2.0)
    b.text("AVDD = 1,25 V × (1 + 20 kΩ / 8,2 kΩ) = 4,30 V; VSUP − AVDD ≥ 0,1 V", 198.12, 106.68, 1.5)
    b.text("3  Wägezelle J501 (= J4): E+ über Ferrit aus AVDD, S± mit 100 Ω und Filter", 30.48, 152.4, 2.0)
    b.text("ESD direkt hinter J501, Leckstrom ≤ 10 nA", 30.48, 199.39, 1.5)
    b.text("4  Zum MCU: je 1 kΩ in Reihe", 297.18, 172.72, 2.0)
    b.text("Regeln (waage.md 7): Wandler nur beim Wiegen an, nie während einer Funkübertragung; erst 3V3_SW, dann WAAGE_EIN; "
           "SCK low, solange VSUP aus ist.", 30.48, 236.22, 1.5)
    b.text("Layout: Analogmasse und Zellenleitungen getrennt von Wandler und Funk; Wandler weit weg vom Mikrofoneingang; "
           "Schirm nur auf der Platine an Masse.", 30.48, 241.3, 1.5)

    # --- 1 5-V-Wandler ---------------------------------------------------------
    U = S(T["U501"], 86.36, 124.46, text="oben")
    D((30.48, yr), U.p("VIN"))
    L("SYS", 30.48, yr, 180)
    S(T["C501"], 38.1, 123.19)
    S(T["L501"], 58.42, 123.19)
    D(T["L501"].p("2"), (68.58, 127.0), (68.58, U.p("L")[1]), U.p("L"))
    L("L_5V", 69.85, U.p("L")[1])
    D(U.p("EN"), (71.12, U.p("EN")[1]), (71.12, 137.16), (30.48, 137.16))
    L("WAAGE_EIN", 30.48, 137.16, 180)
    S(T["R501"], 45.72, 140.97)
    D(U.p("GND"), (U.p("GND")[0], 137.16), (U.p("EP")[0], 137.16), U.p("EP"))
    b.versorgung("GND", U.p("GND")[0], 137.16, "unten")
    D(U.p("FB"), (99.06, U.p("FB")[1]), (99.06, yr))
    F = S(T["FB501"], 142.24, yr, rot=90, text="oben")
    D(U.p("VOUT"), F.p("1"))
    S(T["C502"], 106.68, 123.19)
    S(T["R502"], 124.46, 123.19)
    L("5V_WAAGE", 127.0, yr)
    D(F.p("2"), (261.62, yr))
    S(T["C503"], 152.4, 123.19)
    S(T["C504"], 170.18, 123.19)
    L("VSUP_HX", 177.8, yr)
    S(T["#FLG501"], 193.04, yr, text="oben")

    # --- 2 HX711 und AVDD-Regler -----------------------------------------------
    H = S(T["U502"], 264.16, 157.48, text=(267.97, 182.88))
    D(H.p("VSUP"), (H.p("VSUP")[0], yr))
    Q = S(T["Q501"], 226.06, yb, rot=180, text="links")
    D(Q.p("E"), (Q.p("E")[0], yr))
    D(Q.p("B"), (248.92, yb), (248.92, H.p("BASE")[1]), H.p("BASE"))
    L("HX_BASE", 233.68, yb)
    D(Q.p("C"), (Q.p("C")[0], ya))
    D((180.34, ya), (246.38, ya), (246.38, H.p("AVDD")[1]), H.p("AVDD"))
    S(T["FB502"], 180.34, 139.7, text="links")
    S(T["#FLG502"], 193.04, ya, text="oben")
    L("HX_AVDD", 181.61, ya)
    S(T["C505"], 203.2, 140.97, text="links")
    S(T["C506"], 213.36, 140.97)
    S(T["R503"], 233.68, 140.97, text="links")
    S(T["R504"], 233.68, 148.59, text="links")
    D(T["R503"].p("2"), (243.84, 144.78), (243.84, H.p("VFB")[1]), H.p("VFB"))
    L("HX_VFB", 234.95, 144.78)
    # Eingänge über Netznamen, Kanal B über R507 an INA−
    for pin, netz in (("INA+", "HX_INP"), ("INA-", "HX_INN")):
        D(H.p(pin), (243.84, H.p(pin)[1]))
        L(netz, 243.84, H.p(pin)[1], 180)
    S(T["R507"], 246.38, 163.83, text="links")
    D(H.p("INB-"), (238.76, H.p("INB-")[1]))
    D(H.p("INB+"), (248.92, H.p("INB+")[1]), (248.92, H.p("INB-")[1]))
    L("HX_INB", 238.76, H.p("INB-")[1], 180)
    D(H.p("VBG"), (238.76, H.p("VBG")[1]))
    S(T["C507"], 238.76, 176.53, text="links")
    L("HX_VBG", 240.03, H.p("VBG")[1])
    # DVDD an 3V3_SW
    D(H.p("DVDD"), (H.p("DVDD")[0], 127.0), (289.56, 127.0))
    S(T["C508"], 279.4, 130.81)
    L("3V3_SW", 289.56, 127.0)
    # Leitungen zum MCU
    R9 = S(T["R509"], 304.8, 142.24, rot=90, text="oben")
    D(H.p("DOUT"), (281.94, H.p("DOUT")[1]), (281.94, 142.24), R9.p("1"))
    D(R9.p("2"), (320.04, 142.24))
    L("HX_DOUT_IC", 283.21, 142.24)
    L("HX_DOUT", 320.04, 142.24)
    R8 = S(T["R508"], 304.8, H.p("PD_SCK")[1], rot=90, text="unten")
    D(H.p("PD_SCK"), R8.p("1"))
    D(R8.p("2"), (320.04, H.p("PD_SCK")[1]))
    L("HX_PD_SCK", 283.21, H.p("PD_SCK")[1])
    L("HX_SCK", 320.04, H.p("PD_SCK")[1])

    # --- 3 Wägezelle -----------------------------------------------------------
    J = S(T["J501"], 45.72, 177.8, rot=180, text="links")
    D(J.p("5"), (55.88, J.p("5")[1]), (55.88, 160.02), (180.34, 160.02), T["FB502"].p("2"))
    L("ZELLE_EP", 60.96, 160.02)
    R5 = S(T["R505"], 96.52, J.p("4")[1], rot=90, text="oben")
    D(J.p("4"), R5.p("1"))
    L("ZELLE_SP", 60.96, J.p("4")[1])
    y_sn = 182.88
    R6 = S(T["R506"], 96.52, y_sn, rot=90, text="unten")
    D(J.p("3"), (58.42, J.p("3")[1]), (58.42, y_sn), R6.p("1"))
    L("ZELLE_SN", 60.96, y_sn)
    D(J.p("1"), (53.34, J.p("1")[1]), (53.34, J.p("2")[1]), J.p("2"))
    b.versorgung("GND", 53.34, J.p("1")[1], "unten")
    D(R5.p("2"), (165.1, R5.p("2")[1]))
    D(R6.p("2"), (139.7, y_sn))
    S(T["C510"], 111.76, 179.07)
    S(T["C512"], 127.0, 186.69)
    S(T["C511"], 152.4, 179.07)
    L("HX_INP", 165.1, R5.p("2")[1])
    L("HX_INN", 139.7, y_sn)
    E = S(T["D501"], 78.74, 215.9, text=(95.25, 226.06))
    for pin in ("D1+", "D1-", "D2+"):
        stub(b, E, pin, 7.62)


def mikrofon(p):
    """Blatt Mikrofon (HW-07, mikrofon.md 2, anschluesse.md J5, Lastenheft A1–A7): zwei Mikrofone mit verschiedener
    Bauart am Audio-ADC TLV320ADC3101 (U601): Elektret analog, pseudo-differenziell an IN2L(P)/IN3L(M) (linker Kanal),
    MEMS IM69D127 als PDM an DMDIN/DMCLK (rechter Kanal). Ausgang I²S an I2S3 des STM32 (PB12 CK, PA15 WS, PB5 SD),
    Einstellung über I²C (Adresse 0x18). RJ45-Buchse J601 (= J5) für Cat7 S/FTP (4 Paare) mit ESD.
    Kennzeichnung: [V] Datenblatt, [A] Annahme/Rechnung, [P] am Muster bzw. vor der Bestellung prüfen."""
    b = p.blatt("Mikrofon", "mikrofon.kicad_sch",
                titel="Mikrofon: Audio-ADC TLV320ADC3101, Elektret (analog) + MEMS IM69D127 (PDM), I²S an I2S3")
    # --- 1 Versorgung ---------------------------------------------------------------------------
    b.teil("Device:FerriteBead_Small", "FB601", "600R@100MHz", fp="Inductor_SMD:L_0603_1608Metric",
           netze={"1": "3V3_SW", "2": "MIC_FB"}, info="wie FB301; Teil wählen [P]")
    b.teil("Device:R", "R602", "10", fp=R0603, netze={"1": "MIC_FB", "2": "3V3_ANA"},
           info="mit C601 RC-Tiefpass ca. 720 Hz; Abfall ca. 60 mV bei 6 mA (AVDD + MICBIAS) [A]")
    b.teil("Device:C", "C601", "22µ 10V X5R", fp=C0805, netze={"1": "3V3_ANA", "2": "GND"},
           info="wirksam bei 3,3 V geringer (DC-Bias); für die Siebung unkritisch [A]")
    b.teil("Device:C", "C602", "100n", fp=C0603, netze={"1": "3V3_ANA", "2": "GND"})
    b.teil("power:PWR_FLAG", "#FLG601", "PWR_FLAG", netze={"1": "3V3_ANA"},
           info="3V3_ANA aus 3V3_SW über FB601 und R602 (passive Bauteile sind für den ERC kein Treiber)")
    b.teil("Bienen:TPS70933DBV", "U602", "TPS70918DBVR", fp="Package_TO_SOT_SMD:SOT-23-5",
           netze={"IN": "3V3_SW", "EN": "3V3_SW", "OUT": "1V8_ADC", "GND": "GND"},
           info="DVDD 1,8 V für U601 (1,65–1,95 V [V]); gleiche Familie und Pinfolge wie U204 (TI SBVS186, DBV) [V]; "
                "1 µA Ruhestrom; LCSC [P]")
    b.teil("Device:C", "C609", "1µ", fp=C0603, netze={"1": "3V3_SW", "2": "GND"}, info="Eingang U602")
    b.teil("Device:C", "C610", "4,7µ 16V X7R", fp=C0805, netze={"1": "1V8_ADC", "2": "GND"},
           info="TPS709 verlangt ≥ 2,2 µF am Ausgang (wie C212)")
    b.teil("Device:FerriteBead_Small", "FB602", "600R@100MHz", fp="Inductor_SMD:L_0603_1608Metric",
           netze={"1": "3V3_SW", "2": "3V3_MEMS"}, info="Versorgung MEMS-Mikrofon über das Kabel, getrennt von 3V3_ANA")
    b.teil("Device:C", "C611", "1µ", fp=C0603, netze={"1": "3V3_MEMS", "2": "GND"},
           info="am Mikrofon zusätzlich 100 nF (Infineon) – auf der fertigen Mikrofonplatine prüfen [P]")
    b.teil("power:PWR_FLAG", "#FLG603", "PWR_FLAG", netze={"1": "3V3_MEMS"}, info="3V3_MEMS aus 3V3_SW über FB602")
    # --- 2 Audio-ADC ------------------------------------------------------------------------------
    b.teil("Bienen:TLV320ADC3101", "U601", "TLV320ADC3101IRGET", fp="Package_DFN_QFN:VQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm",
           netze={"IN2L(P)": "MIC_INP", "IN3L(M)": "MIC_INN", "IN1L(P)": "NC", "IN1R(M)": "NC", "IN2R(P)": "NC",
                  "IN3R(M)": "NC", "MICBIAS1": "MICBIAS", "MICBIAS2": "NC", "DMDIN/GPIO1": "PDM_DATA",
                  "DMCLK/GPIO2": "PDM_CLK_ADC", "BCLK": "I2S_CK", "WCLK": "I2S_WS", "DOUT": "I2S_SD", "MCLK": "GND",
                  "SCL": "I2C_SCL", "SDA": "I2C_SDA", "~{RESET}": "ADC_RESET", "I2C_ADR0": "GND", "I2C_ADR1": "GND",
                  "AVDD": "3V3_ANA", "DVDD": "1V8_ADC", "IOVDD": "3V3_SW", "AVSS": "GND", "DVSS": "GND", "EP": "GND"},
           info="Elektret links (IN2L/IN3L, pseudo-differenziell), PDM-Mikrofon rechts (DMDIN, Abschnitt 10.3.12.6: "
                "Digitalmikrofon je Kanal wählbar [V]); Takt aus BCLK über die PLL (MCLK unbenutzt, an GND); "
                "DMCLK = ADC_MOD_CLK = AOSR·fS muss 2,8–6,2 MHz sein [V] → fS 24 576 Hz, AOSR 128 = 3,146 MHz "
                "(IM69D127-Band 2,9–3,3 MHz [V]); I²C 0x18; LCSC [P]")
    for ref, wert, netz, fp, info in (
            ("C612", "100n", "3V3_ANA", C0603, "AVDD (Pin 10), TI Abb. 48: 0,1 µF + 1 µF je Versorgung"),
            ("C613", "1µ", "3V3_ANA", C0603, "AVDD"),
            ("C614", "100n", "1V8_ADC", C0603, "DVDD (Pin 22)"),
            ("C615", "1µ", "1V8_ADC", C0603, "DVDD"),
            ("C616", "100n", "3V3_SW", C0603, "IOVDD (Pin 21)"),
            ("C617", "1µ", "3V3_SW", C0603, "IOVDD")):
        b.teil("Device:C", ref, wert, fp=fp, netze={"1": netz, "2": "GND"}, info=info)
    b.teil("Device:R", "R609", "10k", fp=R0603, netze={"1": "3V3_SW", "2": "ADC_RESET"},
           info="Reset nach dem Einschalten (RC 1 ms, alle Versorgungen zuerst stabil, Abschnitt 10.3.1 [V]); "
                "danach Software-Reset über I²C; kein freier GPIO (HW-07) [A]")
    b.teil("Device:C", "C618", "100n", fp=C0603, netze={"1": "ADC_RESET", "2": "GND"})
    # --- 3 Elektret, pseudo-differenziell ------------------------------------------------------------------
    b.teil("Device:R", "R610", "1k", fp=R0603, netze={"1": "MICBIAS", "2": "MIC_P"},
           info="Vorspannung aus MICBIAS1 (2,5 V eingestellt, max. 4 mA [V]); mit R611 symmetrisch, Kapsel schwebend "
                "über dem Kabelpaar; Spannung an der Kapsel ≥ 1,5 V bei ≤ 0,5 mA Kapselstrom [A/P]")
    b.teil("Device:R", "R611", "1k", fp=R0603, netze={"1": "MIC_N", "2": "GND"}, info="Gegenstück zu R610")
    b.teil("Device:C", "C621", "1µ", fp=C0603, netze={"1": "MICBIAS", "2": "GND"},
           info="MICBIAS-Siebung; TI-Rauschangabe mit 1 µF [V]")
    b.teil("Device:C", "C619", "1µ X7R", fp=C0603, netze={"1": "MIC_P", "2": "MIC_INP"},
           info="Koppelkondensator; mit ca. 35 kΩ Eingangswiderstand 4,5 Hz (Abschnitt 10.3.10 [V])")
    b.teil("Device:C", "C620", "1µ X7R", fp=C0603, netze={"1": "MIC_N", "2": "MIC_INN"}, info="Koppelkondensator")
    b.teil("Device:C", "C622", "100p C0G", fp=C0603, netze={"1": "MIC_P", "2": "GND"}, info="HF-Ableitung an der Klemme")
    b.teil("Device:C", "C623", "100p C0G", fp=C0603, netze={"1": "MIC_N", "2": "GND"}, info="HF-Ableitung an der Klemme")
    # --- 4 PDM-Mikrofon: Takttreiber und Datenleitung ----------------------------------------------------------
    b.teil("74xGxx:74LVC1G17", "U603", "74LVC1G17GW", fp="Package_TO_SOT_SMD:SOT-353_SC-70-5",
           netze={"2": "PDM_CLK_ADC", "4": "PDM_CLK_BUF", "5": "3V3_SW", "3": "GND"},
           info="Schmitt-Puffer treibt den PDM-Takt ins Kabel: IM69D127 verlangt Flanken ≤ 13 ns [V], Cat7 0,5–1 m "
                "ca. 50–110 pF [A]; LCSC [P]")
    b.teil("Device:C", "C624", "100n", fp=C0603, netze={"1": "3V3_SW", "2": "GND"}, info="an U603")
    b.teil("Device:R", "R612", "33", fp=R0603, netze={"1": "PDM_CLK", "2": "PDM_CLK_BUF"},
           info="Serienterminierung am Taktausgang [A]; Flanke am Mikrofon messen (T4) [P]")
    b.teil("Device:R", "R613", "22", fp=R0603, netze={"1": "PDM_DATA_K", "2": "PDM_DATA"},
           info="Schutzwiderstand vor DMDIN; Quellterminierung ca. 100 Ω sitzt am Mikrofon (Infineon) [P]")
    # --- 5 Klemme und ESD -----------------------------------------------------------------------------------
    b.teil("Connector:RJ45_Shielded", "J601", "Mikrofone", fp="Connector_RJ:RJ45_RCH_RC01937",
           netze={"1": "GND", "2": "PDM_CLK", "3": "PDM_DATA_K", "4": "3V3_MEMS", "5": "GND", "6": "GND",
                  "7": "MIC_P", "8": "MIC_N", "SH": "GND"},
           info="= J5 in anschluesse.md: RJ45 geschirmt ohne Übertrager; Paare nach T568B: 1/2 GND+CLK, 3/6 DATA+GND, "
                "4/5 VDD+GND, 7/8 MIC+/MIC− (Elektret am Rand, weit weg vom Takt); Schirm nur hier an Masse; "
                "Teil und LCSC-Nummer wählt der Layouter [P]; NICHT mit Netzwerk-/PoE-Geräten verbinden")
    b.teil("Power_Protection:ESDS304", "D601", "ESDS304DBVR", fp="Package_TO_SOT_SMD:SOT-23-5",
           netze={"1": "PDM_CLK", "3": "PDM_DATA_K", "4": "MIC_P", "5": "MIC_N", "2": "GND"},
           info="3,6 V, 2,3 pF, Leckstrom 50 nA max. [V: TI SLVSE24]; direkt hinter J601 (anschluesse.md 3); LCSC [P]")
    zeichne_mikrofon(b, {t.ref: t for t in b.teile})
    return b


def zeichne_mikrofon(b, T):
    """Links die Klemme mit ESD und den beiden Mikrofonpfaden, in der Mitte der Audio-ADC, oben die Versorgung.
    Verbindungen zwischen den Gruppen über Netznamen; jeder Pin hängt an einem Draht."""
    S, D, L = b.setze, b.draht, b.label
    b.text("1  Versorgung: 3V3_ANA (AVDD, Ferrit + 10 Ω), 1V8_ADC (DVDD, TPS70918), 3V3_MEMS (Ferrit, über das Kabel)",
           30.48, 35.56, 2.0)
    b.text("2  Audio-ADC TLV320ADC3101: links Elektret (analog), rechts MEMS (PDM); I²S an I2S3, I²C 0x18",
           175.26, 111.76, 2.0)
    b.text("3  RJ45-Buchse J601 (= J5): MIC−, MIC+ (Elektret, MICBIAS 2,5 V über 2 × 1 kΩ), VDD, DATA, CLK (Schmitt-Puffer)",
           30.48, 96.52, 2.0)
    b.text("ESD D601 direkt an J601", 43.18, 236.22, 1.5)
    b.text("Kabel: Cat7 S/FTP mit geschirmtem RJ45-Stecker, 0,5–1 m, Paare T568B; Schirm nur hier an Masse; kein Netzwerk/PoE anstecken. "
           "Mikrofonkopf am Gitterboden: fertige IM69D127-Platine (100 nF, ca. 100 Ω in DATA, L/R-Wahl) + Elektretkapsel.",
           30.48, 264.16, 1.5)
    b.text("Firmware: 3V3_SW aus → I²S- und I²C-Pins hochohmig (keine Rückspeisung in U601); fS 24 576 Hz, "
           "AOSR 128, DMCLK 3,146 MHz; Messung ohne Funk und ohne 5-V-Wandler (mikrofon.md).", 30.48, 269.24, 1.5)

    def zwei(ref, x, y, laenge=2.54, rot=0):
        t = S(T[ref], x, y, rot=rot, text="rechts")
        for pin in ("1", "2"):
            if t.pin_netz.get(pin) != "GND":
                stub(b, t, pin, laenge)
        return t

    # --- 1 Versorgung (oben) ---------------------------------------------------------------------
    y1 = 50.8
    zwei("FB601", 35.56, y1)
    zwei("R602", 50.8, y1)
    zwei("C601", 66.04, y1)
    zwei("C602", 81.28, y1)
    F1 = S(T["#FLG601"], 96.52, y1 - 3.81, text="oben")
    stub(b, F1, "1", 5.08)
    U2 = S(T["U602"], 132.08, y1, text="oben")
    for pin in ("IN", "EN", "OUT"):
        stub(b, U2, pin, 5.08)
    zwei("C609", 157.48, y1)
    zwei("C610", 172.72, y1)
    zwei("FB602", 198.12, y1)
    F3 = S(T["#FLG603"], 228.6, y1 - 3.81, text="oben")
    stub(b, F3, "1", 5.08)
    # Abblockkondensatoren U601 (oben rechts, nahe AVDD/DVDD/IOVDD)
    for i, ref in enumerate(("C612", "C613", "C614", "C615", "C616", "C617")):
        zwei(ref, 254.0 + 12.7 * i, y1)
    zwei("R609", 254.0, 78.74)
    zwei("C618", 266.7, 78.74)

    # --- 2 Audio-ADC (Mitte) -------------------------------------------------------------------------
    U = S(T["U601"], 220.98, 149.86, text=(233.68, 116.84))
    for pin in ("IN2L(P)", "IN3L(M)", "MICBIAS1", "DMDIN/GPIO1", "DMCLK/GPIO2",
                "BCLK", "WCLK", "DOUT", "SCL", "SDA", "~{RESET}"):
        stub(b, U, pin, 10.16)
    for pin in ("AVDD", "DVDD", "IOVDD"):
        stub(b, U, pin, 5.08)

    # --- 3–5 Klemme und Signalwege (links): je Klemmenpin eine Zeile von links nach rechts ------------------
    J = S(T["J601"], 38.1, 139.7, rot=0, text="links")
    zeilen = {"8": 106.68, "7": 124.46, "4": 157.48, "3": 172.72, "2": 187.96}     # MIC−, MIC+, VDD, DATA, CLK
    knick = {"8": 53.34, "7": 58.42, "2": 53.34, "3": 58.42, "4": 63.5}
    for pin, y in zeilen.items():
        D(J.p(pin), (knick[pin], J.p(pin)[1]), (knick[pin], y), (68.58, y))

    def quer(ref, x, y):                    # Zweipol in der Zeile (Pin 1 links)
        return S(T[ref], x, y, rot=90, text="oben")

    def ab(ref, x, y):                      # Zweipol von der Zeile nach unten (Pin 1 oben an der Zeile)
        return S(T[ref], x, y + 3.81, text="rechts")

    # MIC− : HF-C und 1 kΩ nach GND, Koppel-C zum ADC
    y = zeilen["8"]
    ab("C623", 66.04, y)
    ab("R611", 81.28, y)
    C = quer("C620", 106.68, y)
    D((68.58, y), C.p("1"))
    D(C.p("2"), (127.0, y))
    L("MIC_INN", 127.0, y)
    L("MIC_N", 55.88, y)
    # MIC+ : HF-C, Vorspannung von MICBIAS über 1 kΩ, Koppel-C zum ADC
    y = zeilen["7"]
    ab("C622", 76.2, y)
    R = S(T["R610"], 96.52, y - 3.81, text="rechts")
    stub(b, R, "1", 2.54)
    C = quer("C619", 106.68, y)
    D((68.58, y), C.p("1"))
    D(C.p("2"), (127.0, y))
    L("MIC_INP", 127.0, y)
    L("MIC_P", 60.96, y)
    S(T["C621"], 139.7, 101.6, text="rechts")
    stub(b, T["C621"], "1", 2.54)
    # DATA : 22 Ω zu DMDIN
    y = zeilen["3"]
    R = quer("R613", 81.28, y)
    D((68.58, y), R.p("1"))
    D(R.p("2"), (127.0, y))
    L("PDM_DATA", 127.0, y)
    L("PDM_DATA_K", 60.96, y)
    # CLK : DMCLK → Schmitt-Puffer → 33 Ω → Klemme (Signal läuft hier von rechts nach links)
    y = zeilen["2"]
    R = quer("R612", 81.28, y)
    D((68.58, y), R.p("1"))
    B = S(T["U603"], 109.22, y, rot=180, text=(99.06, y + 7.62))
    D(R.p("2"), B.p("4"))
    stub(b, B, "2", 7.62)
    stub(b, B, "5", 2.54)
    S(T["C624"], 132.08, y + 16.51, text="rechts")
    stub(b, T["C624"], "1", 2.54)
    L("PDM_CLK", 60.96, y)
    L("PDM_CLK_BUF", 88.9, y)
    # VDD : 3V3_MEMS aus FB602 (oben), 1 µF an der Klemme
    y = zeilen["4"]
    ab("C611", 76.2, y)
    D((68.58, y), (76.2, y))
    L("3V3_MEMS", 68.58, y)
    # ESD direkt an der Klemme, Anschluss über Netznamen
    E = S(T["D601"], 30.48, 236.22, text=(38.1, 246.38))
    for pin in ("1", "3", "4", "5"):
        stub(b, E, pin, 5.08)


def anschluesse(p):
    """Blatt Anschlüsse (anschluesse.md 1–3, Lastenheft M4/M5/F10, HW26-04/-09/-13): Sensorklemmen DS18B20 (J701/J702 = J6/J7)
    und BME280 (J703 = J8) mit ESD-Arrays und Pull-ups an der geschalteten Schiene, Erweiterungsleiste J704 (= J11).
    Kennzeichnung: [V] Datenblatt, [A] Annahme/Rechnung, [P] vor der Bestellung bzw. am Muster prüfen."""
    b = p.blatt("Anschlüsse", "anschluesse.kicad_sch", titel="Anschlüsse: DS18B20, BME280, Erweiterungsleiste")
    klemme_text = "DEGSON 15EDGRC-3.5-%02dP"
    # --- 1 DS18B20 an 1-Wire (PA8) ------------------------------------------------
    b.teil("Connector_Generic:Conn_01x03", "J701", "DS18B20 Nr. 1", **klemme(3),
           netze={"1": "GND", "2": "ONEWIRE", "3": "3V3_SW"}, info="= J6 (TempIn): 1 GND, 2 DQ, 3 3V3_SW; " + klemme_text % 3)
    b.teil("Connector_Generic:Conn_01x03", "J702", "DS18B20 Nr. 2", **klemme(3),
           netze={"1": "GND", "2": "ONEWIRE", "3": "3V3_SW"}, info="= J7 (TempIn2), selber Bus; " + klemme_text % 3)
    b.teil("Device:R", "R701", "4,7k", fp=R0603, netze={"1": "3V3_SW", "2": "ONEWIRE"},
           info="1-Wire-Pull-up an der geschalteten Schiene (HW26-04: keine Rückspeisung im Standby); 3-adrig, nicht parasitär")
    b.teil("Power_Protection:ESDS304", "D701", "ESDS304DBVR", fp="Package_TO_SOT_SMD:SOT-23-5",
           netze={"1": "ONEWIRE", "3": "3V3_SW", "4": "NC", "5": "NC", "2": "GND"},
           info="ein Array für J701 + J702 (anschluesse.md 1), zwischen beiden Klemmen; LCSC [P]")
    # --- 2 BME280 an I²C (PB6/PB7) ---------------------------------------------------
    b.teil("Connector_Generic:Conn_01x06", "J703", "BME280", **klemme(6),
           netze={"1": "GND", "2": "GND", "3": "I2C_SDA", "4": "I2C_SCL", "5": "3V3_SW", "6": "NC"},
           info="= J8: 1 Schirm, 2 GND, 3 SDA, 4 SCL, 5 3V3_SW, 6 frei (Verwechslungsschutz gegen J4, 6-polig); " + klemme_text % 6)
    b.teil("Device:R", "R702", "1,8k", fp=R0603, netze={"1": "I2C_SDA", "2": "3V3_SW"},
           info="1,8 kΩ: Anstiegszeit auch mit falschem Kabel ≤ 1000 ns (anschluesse.md 3.1, i2c_leitung.py)")
    b.teil("Device:R", "R703", "1,8k", fp=R0603, netze={"1": "3V3_SW", "2": "I2C_SCL"})
    b.teil("Power_Protection:ESDS304", "D702", "ESDS304DBVR", fp="Package_TO_SOT_SMD:SOT-23-5",
           netze={"1": "I2C_SDA", "3": "I2C_SCL", "4": "3V3_SW", "5": "NC", "2": "GND"},
           info="direkt hinter J703; 2,3 pF je Kanal in der Buskapazität enthalten (i2c_leitung.py); LCSC [P]")
    # --- 3 Erweiterungsleiste (innen) ----------------------------------------------------
    b.teil("Connector_Generic:Conn_02x06_Odd_Even", "J704", "Erweiterung",
           fp="Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical",
           netze={"1": "+3V3", "2": "3V3_SW", "3": "GND", "4": "GND", "5": "I2C_SDA", "6": "I2C_SCL", "7": "DBG_TX",
                  "8": "DBG_RX", "9": "BLE_RXD", "10": "BLE_TXD", "11": "BLE_MODE", "12": "GND"},
           info="= J11 (HW26-13): innen, ohne ESD; I²C-Geräte hier zählen zur Buskapazität (anschluesse.md 3.1); Pins 9–11 seit HW-09 "
                "Modul-UART und Modus des BLE-Moduls (Firmware-Update des Moduls: Pin 11 an Pin 12); keine freien GPIOs mehr "
                "(PB13 Lastschalter BLE, PA15/PB12 I²S seit HW-07)")
    zeichne_anschluesse(b, {t.ref: t for t in b.teile})
    return b


def zeichne_anschluesse(b, T):
    """Links die Außenklemmen (Masse an Pin 1 unten), rechts die Leitungen zum MCU; ESD-Arrays direkt neben den
    Klemmen, über Netznamen angeschlossen. Rechts die Erweiterungsleiste J704 mit Netznamen an jedem Signal."""
    S, D, L = b.setze, b.draht, b.label
    b.text("1  DS18B20 (1-Wire, PA8): J701 = J6, J702 = J7, gemeinsamer Bus, Pull-up 4,7 kΩ an 3V3_SW", 30.48, 60.96, 2.0)
    b.text("2  BME280 (I²C, PB6/PB7): J703 = J8, 6-polig, Pull-ups 1,8 kΩ an 3V3_SW, Takt 50 kHz, Kabel ≤ 1 m", 30.48, 137.16, 2.0)
    b.text("3  Erweiterung J704 = J11 (innen, ohne ESD); Pin 9–11: BLE-Modul (HW-09)", 233.68, 71.12, 2.0)
    b.text("Regeln (anschluesse.md 1, 4): Masse an Pin 1, Versorgung am anderen Ende; jede Klemme eigene Polzahl; ESD direkt hinter "
           "der Klemme mit kurzer Masseanbindung; alle Außenklemmen an einer Kante.", 30.48, 228.6, 1.5)
    b.text("Pull-ups nur an 3V3_SW (HW26-04): im Standby keine Rückspeisung über Sensorleitungen.", 30.48, 233.68, 1.5)

    # --- 1 DS18B20 --------------------------------------------------------------------
    y1, y2, xb = 91.44, 116.84, 66.04
    J1 = S(T["J701"], 40.64, y1, rot=180, text="links")
    J2 = S(T["J702"], 40.64, y2, rot=180, text="links")
    for J in (J1, J2):
        stub(b, J, "3", 5.08)
    D(J1.p("2"), (xb, y1))
    D(J2.p("2"), (xb, y2), (xb, y1))
    D((xb, y1), (139.7, y1))
    L("ONEWIRE", 139.7, y1)
    R1 = S(T["R701"], 111.76, 85.09, text="links")
    D(R1.p("2"), (111.76, y1))
    stub(b, R1, "1", 5.08)
    E1 = S(T["D701"], 86.36, 109.22, text=(93.98, 116.84))
    for pin in ("1", "3"):
        stub(b, E1, pin, 5.08)

    # --- 2 BME280 ------------------------------------------------------------------------
    J3 = S(T["J703"], 40.64, 165.1, rot=180, text="links")
    stub(b, J3, "5", 5.08)
    D(J3.p("1"), (48.26, J3.p("1")[1]), (48.26, J3.p("2")[1]), J3.p("2"))
    b.versorgung("GND", 48.26, J3.p("1")[1], "unten")
    xs = 139.7
    D(J3.p("3"), (xs, J3.p("3")[1]))
    L("I2C_SDA", xs, J3.p("3")[1])
    D(J3.p("4"), (xs, J3.p("4")[1]))
    L("I2C_SCL", xs, J3.p("4")[1])
    R3 = S(T["R703"], 111.76, J3.p("4")[1] - 6.35, text="links")
    D(R3.p("2"), (111.76, J3.p("4")[1]))
    stub(b, R3, "1", 5.08)
    R2 = S(T["R702"], 121.92, J3.p("3")[1] + 6.35, text="rechts")
    D(R2.p("1"), (121.92, J3.p("3")[1]))
    stub(b, R2, "2", 5.08)
    E2 = S(T["D702"], 86.36, 185.42, text=(93.98, 193.04))
    for pin in ("1", "3", "4"):
        stub(b, E2, pin, 5.08)

    # --- 3 Erweiterungsleiste ---------------------------------------------------------------
    X = S(T["J704"], 266.7, 106.68, text="oben")
    for pin in ("5", "7", "9", "11"):           # Pins 9–11 seit HW-09 BLE-Modul (vorher frei)
        stub(b, X, pin, 10.16)
    for pin in ("2", "6", "8", "10"):
        stub(b, X, pin, 10.16)
    # Versorgung: Leitungen außen um die Netznamen herum, damit Symbole und Texte frei stehen
    x1, y1_ = X.p("1")
    D(X.p("1"), (x1 - 5.08, y1_))
    b.versorgung("+3V3", x1 - 5.08, y1_, "oben")
    xl, yb = x1 - 30.48, X.p("12")[1] + 5.08
    D(X.p("3"), (xl, X.p("3")[1]), (xl, yb))
    b.versorgung("GND", xl, yb, "unten")
    xr = X.p("4")[0] + 30.48
    D(X.p("4"), (xr, X.p("4")[1]), (xr, X.p("12")[1]), X.p("12"))
    b.versorgung("GND", xr, X.p("12")[1], "unten")


def pins_von_lib(lib_id):
    from kicad_gen import lib_symbol, pins_von
    return pins_von(lib_symbol(lib_id))


def stub(b, t, pin, laenge=7.62, netz=None):
    """Kurzer Draht vom Pin nach außen, am Ende das Netzlabel (Verbindung zu einem anderen Teil oder Blatt)."""
    nr, _n, _ty, _px, _py, w, _e = t.pin_daten(pin)
    x, y = t.p(pin)
    dx, dy, winkel = {0: (-1, 0, 180), 180: (1, 0, 0), 90: (0, 1, 270), 270: (0, -1, 90)}[t.pin_winkel(w)]
    ende = (round(x + dx * laenge, 4), round(y + dy * laenge, 4))
    b.draht((x, y), ende)
    b.label(netz or t.pin_netz[nr], ende[0], ende[1], winkel)


def versorgung(p):
    b = p.blatt("Versorgung", "versorgung.kicad_sch", titel="Versorgung: Solar, Lader, 3,3 V, Sensorschiene")

    eingang = [
        b.teil("Connector_Generic:Conn_01x02", "J201", "Solar 1", **klemme(2),
               netze={"1": "GND", "2": "PV1"}, info="DEGSON 15EDGRC-3.5-02P (einreihig, SCH26-13)"),
        b.teil("Connector_Generic:Conn_01x02", "J202", "Solar 2", **klemme(2),
               netze={"1": "GND", "2": "PV2"}, info="wie J201"),
        b.teil("Diode:SS34", "D201", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "PV1", "K": "VIN_LADER"}, info="je Panel eine Schottky"),
        b.teil("Diode:SS34", "D202", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "PV2", "K": "VIN_LADER"}),
        b.teil("Diode:SS34", "D203", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "VBUS", "K": "VIN_LADER"}, info="Ladepads J301 (5 V, HW-09): lädt, speist nie ins Panel, sperrt Verpolung"),
        b.teil("Diode:SMAJ12A", "D204", "SMAJ12A", fp="Diode_SMD:D_SMA", netze={"1": "VIN_LADER", "2": "GND"},  # Pin 1 = Kathode
               info="TVS 12 V, begrenzt Störungen unter 25 V (BQ25185 abs.)"),
        b.teil("Device:C", "C201", "4,7µ 50V X7R", fp=C1206, netze={"1": "VIN_LADER", "2": "GND"}, info="≥ 1 µF an IN; 50 V wegen 25 V abs. am Eingang und DC-Bias (SCH26-08)"),
        b.teil("Device:C", "C202", "100n 50V", fp=C0603, netze={"1": "VIN_LADER", "2": "GND"}),
        b.teil("Device:R", "R201", "3,3M", fp=R0603, netze={"1": "VIN_LADER", "2": "ADC_SOLAR"}, info="HW26-08: 25 V → 3,12 V"),
        b.teil("Device:R", "R202", "470k", fp=R0603, netze={"1": "ADC_SOLAR", "2": "GND"}),
        b.teil("Device:C", "C203", "100n", fp=C0603, netze={"1": "ADC_SOLAR", "2": "GND"}, info="Ladung für die ADC-Abtastung"),
        b.teil("power:PWR_FLAG", "#FLG201", "PWR_FLAG", netze={"1": "VIN_LADER"}, info="Quellen: Panels an J201/J202 und VBUS über D201–D203; Klemmen sind für den ERC passive Pins"),
        b.teil("power:PWR_FLAG", "#FLG202", "PWR_FLAG", netze={"1": "GND"}, info="Bezug über die Klemmen J201/J202 und die Zelle über Q801 (passive Pins)"),
    ]

    lader = [
        b.teil("Bienen:BQ25185", "U201", "BQ25185DLHR", fp="Bienen:WSON-10-1EP_2.2x2mm_DLH0010A",
               netze={"IN": "VIN_LADER", "SYS": "SYS", "BAT": "VBAT", "~{CE}": "CE_LADEN", "TS/~{MR}": "NTC",
                      "ISET": "ISET", "ILIM/VSET": "ILIM", "STAT1": "LADE_STAT1", "STAT2": "LADE_STAT2",
                      "GND": "GND", "EP": "GND"},
               info="Footprint Bienen.pretty nach TI 4226298/A; Thermal-Pad 0,9 × 1,5 mm mit 2 Vias Ø 0,2 mm nach TI-Beispiel (verfüllt/abgedeckt) auf L2"),
        b.teil("Device:R", "R203", "2,0k 1%", fp=R0603, netze={"1": "ISET", "2": "GND"}, info="ICHG = 300 AΩ / 2 kΩ = 150 mA (HW26-11)"),
        b.teil("Device:R", "R204", "130k 1%", fp=R0603, netze={"1": "ILIM", "2": "GND"}, info="Tab. 6-1: VBATREG 4,1 V, ILIM 500 mA"),
        b.teil("Device:C", "C204", "22µ 25V X5R", fp=C1206, netze={"1": "SYS", "2": "GND"},
               info="≥ 10 µF an SYS wirksam bei 4,5 V; 10 µF/0805 fiele durch DC-Bias darunter (REG26-11, versorgung.md 3.9)"),
        b.teil("Device:C", "C205", "4,7µ", fp=C0805, netze={"1": "VBAT", "2": "GND"}, info="≥ 1 µF an BAT"),
        b.teil("Device:R", "R205", "100k", fp=R0603, netze={"1": "SYS", "2": "CE_LADEN"},
               info="CE-Pull-up: Leitungsbruch CE_FREI → Laden gesperrt. Strom nur bei Sonne (Q2 an TMP_VCC); SCH26-02"),
        b.teil("Device:C", "C206", "10n", fp=C0603, netze={"1": "CE_LADEN", "2": "GND"}, info="Störschutz an CE (RC 1 ms)"),
        b.teil("Bienen:TPS70933DBV", "U204", "TPS70933DBV", fp="Package_TO_SOT_SMD:SOT-23-5",
               netze={"IN": "VIN_LADER", "EN": "NC", "OUT": "TMP_VCC", "GND": "GND"},
               info="TMP_VCC für die Ladesperre (Blatt Akku), nur bei Sonne/USB (SCH26-01); EN offen = ein (max. 6,5 V)"),
        b.teil("Device:C", "C212", "4,7µ 16V X7R", fp=C0805, netze={"1": "TMP_VCC", "2": "GND"},
               info="Datenblatt verlangt ≥ 2,2 µF am Ausgang; 4,7 µF/0805 hält das bei 3,3 V trotz DC-Bias (REG26-11)"),
        b.teil("Connector:TestPoint", "TP201", "STAT1", bom=False, fp="TestPoint:TestPoint_Pad_D1.0mm", netze={"1": "LADE_STAT1"}),
        b.teil("Connector:TestPoint", "TP202", "STAT2", bom=False, fp="TestPoint:TestPoint_Pad_D1.0mm", netze={"1": "LADE_STAT2"}),
        b.teil("power:PWR_FLAG", "#FLG203", "PWR_FLAG", netze={"1": "VBAT"}, info="Quelle: Zelle BT801 über die Lötbrücke JP801 (Blatt Akku, passive Pins)"),
        b.teil("Device:R", "R206", "2,2M", fp=R0603, netze={"1": "VBAT", "2": "ADC_AKKU"}, info="Akkuteiler 1:2, 0,9 µA"),
        b.teil("Device:R", "R207", "2,2M", fp=R0603, netze={"1": "ADC_AKKU", "2": "GND"}),
        b.teil("Device:C", "C207", "100n", fp=C0603, netze={"1": "ADC_AKKU", "2": "GND"}),
    ]

    regler = [
        b.teil("Bienen:RT9080-33GJ5", "U202", "RT9080-33GJ5", fp="Package_TO_SOT_SMD:TSOT-23-5", lcsc="C841192",
               netze={"VIN": "SYS", "EN": "SYS", "VOUT": "+3V3", "GND": "GND"}, info="EN an VIN (nicht offen lassen)"),
        b.teil("Device:C", "C208", "2,2µ 16V X7R", fp=C0603, netze={"1": "SYS", "2": "GND"}, info="≥ 1 µF wirksam bei 4,5 V (REG26-11)"),
        b.teil("Device:C", "C209", "2,2µ 16V X7R", fp=C0603, netze={"1": "+3V3", "2": "GND"},
               info="≥ 1 µF wirksam bei 3,3 V (REG26-11); dazu 100 µF + 10 µF am Funkmodul (Blatt Funk)"),
        b.teil("Power_Management:TPS22917DBV", "U203", "TPS22917DBV", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C2681320",
               netze={"VIN": "+3V3", "VOUT": "3V3_SW", "ON": "SENSOR_EIN", "CT": "SW_CT", "QOD": "SW_QOD", "GND": "GND"},
               info="QOD über R209 an VOUT: aktive Entladung; CT nach VIN (Datenblatt Tab. 6-1)"),
        b.teil("Device:R", "R209", "0", fp=R0603, netze={"1": "SW_QOD", "2": "3V3_SW"},
               info="QOD-Widerstand (Datenblatt: extern oder direkt); 0 Ω = interner Wert, bei Bedarf erhöhen"),
        b.teil("Device:C", "C210", "1n", fp=C0603, netze={"1": "SW_CT", "2": "+3V3"}, info="CT 1 nF → Anstieg ca. 1,7 ms bei 3,3 V"),
        b.teil("Device:R", "R208", "100k", fp=R0603, netze={"1": "SENSOR_EIN", "2": "GND"}, info="ON nie offen (Standby: GPIO hochohmig); 100 kΩ wie versorgung.md 3.7 (SCH26-05)"),
        b.teil("Device:C", "C211", "1µ", fp=C0603, netze={"1": "3V3_SW", "2": "GND"}),
    ]

    zeichne_versorgung(b, {t.ref: t for t in b.teile})
    return b


def akku(p):
    """Blatt „Akku“ (HW-06, 14.10.2026): Zelle 18650 im Halter Keystone 1042 auf der Hauptplatine, Zellschutz
    HY2111 + FS8205 direkt am Halter, Strommessbrücke, zweistufige Temperatur-Ladesperre (2 × TMP390, NTC).
    Bis dahin eigene Akku-Platine (akku_platine.py, Kabel J1 ↔ J203); Schaltung unverändert übernommen,
    Bauteile 8xx. Quellen: versorgung.md 3.3/3.4, sicherheit-akku.md, LASTENHEFT V1–V3."""
    b = p.blatt("Akku", "akku.kicad_sch", titel="Akku: Zelle 18650, Zellschutz, Temperatur-Ladesperre")
    # --- Zelle, Messbrücke, Stecker ---
    zelle = [
        b.teil("Device:Battery_Cell", "BT801", "18650 3,6 V", fp="Battery:BatteryHolder_Keystone_1042_1x18650",
               netze={"+": "B+", "-": "B-"},
               info="Keystone 1042 (SMD), HW-02; seit HW-06 auf der Hauptplatine; Pad 1 = Plus; LCSC-Nummer [P]"),
        b.teil("Jumper:SolderJumper_2_Bridged", "JP801", "Messbrücke B+", bom=False, fp="Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
               netze={"A": "B+", "B": "VBAT"}, info="Zum Strommessen auftrennen, Amperemeter an J801"),
        b.teil("Connector_Generic:Conn_01x02", "J801", "Strommessung", fp="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
               netze={"1": "B+", "2": "VBAT"}, dnp=True, info="nur bei Bedarf bestücken"),
        b.teil("power:PWR_FLAG", "#FLG801", "PWR_FLAG", netze={"1": "B+"}, info="Quelle: Zelle BT1 (+); der Halter ist für den ERC nur ein passiver Pin"),
        b.teil("power:PWR_FLAG", "#FLG802", "PWR_FLAG", netze={"1": "B-"}, info="Quelle: Zelle BT1 (−)"),
    ]

    # --- Zellschutz (HYCON-Anwendungsschaltung: R1 100 Ω, C1 100 nF, R2 2 kΩ) ---
    schutz = [
        b.teil("Bienen:HY2111-GB", "U801", "HY2111-GB", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C82747",
               netze={"VDD": "HY_VDD", "VSS": "B-", "CS": "HY_CS", "OD": "GATE_ENTL", "OC": "GATE_LADE"}),
        b.teil("Device:R", "R801", "100", fp=R0603, netze={"1": "B+", "2": "HY_VDD"}, info="HYCON-Anwendungsschaltung R1"),
        b.teil("Device:C", "C801", "100n", fp=C0603, netze={"1": "HY_VDD", "2": "B-"}, info="HYCON C1"),
        b.teil("power:PWR_FLAG", "#FLG805", "PWR_FLAG", netze={"1": "HY_VDD"}, info="aus B+ über R801 100 Ω (HYCON-Anwendungsschaltung); der ERC sieht den Widerstand nicht als Treiber"),
        b.teil("Device:R", "R802", "2k", fp=R0603, netze={"1": "HY_CS", "2": "GND"}, info="HYCON R2 (CS an P−)"),
        b.teil("Bienen:FS8205", "Q801", "FS8205", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C32254",
               netze={"G1": "GATE_ENTL", "S1": "B-", "G2": "GATE_LADE", "S2": "GND", "D12": "D12"},
               info="M1 Entladen (G1, S1 an B−), M2 Laden (G2, S2 an P−)"),
    ]

    # --- Ladesperre Stufe 1: TMP390 U2 → Q2 → CE ---
    stufe1 = [
        b.teil("Bienen:TMP390", "U802", "TMP390A2DRL", fp="Package_TO_SOT_SMD:SOT-563",
               netze={"VDD": "TMP_VCC", "GND": "GND", "SETA": "SETA1", "SETB": "SETB1", "~{OUTA}": "GATE_CE", "~{OUTB}": "GATE_CE"},
               info="OUTA heiß 42 °C, OUTB kalt +5 °C, Hysterese 5 °C; Ausgänge verbunden (wired-OR)"),
        b.teil("Device:C", "C802", "100n", fp=C0603, netze={"1": "TMP_VCC", "2": "GND"}),
        b.teil("Device:R", "R803", "2,49k 1%", fp=R0603, netze={"1": "SETA1", "2": "GND"}, info="TMP390 Tab. 7-1: 42 °C"),
        b.teil("Device:R", "R804", "18,7k 1%", fp=R0603, netze={"1": "SETB1", "2": "GND"}, info="TMP390 Tab. 7-2: +5 °C, Hysterese 5 °C"),
        b.teil("Device:R", "R805", "100k", fp=R0603, netze={"1": "TMP_VCC", "2": "GATE_CE"},
               info="Gate-Pull-up an TMP_VCC: Leckstrom TMP390 ±0,1 µA → 10 mV (SCH26-02)"),
        b.teil("Transistor_FET:AO3400A", "Q802", "AO3400A", fp="Package_TO_SOT_SMD:SOT-23",
               netze={"G": "GATE_CE", "S": "GND", "D": "CE_LADEN"}, info="leitet → CE low → Laden erlaubt (gegen R205 100 kΩ nach SYS)"),
    ]

    # --- Ladesperre Stufe 2: TMP390 U3 trennt den NTC ---
    stufe2 = [
        b.teil("Bienen:TMP390", "U803", "TMP390A2DRL", fp="Package_TO_SOT_SMD:SOT-563",
               netze={"VDD": "TMP_VCC", "GND": "GND", "SETA": "SETA2", "SETB": "SETB2", "~{OUTA}": "GATE_NTC", "~{OUTB}": "NC"},
               info="nur Kanal A (heiß 42 °C, Hysterese 5 °C); OUTB offen (Datenblatt: erlaubt)"),
        b.teil("Device:C", "C803", "100n", fp=C0603, netze={"1": "TMP_VCC", "2": "GND"}),
        b.teil("Device:R", "R806", "2,49k 1%", fp=R0603, netze={"1": "SETA2", "2": "GND"}, info="TMP390 Tab. 7-1: 42 °C"),
        b.teil("Device:R", "R807", "18,7k 1%", fp=R0603, netze={"1": "SETB2", "2": "GND"}, info="Hysterese 5 °C (Kanal B ungenutzt)"),
        b.teil("Device:R", "R808", "100k", fp=R0603, netze={"1": "TMP_VCC", "2": "GATE_NTC"}, info="Gate-Pull-up Q803"),
        b.teil("Transistor_FET:AO3400A", "Q803", "AO3400A", fp="Package_TO_SOT_SMD:SOT-23",
               netze={"G": "GATE_NTC", "S": "GND", "D": "NTC_FUSS"},
               info="leitet → NTC wirkt; sperrt (zu heiß oder TMP_VCC fehlt) → TS offen → BQ25185 sperrt"),
        b.teil("Device:Thermistor_NTC", "TH801", "10k B3435", fp="Resistor_SMD:R_0603_1608Metric",
               netze={"1": "NTC", "2": "NTC_FUSS"}, info="Layout: unter der Zelle, Wärmeleitpad; B = 3435 K (BQ25185-Schwellen)"),
    ]
    zeichne_akku(b, {t.ref: t for t in b.teile})
    return b


def zeichne_akku(b, T):
    """Platzierung und Leitungen nach Stromfluss (Verdrahtungsmodus, A3 quer, Maße in mm).
    Oben der Leistungspfad B+ → Messbrücke → VBAT (zum Laderegler, Blatt Versorgung), darunter der Zellschutz im Minuspfad
    B− → FS8205 → P− (GND). Unten die Ladesperre: Stufe 2 (NTC-Kreis) und Stufe 1 (CE), beide
    aus TMP_VCC (TPS70933, Blatt Versorgung). Bis HW-06 (14.10.2026) eigene Akku-Platine mit Kabel J1 ↔ J203. Jede Verbindung prüft netz_tests.py gegen die Netzbeschreibung."""
    S, D, L = b.setze, b.draht, b.label

    # --- Überschriften ------------------------------------------------------
    b.text("1  Leistungspfad: Zelle → Messbrücke JP801 → VBAT (P+) zum Laderegler", 40.64, 22.86, 2.0)
    b.text("2  Zellschutz im Minuspfad: HY2111 schaltet Q801 (M1 Entladen, M2 Laden); GND = P−, B− nur als Insel an der Zelle", 101.6, 58.42, 2.0)
    b.text("3  Ladesperre Stufe 2 (SCH26-03): U803 öffnet über 42 °C mit Q803 den NTC-Kreis → TS offen → BQ25185 lädt nicht", 40.64, 129.54, 2.0)
    b.text("4  Ladesperre Stufe 1 (CE)", 40.64, 203.2, 2.0)
    b.text("U802 sperrt außerhalb +5 … 42 °C über Q802: CE_LADEN high → BQ25185 lädt nicht", 40.64, 208.28, 1.5)
    b.text("TMP_VCC kommt vom TPS70933 am Ladereingang: nur bei Sonne/USB vorhanden; fehlt es, sperren beide Stufen. "
           "Keine Verbindung der Sperre zu B+/B− (SCH26-01). Layout: TH801, U802, U803 direkt unter der Zelle (Wärmeleitpad).",
           40.64, 276.86, 1.5)

    # --- 1 Leistungspfad ----------------------------------------------------
    yb = 45.72                       # B+/P+-Schiene
    S(T["BT801"], 50.8, 76.2, text="links")
    S(T["JP801"], 127.0, yb, text="unten")
    S(T["J801"], 124.46, 33.02, rot=90, text="links")
    D(T["BT801"].p("+"), (50.8, yb), T["JP801"].p("A"))
    D(T["J801"].p("1"), (124.46, 40.64), (119.38, 40.64), (119.38, yb))
    D(T["J801"].p("2"), (127.0, 40.64), (134.62, 40.64), (134.62, yb))
    D(T["JP801"].p("B"), (190.5, yb))
    L("B+", 55.88, yb)
    L("VBAT", 190.5, yb)

    # --- 2 Zellschutz -------------------------------------------------------
    yminus = 99.06                   # B−-Schiene
    S(T["R801"], 76.2, 57.15, text="links")
    S(T["U801"], 116.84, 76.2)
    S(T["C801"], 86.36, 81.28, text="links")
    S(T["R802"], 99.06, 86.36)
    S(T["Q801"], 165.1, 96.52)
    D(T["R801"].p("1"), (76.2, yb))
    D(T["R801"].p("2"), (76.2, 71.12), T["U801"].p("VDD"))
    D(T["C801"].p("1"), (86.36, 71.12))
    D(T["U801"].p("CS"), (99.06, 73.66), T["R802"].p("1"))
    D(T["BT801"].p("-"), (50.8, yminus), T["Q801"].p("S1"))
    D(T["U801"].p("VSS"), (116.84, yminus))
    D(T["C801"].p("2"), (86.36, yminus))
    D(T["U801"].p("OD"), (149.86, 71.12), (149.86, 96.52), T["Q801"].p("G1"))
    D(T["U801"].p("OC"), (177.8, 73.66), (177.8, 96.52), T["Q801"].p("G2"))
    D(T["Q801"].p("2"), T["Q801"].p("5"))
    L("HY_VDD", 76.2, 69.85, 90)
    L("HY_CS", 99.06, 81.28, 90)
    L("B-", 55.88, yminus)
    L("GATE_ENTL", 129.54, 71.12)
    L("GATE_LADE", 157.48, 73.66)
    L("D12", 163.83, 86.36)

    # --- Anschlüsse zum Blatt Versorgung: NTC, CE_LADEN, TMP_VCC (globale Labels) ---
    x_li = 55.88

    # --- 3 Stufe 2 ----------------------------------------------------------
    o = 7.62
    y2 = 139.7 + o                   # TMP_VCC-Schiene Stufe 2
    S(T["C803"], 66.04, 147.32 + o, text="links")
    S(T["U803"], 106.68, 160.02 + o)
    S(T["R806"], 81.28, 177.8 + o, text="links")
    S(T["R807"], 91.44, 177.8 + o)
    S(T["R808"], 127.0, 147.32 + o)
    S(T["Q803"], 139.7, 160.02 + o)
    S(T["TH801"], 142.24, 139.7 + o)
    D((x_li, y2), (127.0, y2))
    D(T["C803"].p("1"), (66.04, y2))
    D(T["U803"].p("VDD"), (76.2, 154.94 + o), (76.2, y2))
    D(T["U803"].p("SETA"), (81.28, 157.48 + o), T["R806"].p("1"))
    D(T["U803"].p("SETB"), (91.44, 160.02 + o), T["R807"].p("1"))
    D(T["R808"].p("1"), (127.0, y2))
    D(T["U803"].p("~{OUTA}"), (132.08, 154.94 + o), (132.08, 160.02 + o), T["Q803"].p("G"))
    D(T["R808"].p("2"), (127.0, 154.94 + o))
    D(T["TH801"].p("2"), T["Q803"].p("D"))
    D(T["TH801"].p("1"), (142.24, 137.16), (190.5, 137.16))
    L("SETA2", 81.28, 171.45 + o, 90)
    L("SETB2", 91.44, 171.45 + o, 90)
    L("GATE_NTC", 132.08, 160.02 + o)
    L("NTC_FUSS", 142.24, 151.13 + o)
    L("NTC", 190.5, 137.16)

    # --- 4 Stufe 1 ----------------------------------------------------------
    o = 20.32
    y1 = 193.04 + o                  # TMP_VCC-Schiene Stufe 1
    S(T["C802"], 66.04, 200.66 + o, text="links")
    S(T["U802"], 106.68, 213.36 + o)
    S(T["R803"], 81.28, 231.14 + o, text="links")
    S(T["R804"], 91.44, 231.14 + o)
    S(T["R805"], 127.0, 200.66 + o)
    S(T["Q802"], 139.7, 213.36 + o)
    D((x_li, y1), (127.0, y1))
    D(T["C802"].p("1"), (66.04, y1))
    D(T["U802"].p("VDD"), (76.2, 208.28 + o), (76.2, y1))
    D(T["U802"].p("SETA"), (81.28, 210.82 + o), T["R803"].p("1"))
    D(T["U802"].p("SETB"), (91.44, 213.36 + o), T["R804"].p("1"))
    D(T["R805"].p("1"), (127.0, y1))
    D(T["U802"].p("~{OUTA}"), (121.92, 208.28 + o), (132.08, 208.28 + o), (132.08, 213.36 + o), T["Q802"].p("G"))
    D(T["U802"].p("~{OUTB}"), (121.92, 210.82 + o), (121.92, 208.28 + o))
    D(T["R805"].p("2"), (127.0, 208.28 + o))
    D(T["Q802"].p("D"), (142.24, 198.12), (190.5, 198.12))
    L("SETA1", 81.28, 224.79 + o, 90)
    L("SETB1", 91.44, 224.79 + o, 90)
    L("GATE_CE", 124.46, 208.28 + o)
    L("CE_LADEN", 190.5, 198.12)

    # --- TMP_VCC: vom Label nach links hoch zu beiden Stufen ----------------
    y_unten = 266.7
    D((190.5, y_unten), (x_li, y_unten), (x_li, y2))
    L("TMP_VCC", 190.5, y_unten)

    # --- PWR_FLAGs auf den Schienen (Begründung je Flag in der Beschreibung) --
    S(T["#FLG801"], 63.5, yb)
    S(T["#FLG802"], 63.5, yminus)
    S(T["#FLG805"], 81.28, 71.12)



def baue():
    p = Projekt("logger", os.path.join(HIER, "hauptplatine"), firma="Bienenlogger – Philipp Schnabel",
                rev="0.1 Entwurf", datum="2026-10-09", eigene_bibs={"Bienen": BIB},
                kommentare=["Board-Kennung PCB-MAIN-0.1 (REG26-10)",
                            "Umgebung [A]: Gehäuse −20 … +60 °C, Betauung möglich; VIN ≤ 12 V dauernd, 25 V absolut"])
    p.schnittstellen = set(SCHNITTSTELLEN)
    p.eigene_fps = {"Bienen": os.path.join(HIER, "Bienen.pretty")}
    w = p.blatt("Bienenlogger Hauptplatine", "logger.kicad_sch", titel="Bienenlogger Hauptplatine 121 × 121 mm, 4 Lagen")
    w.text("Blätter: Versorgung, MCU, Funk + Flash, Waage, Mikrofon, Anschlüsse, Akku (Entwurf vollständig; Akku seit HW-06 auf der Hauptplatine).", 30, 25, 2.0)
    versorgung(p)
    mcu(p)
    funk(p)
    waage(p)
    mikrofon(p)
    anschluesse(p)
    akku(p)
    return p


if __name__ == "__main__":
    pr = baue()
    g = pr.schreibe()
    print("geschrieben:", pr.ordner, "| globale Netze:", ", ".join(sorted(g)))
