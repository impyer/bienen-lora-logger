#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Schaltplan der Hauptplatine (KiCad-Projekt hardware/kicad/hauptplatine/), Blätter je Block.

Stand 10.10.2026: Blätter „Versorgung“ und „MCU“. Weitere Blätter (Funk + Flash, Waage, Mikrofon,
Anschlüsse) folgen; Netze zu diesen Blättern sind als Schnittstellen (globale Labels) angelegt.

Quellen der Werte: hardware/versorgung.md (3.1–3.8), LASTENHEFT.md V1–V7.
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
KLEMME = "Connector_Phoenix_MC:PhoenixContact_MC_1,5_%d-G-3.5_1x0%d_P3.50mm_Horizontal"

# Netze, die zu anderen (noch folgenden) Blättern gehen
SCHNITTSTELLEN = {
    "VBUS",        # USB-C (Blatt MCU) → Diode → Ladereingang
    "ADC_SOLAR",   # PB1
    "ADC_AKKU",    # Akkuteiler → ADC (Pin auf Blatt MCU)
    "SENSOR_EIN",  # PB5 → ON des TPS22917
    "3V3_SW",      # geschaltete Sensorschiene
    "SYS",         # 5-V-Wandler der Waage hängt an SYS
    # Blatt MCU → Funk + Flash
    "SPI_SCK", "SPI_MISO", "SPI_MOSI", "LORA_NSS", "LORA_DIO1", "LORA_BUSY", "LORA_RST", "LORA_TXEN", "LORA_RXEN",
    "FLASH_CS",
    # Blatt MCU → Mikrofon, Waage, Anschlüsse
    "MIC_ADC", "HX_DOUT", "HX_SCK", "WAAGE_EIN", "ONEWIRE", "I2C_SCL", "I2C_SDA", "EXT_PA15", "EXT_PB12", "EXT_PB13",
}


def zeichne_versorgung(b, T):
    """Platzierung und Leitungen nach Stromfluss (A3 quer, mm).
    Obere Reihe: Panels/USB → Schottky → VIN_LADER → Laderegler → SYS. Mitte: Akku-Stecker J203 mit
    VBAT, CE, NTC und TMP_VCC (TPS70933 aus VIN_LADER). Untere Reihe: SYS → 3,3 V → Sensorschiene.
    netz_tests.py prüft jede gezeichnete Verbindung gegen die Netzbeschreibung."""
    S, D, L = b.setze, b.draht, b.label
    yv = 76.2                        # obere Schiene VIN_LADER / SYS
    y3 = 180.34                      # untere Schiene SYS / +3V3 / 3V3_SW

    b.text("1  Solar und USB → Schottky-Dioden → VIN_LADER (TVS, Messung der Eingangsspannung)", 30.48, 55.88, 2.0)
    b.text("2  Laderegler BQ25185: 4,1 V, 150 mA; CE und TS kommen von der Ladesperre der Akku-Platine", 152.4, 63.5, 2.0)
    b.text("3  Akku-Stecker J203, TMP_VCC", 175.26, 124.46, 2.0)
    b.text("4  SYS → 3,3 V (RT9080) → geschaltete Sensorschiene 3V3_SW (TPS22917, Ein/Aus von der MCU)", 152.4, 215.9, 2.0)
    b.text("Regeln: Pull-ups nur an 3V3_SW; TS/MR nie aktiv auf Masse (Werksmodus); Laderegler nicht neben der Zelle; "
           "SPI-Flash an +3V3 (dauernd).", 30.48, 233.68, 1.5)
    b.text("J203: Kabel 1:1 zur Akku-Platine J1 (anschluesse.md). TMP_VCC aus dem TPS70933 am Ladereingang gibt es nur bei "
           "Sonne/USB; ohne TMP_VCC sperrt die Ladesperre (sicherheit-akku.md).", 30.48, 240.03, 1.5)

    # Teile, auf die mehrere Abschnitte zeigen, zuerst setzen
    S(T["U201"], 205.74, 83.82, text="oben")
    S(T["J203"], 302.26, 134.62, text="oben")
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
    D(T["U201"].p("~{CE}"), (x_ce, 78.74), (x_ce, 134.62), T["J203"].p("3"))
    D(T["U201"].p("TS/~{MR}"), (x_ts, 81.28), (x_ts, 132.08), T["J203"].p("2"))
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

    # --- 3 Akku-Stecker: VBAT, Akkuteiler, TMP_VCC --------------------------
    x_vbat = 317.5
    D(T["U201"].p("BAT"), (x_vbat, 78.74), (x_vbat, 142.24), (297.18, 142.24), T["J203"].p("5"))
    L("VBAT", 302.26, 78.74)
    S(T["C205"], 264.16, 82.55)
    
    S(T["R206"], 279.4, 82.55, text="links")
    S(T["R207"], 279.4, 97.79, text="links")
    S(T["C207"], 289.56, 97.79)
    D(T["R206"].p("2"), T["R207"].p("1"))
    D(T["C207"].p("1"), (289.56, 90.17), (279.4, 90.17))
    D((289.56, 90.17), (294.64, 90.17))
    L("ADC_AKKU", 294.64, 90.17)
    S(T["#FLG203"], 309.88, 78.74)
    D((73.66, yv), (73.66, 147.32), T["U204"].p("IN"))
    S(T["C212"], 236.22, 151.13)
    D(T["U204"].p("OUT"), (292.1, 147.32), (292.1, 137.16), T["J203"].p("4"))
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
    """Blatt MCU (mcu-funk.md 1, 3.3, 4): STM32F411CEU6, Takt, Reset/BOOT, USB-C, Debug, Magnet/Taster, LED."""
    b = p.blatt("MCU", "mcu.kicad_sch", titel="MCU: STM32F411CEU6, Takt, USB-C, Debug, Magnet und LED")
    pins = {"VDD": "+3V3", "VBAT": "+3V3", "VDDA": "VDDA", "VSS": "GND", "VSSA": "GND", "VCAP1": "VCAP",
            "NRST": "NRST", "BOOT0": "BOOT0", "PH0": "HSE_IN", "PH1": "HSE_OUT", "PC14": "LSE_IN", "PC15": "LSE_OUT",
            "PC13": "LED", "PA0": "WAKE", "PA1": "MIC_ADC", "PA2": "LORA_DIO1", "PA3": "LORA_BUSY", "PA4": "LORA_NSS",
            "PA5": "SPI_SCK", "PA6": "SPI_MISO", "PA7": "SPI_MOSI", "PA8": "ONEWIRE", "PA9": "DBG_TX", "PA10": "DBG_RX",
            "PA11": "USB_DM", "PA12": "USB_DP", "PA13": "SWDIO", "PA14": "SWCLK", "PA15": "EXT_PA15",
            "PB0": "ADC_AKKU", "PB1": "ADC_SOLAR", "PB2": "BOOT1", "PB3": "FLASH_CS", "PB4": "LORA_RST",
            "PB5": "SENSOR_EIN", "PB6": "I2C_SCL", "PB7": "I2C_SDA", "PB8": "HX_DOUT", "PB9": "HX_SCK", "PB10": "WAAGE_EIN",
            "PB12": "EXT_PB12", "PB13": "EXT_PB13", "PB14": "LORA_TXEN", "PB15": "LORA_RXEN"}
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
           info="gedrückt halten + Reset → USB-DFU")
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
    b.teil("Switch:SW_Reed", "SW304", "Reedkontakt", fp="", netze={"1": "WAKE", "2": "+3V3"},
           info="an der Platinenkante neben der LED; Teil und Footprint [P]")
    b.teil("Device:R", "R305", "100k", fp=R0603, netze={"1": "WAKE", "2": "GND"}, info="Pull-down WKUP1")
    b.teil("Device:R", "R306", "1k", fp=R0603, netze={"1": "+3V3", "2": "LED_A"}, info="≥ 1 kΩ (mcu-funk.md 4)")
    b.teil("Device:LED", "D301", "Side-View", fp="LED_SMD:LED_0603_1608Metric", netze={"A": "LED_A", "K": "LED"},
           info="seitlich abstrahlend am Rand unter dem Lichtleiter; Teil/Footprint [P]")
    # USB-C
    b.teil("Connector:USB_C_Receptacle_USB2.0_16P", "J301", "USB-C", fp="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
           lcsc="C165948", netze={"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS",
                                  "B9": "VBUS", "A5": "USB_CC1", "B5": "USB_CC2", "A6": "USB_DP", "B6": "USB_DP",
                                  "A7": "USB_DM", "B7": "USB_DM", "A8": "NC", "B8": "NC", "SH": "GND"},
           info="Schirm direkt an GND [A]")
    b.teil("Device:R", "R303", "5,1k", fp=R0603, netze={"1": "GND", "2": "USB_CC1"}, info="USB-2.0-Gerät")
    b.teil("Device:R", "R304", "5,1k", fp=R0603, netze={"1": "GND", "2": "USB_CC2"})
    b.teil("Power_Protection:USBLC6-2SC6", "U302", "USBLC6-2SC6", fp="Package_TO_SOT_SMD:SOT-23-6", lcsc="C7519",
           netze={"1": "USB_DM", "6": "USB_DM", "3": "USB_DP", "4": "USB_DP", "5": "VBUS", "2": "GND"})
    # Debug
    b.teil("Connector_Generic:Conn_01x07", "J302", "Debug (SWD + Serial1)", fp="Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
           netze={"1": "+3V3", "2": "SWDIO", "3": "SWCLK", "4": "NRST", "5": "DBG_TX", "6": "DBG_RX", "7": "GND"})
    b.teil("power:PWR_FLAG", "#FLG301", "PWR_FLAG", netze={"1": "VDDA"}, info="VDDA aus +3V3 über FB301 (Ferrit ist für den ERC kein Treiber)")
    zeichne_mcu(b, {t.ref: t for t in b.teile})
    return b


def zeichne_mcu(b, T):
    """Platzierung und Leitungen (A3 quer, mm). Mitte der STM32; oben die 3,3-V-Versorgung mit den
    Abblockkondensatoren, links Reset/BOOT und Quarze, rechts Magnet/Taster. Leitungen zu anderen
    Blättern und zu den Gruppen USB-C und Debug enden an Netznamen."""
    S, D, L = b.setze, b.draht, b.label
    U = S(T["U301"], 200.66, 139.7, text="unten")

    b.text("1  Versorgung: VDD je 100 nF am Pin, VDDA über Ferrit, VBAT an 3,3 V, VCAP 4,7 µF", 144.78, 48.26, 2.0)
    b.text("2  Reset, BOOT, Quarze 25 MHz und 32,768 kHz (CL ≤ 7 pF)", 30.48, 81.28, 2.0)
    b.text("3  Magnet/Taster weckt (WKUP1), LED unter dem Lichtleiter", 236.22, 60.96, 2.0)
    b.text("4  USB-C (Aufspielen, Laden am Tisch) mit ESD-Schutz", 279.4, 157.48, 2.0)
    b.text("5  Debug-Leiste: SWD und Serial1", 279.4, 101.6, 2.0)
    b.text("Netznamen ohne Gegenstück auf diesem Blatt führen zu den Blättern Versorgung, Funk + Flash, Waage, "
           "Mikrofon und Anschlüsse (mcu-funk.md 4).", 30.48, 233.68, 1.5)

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
    for pin in ("2", "3", "4", "5", "6"):
        stub(b, J, pin, 10.16)

    # --- 4 USB-C ------------------------------------------------------------
    K = S(T["J301"], 345.44, 193.04, rot=180, text="oben")
    D(K.p("A6"), (327.66, K.p("A6")[1]), (327.66, K.p("B6")[1]), K.p("B6"))   # D+ A/B
    D(K.p("A7"), (325.12, K.p("A7")[1]), (325.12, K.p("B7")[1]), K.p("B7"))   # D− A/B
    D((327.66, K.p("A6")[1]), (314.96, K.p("A6")[1]))
    D((325.12, K.p("A7")[1]), (314.96, K.p("A7")[1]))
    L("USB_DP", 314.96, K.p("A6")[1], 180)
    L("USB_DM", 314.96, K.p("A7")[1], 180)
    stub(b, K, "A5", 10.16)
    stub(b, K, "B5", 10.16)
    for ref, x in (("R303", 292.1), ("R304", 304.8)):
        R = S(T[ref], x, 223.52, rot=180, text="rechts")
        stub(b, R, "2", 5.08)
    D(K.p("A4"), (314.96, K.p("A4")[1]))
    L("VBUS", 314.96, K.p("A4")[1], 180)
    E = S(T["U302"], 289.56, 182.88, text="unten")
    for pin in ("1", "3", "4", "6", "5"):
        stub(b, E, pin, 5.08)

def funk(p):
    """Blatt Funk + Flash (mcu-funk.md 2, 3.1, 3.2): Ra-01SH an SPI1, SPI-Flash 64 Mbit am selben Bus."""
    b = p.blatt("Funk + Flash", "funk.kicad_sch", titel="Funk + Flash: Ra-01SH (SX1262/LLCC68), SPI-NOR-Flash 64 Mbit")
    b.teil("Bienen:Ra-01SH", "U401", "Ra-01SH", lcsc="C2764087",
           netze={"3.3V": "+3V3", "RESET": "LORA_RST", "NSS": "RF_NSS", "SCK": "RF_SCK", "MOSI": "RF_MOSI", "MISO": "RF_MISO",
                  "BUSY": "LORA_BUSY", "DIO1": "LORA_DIO1", "ANT": "NC", "TXEN": "TXEN_MOD", "RXEN": "RXEN_MOD",
                  "DIO2": "NC", "DIO3": "NC", "GND": "GND"},
           info="Antenne über IPEX; Pin ANT ohne Leiterbahn (mcu-funk.md 2.3); DIO2 schaltet HF-Schalter, DIO3 offen (kein TCXO)")
    b.teil("Device:C", "C401", "100µ 6,3V X5R", fp="Capacitor_SMD:C_1210_3225Metric", netze={"1": "+3V3", "2": "GND"},
           info="Puffer für Sendestromspitzen > 200 mA (mcu-funk.md 2.2) [A]")
    b.teil("Device:C", "C402", "10µ 10V X5R", fp=C0805, netze={"1": "+3V3", "2": "GND"})
    b.teil("Device:C", "C403", "100n", fp=C0603, netze={"1": "+3V3", "2": "GND"}, info="direkt an Pin 3")
    b.teil("Device:D_TVS", "D401", "TVS 3,3V", fp="Diode_SMD:D_SOD-523", netze={"1": "GND", "2": "+3V3"},
           info="ESD-Schutz am 3,3-V-Eingang des Moduls (Datenblatt-Empfehlung); Teil wählen [P]")
    for ref, mod, mcu_ in (("R401", "RF_SCK", "SPI_SCK"), ("R402", "RF_MISO", "SPI_MISO"), ("R403", "RF_MOSI", "SPI_MOSI"),
                           ("R404", "RF_NSS", "LORA_NSS")):
        b.teil("Device:R", ref, "33", fp=R0603, netze={"1": mcu_, "2": mod}, info="Reihenwiderstand 10–100 Ω laut Datenblatt")
    b.teil("Device:R", "R405", "100k", fp=R0603, netze={"1": "+3V3", "2": "LORA_NSS"}, info="NSS nicht ausgewählt, solange PA4 im Standby hochohmig ist")
    b.teil("Jumper:SolderJumper_2_Open", "JP401", "TXEN", fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
           netze={"A": "TXEN_MOD", "B": "LORA_TXEN"}, info="offen; nur schließen, falls Senden ohne TXEN nicht geht (mcu-funk.md 2.1)")
    b.teil("Jumper:SolderJumper_2_Open", "JP402", "RXEN", fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
           netze={"A": "RXEN_MOD", "B": "LORA_RXEN"})
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
        rot = 90 if ref == "D401" else 0
        S(T[ref], x, 82.55 if ref != "D401" else 82.55, rot=rot)
        pin = "2" if ref == "D401" else "1"
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
        b.teil("Connector_Generic:Conn_01x02", "J201", "Solar 1", fp=KLEMME % (2, 2),
               netze={"1": "GND", "2": "PV1"}, info="DEGSON 15EDGRHC-3.5 (Platzhalter-Footprint Phoenix MC 3,5 mm) [P]"),
        b.teil("Connector_Generic:Conn_01x02", "J202", "Solar 2", fp=KLEMME % (2, 2),
               netze={"1": "GND", "2": "PV2"}, info="wie J201"),
        b.teil("Diode:SS34", "D201", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "PV1", "K": "VIN_LADER"}, info="je Panel eine Schottky"),
        b.teil("Diode:SS34", "D202", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "PV2", "K": "VIN_LADER"}),
        b.teil("Diode:SS34", "D203", "SS34", fp="Diode_SMD:D_SMA", netze={"A": "VBUS", "K": "VIN_LADER"}, info="USB lädt, speist nie ins Panel"),
        b.teil("Diode:SMAJ12A", "D204", "SMAJ12A", fp="Diode_SMD:D_SMA", netze={"1": "VIN_LADER", "2": "GND"},  # Pin 1 = Kathode
               info="TVS 12 V, begrenzt Störungen unter 25 V (BQ25185 abs.)"),
        b.teil("Device:C", "C201", "4,7µ 50V X7R", fp=C1206, netze={"1": "VIN_LADER", "2": "GND"}, info="≥ 1 µF an IN; 50 V wegen 25 V abs. am Eingang und DC-Bias (SCH26-08)"),
        b.teil("Device:C", "C202", "100n 50V", fp=C0603, netze={"1": "VIN_LADER", "2": "GND"}),
        b.teil("Device:R", "R201", "3,3M", fp=R0603, netze={"1": "VIN_LADER", "2": "ADC_SOLAR"}, info="HW26-08: 25 V → 3,12 V"),
        b.teil("Device:R", "R202", "470k", fp=R0603, netze={"1": "ADC_SOLAR", "2": "GND"}),
        b.teil("Device:C", "C203", "100n", fp=C0603, netze={"1": "ADC_SOLAR", "2": "GND"}, info="Ladung für die ADC-Abtastung"),
        b.teil("power:PWR_FLAG", "#FLG201", "PWR_FLAG", netze={"1": "VIN_LADER"}, info="Quellen: Panels an J201/J202 und VBUS über D201–D203; Klemmen sind für den ERC passive Pins"),
        b.teil("power:PWR_FLAG", "#FLG202", "PWR_FLAG", netze={"1": "GND"}, info="Bezug über die Klemmen J201/J202 und den Akku-Stecker J203 (passive Pins)"),
    ]

    lader = [
        b.teil("Bienen:BQ25185", "U201", "BQ25185DLHR", fp="Bienen:WSON-10-1EP_2.2x2mm_DLH0010A",
               netze={"IN": "VIN_LADER", "SYS": "SYS", "BAT": "VBAT", "~{CE}": "CE_LADEN", "TS/~{MR}": "NTC",
                      "ISET": "ISET", "ILIM/VSET": "ILIM", "STAT1": "LADE_STAT1", "STAT2": "LADE_STAT2",
                      "GND": "GND", "EP": "GND"},
               info="Footprint DLH 2,2 × 2 mm selbst anlegen [P]; Thermal-Pad mit 6–9 Vias auf L2"),
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
               info="TMP_VCC für die Ladesperre auf der Akku-Platine, nur bei Sonne/USB (SCH26-01); EN offen = ein (max. 6,5 V)"),
        b.teil("Device:C", "C212", "4,7µ 16V X7R", fp=C0805, netze={"1": "TMP_VCC", "2": "GND"},
               info="Datenblatt verlangt ≥ 2,2 µF am Ausgang; 4,7 µF/0805 hält das bei 3,3 V trotz DC-Bias (REG26-11)"),
        b.teil("Connector:TestPoint", "TP201", "STAT1", fp="TestPoint:TestPoint_Pad_D1.0mm", netze={"1": "LADE_STAT1"}),
        b.teil("Connector:TestPoint", "TP202", "STAT2", fp="TestPoint:TestPoint_Pad_D1.0mm", netze={"1": "LADE_STAT2"}),
        b.teil("Connector_Generic:Conn_01x05", "J203", "Akku (JST PH 5)", fp="Connector_JST:JST_PH_B5B-PH-K_1x05_P2.00mm_Vertical",
               netze={"1": "GND", "2": "NTC", "3": "CE_LADEN", "4": "TMP_VCC", "5": "VBAT"},
               info="Kabel 1:1 zur Akku-Platine J1: 1 P−, 2 NTC, 3 CE_FREI, 4 TMP_VCC, 5 P+"),
        b.teil("power:PWR_FLAG", "#FLG203", "PWR_FLAG", netze={"1": "VBAT"}, info="Quelle: Akku-Platine über J203 Pin 5 (P+), anderes KiCad-Projekt"),
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


def baue():
    p = Projekt("logger", os.path.join(HIER, "hauptplatine"), firma="Bienenlogger – Philipp Schnabel",
                rev="0.1 Entwurf", datum="2026-10-09", eigene_bibs={"Bienen": BIB},
                kommentare=["Board-Kennung PCB-MAIN-0.1 (REG26-10)",
                            "Umgebung [A]: Gehäuse −20 … +60 °C, Betauung möglich; VIN ≤ 12 V dauernd, 25 V absolut"])
    p.schnittstellen = set(SCHNITTSTELLEN)
    w = p.blatt("Bienenlogger Hauptplatine", "logger.kicad_sch", titel="Bienenlogger Hauptplatine 121 × 121 mm, 4 Lagen")
    w.text("Blätter: Versorgung, MCU, Funk + Flash (fertig). Folgen: Waage, Mikrofon, Anschlüsse.", 30, 25, 2.0)
    versorgung(p)
    mcu(p)
    funk(p)
    return p


if __name__ == "__main__":
    pr = baue()
    g = pr.schreibe()
    print("geschrieben:", pr.ordner, "| globale Netze:", ", ".join(sorted(g)))
