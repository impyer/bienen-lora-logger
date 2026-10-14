# PCB Layout Specification – Beehive Logger Main Board PCB-MAIN-0.1

**Client:** Philipp Schnabel (GitHub `impyer`) · **Project:** open-hardware beehive logger, repository `impyer/bienen-lora-logger`
**Document status:** issue 1, 14 Oct 2026 · Schematic revision: V0.1 draft (decisions HW-01 … HW-08)
**License of the result:** CERN-OHL-S-2.0 (see section 10)

> **Kurzfassung (Deutsch):** Auftrag an einen externen Layouter: Platzierung, Routing und JLCPCB-Fertigungsdaten
> (Gerber, Bohrdaten, BOM, CPL) für die 4-lagige Hauptplatine 121 × 121 mm im KiCad-10-Projekt. Der Schaltplan ist
> vorgegeben und wird nicht vom Layouter geändert; fehlende LCSC-Nummern schlägt er vor, Philipp gibt frei. Abnahme:
> DRC 0, Schaltplanabgleich 0, Freigabe Platzierung vor dem Routing, JLCPCB-DFM ohne Fehler. Ergebnis unter CERN-OHL-S-2.0.

---

## 1. Scope of work

| # | Task | Required |
|---|---|---|
| 1 | Review the package, ask questions, confirm feasibility (section 9, milestone M0) | yes |
| 2 | **Component placement** inside the given board frame, respecting sections 3–6 | yes |
| 3 | **Routing** of all nets on 4 layers, copper zones, stitching vias | yes |
| 4 | **LCSC part selection** for every BOM line without an LCSC number (151 of 172 parts), preferring JLCPCB *Basic* parts and parts in stock (section 7) | yes |
| 5 | **Manufacturing outputs** for JLCPCB: Gerber, drill files, BOM and CPL in JLCPCB format (section 8) | yes |
| 6 | Updated **KiCad 10 project** (`logger.kicad_pcb`, project file) with the routed board | yes |
| 7 | Support until the JLCPCB DFM/assembly check passes without errors | yes |

Not in scope: changing the circuit, firmware, enclosure design. If you find a schematic problem, **report it** (section 2.3) – it will be fixed at the source.

## 2. Input package

### 2.1 Contents (ZIP `layout-auftrag-PCB-MAIN-0.1-<sha>.zip`, built by `hardware/layout-auftrag/paket_bauen.py`)

| Item | File(s) |
|---|---|
| KiCad 10 project (schematic with 7 sheets, board frame) | `kicad/hauptplatine/` (`logger.kicad_pro`, `logger.kicad_sch` + sheets, `logger.kicad_pcb`) |
| Project libraries | `kicad/bienen.kicad_sym`, `kicad/Bienen.pretty/` (footprints), `fp-lib-table`, `sym-lib-table` |
| Schematic PDF, netlist | `kicad/pdf/logger.pdf`, `kicad/netzliste/logger.net` |
| BOM (current state, with known LCSC numbers) | `bom_aktuell.csv` |
| Pin/footprint cross-check | `kicad/pin_footprint.md` |
| Requirements (German originals) | `doku/LASTENHEFT.md`, `doku/anschluesse.md`, `doku/mcu-funk.md`, `doku/versorgung.md`, `doku/waage.md`, `doku/mikrofon.md`, `doku/sicherheit-akku.md` (section 10) |
| This specification | `PFLICHTENHEFT.md` |

The enclosure 3D model (Camdenboss CBHUB-02, STEP) is a manufacturer file and is **not** in the repository; the client sends it separately on request. All dimensions you need are in section 3.

### 2.2 Tools

- **KiCad 10.0.x** (the project is generated with KiCad 10.0.6). Please do not save with an older or newer major version.
- Libraries: KiCad 10 standard libraries plus the two project libraries above (paths are relative in `fp-lib-table` / `sym-lib-table`).

### 2.3 Source of truth – do not edit the schematic

The schematic files are **generated** by `hardware/kicad/hauptplatine.py` and checked automatically (ERC, net tests). Therefore:

- **Do not edit the schematic in KiCad.** Edits would be overwritten.
- Footprint changes, pin swaps, value changes, added test points or parts: send a **change request** (list with reference, old, new, reason). The client changes the generator and sends an updated schematic; you then run *Tools → Update PCB from Schematic* (F8).
- Gate/pin swaps for routing convenience are possible **only** after agreement (e.g. STM32 GPIOs are fixed by alternate functions, see `doku/mcu-funk.md` §4).

## 3. Board and mechanics

| Item | Requirement |
|---|---|
| Outline | **121.0 × 121.0 mm**, corner radius 3 mm (already in `logger.kicad_pcb`, Edge.Cuts) |
| Mounting holes | 4 × Ø 3.4 mm NPTH on a **110.2 × 110.2 mm** square, centred; copper keep-out Ø 7 mm (already placed). Standoffs 10 mm, self-tapping screws Ø 3 mm |
| Thickness / layers | 1.6 mm, **4 layers** |
| Bottom side | **no components** (only THT leads/solder joints). Free space below the board ≥ 13 mm |
| Component height above the board | **≤ 40 mm** including mated plugs and the 18650 cell in its holder (~21 mm) |
| Enclosure | board edge to inner wall 16.2 mm on all sides; cables enter later through glands in the bottom wall (position not yet fixed) |
| Status LED | D301 (side-view LED) at a **side edge**, LED front ≤ 0.7 mm inside the board edge; a light pipe (Bivar PLTR2, wall mounted) bridges ~19.4 mm to the outside |
| Reed switch | SW304 parallel to the same side edge, **10–20 mm** from D301 (operated with a magnet from outside; silkscreen "Magnet hier" is on the enclosure) |
| Board ID | silkscreen `PCB-MAIN-0.1` (already on F.Silkscreen, may be moved) plus `CERN-OHL-S-2.0` and the project name `bienen-lora-logger` |

## 4. Placement rules

**You decide the placement and the connector positions** (client decision HW-08). Constraints:

1. **External connectors** J201/J202 (solar), J703 (BME280, 6-pin), J701/J702 (DS18B20), J501 (load cell, 5-pin), J601 (RJ45, microphones): preferably along **one board edge** facing the future cable glands; two edges are acceptable. Each terminal must be pluggable/unpluggable with the mating plug (DEGSON 15EDGK) without touching neighbours. Width reference: between the hole keep-outs of one edge ~102 mm are free; the terminals need ~86 mm plus ~16 mm for the RJ45.
2. **ESD parts directly behind each external connector**, before any other part: D204 (J201/J202), D702 (J703), D701 (J701/J702), D501 (J501), D601 (J601). Ground pin of the ESD part to L2 with ≥ 2 vias, shortest path.
3. **Radio module U401 (Ra-01SH) at the board edge opposite the external connectors**, IPEX connector side towards the enclosure wall. **Pin 1 (ANT) must stay unconnected – no trace, no copper stub** (antenna via IPEX only; ANT pad and IPEX share RF_OUT inside the module).
4. **USB-C J301**, debug header J302, expansion header J704, buttons SW301 (Reset), SW302 (BOOT), SW303 (Service): inside, easy to reach when the lid is open; J301 accessible with a cable plugged (not hidden under the cell).
5. **Battery holder BT801** (Keystone 1042, 88 × 22 mm): not at the radio edge, not next to the charger U201. **U802, U803, TH801 (temperature sensors for the charge lock) under the cell**, thermally coupled to it (a thermal pad will be placed between cell and sensors), away from heat sources (U201, U202, U204, U401).
6. Microphone/audio block (U601 audio ADC, J601) and load-cell block (U502 HX711, J501) **far from the 5 V boost converter U501/L501 and from the radio**; U601 close to J601.
7. The 5 V boost converter U501 (TPS61240, 3.5 MHz) with C501, L501, C502 as a tight loop (TI layout example).
8. Crystals Y301 (25 MHz) and Y302 (32.768 kHz) directly at the STM32 U301; load capacitors next to the crystal; no other signals between crystal and MCU pins; GND below.
9. STM32 decoupling: each 100 nF next to its VDD/VSS pair, VCAP (C307, pin 22) and VDDA filter (FB301, C305, C306) close to their pins. Lesson from our own trial: put the capacitors **at the package corners** so the signal pins can escape.
10. Leave roughly one third of the area free/usable if possible (future extensions) – a wish, not a must.

## 5. Routing rules

### 5.1 Stack-up and planes (requirement M8)

| Layer | Use |
|---|---|
| L1 (F.Cu) | components, signals |
| **L2 (In1.Cu)** | **continuous GND plane – do not split, no signal tracks** |
| L3 (In2.Cu) | power (+3V3 zone, SYS, 5 V where needed) with GND fill in the remaining area |
| L4 (B.Cu) | signals, GND fill |

- GND stitching vias along the board edge and around the radio module, the boost converter and the load-cell and microphone blocks.
- Thermal pads (U201, U301, U501, U601) soldered to GND with vias to L2 (U201: 2 vias inside the pad as in the TI example; U301: up to 9).

### 5.2 Design rules (JLCPCB standard 4-layer; check current JLCPCB capabilities)

Track/space ≥ 0.15/0.15 mm (preferably 0.2 mm where possible), via 0.3 mm drill / 0.6 mm pad, copper to board edge ≥ 0.3 mm, hole clearance 0.25 mm. These values are set in the project; keep DRC at **0 errors**.

### 5.3 Net-specific requirements

| Net / block | Requirement |
|---|---|
| **B− (battery minus)** | **B− is NOT GND.** It is a small island between BT801 (−), U801 VSS and Q801 S1 only. Any connection B− ↔ GND bypasses the protection FET (safety issue, D3). Do not include B− in any GND zone. |
| VBAT, B+, SYS, VIN_LADER | power paths, ≥ 0.5 mm (charge current up to 150 mA, system peaks ~120 mA during radio TX, boost input ~0.4 A peak); short |
| PV1/PV2 → D201/D202 → VIN_LADER | ≥ 0.5 mm; SMAJ12A D204 right at the input |
| VBUS, USB_DP/USB_DM | USB 2.0 full speed: route D+/D− as a pair (~90 Ω differential, length matched within 2 mm), short, USBLC6 U302 next to J301 |
| SPI1 (SPI_SCK/MISO/MOSI, LORA_NSS, FLASH_CS) | short; series resistors R401–R404 (33 Ω) close to the radio module U401; keep away from the audio block |
| I2S_CK, I2S_WS, I2S_SD (PB12/PA15/PB5 ↔ U601) | direct, avoid crossing the analog microphone path |
| **PDM_CLK** (U603 → R612 → J601 pin 2) | U603 and R612 close to J601; continuous GND below; required edge rate at the microphone ≤ 13 ns – keep it short on the board |
| PDM_DATA_K → R613 → PDM_DATA (DMDIN) | short, GND reference |
| **MIC_P / MIC_N** (J601 7/8 → C619/C620 → U601 IN2L/IN3L) | analog, **route as a pair**, symmetric, away from clocks/SPI/converter; C622/C623 at the connector |
| U601 supplies | 3V3_ANA, 1V8_ADC, 3V3_SW decoupling (100 nF + 1 µF each) directly at pins 10/22/21 |
| HX711 (U502) and load cell lines ZELLE_EP/SP/SN | analog, short, symmetric S+/S−, away from U501; ferrites per schematic |
| 1-Wire, I²C (ONEWIRE, I2C_SCL/SDA) | no special constraints; pull-ups at the connectors as drawn |
| RF | no traces under the radio module except as the module datasheet allows; GND below with stitching |

## 6. Silkscreen and assembly

- Every external connector: name (J1 … J11 per `doku/anschluesse.md`, e.g. "J5 MIKROFON") and pin names on silkscreen. At J601 additionally **"MIKROFON – KEIN NETZWERK/PoE"**.
- Polarity marks for BT801 (+), diodes, LED, USB.
- Test points (requirement M9): 3V3, VBAT, SYS, VIN_LADER, GND, PDM_CLK, I2S_CK – exposed copper pads ≥ 1.0 mm or the TP footprints you propose (change request, section 2.3). TP201/TP202 exist already.
- Fiducials as needed for JLCPCB assembly. **All parts top side**, SMD and THT assembled by JLCPCB (requirement M7).
- Keep reference designators readable where space allows; otherwise on F.Fab.

## 7. Part selection (LCSC)

- 21 BOM lines already have an LCSC number (fixed – keep them). For the others, propose an LCSC part per line: **JLCPCB Basic part preferred**, otherwise Extended with stock ≥ 100; footprint must match the schematic footprint, or state the needed footprint change.
- Values with tolerance/voltage/dielectric in the schematic are binding (e.g. "4,7µ 16V X7R", "2,49k 1%", "C0G").
- Parts with open choice (marked [P] in the docs): RJ45 J601 (**shielded, without magnetics, without LEDs**, through-hole; footprint proposal `RJ45_RCH_RC01937`), ferrites FB301/FB501/FB502/FB601/FB602, L501 (1 µH, Isat ≥ 0.7 A), TVS D401 (3.3 V), SPI flash U402 (64 Mbit SOIC-8 208 mil, e.g. XT25F64B/ZD25Q64D), DEGSON terminals (part numbers per pole count in `doku/anschluesse.md` §2).
- Deliver the proposals as a table (reference, value, LCSC number, Basic/Extended, stock, price, remark). **The client approves before ordering.**

## 8. Deliverables

1. `logger.kicad_pcb` (+ project file) – routed, zones filled, **DRC 0 errors**, *Schematic parity* 0 errors (KiCad 10).
2. **Gerber** files (all copper layers, masks, silkscreen, paste, Edge.Cuts) and **drill files** (Excellon, PTH/NPTH), as a ZIP that JLCPCB accepts without warnings.
3. **BOM** (JLCPCB format: Comment, Designator, Footprint, LCSC Part #) and **CPL/pick-and-place** (Designator, Mid X, Mid Y, Layer, Rotation) with rotations checked against the JLCPCB preview.
4. LCSC proposal table (section 7) and the list of change requests you raised.
5. Screenshots/PDF of all layers and a 3D view (top).

The client uploads the files to his JLCPCB project himself (no account sharing is needed).

## 9. Milestones and acceptance

| Milestone | Content | Acceptance by the client |
|---|---|---|
| M0 | Questions answered, feasibility and price confirmed | written OK |
| **M1** | **Placement proposal** (KiCad file + PDF/screenshot), connector positions, LCSC proposals (draft) | **review before routing starts** (1 round included) |
| M2 | Routed board, DRC 0, parity 0 | review (1 round included) |
| M3 | Manufacturing outputs, final BOM/CPL | JLCPCB upload and DFM/assembly check without errors |

Acceptance criteria for M2/M3: all rules of sections 3–6 met, DRC 0, parity 0, no schematic file changed (the client re-runs the generator; only `logger.kicad_pcb` and the project file may differ), Gerber/BOM/CPL accepted by JLCPCB.

## 10. License and rights

The repository is open hardware: design data (schematics, footprints, board) under **CERN-OHL-S-2.0**, scripts under GPL-3.0-or-later. By delivering, you agree that your layout is published under CERN-OHL-S-2.0 in the repository; you may be credited as contributor (name or handle as you wish). Please do not include third-party footprints or 3D models with incompatible licenses; state the source of any footprint you add.

## 11. Contact and communication

Questions via the Fiverr order chat. Language: English (German welcome). Please ask early rather than assume – especially for anything in section 5.3 (safety: B− net) and section 4 (mechanics).
