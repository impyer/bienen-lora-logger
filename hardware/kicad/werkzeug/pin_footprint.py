#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""REG26-08: Pin-/Footprint-Abgleich für die Hauptplatine (seit HW-06 mit Blatt Akku).

Prüft für jedes Bauteil aus den Generatoren (Quelle der Wahrheit):
  1. Footprint vorhanden: Datei in der KiCad-Bibliothek; fehlende eigene Footprints nur aus der Liste OFFEN.
  2. Symbol-Pins = Footprint-Pads (Nummern), Ausnahmen begründet in PAD_AUSNAHMEN.
  3. Datenblatt: Für jedes aktive Bauteil steht in DATENBLATT die Pinbelegung laut Hersteller (Pin → Name im
     Datenblatt → Name im Symbol) mit Quelle. Das Skript prüft, dass jeder Symbol-Pin dort steht und den
     erwarteten Namen trägt. Passive Zweipoler (R, C, L, Ferrit, Klemmen, Stiftleisten) brauchen das nicht.
Ergebnis: hardware/kicad/pin_footprint.md (erzeugt, nicht von Hand ändern). Exitcode 1 bei einer Abweichung.

Kennzeichnung der Quellen: [V] in dieser Prüfung im Datenblatt gelesen; [V*] in einer früheren Sitzung gelesen
(Quelle im Symbolkommentar), hier nicht erneut geöffnet; [A] Konvention/Annahme; [P] vor der Bestellung prüfen.
Aufruf: python3 hardware/kicad/werkzeug/pin_footprint.py
"""
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
KICAD = os.path.dirname(HIER)
sys.path.insert(0, HIER)
sys.path.insert(0, KICAD)
FP_WURZEL = os.environ.get("KICAD_FOOTPRINTS", "/usr/share/kicad/footprints")
ZIEL = os.path.join(KICAD, "pin_footprint.md")

# Eigene Footprints, die vor dem Layout noch angelegt bzw. gewählt werden müssen (Ref → Grund)
OFFEN = {
}
# Footprints, die nur Platzhalter sind (Pads passen, Teil/Maße weichen ab)
PLATZHALTER = {
}
for _r in ("J201", "J202", "J501", "J601", "J701", "J702", "J703"):
    PLATZHALTER[_r] = "DEGSON 15EDGRC-3.5: Geometrie aus EasyEDA/LCSC, gegen DEGSON-Zeichnung prüfen [P]"
# Pads ohne Symbol-Pin, die gewollt sind (Ref-Präfix oder Ref → erlaubte Pads, Grund)
PAD_AUSNAHMEN = {}

# Pinbelegung laut Datenblatt: lib_id → (Quelle, Status, {Pin: (Name im Datenblatt, Name im Symbol)})
DATENBLATT = {
    "Bienen:BQ25185": ("TI SLUSF65 Tab. 4-1 (DLH)", "[V]", {
        "1": ("SYS", "SYS"), "2": ("BAT", "BAT"), "3": ("STAT2", "STAT2"), "4": ("CE", "~{CE}"), "5": ("GND", "GND"),
        "6": ("TS/MR", "TS/~{MR}"), "7": ("ILIM/VSET", "ILIM/VSET"), "8": ("ISET", "ISET"), "9": ("STAT1", "STAT1"),
        "10": ("IN", "IN"), "11": ("PAD (Thermal-Pad)", "EP")}),
    "Bienen:TMP390": ("TI SBOS904A Pin Functions (DRL)", "[V]", {
        "1": ("SETA", "SETA"), "2": ("SETB", "SETB"), "3": ("GND", "GND"), "4": ("OUTB", "~{OUTB}"),
        "5": ("VDD", "VDD"), "6": ("OUTA", "~{OUTA}")}),
    "Bienen:TPS70933DBV": ("TI SBVS186 Tab. 5-1, Spalte TPS709 DBV", "[V]", {
        "1": ("IN", "IN"), "2": ("GND", "GND"), "3": ("EN", "EN"), "4": ("NC", "NC"), "5": ("OUT", "OUT")}),
    "Bienen:TPS61240": ("TI SLVS806D Pin Functions (WSON)", "[V]", {
        "1": ("GND", "GND"), "2": ("VOUT", "VOUT"), "3": ("FB", "FB"), "4": ("EN", "EN"), "5": ("L", "L"),
        "6": ("VIN", "VIN"), "7": ("Thermal-Pad", "EP")}),
    "Power_Management:TPS22917DBV": ("TI SLVSDW8B Tab. 6-1 (DBV)", "[V]", {
        "1": ("VIN", "VIN"), "2": ("GND", "GND"), "3": ("ON", "ON"), "4": ("CT", "CT"), "5": ("QOD", "QOD"),
        "6": ("VOUT", "VOUT")}),
    "Power_Protection:TPD4E05U06DQA": ("TI TPD4E05U06 Tab. 4-2 (DQA)", "[V]", {
        "1": ("D1+", "D1+"), "2": ("D1−", "D1-"), "3": ("GND", "GND"), "4": ("D2+", "D2+"), "5": ("D2−", "D2-"),
        "6": ("NC", "NC"), "7": ("NC", "NC"), "8": ("GND", "GND"), "9": ("NC", "NC"), "10": ("NC", "NC")}),
    "Power_Protection:ESDS304": ("TI ESDS304 Tab. 4-2 (DBV)", "[V]", {
        "1": ("I/O1", "K"), "2": ("GND", "A"), "3": ("I/O2", "K"), "4": ("I/O3", "K"), "5": ("I/O4", "K")}),
    "Amplifier_Operational:MCP6001-OT": ("TI SBOS833R Tab. 6-1, TLV9001 DBV (Wert TLV9001IDBVR)", "[V]", {
        "1": ("OUT", ""), "2": ("V−", "V-"), "3": ("IN+", "+"), "4": ("IN−", "-"), "5": ("V+", "V+")}),
    "Analog_ADC:HX711": ("AVIA HX711 (engl. Datenblatt, SparkFun-Kopie), Pin-Tabelle; SOP-16L 3,9 × 9,9 mm", "[V]", {
        "1": ("VSUP", "VSUP"), "2": ("BASE", "BASE"), "3": ("AVDD", "AVDD"), "4": ("VFB", "VFB"), "5": ("AGND", "AGND"),
        "6": ("VBG", "VBG"), "7": ("INA-", "INA-"), "8": ("INA+", "INA+"), "9": ("INB-", "INB-"), "10": ("INB+", "INB+"),
        "11": ("PD_SCK", "PD_SCK"), "12": ("DOUT", "DOUT"), "13": ("XO", "XO"), "14": ("XI", "XI"), "15": ("RATE", "RATE"),
        "16": ("DVDD", "DVDD")}),
    "Bienen:HY2111-GB": ("HYCON HY2111 (LCSC C82747), Abschnitt 7", "[V*]", {
        "1": ("OD", "OD"), "2": ("CS", "CS"), "3": ("OC", "OC"), "4": ("NC", "NC"), "5": ("VDD", "VDD"), "6": ("VSS", "VSS")}),
    "Bienen:FS8205": ("Fortune FS8205 (LCSC C32254), Abschnitt 4", "[V*]", {
        "1": ("S1", "S1"), "2": ("D12", "D12"), "3": ("S2", "S2"), "4": ("G2", "G2"), "5": ("D12", "D12"), "6": ("G1", "G1")}),
    "Bienen:RT9080-33GJ5": ("Richtek DS9080 (TSOT-23-5)", "[V*]", {
        "1": ("VIN", "VIN"), "2": ("GND", "GND"), "3": ("EN", "EN"), "4": ("NC", "NC"), "5": ("VOUT", "VOUT")}),
    "Bienen:Ra-01SH": ("Ai-Thinker Ra-01SH Specification V1.1 (2020-08-18), S. 11", "[V]", {
        "1": ("ANT", "ANT"), "2": ("GND", "GND"), "3": ("3.3V", "3.3V"), "4": ("RESET", "RESET"), "5": ("TXEN", "TXEN"),
        "6": ("DIO1", "DIO1"), "7": ("DIO2", "DIO2"), "8": ("DIO3", "DIO3"), "9": ("GND", "GND"), "10": ("BUSY", "BUSY"),
        "11": ("RXEN", "RXEN"), "12": ("SCK", "SCK"), "13": ("MISO", "MISO"), "14": ("MOSI", "MOSI"), "15": ("NSS", "NSS"),
        "16": ("GND", "GND")}),
    "Power_Protection:USBLC6-2SC6": ("ST USBLC6-2 (SOT23-6L); Download hier gescheitert", "[A] [P]", {
        "1": ("I/O1", "I/O1"), "2": ("GND", "GND"), "3": ("I/O2", "I/O2"), "4": ("I/O2", "I/O2"), "5": ("VBUS", "VBUS"),
        "6": ("I/O1", "I/O1")}),
    "Memory_Flash:W25Q32JVSS": ("Standard-Pinbelegung 25er-SPI-Flash SOIC-8 (XT25F64B / ZD25Q64D) – je Teil prüfen", "[A] [P]", {
        "1": ("CS#", "~{CS}"), "2": ("SO", "DO/IO_{1}"), "3": ("WP#", "~{WP}/IO_{2}"), "4": ("VSS", "GND"),
        "5": ("SI", "DI/IO_{0}"), "6": ("SCLK", "CLK"), "7": ("HOLD#", "~{HOLD}/~{RESET}/IO_{3}"), "8": ("VCC", "VCC")}),
    "Transistor_FET:AO3400A": ("AOS AO3400A SOT-23: 1 G, 2 S, 3 D", "[A] [P]", {
        "1": ("G", "G"), "2": ("S", "S"), "3": ("D", "D")}),
    "Transistor_BJT:SS8550": ("S8550 SOT-23 (C397181): 1 B, 2 E, 3 C – je Hersteller verschieden", "[A] [P]", {
        "1": ("B", "B"), "2": ("E", "E"), "3": ("C", "C")}),
    "Diode:SS34": ("KiCad-Konvention D_SMA: Pad 1 = Kathode (Ring)", "[A]", {"1": ("K", "K"), "2": ("A", "A")}),
    "Diode:SMAJ12A": ("unidirektional: Pad 1 = Kathode (Ring) an VIN_LADER", "[A]", {"1": ("K", "A1"), "2": ("A", "A2")}),
    "Device:D_TVS": ("Teil offen; Pad 1 = Kathode bei unidirektionaler TVS, an +3V3", "[P]", {"1": ("K", "A1"), "2": ("A", "A2")}),
    "Device:LED": ("Lite-On LTST-S220 DS22-2000-075: Pad 1 = Kathode (Cathode Mask)", "[V]", {"1": ("K", "K"), "2": ("A", "A")}),
    "Device:Crystal_GND24": ("YXC X322525MOB4SI 3225-4: 1/3 Quarz, 2/4 Gehäuse", "[A] [P]", {
        "1": ("XTAL", "1"), "2": ("GND", "G"), "3": ("XTAL", "3"), "4": ("GND", "G")}),
    "Device:Crystal": ("Seiko SC-32S, 2 Pads, ungepolt", "[A]", {"1": ("XTAL", "1"), "2": ("XTAL", "2")}),
    "Device:Battery_Cell": ("Keystone 1042 (HW-02): Pad 1 = Plus laut KiCad-Footprint (Silkscreen „+“)", "[A] [P]", {"1": ("+", "+"), "2": ("−", "-")}),
    "Switch:SW_Reed": ("MiRelay MRS03-B-3, ungepolt (Datenblatt Abschnitt 5)", "[V]", {"1": ("1", "1"), "2": ("2", "2")}),
    "Connector:USB_C_Receptacle_USB2.0_16P": ("KiCad-Symbol mit HRO-Footprint (Pads geprüft)", "[A]", None),
    "MCU_ST_STM32F4:STM32F411CEUx": ("ST-Symbol aus der KiCad-Bibliothek (UFQFPN-48); Pinbelegung mcu-funk.md 4", "[A]", None),
}
PASSIV = ("Device:R", "Device:C", "Device:L", "Device:FerriteBead_Small", "Device:Thermistor_NTC", "Connector:TestPoint",
          "Switch:SW_Push", "Jumper:SolderJumper_2_Open", "Jumper:SolderJumper_2_Bridged")


def pads(fp):
    if not fp or ":" not in fp:
        return None
    lib, name = fp.split(":", 1)
    wurzel = KICAD if lib == "Bienen" else FP_WURZEL      # Projektfootprints in hardware/kicad/Bienen.pretty
    datei = os.path.join(wurzel, lib + ".pretty", name + ".kicad_mod")
    if not os.path.exists(datei):
        return None
    with open(datei, encoding="utf-8") as f:
        return set(re.findall(r'\(pad "([^"]*)"', f.read())) - {""}


def teile():
    import hauptplatine
    for mod, platine in ((hauptplatine, "Haupt"),):          # Akku-Platine seit HW-06 Teil der Hauptplatine
        p = mod.baue()
        for b in [p.wurzel] + p.blaetter:
            for t in b.teile:
                if not t.ref.startswith("#"):
                    yield platine, b.name, t


def main():
    fehler, zeilen, offen = [], [], []
    for platine, blatt, t in sorted(teile(), key=lambda x: (x[0], x[2].ref)):
        pins = {p[0]: p[1] for p in t.pins}
        pd = pads(t.fp)
        # 1/2 Footprint und Pads
        if pd is None:
            if t.ref in OFFEN:
                fp_stat = "offen: " + OFFEN[t.ref]
                offen.append(t.ref)
            else:
                fp_stat = "FEHLT"
                fehler.append("%s: Footprint %r nicht in der Bibliothek" % (t.ref, t.fp))
        else:
            ohne_pad = sorted(set(pins) - pd)
            ohne_pin = sorted(pd - set(pins) - set(PAD_AUSNAHMEN.get(t.ref, ())))
            if ohne_pad or ohne_pin:
                fp_stat = "Pins ohne Pad %s, Pads ohne Pin %s" % (ohne_pad, ohne_pin)
                fehler.append("%s: %s" % (t.ref, fp_stat))
            else:
                fp_stat = "Pads = Pins (%d)" % len(pd)
            if t.ref in PLATZHALTER:
                fp_stat += "; Platzhalter: " + PLATZHALTER[t.ref]
        # 3 Datenblatt
        if t.lib_id in PASSIV or t.lib_id.startswith("Connector_Generic:"):
            db_stat, quelle = "passiv/Stecker", "–"
        elif t.lib_id not in DATENBLATT:
            db_stat, quelle = "FEHLT", "–"
            fehler.append("%s (%s): keine Datenblatt-Pinbelegung in DATENBLATT" % (t.ref, t.lib_id))
        else:
            quelle, status, tabelle = DATENBLATT[t.lib_id]
            if tabelle is None:
                db_stat = status
            else:
                abw = [(nr, pins.get(nr), tabelle.get(nr, (None, None))[1]) for nr in sorted(set(pins) | set(tabelle), key=str)
                       if pins.get(nr) != tabelle.get(nr, (None, None))[1]]
                if abw:
                    db_stat = "ABWEICHUNG %s" % abw
                    fehler.append("%s: Symbol ≠ Datenblatt %s" % (t.ref, abw))
                else:
                    db_stat = "%s %d Pins = Datenblatt" % (status, len(tabelle))
        zeilen.append("| %s | %s | %s | %s | `%s` | %s | %s | %s |" % (
            t.ref, platine, blatt, t.wert, t.fp.split(":")[-1] if t.fp else "–", fp_stat, db_stat, quelle))

    with open(ZIEL, "w", encoding="utf-8") as f:
        f.write("# Pin-/Footprint-Abgleich (REG26-08)\n\n")
        f.write("Erzeugt von `werkzeug/pin_footprint.py` aus den Generatoren; nicht von Hand ändern. "
                "Kennzeichnung: [V] in dieser Prüfung im Datenblatt gelesen, [V*] früher gelesen (Symbolkommentar), "
                "[A] Konvention/Annahme, [P] vor der Bestellung prüfen.\n\n")
        f.write("Ergebnis: %d Bauteile, %d Abweichungen, %d Footprints offen (%s).\n\n" % (
            len(zeilen), len(fehler), len(offen), ", ".join(offen) or "–"))
        f.write("| Ref. | Platine | Blatt | Wert | Footprint | Footprint-Prüfung | Datenblatt-Prüfung | Quelle |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        f.write("\n".join(zeilen) + "\n")
    for z in fehler:
        print("FEHL - " + z)
    print("Pin-/Footprint-Abgleich: %d Bauteile, %d Abweichungen, offen: %s" % (len(zeilen), len(fehler), ", ".join(offen)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
