# Hardware-Review 0.4 – Stromversorgung, STM32/SX1262, Sensoren und PCB-Vorbereitung

**Prüftag:** 09.10.2026 (MESZ)  
**Hardware-Quellstand:** [5c94e1b046d3075bd0e5b4e62870662da280b583](https://github.com/impyer/bienen-lora-logger/commit/5c94e1b046d3075bd0e5b4e62870662da280b583), Lastenheft 0.4  
**Zusätzlicher CI-Workflowstand:** [6b83d367f4383710bcb8503a2989c75b8c0c5390](https://github.com/impyer/bienen-lora-logger/commit/6b83d367f4383710bcb8503a2989c75b8c0c5390) (ausschließlich Workflowänderung gegenüber 5c94e1b)  
**Vergleich:** vorheriges Hardware-Review [0.3](2026-10-08-hardware-architektur-review.md); ältere Architekturannahmen werden nicht als bereits gemessene Resultate dargestellt.  
**Methode:** GitHub-Diff und Schaltungs-Konzeptreview; unabhängige numerische Gegenrechnung ausgewählter Annahmen mit Python; Abgleich der offiziellen Herstellerangaben; Prüfung aktueller GitHub-Actions-Logs. **Kein KiCad-Schaltplan, keine Netzliste, kein Layout, kein Hardwaremuster.** Keine ERC/DRC-, thermische oder elektrische Messung möglich. Die drei Repository-Rechenskripte wurden als Quelltext geprüft; die Gegenrechnungen waren unabhängig und sind unten reproduzierbar dokumentiert.

## Ergebnis / Freigabe

**Lastenheft 0.4 als Arbeitsgrundlage verwendbar; KEINE Schaltplan-/PCB-Fertigungsfreigabe.** Besonders die Ladeübertemperaturgrenze ist sicherheitskritisch. Die vorgesehene Architektur unterscheidet sich von der vorhandenen BlackPill/RFM95-Firmware (MCCI): **Neue Platine mit Ra-01SH/SX1262 und eigener RadioLib-Firmware ist noch nicht implementiert und wurde nicht durch den grünen BlackPill-Build validiert.**

Positive Fortschritte gegenüber 0.3: Zwei voneinander unabhängige Schutzansätze am Akku geplant, Schutzschaltung räumlich nahe an der Zelle; NTC an Zelle statt Hauptplatine; rückspeisungsbewusste geschaltete Sensorschiene (TPS22917, Pull-ups nur geschaltet), ESD-Konzept an Außenanschlüssen; zusammenhängende 4-Lagen-Massefläche; konkrete separate Audio- und HX711-Ketten; Quarz-, Debug-, Antennen- und Montageanforderungen konkretisiert. **Alle Aussagen sind Entwurfsstand, nicht nachgemessene Funktion.**

## 1. Sperrende und offene Befunde

### HW26-07 — P0 vor Layout-/Fertigungsfreigabe: Ladesperre zu heiß

**Fundstelle:** [hardware/versorgung.md `3.3](../../hardware/versorgung.md) und [LASTENHEFT.md V3](../../hardware/LASTENHEFT.md). Vorgesehen: BQ25185, 10 kΩ bei 25 °C / β=3435 NTC, TS-Bias typ. 38 µA, HOT-Schwelle typ. 0,115 V. Daraus: **59,5 °C Abschaltpunkt** und etwa 54,4 °C Wiederfreigabe. Auch die **Kaltabschaltung nominal +1,7 °C** hat mit Schwellwert-/Strom-/NTC-Toleranz nur geringe Reserve bis 0 °C.

**Quellenkonflikt:** Das Projekt nennt für die geplante Zelle maximal **45 °C Ladetemperatur** (Händlerangabe), der aktuelle [offizielle Hersteller-Datensatz für N18650CP-34E](https://www.bakpower.com/uploads/cpxl_table1_en/N18650CP-34E_en.pdf) nennt **0 bis 55 °C** an der Zelloberfläche. Beide Werte liegen unter den derzeit berechneten 59,5 °C. **Beschaffte Zellvariante und gültige Herstellerrevision klären; bis dahin konservativ auf ≤45 °C auslegen.**

Texas Instruments erklärt für den [BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf) die festen HOT/COLD-TS-Schwellen. Ein [TI-Application-Engineer](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1472003/bq25185-ntc-temperature-threshold) weist ausdrücklich darauf hin, dass das gewünschte 5–45-°C-Fenster beim BQ25185 und Standard-10-kΩ-NTC β3435 **nicht durch beliebige einfache Serien-/Parallelwiderstände zuverlässig erzwingbar** ist. Als Alternative wird BQ25186 mit konfigurierbaren Schwellen genannt; dessen I²C-/Versorgungs-/Standby-Konsequenzen sind im eigenen System gesondert zu prüfen. Weitere Alternative: ein unabhängiger, hardwareseitiger Temperatur-Abschalter, der die **Ladung** sperrt (nicht nur die MCU-Warnung).

**Abnahme:** Verbindliche Zellspezifikation + min/max-Temperaturschaltwerte einschließlich Toleranzen; Ladung unterhalb 0 °C und oberhalb des erlaubten Zellmaximums **zuverlässig gesperrt**; Kalt-/Heiß-Fehler, NTC-Kurzschluss/-Unterbrechung sowie Wiedereinschalten geprüft. **Firmware-Abschaltung allein nicht ausreichend.**

### HW26-08 — P1: Solar-ADC-Teiler nicht bis Lade-IC-Eingangsgrenze geschützt

**Fundstelle:** [versorgung.md `3.1](../../hardware/versorgung.md), Solar-ADC an PB1 mit **3,3 MΩ oben / 1,0 MΩ unten**. Formel: V_ADC=V_PV×1/4,3. Bei **12 V → 2,79 V** (wie geplant), bei **18 V → 4,19 V** (oberhalb der 3,3-V-Versorgung), bei 25 V → 5,81 V. Der BQ25185 kann laut [TI](https://www.ti.com/product/BQ25185) mit **3–18 V** arbeiten, 25 V sind seine absolute Eingangsgrenze; daraus folgt **nicht**, dass PB1 ohne Begrenzung so hoch belastet werden darf.

Zudem ist der reale Abgriff **vor oder nach den je Panel vorgeschalteten Schottky-Dioden** zwischen Blockbild und Tabelle widersprüchlich; bei nur einem Teiler an einem der beiden Panelzweige wird nicht automatisch die Spannung beider Panels korrekt erfasst.

**Abnahme:** Kleineren Teilerfaktor oder Schutz/Clamp mit Einhaltung zulässiger STM32-ADC-Eingangs- und Einspritzströme bei allen vorgesehenen Betriebs-/Fehlerfällen festlegen; definieren, was bei USB-VBUS + Panel gemessen wird; Schaltplan mit eindeutiger Verknüpfung zeichnen. Prüfung bei 0, 12, 18 V und Fehler-/Surge-Betrachtung.

### HW26-09 — P1: Externer I²C-Bus überschreitet im oberen Szenario 400 pF

**Fundstellen:** [anschluesse.md `3.1](../../hardware/anschluesse.md), [i2c_leitung.py](../../hardware/i2c_leitung.py), [BME280-Datenblatt](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf).

Rechnungsannahme bei 1 m Kabel: 250–400 pF/m + 40 pF Platine/ESD/Geräte → **290–440 pF**, nominaler Pull-up **1,8 kΩ**, daraus **442–671 ns Anstiegszeit**. Der 1000-ns-Standard-Mode-Grenzwert ist eingehalten, der **400-pF-Kapazitätswert im oberen Fall nicht**. 50 kHz verbessert die Periodenreserve, ändert die spezifizierte Buslast aber nicht. Auf dem exponierten Bus hängt zugleich das AT24C256-Sitzungs-EEPROM.

**Abnahme:** Tatsächliches Kabel samt Modul-Pull-ups/ESD/Klemmen identifizieren und Gesamtkapazität auf **≤400 pF mit Reserve** auslegen. Ggf. kürzeres/kapazitätsärmeres Kabel oder Buspuffer; Rise-/Fall-Flanken am BME280-Ende, ACK und Wiederholungen bei Kälte/Nässe prüfen.

### HW26-10 — P1: Persistenz der LoRaWAN-Sitzung bei Stromabfall noch nicht spezifiziert

**Fundstellen:** [mcu-funk.md `3.1](../../hardware/mcu-funk.md), [versorgung.md `3.7](../../hardware/versorgung.md). AT24C256 hängt **an 3V3_SW**, Sitzung 302+14 Byte wird nach jedem Senden gespeichert. Eine Änderung des Lastschalters oder ein Brownout kann eine seitenweise EEPROM-Aktualisierung unterbrechen. Das ist **ein Designrisiko**, kein beobachteter Firmwarefehler.

**Abnahme:** Plan für atomaren/journalisierten Sitzungsstand samt Generation, CRC/Prüfwort und wiederholbarer Wiederherstellung; EEPROM-Page-Write-Zeit und garantierte ausreichende Energie vor 3V3_SW-Abschaltung prüfen, Startup-Reihenfolge MCU/I²C. Gezielter Power-Cut in jedem Schreibschritt am HiL, kein FCnt-/Session-Verlust.

### HW26-11 — P1: Ungeprüfte Thermik des linearen Solar-Ladereglers

**Fundstelle:** [versorgung.md `3.2](../../hardware/versorgung.md), BQ25185 WSON 2,2×2 mm, Soll 300 mA, mögliches Panel-Voc bis 10–12 V, SYS/BAT um 4–4,5 V. Oberes Rechenbeispiel bei 10 V und 300 mA: **(10−4,1)×0,3 ≈ 1,77 W**, ohne Leistungsanteile für SYS-Last. Dies ist **kein realer Betriebspunkt** — die unbekannten Solarpanels begrenzen den Strom und der IC regelt thermisch ab; die Kombination ist dennoch vor Festlegung der Kühlflächen durch thermische Rechnung/Simulation zu begrenzen.

**Abnahme:** Tatsächliches I-V-Verhalten der Panels, thermischer Worst Case unter Sonne, RθJA je PCB-Aufbau und Strombegrenzung/Power-Path prüfen; Ladestrom mit intakter NTC-Heißsperre verifizieren.

### HW26-12 — P2: SPI-Flash-Kapazität für FFT-Rohdaten missverständlich

**Fundstelle:** [mcu-funk.md `3.2](../../hardware/mcu-funk.md), 64 Mbit/8 MiB als Puffer für **alle Messwerte und Rohdaten der FFT**; zugleich Beispiel „3,5 Jahre“ bei 64-Byte-Datensatz alle 15 min. Die letzte Aussage stimmt nur, wenn hauptsächlich **Metriken** gespeichert werden.

Bei 9.342 ADC-Samples × 2 Byte alle 15 min: **18.684 Byte/FFT**, 96 Zyklen/Tag → **1.793.664 Byte/Tag**, 8 MiB sind nach **ca. 4,7 Tagen** gefüllt, vor Metadaten und NOR-Erase-Overhead. Bei 64 Byte/15 min sind es dagegen ca. 3,7 Jahre.

**Abnahme:** Speicherformat, zyklische Rohdaten-Snapshots (z. B. nur bei Anomalien), Ringpuffer, Wear-Level, Stromunterbrechungsfestigkeit und USB-/LoRa-Export ausdrücklich festlegen. **Nicht** die 3,5 Jahre pauschal für vollständige FFT-Rohdaten zusagen.

### HW26-13 — P2 vor Footprint: Debug-/Erweiterungsleisten passen nicht zur Pinzahl

**Fundstelle:** [anschluesse.md Tabelle 1](../../hardware/anschluesse.md). **J10 1×6** nennt VCC, SWDIO, SWCLK, NRST, GND, TX, RX = **7 Signale**. **J11 2×5** nennt zwei Versorgungspins, zwei GND, SDA, SCL, TX, RX, PA15, PB12, PB13 = **11 Signale**. Beide Stellen sind zwar als [P] markiert, aber noch widersprüchlich.

**Abnahme:** J10 mindestens 1×7 oder Serial getrennt; J11 2×6 oder eine definierte Leitung streichen, Pin1/2, Verpolung und JLCPCB-Teilenummer in einem verbindlichen Anschlussplan festhalten.

### HW26-14 — P2: Modulrevision SX1262/LLCC68 / HF-Umschalter

**Fundstelle:** [mcu-funk.md `2](../../hardware/mcu-funk.md). Das Ra-01SH-Modul ist im Entwurf teils als SX1262, teils als potenziell LLCC68 beschrieben. **SF11/SF12** sind daher nicht pauschal als verfügbar anzunehmen; die Energiebilanz verwendet SF12 nur als ungünstige Vergleichsannahme, die beim tatsächlich gelieferten Modul möglicherweise keine nutzbare Betriebsart ist. Die **DIO2→HF-Schalter**-Schaltung und die Reserve TXEN/RXEN über Lötbrücken sind sinnvoll, aber nicht per Modulschaltbild bestätigt.

**Abnahme:** Modul-/Chipaufdruck und Pin-/IPEX-Schaltung am gelieferten Sample prüfen; RadioLib-Initialisierung für genaue Variante, DIO2-RF-Switch und QUARZ (kein TCXO) nachweisen. HF-Ausgang und RX mit 868-MHz-Gateway prüfen, keine Freigabe allein durch kurzen Antennenabstand.

### HW26-15 — P2: Mechanik, USB und PCBA-Konfiguration noch unbestimmt

**Quellen:** [LASTENHEFT.md M2/M3/M7/M8](../../hardware/LASTENHEFT.md), [mechanik/README.md](../../mechanik/README.md). PCB-Grundfläche 121×121 mm und Befestigungsraster 110,2 mm sind definiert; Domhöhe, Bauteilfreiheit unter PCB, Trägerplatte des 18650, Lichtleiter-Bohrung und die Realisierbarkeit vollständiger THT-Bestückung bei JLCPCB sind noch nicht durch STEP/Bestellvorschau gesichert. USB-DFU mit geplantem 25-MHz-HSE noch nicht auf eigener Platine belegt; SWD-Fallback ist vorhanden.

**Abnahme:** STEP-/3D-Assembly inklusive Halter, Akku, FPC-Antenne, Lichtleiter, USB/Klemmen und THT-Lötstellen; echte BOM/LCSC/Assembly-Angebotsprüfung; SWD-Testkabel vorsehen.

## 2. Numerische Gegenrechnung (isoliertes SiL des Hardware-Konzepts)

Die folgenden Werte wurden **unabhängig aus den Dokument-Konstanten nachgerechnet**. Es handelt sich **nicht** um einen GitHub-Actions-Lauf der drei neuen Python-Skripte und nicht um eine Messung am Sensor:

| Rechenfall | Ergebnis | Bewertung |
|---|---|---|
| TS: 38 µA × NTC10k β3435 | HOT 0,115V → **59,5°C**; COLD 1,0075V → **+1,7°C** | Rechenweg plausibel, Sicherheit unzureichend |
| PV-ADC 3,3MΩ/1MΩ | 12V → 2,79V, 18V → **4,19V** | Schutz-/Auslegungslücke |
| 1m I²C, 1,8kΩ | 290–440pF, 442–671ns | Anstiegszeit ok; max. C überschritten |
| Mikrofonfilter bei 60 / 250 / 900 Hz | −0,80 / −0,30 / −1,35 dB | Nominalmodell konsistent mit Dokument |
| Mikrofonfilter bei 7.168 Hz | ca. −36,7 dB | Digitale FFT allein beseitigt ADC-Aliasing nicht; analoger Filter erforderlich |
| MCU/Sensor-Aktivzeit und Funk, Szenario A | ca. **206,9 mAs je Zyklus**, ~5,9 mAh/Tag einschließlich 15,7µA Standby | Algebra plausibel, viele Dauer-/Stromwerte angenommene Größen |
| Szenario B | ca. **91,3 mAs je Zyklus**, ~2,8 mAh/Tag einschl. Standby | Nur Ziel-Firmware-Modell, nicht gebaut und nicht gemessen |
| Winter-PV-Ertrag | ~**1,65 Wh/Tag** unter angenommenen Wetter-/Panel-/Wirkungsgradwerten | Keine Zusicherung „40× Reserve“ für konkrete Montage; Panelspezifikation unbekannt |

Für Änderungen sollen die Originalskripte in die CI aufgenommen und mittels nachvollziehbarer Assertions geschützt werden:

```sh
python3 hardware/energiebilanz.py
python3 hardware/mikrofon_filter.py
python3 hardware/i2c_leitung.py
```

Das sind zunächst **Berechnungsmodelle**. Netzliste, Bauteiltoleranzen, thermische Kopplung, ADC-Rauschleistung und EMV benötigen erst KiCad/Simulation/HiL.

## 3. CI-/Server-Regression auf aktuellem main (nicht durch Hardware-Docs verursacht)

### CI26-01 — P1: Server-/Winterzeit-End-to-End-Test weiterhin rot

- [CI zu Hardware-Commit 5c94e1b, Run 37856443046](https://github.com/impyer/bienen-lora-logger/actions/runs/37856443046): 4 von 5 Jobs erfolgreich; Serverjob fehlgeschlagen. In der eigenen UTC-Variante **69/70 Prüfungen**, der DST-Test zählt **6/7 HTTP-Antworten „gespeichert“**, obwohl die letzten **sieben UTC-Zeitstempel korrekt in week.csv** stehen.
- [CI zum Workflow-Fix 6b83d, Run 37856752618](https://github.com/impyer/bienen-lora-logger/actions/runs/37856752618): wieder 4 von 5 Jobs erfolgreich; eigener Servertest **72/73**. Alle **sieben CSV-Zeitstempel** sind vorhanden und der jetzt verpflichtende **Chromium/Playwright-Test bestätigt 7 Punkte, streng steigende Achse und keine JS-Fehler**. Aber erneut nur **6/7** Antworten als „gespeichert“ klassifiziert. Der originale Servertest wurde wegen vorherigem Fehler übersprungen.
- [Vorgänger-Commit 3f2f9d6, CI Run 37808002801](https://github.com/impyer/bienen-lora-logger/actions/runs/37808002801) war an gleicher Stelle **70/70 grün**, mit 7/7 Antworten. Der Hardware-Commit verändert **keinen** ausführbaren Servercode, nur Hardwaretexte; der zweite Commit verändert nur den Workflow. Die Ursache kann ein Test-/Zustands-/Race-Effekt sein; **nicht als nachgewiesene Ursache behaupten**.
- **Fundstelle:** `tests/server/test_lora_eingang.sh` Zeilen 246–259 zählt nur Antworten, die mit `gespeichert` beginnen, verwirft aber bei Fehler die konkrete Antwort; `server/lora/lora_verarbeitung.php` Zeilen 153–163 bestimmt den Speichervorgang nach Größenänderung von `week.csv` und Zeitstempel der letzten Zeile.

**Akzeptanz:** Test loggt für jeden der sieben Events den exakten Unixzeitstempel, HTTP-Code, Ergebnisklasse, Event-ID sowie CSV-Zeilenanzahl vorher/nachher. Korrigierten Fehler durch wiederholte CI-Läufe nachweisen. Wird bereits gespeichert, darf Retry nicht erneut schreiben; HTTP-Klasse und Datendatei müssen nachvollziehbar konsistent sein. **Keine stille Aufweichung der 7/7-Assertion**.

## 4. Übergabe an Claude / Reihenfolge

1. **HW26-07 P0:** Lade-/Schutzarchitektur für die **tatsächlich beschaffte Zelle** mit Herstellerdatenblatt, HOT/COLD-Toleranz und Schaltplan neu entscheiden. Vorher keine PCB-Fertigungsfreigabe.
2. **HW26-08/09/10/11 P1:** PV-ADC schützen; Kabelkapazität spezifikationsgerecht auslegen; EEPROM-Stromausfallkonzept; BQ25185-Temperatur/Verlustleistung berücksichtigen.
3. **HW26-12/13 P2:** Flash-Speicherpolitik präzisieren, Anschlussbelegung J10/J11 korrigieren.
4. **HW26-14/15 P2:** Radio-Modulstückmuster, STEP, PCB-Footprints, PCBA-Angebot und SWD/USB-Rettungsweg bestätigen.
5. **CI26-01 P1 separat:** Roten UTC-Test **diagnostizieren**, nicht durch Testabschaltung „grün“ machen. Das heißt nicht, dass das beobachtete DST-Datenpersistenz-Problem wieder aufgetreten ist; die sieben CSV-Zeitpunkte waren im CI vorhanden.
6. **Dann** KiCad-Schaltplan mit ERC, Strom-/Schienen- und Ladesperrensimulation, Signalintegrität/Rückspeisungsanalyse, realem 3D-Bauraum und BOM/CPL; anschließend PCB-DRC und Labor-HiL.

## 5. Checkliste vor Schaltplan- und Fertigungsfreigabe

| Prüfpunkt | Status |
|---|---|
| Architekturglieder und Zielpins dokumentiert | **ja, textuell** |
| Numerische Grundmodelle im Quellstand vorhanden | **ja, unabhängig plausibilisiert** |
| Akku-NTC-Ladegrenze vollständig sicher | **nein, P0** |
| Solar-ADC über erwartbare Eingänge geschützt | **nein, P1** |
| I²C-Bus innerhalb 400pF Worst-Case | **nein, P1** |
| KiCad-Schaltplan/Netzliste erstellt, ERC | **nicht vorhanden** |
| PCB-Gerber, Bohrplan, BOM, CPL/DRC | **nicht vorhanden** |
| JLCPCB-Komplettbestückung real bestätigt | **nein** |
| Akkuzellen-/Funk-/Mikrofon-/Waagenmuster gemessen | **nein** |
| Volle CI-Hauptpipeline | **nein, 4/5 Jobs, CI26-01** |

**Schlussfolgerung:** Die Hardwaredefinition ist eine solide Grundlage für den nächsten Entwurfsschritt, doch der Akku-Temperaturschutz ist sicherheitskritisch, und mehrere P1-Spezifikationsrisiken sind vor dem Schema zu korrigieren. Freigabe nur für **weitere Konstruktion und Prüfstandsplanung** — nicht für Fertigung oder unbeaufsichtigten Feldeinsatz.
