# Unabhängiges Schaltplan-Review: main 4c12b6d – Akku, STM32, Ra-01SH, Flash

**Reviewdatum:** 10.10.2026 (MESZ)  
**Vollständiger geprüfter SHA:** [`4c12b6d77fdda784b83fffc3b4bdbb88e74cf614`](https://github.com/impyer/bienen-lora-logger/commit/4c12b6d77fdda784b83fffc3b4bdbb88e74cf614) („Hardware update“, 10.10.2026 04:10 UTC)  
**Vergleich:** [`6dbba8d`](https://github.com/impyer/bienen-lora-logger/commit/6dbba8d6bd5d255b94fc4c396584508698f3100d), [älteres unabhängiges Schaltplanreview V0.1](2026-10-09-schaltplan-v01-review.md) und [SCH26-Fix-Bericht](2026-10-09-sch26-behebung.md).  
**Normativ:** [Regelwerk 1.1](../entwicklung/README.md), D2 (MCU/Funk/Stecker) und D3 (Akku-/Ladeschutz), G0–G4 / T0–T6.  
**Verfahren:** GitHub-Commitvergleich, Quell- und Netzmodellreview, unabhängige textbasierte Pin-/Dokumenten-Gegenprobe, offizielle externe Herstellerunterlagen sowie **Logauswertung** des GitHub-KiCad-10-/Firmware-/Server-CI-Laufs. **Keine eigene lokale KiCad-ERC-Ausführung und kein direkt gerenderter visueller Schaltplan-/PDF-Review; kein PCB-/DRC-, SPICE-, Labor-, Funk- oder Akkutest.**

## 1. Kurzurteil und Scope

**Schaltplanentwicklung deutlich fortgeschritten, T3-CI für aktuellen Commit bestanden. Noch keine G2-Labor-/G3-Feld-/G4-Fertigungsfreigabe.** Die frühere Quell-/Generator-Divergenz (`REG26-13`, KiCad-CI rot auf `6dbba8d`) ist nachweislich behoben. Die neue Hauptplatine besteht inzwischen aus **Versorgung, MCU, Funk + Flash**. **Waage, Mikrofon und Außenanschlüsse** sind weiterhin nur spezifiziert, nicht als KiCad-Schaltplanblätter integriert. Es gibt **keine KiCad-Leiterplatte, Gerber-/Bohrdateien, CPL, fertige komplette Footprintbibliothek oder Zielboard-HiL-Daten**.

Neue Findings sind im [aktuellen Befundregister](befunde.md) und den Issues **[#4](https://github.com/impyer/bienen-lora-logger/issues/4), [#5](https://github.com/impyer/bienen-lora-logger/issues/5), [#6](https://github.com/impyer/bienen-lora-logger/issues/6), [#7](https://github.com/impyer/bienen-lora-logger/issues/7)** mit Abnahmekriterien hinterlegt.

## 2. Tatsächliche T0-/T3-Nachweise

| Prüfung | Evidenz / Ist | Status |
|---|---|---|
| GitHub Actions [Run 38023150749](https://github.com/impyer/bienen-lora-logger/actions/runs/38023150749) | **7/7 Jobs erfolgreich**: Firmware (bestehender BlackPill-F411CE + RFM95), Windows-Build, PC/Zeitsync/FFT, TTN-Formatter samt neuer Wetterstation S2120, Server-E2E, Hardwaremodelle, KiCad | **PASS für die genannten CI-Jobs** |
| KiCad 10.0.6 auf Ubuntu 24.04 | [KiCad-Job 114128277552](https://github.com/impyer/bienen-lora-logger/actions/runs/38023150749/job/114128277552): zwei Generatorläufe, diff gegen eingecheckte Quellen: **PASS** | T3, **PASS** |
| KiCad-ERC alle Schweregrade | Akku-Platine **0 Meldungen**; Hauptplatine **11 bekannte, begründete Meldungen**, davon 1 noch fehlende BQ25185-Footprintbibliothek und 10 global noch ohne Gegenstelle; **0 unerwartete Meldungen** | T3, **PASS**, *nicht ERC = 0 Warnungen* |
| KiCad-Netzlistenexport / Modellvergleich | **19/19 Akku-Netze** und **69/69 Hauptplatinen-Netze**, keine zusätzlichen Netze/abweichenden Pins; **48/48** Prüfungen bestanden (inkl. spezifischer Akku-/CE-/TMP_VCC-/J1-J203-Verbindungen) | T3, **PASS** |
| Eigene statische Gegenprüfung J302 ↔ `anschluesse.md` | Schaltplan-Pinmap und Dokumentations-Pinmap unabhängig aus den eingecheckten Quellen verglichen: **Pin 5/6/7 widersprüchlich** | T0, **FAIL**, SCH26-09 |
| Eigene Prüfung Automatisierung `pruefen.sh` | `DATEIEN` für doppelten SHA-256-Vergleich enthält nur Akku/Root/Versorgung/Symbolbibliothek; neue Blattdateien `mcu.kicad_sch` und `funk.kicad_sch` fehlen darin. **Separater CI-Git-Diff prüft sie trotzdem gegen den eingecheckten Stand.** | T0, **Teilabdeckung**, SCH26-12 |

**Grenze:** Die Host-/Firmware-CI kompiliert weiterhin die **bestehende BlackPill/RFM95/LMIC-Firmware**, **nicht** die noch zu erstellende **SX1262/RadioLib-Zielboard-Firmware**. Auch die 48 Netztests beweisen primär **Modell ↔ Zeichnung**, nicht die Richtigkeit aller Modellannahmen gegenüber externer Pin-/USB-/RF-Spezifikation.

## 3. Positive Überprüfungen am Schaltplan

- **Akku-Schutz:** `U1 HY2111-GB` / `Q1 FS8205`, `U2` und `U3 TMP390` an `TMP_VCC` über den aus Solar/USB versorgten `U204 TPS70933`; `Q2` für `CE_FREI` und `Q3` im NTC-Fuß `NTC_FUSS`. Fünfpoliges Akku-Kabel `J1 ↔ J203` im aktuellen Netzvergleich korrekt: GND, NTC, CE, TMP_VCC, VBAT. Die früheren 10-MΩ-Widerstände sind in den **führenden Quellen** `R5`/`R8`/`R205` jetzt 100 kΩ. **T3 bestanden, T4/Fault-HiL ausstehend.**
- **STM32F411CEU6 / MCU:** alle VDD/VSS/VDDA/VCAP/VBAT-Pins in der Generator-MCU-Pinmatrix zugewiesen; je VDD 100 nF und Sammelkondensator, VDDA mit Ferrit und 100 nF + 1 µF, VCAP1 mit 4,7 µF, BOOT0/BOOT1 mit definierten Pull-downs, HSE 25 MHz und LSE 32,768 kHz, NRST/SWD sowie USB-C CC1/CC2 je 5,1 kΩ. **HSE-/LSE-Anschwingen, USB-DFU und Steckertechnik real noch ungetestet.**
- **Funk + Flash:** SPI1 PA5/6/7 gemeinsam zu `U401 Ra-01SH` und `U402 NOR-Flash`, je eigenem Chipselect, 33-Ω-Reihenwiderstände auf Modul-SPI, 100-kΩ-Pull-ups auf `LORA_NSS`/`FLASH_CS`, Flash WP/HOLD je 10 kΩ nach 3,3 V. Radio-DIO1/BUSY/Reset global mit MCU verbunden. **Kein Test von realem SX1262/LLCC68/RX/TX/ADC-/RTC-/Flash-Powerloss.**
- **Versorgung:** BQ25185 150-mA-Sollstrom, RT9080 3,3 V, TPS22917 geschaltetes 3V3_SW, PV-ADC-Teiler 3,3 MΩ/470 kΩ, Eingangskondensator C201 inzwischen 50 V; einige Ausgangskondensatoren wegen DC-Bias vergrößert. **Datenblatt-/Temperatur-/Feldgrenzen am Muster noch offen.**

## 4. Neue Befunde – konkret und reproduzierbar

### SCH26-09 – P1 – Debug-Stecker J302/GND: Schaltplan widerspricht verbindlichem Kabelplan

**Beleg A – führende KiCad-Quelle:** [`hardware/kicad/hauptplatine.py`, `mcu()`, `J302`](../../hardware/kicad/hauptplatine.py): \`{"1":"+3V3","2":"SWDIO","3":"SWCLK","4":"NRST","5":"DBG_TX","6":"DBG_RX","7":"GND"}\`.

**Beleg B – Anschlussdokument:** [`hardware/anschluesse.md`, Tabelle 1, `J10`](../../hardware/anschluesse.md): \`1=3V3,2=SWDIO,3=SWCLK,4=NRST,5=GND,6=TX1,7=RX1\`.

**Folge:** Ein nach Dokumentation gefertigtes Debugkabel verbindet potenziell `TX1` des MCU (Schaltplan Pin 5) mit GND (Kabel laut Dokument Pin 5). An Pin 7 wird statt Dokumentations-RX die tatsächlich zu GND führende Leiterbahn angeschlossen. **Ausgangstreiber-/Signalrisiko; bisher kein reales Kabel getestet.**

**Abnahme:** Eine einzige autoritative Pinbelegung mit Draufsicht auf den realen Stecker festlegen; Generator und Dokumentation konsistent machen; **Netzlisten-Assertion pro Pin** plus Negativtest (Pin5 fälschlich auf GND); vor Verwendung Durchgangsmessung am stromlosen Muster. [Issue #4](https://github.com/impyer/bienen-lora-logger/issues/4).

### SCH26-10 – P1 – USB-VBUS-Presence bei akku-/solarversorgtem USB-Gerät nicht vorgesehen

**Beleg:** `J301` führt VBUS zur Schottky `D203` und gemeinsamem `VIN_LADER`. `U301 PA9` ist `DBG_TX`, `PA11/PA12` sind USB D−/D+. Kein separater `VBUS_SENSE`-Eingang am MCU; `ADC_SOLAR` sieht hinter den Schottkys **Solar oder USB**, nicht getrennt die Anwesenheit eines USB-Hosts. Dies ist zunächst **eine Design-/Compliance-Lücke bei geplanter regulärer USB-Gerätefunktion**, kein nachgewiesener USB-Ausfall.

**Externe Quelle:** ST [AN4879, VBUS sensing detection](https://www.st.com/content/st_com/en/technical-documents/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics_asset/chunk-003-topic-an4879-vbus-sensing-detection.html) verlangt bei selbstversorgten USB-Geräten die Host-/VBUS-Erkennung. Der alleinige STM32-ROM-DFU-Betrieb des F411 muss **gesondert nach AN2606 und am Muster** beurteilt werden; aus der fehlenden PA9-Verbindung folgt **nicht** automatisch, dass ROM-DFU scheitert.

**Abnahme:** USB-Anwendungsfall verbindlich festlegen (nur ROM-DFU oder eigenes USB-Device); bei eigener aktiver USB-Funktion VBUS-Presence via geschützten freien GPIO/Teiler erwägen, mit korrektem Verhalten auch bei MCU-VDD=0 und nicht gleichzeitig PA9 als USART-TX/VBUS; getrennte Tests bei USB-only, Solar-only, Akku-only und angeschlossenem USB-Kabel. [Issue #5](https://github.com/impyer/bienen-lora-logger/issues/5).

### SCH26-11 – P1 – HF-Antennenumstellung des Ra-01SH und DIO2/TXEN/RXEN nicht verifiziert

**Beleg:** `hauptplatine.py` `funk()`: `U401 DIO2=NC`, `DIO3=NC`, `ANT=NC`, `TXEN` über **offene** `JP401` zu PB14, `RXEN` über **offene** `JP402` zu PB15. `mcu-funk.md` begründet den Betrieb mit durch **DIO2 intern** kontrolliertem HF-Umschalter ausdrücklich nur anhand einer **Drittquelle**. Offizielle [Ai-Thinker-Ra-01SH-Pinbelegung](https://docs.ai-thinker.com/_media/lora/docs/ra-01sh_specification.pdf) benennt TXEN und RXEN als „RF control port“, aber das konkrete interne Schalt-/IPEX-Verhalten ist noch nicht für die beabsichtigte Liefercharge belegt. [LCSC C2764087](https://www.lcsc.com/product-detail/LoRa-Modules_Ai-Thinker-Ra-01SH_C2764087.html) listet die IPEX-Variante.

**Folge:** Offene Enable-Pfade könnten abhängig von der Modulrevision RX/TX unterbinden; das **ist noch kein bestätigter Hardwarefehler**. Die Lötbrücken bieten einen Reparaturpfad, ersetzen jedoch nicht die Verifikation vor einem Freigabe-Gate.

**Abnahme:** Exaktes Liefermodul/Chip identifizieren, Hersteller-Schematic oder Signal-/RF-Messung; RadioLib `setDio2AsRfSwitch`/Quarz-/Regulatorwahl prüfen; definierte Lötbrücken- und Resetzustände, SPI/BUSY/DIO1 sowie RX-/TX-/Strom-/Antenna-HiL mit geeigneter Antenne. Eigener Funkmodul-Footprint mit realer Padgeometrie prüfen. [Issue #6](https://github.com/impyer/bienen-lora-logger/issues/6).

### SCH26-12 – P2 – Zweimalige Generator-Prüfsumme deckt neue Schaltplanblätter nicht ab

**Beleg:** [`hardware/kicad/pruefen.sh`](../../hardware/kicad/pruefen.sh) setzt `DATEIEN` nur auf `bienen.kicad_sym`, `akku-platine/akku.kicad_sch`, `hauptplatine/logger.kicad_sch` und `hauptplatine/versorgung.kicad_sch`. `mcu.kicad_sch` und `funk.kicad_sch` fehlen bei der H1/H2-Doppelerzeugung.

**Einschränkung:** Der separate finale `git diff --exit-code` im [aktuellen KiCad-CI](https://github.com/impyer/bienen-lora-logger/actions/runs/38023150749/job/114128277552) umfasst die neuen Dateien und ist grün. Daher ist der **aktuell eingecheckte Stand T3-reproduzierbar**; nur ein spezifischer deterministischer Test hat noch eine Lücke.

**Abnahme:** beide Dateien in `DATEIEN` aufnehmen bzw. dynamisch alle geführten `.kicad_sch` erfassen, spezifische künstliche Nondeterminismus-Gegenprobe, KiCad-CI erneut grün. [Issue #7](https://github.com/impyer/bienen-lora-logger/issues/7).

## 5. Unverändert kritische und noch offene Entwurfsrisiken

- **Akku D3 – [`sicherheit-akku.md`](../../hardware/sicherheit-akku.md):** `HW26-16` gemeinsamer Fehlerpunkt BQ25185 für beide Temperaturabschaltungen (P1); `HW26-17` theoretisches Wiederladen einer extrem tiefentladenen Zelle aufgrund HY2111-0-V-Start (P1); `HW26-18` gefährliche Überspannungs-Fehlerart bei `U204`-Durchschlag auf `TMP_VCC`; `HW26-19` enge Kältereserve beim NTC-Fallback. Die dort vorgesehenen Entscheidungen **E-1 bis E-5** und sicherer G2-Prüfplan sind **noch nicht vollständig freigegeben oder nachgemessen**. 42-°C-TMP390-Stufe ist **im Entwurf** plausibel, keine nachgewiesene Hardware-Safety.
- **Noch kein vollständiger Schaltplan:** Waage, Mikrofon und Außenanschlüsse/ESD sowie reale PCB-Netzliste erst nach Ergänzung vollständig. Das Projekt nennt 104 Teile **für bisherige Blätter**, nicht für eine fertige Hauptplatine. ERC meldet 10 fehlende Gegenstellen an absichtlich noch offenen Signalnetzen.
- **Footprints und konkrete Bauteile fehlen:** BQ25185 DLH (Custom), Ra-01SH (Custom), Akkuhalter Keystone 1043 statt Platzhalter 1042; Reedkontakt, Side-View-LED, Modul-TVS, finaler SPI-Flash, Klemmen, LCSC-Nachweis. **Keine Layout-DRC/PCB-Daten vorhanden.**
- **Ungeprüfte reale Systemfunktionen:** USB-DFU mit 25-MHz-HSE, USB-C-Signalverhalten, SX1262/LLCC68-Pin-/RF-Schalter, LSE-Quarz, RTC-Weckraster, PCB-Stromaufnahme, RX1/RX2, LoRaWAN-Session im externen NOR unter Power-Cut, RTC-/FFT-/Mikrofon-Analogpfad. BlackPill-Firmwarebuild ist **nicht** der SX1262-Zielboard-Build.
- **EMV/Outdoor:** Solar-Panelspec, ESD-/Surge-Layout, gemessene Leitungs-/I²C-Kapazität, Kondensator-DC-Bias je finaler LCSC-Nummer und thermischer Belastungsfall bei Sonne bleiben zukünftige Design-/HiL-Prüfungen.

## 6. Arbeitspakete für Claude (Reihenfolge)

1. **P1 SCH26-09:** J302/J10-Stecker-Pinmap/Bestückungsdruck/Kabelplan eindeutig korrigieren, Netzlistentest ergänzen. Keine physische Debugbelegung nutzen, bis verifiziert.
2. **P1 SCH26-10:** USB-Rolle und VBUS-Detektion entscheiden (ROM-DFU vs. eigene USB-Firmware); falls erforderlich freier GPIO samt Spannungsteiler/Schutz, Pinmatrix, Testfälle und Standby-Verhalten spezifizieren. Kein unkontrollierter Zugriff auf PA9 wegen Debug-TX.
3. **P1 SCH26-11:** RF-Modulstückmuster, interne HF-Schaltung / TXEN/RXEN/DIO2 und IPEX-ANT-Verbindung ermitteln; Footprint vervollständigen, HiL-RF-Prüfplan abarbeiten.
4. **P2 SCH26-12:** neuen MCU-/Funk-Sheets in doppelte H1/H2-Prüfung aufnehmen.
5. **D3-Ladeschutz:** Offene `HW26-16–19`/E-1–E-5 vor sicherer Labormusterentscheidung überprüfen; keine gefährlichen Tests mit absichtlich tiefentladener echter Zelle. Testergebnisse aus Emulator und Hardware erst nach realer Durchführung eintragen.
6. **D2/D3 Gesamtboard:** Waage, Mikrofon, Anschluss-/ESD-Blätter hinzufügen; Custom-Footprints, PCB/DRC und Fertigungsdaten. Danach erst G2/G3/G4 entsprechend [Freigaberegelwerk](../entwicklung/tests-freigaben.md) prüfen.

## 7. Freigabeentscheidung

| Gate | Status bei `4c12b6d` | Begründung |
|---|---|---|
| **G1: GitHub-Code-/Schaltplan-Integration** | **T3-CI bestanden (7/7)**; vier neue Reviewaufgaben, insbesondere Steckerplan und USB/RF, offen | Unterlagen/Details gehören noch zur nächsten Revision; sie sind **kein CI-Fehler** dieses Commitstands |
| **G2: sicher begrenzter Akku-/Board-Laborversuch** | **nicht automatisch freigegeben** | vollständiger Aufbau, sichere Gegenprüfung, Entscheidungen E-1–E-5/Boardrisiken stehen aus |
| **G3: überwachter Feldtest** | **nicht freigegeben** | kein realer SX1262-/Batterie-/USB-HiL-Nachweis |
| **G4: Fertigung / Release** | **nicht freigegeben** | unvollständige Blätter, Footprints, Layout, DRC/BOM/CPL und Sicherheitsabnahme |

**Urteil:** Aktuelle KiCad-GitHub-Integration ist **nachweislich funktionsfähig und reproduzierbar auf T3-Ebene**. Die unabhängige Kontrolle zeigt einen **konkreten externen Pinbelegungsfehler** und zwei **gezielte Schnittstellen-/Hardware-Risiken**, welche die modellinternen 48/48 Tests nicht erkennen können. Der sicherheitsrelevante Teil bleibt bis zur geeigneten Hardwareprüfung unter Sperre.
