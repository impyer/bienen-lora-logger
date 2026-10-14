# Anfragetext Fiverr (Entwurf, 14.10.2026)

Zum Einfügen als Fiverr-„Brief“ oder als Nachricht an ausgewählte Anbieter. Budget und Termin vor dem Absenden eintragen.
Pflichtenheft und Übergabe-ZIP erst dem ausgewählten Anbieter geben.

---

**Title:** 4- or 6-layer PCB layout (121 × 121 mm, STM32 + LoRa + audio ADC) – placement, routing, JLCPCB-ready files

I need an experienced PCB layout designer for an open-hardware beehive monitoring logger. The schematic is finished and verified (ERC clean, automated net checks); I need placement, routing and manufacturing data for JLCPCB assembly.

**Board**
- 121 × 121 mm, **4 or 6 layers (your choice)**, 1.6 mm, 4 fixed mounting holes, all components on top
- approx. 172 parts: STM32F411 (QFN-48), Ai-Thinker Ra-01SH LoRa module (SX1262, IPEX antenna), Li-ion charger BQ25185 (WSON, 0.4 mm pitch), 5 V boost converter, HX711 load-cell ADC, TI TLV320ADC3101 audio ADC with an analog and a PDM microphone, USB-C, 18650 holder on board, pluggable terminals and an RJ45 jack
- Mixed-signal: low-noise analog paths (load cell, microphone) next to a 3.5 MHz boost converter and a LoRa radio

**Scope**
1. Component placement (you choose connector positions within the given constraints) – I review before routing
2. Routing (continuous GND plane under the top layer), DRC clean
3. LCSC part selection for the BOM lines without an LCSC number (Basic parts preferred), approved by me
4. JLCPCB-ready outputs: Gerber, drill files, BOM and CPL, plus an IPC-D-356 netlist
5. Editable source files – **any EDA tool is fine** (design data are KiCad 10; if you use another tool, please check that your board imports into KiCad)

**Provided:** a detailed layout specification (mechanics, placement rules, net-specific routing rules, deliverables, acceptance), KiCad project, schematic PDF, netlist and BOM.

**Acceptance:** DRC 0, your IPC-D-356 netlist matches my netlist (checked by script), JLCPCB file check without errors.

**License:** open hardware (CERN-OHL-S-2.0); your layout will be published under this license, with credit if you wish.

**Please include in your offer:**
1. Which EDA tool and whether you would use 4 or 6 layers (and why)
2. 1–2 examples of comparable boards (MCU + RF + analog), ideally with JLCPCB assembly
3. Price and delivery time for placement (milestone 1) and for routing + output files (milestones 2/3)
4. Whether LCSC part selection for about 150 lines is included

Budget: [your budget] · Desired delivery: [date]
