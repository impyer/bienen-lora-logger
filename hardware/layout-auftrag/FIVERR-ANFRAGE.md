# Anfragetext Fiverr – Kostenvoranschlag (14.10.2026)

Fiverr erlaubt höchstens 2500 Zeichen. Der Text unten hat 1816 Zeichen ohne Titel (Titel 94 Zeichen); bewusst ohne
Markdown-Formatierung, damit er beim Einfügen gleich aussieht. Er verweist auf das öffentliche GitHub-Repository
(Pflichtenheft und Schaltplan); die Links funktionieren erst, wenn der Stand mit `hardware/layout-auftrag/` gepusht und das
Repository öffentlich ist. Langfassung der Anforderungen: [`PFLICHTENHEFT.md`](PFLICHTENHEFT.md).

**Titel:**

```
Quote request: 4- or 6-layer PCB layout, 121 x 121 mm (STM32 + LoRa + audio ADC), JLCPCB-ready
```

**Text:**

```
I am looking for a quote for the layout of an open-hardware beehive logger. The schematic is finished and verified (ERC clean, automated net checks).

Board
- 121 x 121 mm, 4 or 6 layers (your choice), 1.6 mm, 4 fixed mounting holes, all parts on top, max. 40 mm height
- approx. 179 parts: STM32F411 (QFN-48), Ra-01SH LoRa module (SX1262, IPEX), RN4871 BLE module (chip antenna, keep-out zones), BQ25185 charger (WSON, 0.4 mm pitch), 5 V boost converter, HX711 load-cell ADC, TLV320ADC3101 audio ADC (analog + PDM microphone), USB-C (charging only), 18650 holder, pluggable terminals, RJ45
- Mixed-signal: low-noise analog paths next to a boost converter and a LoRa radio; battery minus must stay separate from GND

Scope
1. Placement (you choose connector positions within given constraints), my review before routing
2. Routing with a continuous GND plane under the top layer, DRC clean
3. LCSC part selection for about 157 of 179 BOM lines (Basic parts preferred), approved by me
4. JLCPCB files: Gerber, drill, BOM, CPL, plus IPC-D-356 netlist
5. Editable source files; any EDA tool is fine (design data are KiCad 10, board should import into KiCad)
6. Support until the JLCPCB file check passes
Circuit stays as provided; changes via change requests.

Milestones: M1 placement, M2 routing, M3 manufacturing files. One review round each.
Acceptance: DRC 0, IPC-D-356 netlist matches mine, JLCPCB check without errors.
Details: https://github.com/impyer/bienen-lora-logger
Layout specification: hardware/layout-auftrag/PFLICHTENHEFT.md
Schematic (KiCad 10, PDF): hardware/kicad/
Open hardware (CERN-OHL-S-2.0), credit if you wish.

Please quote:
1. Price and delivery time per milestone (M1, M2, M3)
2. Price for the LCSC part selection (included or separate)
3. EDA tool, 4 or 6 layers and why
4. 1-2 comparable boards you designed (MCU + RF + analog), ideally JLCPCB assembled
```
