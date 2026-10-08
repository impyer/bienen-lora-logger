# Prüfliste Hardware-Entwurf — Musterlogger und neue SMD-Platine

- **Datum:** 2026-10-08
- **Referenz:** `hardware/LASTENHEFT.md`, Entwurf 0.3 unter [d735f0f](https://github.com/impyer/bienen-lora-logger/commit/d735f0f99c7359bcabf2ad05a4c4314809afca04); `docs/fft-konzept.md`.
- **Art:** Kritische Architekturprüfung, **keine Schaltplan-/Layoutfreigabe**. Zum Reviewzeitpunkt kein KiCad-Schaltplan im Repository.
- **Geltungsbereich:** Die geplante eigene STM32F411/SX1262-SMD-Platine ist **nicht** identisch mit der geprüften RFM95-Musterlogger-Firmware.

## Priorisierte Prüfpunkte vor PCB-Freigabe

### HW26-01 — P0 — Ungeschützter 18650-Akku

Der Entwurf sieht eine Zelle ohne integrierte Schutzschaltung und die Wahl „Tiefentladeschutz durch Hardware oder Firmware“ vor. **Reiner Firmware-Unterspannungsschutz ist als alleinige Schutzmaßnahme unzureichend**, weil das System selbst bei nicht ausführender Firmware Ruheströme haben kann. Unterspannungsschutz elektrisch auslegen und gegen Fehler-/Reset-/Schlafzustände prüfen. Auch Ladung bei zu niedriger Zelltemperatur konstruktiv verhindern; Zell- und Lader-Datenblätter nachprüfen.

**Freigabekriterium:** Hardware-seitige Schutzfunktion für die tatsächlich verwendete Zelle, klare Auslöseschwellen, Stromaufnahme im Abschaltzustand und sicheres Wiederanlaufen nachgewiesen.

### HW26-02 — P1 — Solar-Eingang und 3,3-V-Regler

Sechs-Volt-Panelbezeichnung ist kein Grenzwert der Leerlaufspannung. Mindest-/Höchstspannung, Kälteeffekt, zwei parallel geschaltete Panels, CN3065-Absolute-Maximum, Rückstrom und Strombegrenzung gegen reale Paneldaten verifizieren. Regler anhand Dropout, Spitzenstrom, Lastsprüngen und Iq statt nur Nennstrom auswählen.

**Freigabekriterium:** Dokumentierte Worst-Case-Strom-/Spannungsbetrachtung und ESD-/Verpolschutz-Schaltung.

### HW26-03 — P1 — Reale Energiebilanz

Das Ziel „Ruhestrom <20 µA“ ist **nicht** der Durchschnittsverbrauch. Sensor-Anlauf, HX711, 1,14-s-Audioaufnahme, FFT-Rechenzeit, RFM95/SX1262-Sendezeit und RX-Fenster getrennt erfassen. Unter schlechter Winter-Solarernte dimensionieren.

**Freigabekriterium:** Reproduzierbares Strom-/Energieprofil pro Betriebszustand und Rechnung für mehrere Wintertage ohne Ertrag.

### HW26-04 — P1 — Rückspeisung der geschalteten Sensorversorgung

High-Side-Schalter für Sensoren wird geplant, I²C-/OneWire-/HX711-/ADC-Leitungen können jedoch unversorgte Module über Eingangsschutzstrukturen rückspeisen.

**Freigabekriterium:** Schaltplanprüfung sämtlicher Pull-ups/IO-Pegel und Messung von abgeschalteten Sensorströmen. Nicht pauschal „Analogmasse sternförmig“ fordern, sondern Massefläche und Rückströme im Layout nachvollziehen.

### HW26-05 — P1 — Akustik-Antialiasing und Kalibrierung

Eine digitale Dezimier-FIR kann bereits oberhalb der Rohabtast-Nyquistgrenze aliasierte Töne nicht entfernen. Vor dem ADC Bandbegrenzung am realen Mikrofon/Filter messen. dBFS ist ein relativer ADC-Pegel, **kein** kalibrierter dB-SPL-Schalldruck.

**Freigabekriterium:** Filter-/Mikrofon-Frequenzgang, Verstärkung, Clipping, Rauschen sowie Vergleich zweier Logger unter identischem Anregungssignal.

### HW26-06 — P2 — Mechanik/RF

Antenne fern von Metall, HF-Masse-/Leitungsführung, SX1262-DIO2-Schalter, Winter-Frequenzdrift und Abmessungen/Bauhöhen anhand Datenblatt, Schaltplan, STEP und Muster prüfen. Herstellerangaben nicht durch nahen Gateway-Erfolg ersetzen.

## Übergabe an HiL

Messprotokolle mit **Boardrevision, Firmware-SHA, Gerät-ID (ohne Geheimnisse), Messgerät, Spannung, Temperatur und Rohdaten** ablegen. Bei jeder offenen Annahme entweder einen reproduzierbaren Messwert oder den Status „nicht geprüft“ vermerken.

**Review-Entscheid:** Lastenheft weiterentwickeln; keine Fertigungsfreigabe auf Basis der vorhandenen Textentwürfe.
