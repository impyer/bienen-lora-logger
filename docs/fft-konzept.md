# FFT-Messung: Konzept für Platine und Firmware (Entwurf 0.1, 08.10.2026)

## 1. Was der beelogger heute macht (Quelltext, Paket 202610)

- Abtastung an PA1 mit 1212 Hz, 256 Werte, Hamming-Fenster. Die Taktung ist eine Warteschleife mit `micros()`.
- Ergebnis je Messzyklus: Frequenz und Betrag der **einen** stärksten Spitze (`MajorPeak`), Betrag / 10.
- 3 Messungen. Übernommen wird eine Spitze, die zweimal innerhalb von 50 Hz übereinstimmt. Spitzen unter 55,5 Hz werden nach Möglichkeit verworfen.

### Schwächen

| Nr. | Schwäche | Folge |
|---|---|---|
| W1 | **Unrunde Teilung:** 1212 Hz / 256 = 4,734 Hz je Linie. | Frequenzen lassen sich schlecht vergleichen und nur ungenau Bändern zuordnen. |
| W2 | **Kein Anti-Aliasing.** Das GY-MAX4466-Modul reicht nach meinem Wissen bis in den kHz-Bereich. Vor dem ADC sitzt kein Tiefpass. | Töne zwischen 606 und 1212 Hz werden gespiegelt: 700 Hz erscheint als 512 Hz. Gerade im Bereich der Königinnentöne (ca. 400–500 Hz) kann das Fehlmeldungen erzeugen. |
| W3 | Pegel ist ein Rohbetrag / 10. | Er hängt von Fensterlänge, Fenster und Poti ab. Ändert man N (128 → 256), ändert sich der Wert, ohne dass es lauter wurde. |
| W4 | Nur **eine** Spitze, keine Mittelung. | Die 3-aus-3-Abstimmung ist ein Notbehelf. Ein gemitteltes Spektrum ist stabiler und sagt mehr aus. |
| W5 | Grenze 55,5 Hz nur als Nachprüfung im Ergebnis. | Liegt die stärkste Spitze unter 55,5 Hz, misst der Logger bis zu zweimal neu. Das kostet Zeit und Strom, statt die Linien unter 60 Hz einfach auszublenden. |

## 2. Zur Frage „55,5-Hz-Grenze als Filter auf der Platine“

Ein Analogfilter kann 50 Hz nicht scharf von 55 Hz trennen. Ein Hochpass 1. Ordnung bei 55 Hz dämpft:

| Frequenz | Dämpfung |
|---|---|
| 50 Hz | ca. 3,5 dB |
| 100 Hz | ca. 1,2 dB |

Das ist keine Trennung. Ein steiles Filter höherer Ordnung bräuchte einen Operationsverstärker und verschiebt die Phase bis weit ins Summen hinein.

**Mein Vorschlag:**

- **Auf der Platine:** nur ein flacher Hochpass um 20–30 Hz. Er hält Gleichanteil, Wind- und Klopfgeräusche aus dem ADC, damit nichts übersteuert. Diese Aufgabe übernimmt zum Teil schon der Koppelkondensator des Moduls; **[P]** am Modul nachmessen.
- **In der Firmware:** die exakte Grenze. Linien unter 60 Hz werden in der FFT einfach nicht ausgewertet. Das wirkt scharf und kostet nichts.
- **Wichtiger als der Hochpass ist der Tiefpass gegen Aliasing (W2).** Dafür muss die Platine sorgen.

## 3. Vorschlag

### 3.1 Abtastung und Teilung

| Größe | Wert | Begründung |
|---|---|---|
| ADC-Takt | **8192 Hz**, Timer-getriggert mit DMA | genauer Takt ohne Warteschleife; 4-fache Überabtastung |
| Digitale Dezimierung | FIR-Tiefpass, Faktor 4 → **2048 Hz** | Die Digitalstufe übernimmt die steile Flanke; analog reicht ein einfaches Filter. |
| FFT-Länge | **N = 512** | **Teilung genau 4,0 Hz**, auswertbar bis 1024 Hz, 0,25 s je Block |
| Mittelung | 8 Blöcke mit 50 % Überlappung, Leistung gemittelt (Welch) | ca. 1,1 s Messdauer; stabiles Spektrum statt Abstimmung |
| Rechnung | CMSIS-DSP `arm_rfft_fast_f32` auf der FPU des STM32F411 | Ich schätze deutlich unter 1 ms je Block (Schätzung, nicht gemessen). |
| RAM | grob 10 KB | Der F411 hat 128 KB. |

Varianten: Mit N = 1024 bei 2048 Hz wird die Teilung 2,0 Hz, die Messung dauert dann 0,5 s je Block. Alles ist über `#define` einstellbar.

### 3.2 Analogteil auf der Platine (ergänzt Lastenheft A1–A6)

- **Tiefpass 2. Ordnung**, passiv (zwei RC-Glieder mit Trennung) oder aktiv mit einem stromsparenden OPV, Grenzfrequenz ca. **1 kHz**.
  - Der erste Bereich, der in das Nutzband zurückfällt, liegt bei 8192 − 1024 = 7168 Hz.
  - Dort dämpft ein Filter 2. Ordnung grob um 30–35 dB (Abschätzung).
  - Den Rest bis 4096 Hz übernimmt der digitale FIR.
- Hochpass ca. 20–30 Hz (siehe Abschnitt 2).
- Arbeitspunkt: Das Modul liefert VCC/2. Der ADC-Eingang bleibt so im Bereich 0–3,3 V.
- **[P]** Genaue Werte erst nach Messung am Modul festlegen: Ausgangsimpedanz, Rauschen, Frequenzgang.

### 3.3 Ergebniswerte je Messzyklus

| Wert | Format | Bemerkung |
|---|---|---|
| Spitzenfrequenz | uint16, 0,1 Hz | parabolische Interpolation zwischen den Linien, genauer als 4 Hz |
| Spitzenpegel | int8, 0,5 dB | in **dBFS**, bezogen auf den ADC-Vollausschlag und auf das Fenster normiert, also unabhängig von N (behebt W3) |
| Gesamtpegel 60–1000 Hz | int8, 0,5 dBFS | Aktivitätsmaß |
| **Bandpegel** in 6 Bändern | 6 × uint8, 0,5 dB | Vorschlag: 60–140, 140–260, 260–360, 360–440, 440–560, 560–1000 Hz |

Die Bandgrenzen orientieren sich an den Angaben in der Auswertungsbasis: Summen 150–250 Hz, Königin um 316 Hz,
Tüten um 475–500 Hz. Diese Angaben sind Erfahrungswerte bzw. stammen aus Studien mit kleinen Datensätzen.
Deshalb sind die Grenzen vorläufig und als Tabelle in der Firmware leicht zu ändern.

Funk: zusammen etwa 10 Byte.

## 4. Übertragung per LoRa

- Neues Funkformat (siehe `docs/datenformat.md`): Die FFT-Werte bekommen eigene Bits im 32-Bit-Feld.
- Der beelogger-Server legt bei LoRa heute keine FFT-Werte ab:
  - Aux2 ist mit dem RSSI belegt.
  - Aux3 ist mit der Sketch-ID belegt.
  - Details in `docs/server-analyse.md`, B3 und B4.
- Der eigene LoRa-Eingang (Vorschlag dort, Abschnitt 3) speichert sie in eigenen Spalten.
- Die Musterlogger (beelogger-Platine, `STM32_LORA_261008_ZS`) können dieselbe FFT bekommen, mit Abtastung an PA1.
  - Die Überabtastung mit DMA geht auch dort.
  - Es fehlt dort aber der analoge Tiefpass. Bis zur eigenen Platine hilft ein RC-Glied an der Mikrofonklemme.
  - **[P]** Auf der beelogger-Platine nachsehen, ob dafür Platz ist.

## 5. Prüfung

- PC-Test der Rechnung mit Testsignalen (Sinus, Gemisch, Rauschen, 700-Hz-Störer für das Aliasing). Er läuft in der CI wie die Zeitlogik-Tests.
- Am Tisch: Tongenerator oder Handy-App an das Mikrofon. Frequenz, Pegel und die Unterdrückung über 1024 Hz nachmessen.
