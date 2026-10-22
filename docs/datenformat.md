# Datenformat Funk → TTN → beelogger-Webserver (Entwurf 0.1, 08.10.2026)

Entscheidung (Philipp, 08.10.2026): Die neue Firmware schickt ihre Daten weiter an den **eigenen beelogger-Webserver**.

## Grundgedanke

Der Webserver bekommt die Werte nicht als Bytes, sondern als **JSON, das der Payload-Formatter in TTN erzeugt**.
Den Formatter legen wir in TTN selbst fest. Die Schnittstelle zum Server bilden deshalb die **Feldnamen und
Einheiten im JSON**, nicht das Funkformat.

Folge: Die neue Firmware darf ein eigenes, besseres Funkformat haben. Der Formatter muss es nur in die
beelogger-Feldnamen übersetzen. Der Server bleibt unverändert, solange er die Felder kennt.

## Heutige Schnittstelle (aus `payloadformatter_220227.js`, beelogger-Paket 202610)

Der beelogger-Sketch sendet auf **FPort 1**. Die letzten 2 Bytes sind ein Bitfeld, das sagt, welche Werte vorhanden sind. Belegt sind alle 16 Bits.

| Bit | JSON-Feld | Einheit | Funk |
|---|---|---|---|
| 0 | `TempOut` | °C | int16 / 100 |
| 1 | `FeuchteOut` | % | uint8 |
| 2 | `VBatt` | V | uint16 / 1000 |
| 3 | `VSolar` | V | uint16 / 1000 |
| 4 | `Licht` | lx | uint16 |
| 5 | `Gewicht` | kg | int16 / 100 (also höchstens 327,67 kg) |
| 6 | `TempIn` | °C | int16 / 100 |
| 7 | `FeuchteIn` | % | uint8 |
| 8 | `Gewicht2` | kg | int16 / 100 |
| 9 | `TempIn2` | °C | int16 / 100 |
| 10 | `FeuchteIn2` | % | uint8 |
| 11 | `Gewicht3` | kg | int16 / 100 |
| 12 | `Gewicht4` | kg | int16 / 100 |
| 13 | `Aux1` | hPa (Luftdruck) | int16 / 10 |
| 14 | `Service` | – | uint8 |
| 15 | `Aux3` | Sketch-ID | uint32 |

Der Formatter nutzt die alte Schnittstelle `Decoder(bytes, port)` aus TTN v2. The Things Stack ruft sie weiter auf
(Rückfall „for backwards compatibility“ in `pkg/messageprocessors/javascript/javascript.go`, geprüft am 08.10.2026).
Der neue Formatter verwendet `decodeUplink(input)`.

## Befunde im beelogger-Paket 202610 (Quelltext geprüft, 08.10.2026)

### Mikrofon: FFT-Spitze, kein Audiosignal

Der beelogger überträgt kein Audiosignal, sondern zwei Werte aus einer FFT, die je Messzyklus
auf dem STM32 berechnet werden (`fft_new_func.ino` in `STM32_WLAN_MULTI_260705` und `STM32_LTE_MULTI_260705`):

- `Aux[1]` = **Frequenz der stärksten Spitze** in Hz.
- `Aux[2]` = **Pegel dieser Spitze**: Betrag aus `MajorPeak` geteilt durch 10. Es ist ein relativer Wert, kein dB-Wert, und hängt von der Poti-Stellung ab.
- Abtastung: PA1 mit 1212 Hz, 256 Werte, Hamming-Fenster. Damit erfasst die FFT Frequenzen bis 606 Hz, in Schritten von etwa 4,7 Hz.
- Ablauf: 3 Messungen. Übernommen wird eine Spitze, die in zwei Messungen innerhalb von 50 Hz übereinstimmt. Spitzen unter 55,5 Hz werden nach Möglichkeit verworfen.
- Der Test-Sketch `beelogger_Audio.ino` arbeitet nur mit 128 Werten (Schritt ca. 9,5 Hz). Die Logger-Sketche nutzen 256 Werte.
- Der Kommentar in `Config_MULTI.h` nennt „Aux[0], Aux[2]“. Der Code schreibt aber `Aux[1]` und `Aux[2]`; `Aux[0]` ist der Luftdruck.
- `Aux[1]` und `Aux[2]` teilen sich FFT, Regensensor (`Aux[1]`) und den 5./6. DS18B20. Es geht immer nur eines davon.

**Im LoRa-Sketch `STM32_LORA_260705` fehlt die FFT ganz**: Es gibt dort kein `fft_new_func.ino` und keinen Aufruf von `bee_FFT()`.
Der Schalter `beelogger_Audio` in dessen `Config_MULTI.h` bewirkt nichts. Das Funkformat sendet nur `Aux[0]` (Luftdruck).
Das gilt auch für die Musterlogger mit `STM32_LORA_261008_ZS`.

Bei WLAN/LTE gehen `Aux[0..2]` als letzte drei Werte an den Server. Ich nehme an, dass das die Serverfelder `Aux1`, `Aux2` und `Aux3` sind.
Im LoRa-Formatter ist `Aux3` aber mit der Sketch-ID belegt (Bit 15). **[P]** Am Server prüfen, was `LORA=1` mit `Aux3` macht.
Sonst würde die Sketch-ID mit dem FFT-Pegel kollidieren.

### Zweiter DS18B20 bei einer Waage

Wie die Werte belegt werden, entscheidest du. Laut Code gilt Folgendes:

- **Beim Single-System (1 Waage) gibt es kein `TempIn2`.** `TYPE_TEMP_2` wird nur gesendet, wenn `Anzahl_Sensoren_Gewicht` 2 ist, und dann zusammen mit `Gewicht2`.
- Der beelogger löst den 2. DS18B20 bei Single so (`beelogger_DS18B20.ino`):
  - Seine Temperatur landet in `SensorTemp[9]`.
  - Ist Sensor 9 nirgends zugeordnet, steht sie zusätzlich in `SensorFeuchte[8]`.
  - Mit `Beute1 = 8` wird sie damit als **`FeuchteIn`** übertragen.
- **Bei LoRa verliert dieser Weg Genauigkeit:** `FeuchteIn` ist ein vorzeichenloses Byte.
  - 34,6 °C kommt als 34 an; die Nachkommastelle fehlt.
  - Werte unter 0 °C laufen über, zum Beispiel −5 °C → 251.
  - Bei WLAN/LTE gibt es das Problem nicht: Dort geht der Wert als Text mit einer Nachkommastelle.
- Als Duo-System eingestellt käme der 2. DS18B20 sauber als `TempIn2` an (int16, 1/100 °C). Dann sendet der Logger aber auch `Gewicht2`, und der Server muss als Duo angelegt sein.
- Für die neue Firmware heißt das: Die Deckeltemperatur bekommt im Funkformat einen eigenen Wert mit Vorzeichen in 1/100 °C. Unter welchem Feldnamen der Formatter sie an den Server gibt, legst du fest.

### Weiteres

- **Messzeitpunkt:** Den Zeitstempel setzt der Server beim Empfang. Ein Zeitfeld kann der Server nur nutzen, wenn er es kennt.
- **Zustand:** Felder für den Zeitabgleich, den Neustart-Grund und Fehlerzähler fehlen.

## Vorschlag für die neue Firmware

1. **Eigener FPort (2)** für das neue Format. Der Formatter unterscheidet an `fPort`: Port 1 ist das alte beelogger-Format (Musterlogger), Port 2 das neue. Beide Gerätearten können in derselben TTN-Applikation laufen.
2. **Funkformat v2:**
   - Byte 0 ist die Formatversion.
   - Danach folgt ein Bitfeld mit 32 Bit, damit Platz für Erweiterungen bleibt.
   - Danach kommen die Werte in fester Reihenfolge.
   - Neu dabei: FFT-Spitze (Frequenz und Pegel), Deckeltemperatur, Zustand des Zeitabgleichs, Neustart-Grund.
3. **Formatter-Ausgabe:**
   - Für alles, was der Server schon kennt, gelten genau die beelogger-Feldnamen und Einheiten der Tabelle oben.
   - Neue Werte bekommen zusätzliche Feldnamen. Der Server übernimmt sie erst, wenn er dafür erweitert ist (`server/`).
4. **Tests:** Die Testfälle des Formatters (Bytes → erwartetes JSON) liegen im Repo und laufen in der CI mit Node.js.

## Server (geprüft, siehe `docs/server-analyse.md`)

- Der Server M.40 liest bei LoRa: `TempOut`, `TempIn`, `FeuchteOut`, `FeuchteIn`, `Licht`, `VBatt`, `VSolar`, `BienenIn`, `BienenOut`, `Service`, `Aux1`, `Aux3`, `Gewicht`. Ab Duo kommen `TempIn2`, `FeuchteIn2`, `Gewicht2` usw. dazu.
- `Aux2` aus dem JSON wird **nicht** gelesen, sondern mit dem RSSI belegt. `Aux3` wird als Messwert **und** als Sketch-ID gespeichert.
- Ohne Serveränderung gibt es für FFT-Werte und die Deckeltemperatur (Single) keinen Platz.

## Offen

- Funkformat v2: festgelegt in `docs/funkformat-v2.md`, Formatter in `formatter/` (08.10.2026).
- Eigener Eingang am Server: umgesetzt 08.10.2026, seit 22.10.2026 Bienen-Eingang `server/bienen/`.
