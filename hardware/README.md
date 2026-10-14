# Hardware

Hier entsteht eine **eigene, offene Logger-Platine** (KiCad, CERN-OHL-S-2.0), die JLCPCB weitgehend bestückt
mit Funkmodul Ai-Thinker Ra-01SH (SX1262). Dafür entsteht eine neue Firmware mit RadioLib
(siehe Lastenheft, Abschnitt 6); Musterlogger mit beelogger-Platine und RFM95 laufen weiter mit `firmware/STM32_LORA_261008_ZS`.

- Anforderungen: [`LASTENHEFT.md`](LASTENHEFT.md) und die Blöcke [`versorgung.md`](versorgung.md), [`mcu-funk.md`](mcu-funk.md), [`waage.md`](waage.md), [`mikrofon.md`](mikrofon.md), [`anschluesse.md`](anschluesse.md).
- Sicherheitsanalyse Akku und Laden (D3, Voraussetzung für G2): [`sicherheit-akku.md`](sicherheit-akku.md).
- Prüfberichte: [`docs/testberichte/`](../docs/testberichte/README.md); Freigaberegeln für Hardware: [`docs/entwicklung/hardware.md`](../docs/entwicklung/hardware.md).
- KiCad-10-Projekte: [`kicad/`](kicad/README.md) (V0.1 Hauptplatine mit allen Blättern, Akku seit HW-06 auf der Hauptplatine; **Entwurf, noch keine Fertigungsfreigabe**). Stand der Befunde: [Befundregister](../docs/testberichte/befunde.md).
- Layout-Auftrag (HW-08): Pflichtenheft für den externen Layouter (englisch) [`layout-auftrag/PFLICHTENHEFT.md`](layout-auftrag/PFLICHTENHEFT.md); Übergabepaket mit `python3 hardware/layout-auftrag/paket_bauen.py` (ZIP unter `build/`); Abnahme-Netzvergleich `netz_vergleich.py <platine.ipc>`.
- Fertigungsdaten für JLCPCB (Gerber, Bohrdaten, BOM, CPL): liefert der Layouter (Pflichtenheft Abschnitt 8); Ablage im Repo mit der ersten Fertigungsfreigabe.

Die Platinen von beelogger.de gehören nicht hierher, weil ihre Fertigungsdaten nicht offen lizenziert sind.
