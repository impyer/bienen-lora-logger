# Verbesserungsliste: Firmware, Formatter, Server (Stand 08.10.2026)

Ziel: Die Notbehelfe im beelogger-Code sauber lösen, und zwar für die Musterlogger (`STM32_LORA_261008_ZS`), die neue Firmware und den Server.
Grundlage: Quelltext beelogger STM32 202610 und Server M.40. Details in `docs/datenformat.md`, `docs/server-analyse.md` und `docs/fft-konzept.md`.

Priorität: **1** = verfälscht oder verliert Daten, **2** = schränkt ein, **3** = Aufräumen.

## Firmware (beelogger-LoRa-Sketch und ZS-Fassung)

| Nr. | Prio | Notbehelf heute | Saubere Lösung |
|---|---|---|---|
| F1 | 1 | Der 2. DS18B20 wird bei Single über den Feuchte-Platz `FeuchteIn` gesendet: 1 Byte, ohne Nachkommastelle, Minuswerte laufen über (−5 °C → 251). | Eigener Wert mit Vorzeichen in 1/100 °C im neuen Funkformat |
| F2 | 1 | **Fällt der Außensensor aus, meldet der Logger stillschweigend die CPU-Temperatur des STM32 als Außentemperatur** (`Sensor_Temp_Zelle`, „force“). Der Server nutzt sie dann auch für die Gewichtskorrektur. | Ausfall als Fehlwert senden und als Zustandsbit melden. Die CPU-Temperatur kommt, falls gewünscht, in ein eigenes Feld. |
| F3 | 1 | Keine FFT im LoRa-Sketch; der Schalter `beelogger_Audio` wirkt dort nicht. | FFT nach `docs/fft-konzept.md`, eigene Felder im Funkformat |
| F4 | 2 | `Aux[0..2]` werden mehrfach genutzt: Luftdruck, VDD und CPU-Temperatur als Zwischenwert, FFT, Regen, 5./6. DS18B20. | Jeder Messwert bekommt eine eigene Variable und ein eigenes Feld; kein gemeinsames `Aux`-Feld mehr |
| F5 | 2 | 16-Bit-Kopf voll. Die Sketch-ID belegt `Aux3`. | Neues Format: Version + 32-Bit-Kopf, FPort 2. Die Sketch-ID als eigenes Feld, nur nach dem Start und einmal täglich |
| F6 | 2 | Kein Messzeitpunkt im Paket; der Server setzt die Empfangszeit. | Messzeitpunkt als Abstand zur Sendezeit oder als Minutenzähler senden. Die Uhr ist durch den Zeitabgleich genau. |
| F7 | 2 | Kein Zustand im Paket (Zeitabgleich, Neustart-Grund, Sensorfehler) | Zustandsbyte bzw. Fehlerbits |
| F8 | 3 | Kommentar „3 bytes“ beim Gewicht, tatsächlich 2 Byte (int16 / 100 → höchstens 327,67 kg) | Kommentar richtigstellen. Für eine Beute reicht der Bereich. |
| F9 | 3 | Frame-Counter springt bei 16384 auf 0 (ABP, „Resets frame counters“) | bleibt vorerst; bei der neuen Firmware den Zähler im EEPROM durchlaufen lassen |

## Formatter (TTN)

| Nr. | Prio | Heute | Neu |
|---|---|---|---|
| T1 | erledigt | Altes `Decoder(bytes, port)`, ein Format | `decodeUplink` mit Unterscheidung nach FPort: Port 1 = beelogger alt, Port 2 = neues Format; Fehlermeldungen über `errors`/`warnings` |
| T2 | erledigt | Keine Tests | Testfälle (Bytes → JSON) in `tests/`, laufen in der CI mit Node.js |

## Server

| Nr. | Prio | Befund (siehe `docs/server-analyse.md`) | Lösung |
|---|---|---|---|
| S1 | 1 | **B2: Winterzeit-Umstellung am 25.10.2026** – eine Stunde wird 60 min zu spät gespeichert, die nächste verworfen | Eigener LoRa-Eingang oder Patch: UTC-Zeit aus `received_at` bzw. Messzeitpunkt |
| S2 | 1 | B1: Zeitstempel = Empfangszeit, gekürzt auf die Minute | wie S1 |
| S3 | 2 | B3/B4: Aux2 = RSSI, Aux3 = Sketch-ID | eigene Felder für RSSI, SNR, Sketch-ID, FFT |
| S4 | 2 | B5: Single nimmt kein `TempIn2` an | eigene Spalte bzw. Zusatzdatei |
| S5 | 2 | B9: Triple lehnt Pakete ohne `Gewicht3` ab | Typ aus dem Verzeichnis nehmen, nicht aus dem Paket |
| S6 | 3 | B7, B8, B10: `error_reporting(0)`, Tippfehler, Passwort in der URL | Protokollierung, Fehler beheben, Passwort als Header |

## Reihenfolge (Vorschlag)

1. **Vor dem 25.10.2026:** Prüfen, ob die Musterlogger bis dahin Daten liefern. Wenn ja, S1 vorziehen, mindestens als kleiner Patch.
2. Formatter neu (T1, T2) und Funkformat v2 festlegen. Grundlage für alles Weitere.
3. ZS-Firmware: F1–F7 mit Funkformat v2, FFT (F3) zuerst am Tisch.
4. Eigener LoRa-Eingang am Server (S2–S5).
5. Neue Firmware für die eigene Platine mit derselben Logik.
