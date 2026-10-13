# Projektentscheidungen, Governance- und Ausnahmeregister

**Stand:** 10.10.2026 · **Entwicklungsregelwerk:** Version 1.1, ANGENOMMEN.
**Beschlüsse:** [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md) (Regelwerk 1.0), [ADR-0002](entscheidungen/ADR-0002-regelwerk-1-1.md) (Fassung 1.1).
**Maintainer:** Philipp Schnabel (GitHub `impyer`).

Das Register trennt angenommene Verfahrensregeln von noch offenen Sachentscheidungen. **Offen** bedeutet nicht **bestanden**. Die Projektleitung trifft die formale Entscheidung; eine KI ersetzt weder die nötige unabhängige Sicherheitsprüfung noch einen Labornachweis. Der Stand einzelner technischer Befunde steht **nur** im [Befundregister](../testberichte/befunde.md).

## Governance

| ID | Stand | Entscheidung bzw. offene Aufgabe |
|---|---|---|
| **GOV-01** | **ENTSCHIEDEN 09.10.2026** | Lizenzaufteilung in `hardware/` und `mechanik/`: **Python- und Shell-Skripte** (`*.py`, `*.sh`) unter **GPL-3.0-or-later**; **Schaltpläne, Symbole, Footprints, Layouts, KiCad-Projektdateien und Exporte** unter **CERN-OHL-S-2.0**, auch wenn sie von einem GPL-Skript erzeugt werden. Umsetzung: `LICENSE.md`, `SPDX-License-Identifier` in den Skripten. Rechteinhaber: Philipp Schnabel. |
| **GOV-02** | **ANGENOMMEN, präzisiert in 1.1** | G0/G1 dokumentiert der Maintainer; er entscheidet G2. **D3-Sicherheitsfunktionen:** G2 (Labormuster) erfordert Gefährdungs-/Fehleranalyse, Netz-/ERC-Prüfung und einen sicheren Versuchsplan (Zell-Emulator, Strombegrenzung, keine Fehlerversuche an echten Zellen), gegengelesen durch einen zweiten Prüfweg. G3/G4 erfordern zusätzlich bestandene T4-Messungen **und** ein **unabhängiges fachkundiges Review**: ein bis zwei befreundete Hardware-Entwickler des Maintainers, die die Änderung nicht selbst entworfen haben, mit schriftlichem Prüfbericht. CI, Selbstreview oder KI-Review allein genügen dafür nicht. |
| **GOV-03** | **ANGENOMMEN – Lieferumfang Hardware** | Ein als **fertigungsreif** bezeichnetes Open-Hardware-Release umfasst die bearbeitbaren Quellen inkl. Generatoren und eigener Bibliotheken, Netzliste/Schaltplan/ERC, PCB/DRC, Gerber/Bohrdaten, BOM/CPL, Montage-/Kabelpläne, Testpunkte und Prüfanweisungen. Unfertige Prototypen sind nur mit deutlicher Kennzeichnung „**experimentell, nicht fertigungsreif**“ zu veröffentlichen. |
| **GOV-04** | **OFFEN** | Konkrete elektrische, thermische, Energie-, Funk- und Messgrenzwerte für die real beschaffte Zell-, Board- und Bauteilrevision im Anforderungs-/Prüfplan aus Herstellerquellen festlegen. Ohne diese dürfen abhängige PCB-/Labor-/Feld-Gates nicht als bestanden gelten. Erster Schritt: Typ und Datenblatt der gekauften 18650-Zelle. |

## Technische Festlegungen

| ID | Stand | Festlegung |
|---|---|---|
| **HW-01** | **ENTSCHIEDEN 10.10.2026** (Philipp) | **USB-C nur zum Laden und Aufspielen** (ROM-DFU über BOOT0 + Reset). Die Anwendungsfirmware schaltet die USB-Peripherie nie ein; Service-Konsole über Serial1 (J10/J302) und SWD. Damit ist keine VBUS-Erkennung nötig (Befund SCH26-10). Eine eigene USB-Funktion wäre eine neue Entscheidung mit VBUS-Teiler nach ST AN4879. Details: `hardware/mcu-funk.md` 1.3, Lastenheft K5. |
| **HW-02** | **ENTSCHIEDEN 13.10.2026** (Philipp) | **Akkuhalter Keystone 1042 (SMD)** für die 18650-Zelle auf der Akku-Platine, statt 1043 (Durchsteck). Grund: Footprint `Battery:BatteryHolder_Keystone_1042_1x18650` liegt in der KiCad-Bibliothek; Lastenheft V1 und `versorgung.md` 3.3 angepasst. Polung laut Footprint: Pad 1 = Plus. Halterung mechanisch am Muster prüfen (Zelle im Gehäuse, Erschütterung) [P]. Details: `docs/testberichte/2026-10-13-footprints-bienen.md`. |
| **HW-03** | **ENTSCHIEDEN 13.10.2026** (Philipp) | **Bauhöhe im Gehäuse CBHUB-02-GY selbst festgelegt:** Hauptplatine auf **glatten Distanzhülsen 10 mm** (Innen-Ø ca. 3,2 mm, Außen-Ø ≤ 6 mm) über den Gehäusedomen, befestigt mit selbstformenden Schrauben durch Platine und Hülse in die Dombohrung (laut STEP Ø 2,4 mm, nicht 3,6 mm); **Bauhöhe über der Platine höchstens 40 mm** (Reserve zur geschätzten Innenhöhe von ca. 50–55 mm über der Platine). Damit hängt das Layout nicht mehr vom STEP-Modell ab; die Domhöhe verschiebt nur alles gleichmäßig. Lichtleiter-Bohrung am ersten Muster nach Maß bohren und übertragen. STEP-Modell ist angefragt (Philipp) und dient später zur Kontrolle. Schraubentyp und Hülsenlänge am Muster bestätigen [P]. **Kontrolle mit STEP (13.10.2026): bestanden** – Freiraum über der Platine ≥ 44,3 mm (Ecken), unter der Platine ≥ 13 mm (Lastenheft 4.1a). |
| **HW-04** | **ENTSCHIEDEN 13.10.2026** (Philipp) | **Mikrocontroller STM32F411CEU6 bleibt; kein FPGA, kein externer RAM.** Alternativen (STM32L433, F401, APM32F411, AT32F403A, GD32F303, CH32V203, STM32WLE5) geprüft: keine bietet bei gleicher Lieferbarkeit einen spürbaren Vorteil; L433 spart nur ca. 2 % der Tageslast und bringt Neuverdrahtung und 64 KB RAM. FPGA ohne Aufgabe im Lastenheft; PSRAM nicht als Arbeitsspeicher nutzbar, dauerhafte Daten im vorhandenen SPI-Flash. **STM32L433CCU6 als Ausweichoption** bei Lieferproblemen. Details: [`hardware/mcu-funk.md`](../../hardware/mcu-funk.md) 1.5. |

## Ausnahmen

| ID | Regel | Ursache | Risiko | Zulässig | Ersatzmaßnahme | Owner | Review |
|---|---|---|---|---|---|---|---|
| **EX-01** | [S-05 Nr. 5](software.md) (keine Passwörter in URLs) | Die Altschnittstelle `beelogger_log.php` (beelogger M.40) erwartet das Log-Passwort als GET-Parameter `PW`. Der LoRa-Eingang ruft sie so auf. | Passwort kann in Webserver-Zugriffslogs, Proxys oder Browser-Verläufen landen. | eigener Server, Aufruf serverintern bzw. nur über HTTPS | HTTPS für externe Aufrufe; Zugriffslogs des Webservers für diese Pfade schützen bzw. ohne Query-String protokollieren; eigenes Log-Passwort nur für diesen Zweck; Passwort nie in Projektlogs (`le_log`) schreiben | Philipp Schnabel | bei jeder Änderung an Server/LoRa-Eingang, spätestens vor Feldrelease |

## Konkrete nächste Fachaufgaben

1. **Sicherheit:** offene und „im Entwurf behobene“ D3-Befunde laut [Befundregister](../testberichte/befunde.md) bis G2 führen (Gefährdungsanalyse, sicherer Versuchsplan); danach T4-Messungen und unabhängiges Review für G3.
2. **GOV-04:** Für tatsächlich ausgewählte Akkuzelle und PCB alle Soll-/Toleranzgrenzen mit Quellen und Test-IDs definieren.
3. **GOV-01 umsetzen:** `LICENSE.md` und SPDX-Kopfzeilen (mit Fassung 1.1 erledigt; neue Skripte erhalten die Kopfzeile von Anfang an).

Grundsatz-/Gate-Änderungen nur mit neuer ADR und dokumentierter Auswirkung. Historische Testberichte bleiben unverändert.
