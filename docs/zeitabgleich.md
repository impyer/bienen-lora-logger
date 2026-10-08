# Zeitabgleich per LoRaWAN und Weckraster (Firmware ZS 261008)

Testversion vom 08.10.2026, Review-Stand 2. Sie beruht auf beelogger `STM32_LORA_260705`.
Bisher geprüft: übersetzt für die BlackPill F411CE mit STM32-Core 2.6.0 und MCCI-LMIC 5.0.1 und 6.0.1, ohne Fehler und Warnungen. Dazu PC-Tests und Simulation.
**Noch nicht geprüft: der Betrieb auf echter Hardware mit TTN.**

## Was die Version macht

1. Einmal am Tag hängt der Logger eine Zeitabfrage (LoRaWAN `DeviceTimeReq`, 1 Byte) an das normale Datenpaket. TTN antwortet im Empfangsfenster desselben Weckvorgangs. Der Logger stellt seine Uhr dann auf UTC, auf die volle Sekunde.
2. Geweckt wird auf einem festen Raster: `k × Intervall + LOGGER_SLOT × SLOT_ABSTAND_S + 1 s`.
   - Beispiel bei 10 min Intervall: Logger 0 um 12:10:01, Logger 1 um 12:10:11 … Logger 9 um 12:11:31.
   - +1 s statt −1 s wie im Original: Kein Wachfenster läuft über Mitternacht (siehe Review-Änderungen).
   - Alle Logger messen damit innerhalb von etwa 1,5 min, senden aber nie gleichzeitig.
3. Das Nachtfenster (23–6 Uhr) und die Wintermonate rechnet der Logger aus UTC in Ortszeit um, mit automatischer Sommerzeit.
4. Kommt keine Antwort, läuft der Logger weiter wie bisher und fragt frühestens nach 60 min erneut.

## Änderungen gegenüber STM32_LORA_260705

| Datei | Änderung |
|---|---|
| `Config_LORA.h` | `<arduino_lmic.h>` (MCCI) statt `<lmic.h>`; `LORA_CHANNELS 8`; neuer Block **ZS** mit `SLOT_ABSTAND_S`, Abfrage-Intervall, Zeitzone, Testschaltern; Gerätedaten aus `Config_Geraet.h` |
| `Config_Geraet.beispiel.h` (neu) | Vorlage für DevAddr, Schlüssel und `LOGGER_SLOT` je Logger; die echte `Config_Geraet.h` bleibt außerhalb des Repos |
| `STM32_LORA.ino` | MCCI-Pinmap-Felder, leere OTAA-Rückrufe, `LMIC_setAdrMode(0)`, Zeitabfrage vor `LMIC_setTxData2`, Auswertung nach dem Senden, keine Ausgabe bei `EV_TXSTART`, LMIC-Fehler → schlafen, Frame-Counter beim Sendeversuch, Sketch-ID nur in jedem 10. Paket |
| `STM32_LORA_utility.ino` | `Alarm_konfigurieren()` nutzt das neue Raster und die Ortszeit; RTC-Lesen über `zs_rtc_jetzt()`; ZS-Daten in den Backup-Registern 11–16; bei Power-On-Reset zurücksetzen |
| `STM32_LORA_261008_ZS.ino` | Variablen, `l_ID = 261008` (Sketch-Kennung im Paket) |
| `STM32_LORA_zeitsync.ino` (neu) | Ablauf Zeitabfrage, RTC stellen, Backup-Register, Diagnose-Ausgaben |
| `beelogger_zeitsync.h` (neu) | reine Rechenlogik ohne Arduino: GPS→UTC (−18 Schaltsekunden), Sommerzeit, Raster, Plausibilität |

Mit `ZEITSYNC_aktiv 0` verhält sich der Sketch beim Wecken wie das Original. Die MCCI-Bibliothek braucht er trotzdem.

## Review-Änderungen (Stand 2)

Nach einer Prüfung aus Sicht der Embedded-Entwicklung geändert. Jeder Punkt ist im Code mit `ZS` markiert.

| Punkt | Problem | Lösung |
|---|---|---|
| **RTC-Datum nach Mitternacht** | STM32RTC 1.3.7 liest in `getEpoch()` erst das Datum, dann die Uhrzeit. Das Lesen der Uhrzeit sperrt das Datum bis zum nächsten Datumslesen (STM32F4-HAL, Hinweis bei `HAL_RTC_GetTime`). Logger 0 wachte um 23:59:59 auf, ein späteres `getEpoch()` lieferte dann ein um 1 Tag falsches Datum. Simulation ohne Korrektur: 30 falsche Lesungen in 30 Tagen. | `zs_rtc_jetzt()` liest das Datum vorher und nachher (entsperrt). Das Raster liegt jetzt bei +1 s, damit kein Wachfenster über Mitternacht läuft. |
| **LMIC-Fehler** | Ein ASSERT in der LMIC (z. B. RFM95 antwortet nicht) endet in einer Endlosschleife mit laufendem Prozessor, bis der Akku leer ist. Das gilt auch für das Original. | `lmic_hal_set_failure_handler()`: Der Logger legt sich normal schlafen und versucht es beim nächsten Wecken neu. |
| **Uhr von außen verstellt** | System-Check oder Selbsttest stellen die RTC. Die gespeicherte Angabe „RTC ist UTC“ war danach falsch. | Beim Einschlafen wird die geplante Weckzeit gespeichert. Passt die Uhr beim Wecken nicht dazu (mehr als 10 min nach dem Plan oder mehr als 6 h davor), gilt sie als nicht abgeglichen und wird beim nächsten Senden neu gestellt. |
| **Backup-Daten ohne Prüfung** | Beschädigte Register oder ein alter Registeraufbau würden als gültig gelesen. | Prüfwort mit Magic und Version in Register 16. Bei Fehler wird der Zeitabgleich-Zustand zurückgesetzt. |
| **Große Korrektur** | Bisher wurde die 3. Antwort übernommen, ohne zu prüfen, ob die Antworten zueinander passen. | Eine Korrektur über 10 min wird nur übernommen, wenn die vorige Antwort dieselbe Korrektur verlangt hat (±5 s). |
| **Warten auf die volle Sekunde** | Die Warteschleife hatte keine Obergrenze. | Abbruch nach 1,5 s; das zählt als Fehlversuch. Zusätzlich wird geprüft, ob die Zeitreferenz plausibel ist (0–15 s alt). |
| **Frame-Counter nach Timeout** | Hochgezählt wurde nur bei `EV_TXCOMPLETE`. Nach einem Timeout wurde derselbe Zähler erneut gesendet, und TTN kann das Paket als Duplikat verwerfen. | Hochzählen nach erfolgreichem `LMIC_setTxData2()` und sofort in Register 3 sichern. Die Rückgabe von `LMIC_setTxData2()` wird jetzt geprüft. |
| **Sketch-ID in jedem Paket** (Original) | Geprüft wurde `LMIC.seqnoUp % 10`, bevor `seqnoUp` gesetzt war (immer 0). | Jetzt `LoRaSeqCounter % 10`: Die ID kommt in jedem 10. Paket, 9 von 10 Paketen sind 4 Byte kürzer (~67 statt ~72 ms Sendezeit). |

Bewusst **nicht** geändert:

- **ABP mit Zähler-Rücksetzung bei 16384 und „Resets frame counters“ in TTN.** Die Anwendung ist nicht sicherheitskritisch.
  - Ein „Session-Neustart“ vor dem Überlauf bringt bei ABP nichts: Schlüssel und DevAddr bleiben gleich.
  - OTAA wäre die saubere Lösung, ist aber ein anderer Aufbau.
- **Stellgenauigkeit der RTC.** Sie reicht für 10-s-Abstände. Selbsttest 2a misst sie auf der Hardware.

Zur Kenntnis:

- **Sendeleistung:** Die MCCI-LMIC sendet mit 14 dBm. Die alte Bibliothek schrieb `0x80|14` ins PA-Register und sendete damit ca. 16 dBm. Das ist rund 2 dB weniger als bisher und liegt sicher in der EU-Grenze von 25 mW ERP. RSSI/SNR im Feldtest prüfen.
- **Debug-Ausgaben:** Für den Feldbetrieb `myDEBUG 0` setzen (`STM32_beelogger.h`). Bei 9600 Baud kosten die Ausgaben bei jedem Wecken Wachzeit und verschieben den Sendezeitpunkt.
- **MCCI-Konfiguration nach Updates:** Die Bibliothek überschreibt beim Update `lmic_project_config.h` wieder mit US915. Der Sketch bricht dann mit einer klaren Meldung ab; einfach erneut auf EU868 stellen.

## Einrichtung

Arduino-IDE und Bibliotheken: [`../firmware/README.md`](../firmware/README.md). TTN-Einstellungen: [`ttn-einrichtung.md`](ttn-einrichtung.md).

## Tests

### Stufe 1 – Rechenlogik am PC (ohne Hardware)
- Windows: `tests\windows\tests_starten.bat` starten, zusammen mit den Programmen aus dem Actions-Download (Artefakt `windows-tests`). Das Skript führt Stufe 1 und 2 aus.
- Mit Compiler (WSL, MSYS2, Linux): `tests/alle_tests_linux.sh`

Erwartet: `ZS-Tests: 70 bestanden, 0 fehlgeschlagen`.

Geprüft werden:

- GPS→UTC mit Schaltsekunden
- Warten auf die volle Sekunde
- Kalender 1970–2100 Tag für Tag
- Sommerzeit an allen Umstellungen 2024–2035, Referenz: Zeitzonen-Datenbank von Python
- Nachtfenster
- Weckraster: 24.000 Zufallsfälle, Mitternacht (kein Wecken in den letzten 2 min vor 0 Uhr), Slot-Abstände
- Uhr-Plausibilität beim Wecken, Prüfwort der Backup-Register, Annahme großer Korrekturen nur bei Bestätigung
- wann abgefragt wird und welche Korrekturen angenommen werden
- die ganze Kette mit nachgebildeter MCCI-Zeitreferenz: Abweichung ≤ 6 ms

Ich habe absichtlich Fehler in den Code eingebaut (z. B. Schaltsekunden 0, Sommerzeit um 2 Uhr, falsche Raster-Phase, falscher Wochentag, Plausibilitäts- und Prüfwortfehler). Jeder davon wird von den Tests erkannt.

### Stufe 2 – Simulation von 10 Loggern am PC
`sim_sync.exe` und `sim_orig.exe` (Quelle: `tests/sim/sim_zeitsync.cpp`) binden den **echten** ZS-Code des Sketches ein. Nachgebildet werden:

- RTC-Quarz mit ±20 ppm und Temperaturgang
- Netzlatenz, Antwortquote, RX1/RX2
- Kollisionen auf 8 Kanälen
- Gateway kann nicht empfangen, während es sendet
- unterschiedliche Messdauer der Logger
- die Wetterstation im eigenen 10-min-Takt

**Das ist ein Modell, keine Messung.** Die Ergebnisse stehen in `tests/Simulationsergebnisse.txt` (30 Tage, Herbst):

| Variante | verlorene Uplinks | Streuung der Messzeitpunkte |
|---|---|---|
| Original-Firmware | 0,017 % (6), zwei Logger zeitweise < 1 s auseinander | ~9 min |
| Zeitabgleich **ohne** Versatz | **2,9 %** (≈ 1.000) | ~2 s |
| Zeitabgleich **mit 10 s Versatz** | **0** | ~1,5 min |

Weitere Ergebnisse:

- Die RTC-Nachbildung sperrt das Datum wie der STM32F4. Mit `zs_rtc_jetzt()` und Raster +1 s gibt es 0 falsche Datumslesungen, ohne die Korrektur 30 in 30 Tagen.

- Uhrfehler zwischen den Abgleichen: Median ~0,7 s, max ~2 s, im Winter max ~3,7 s.
- 5 s Abstand reicht nicht immer. 10 s ist die Empfehlung.
- Wenn sich die Messdauer der Logger stark unterscheidet (z. B. Audio nur bei einigen), rücken Nachbarn zusammen. Dann gleiche Sensor-Konfiguration verwenden oder `SLOT_ABSTAND_S 20` setzen (bis Slot 9 erlaubt).

Varianten: `sim_sync.exe --hilfe`.

### Stufe 3 – Selbsttest auf der BlackPill
`tests/STM32_ZS_Selbsttest` aufspielen und den Monitor öffnen (FTDI, 9600 Baud).

- Teil 1: dieselben 70 Tests auf dem STM32.
- Teil 2 prüft die RTC:
  - **2a** klärt eine offene Frage: Beginnt die RTC beim Stellen eine neue Sekunde (Stellgenauigkeit ~1 ms) oder behält sie die alte Phase (bis 1 s Fehler)? Beides funktioniert, die Simulation rechnet mit dem ungünstigeren Fall.
  - **2b** Datum über die Zeitumstellung
  - **2c** Alarm wie im Sketch
  - **2e** zeigt, ob `getEpoch()` nach Mitternacht wirklich das alte Datum liefert, und prüft die Umgehung `zs_rtc_jetzt()`

Der Test verstellt die Uhr und löscht die ZS-Register 11–16. Danach wieder den Logger-Sketch aufspielen.

### Stufe 4 – Musterlogger am Tisch mit TTN
1. In `Config_LORA.h` `ZEITSYNC_TEST 1` setzen. Dann wird bei jedem Senden abgefragt, also **höchstens 1 Stunde** so betreiben (TTN Fair Use: 10 Downlinks/Tag).
2. Serieller Monitor, erwartete Zeilen:
   - Erste Antwort: `ZS: Zeitabfrage angehaengt`, danach `ZS: Uhr gestellt, Korrektur: -7xxx.xxx s`. Die Uhr springt von Compile-Ortszeit (MESZ) auf UTC.
   - Folgende Antworten: Korrektur im Bereich ±0,1 s, dazu `Weckzeit (RTC) … UTC = … Ortszeit`.
   - Wenn keine Antwort kommt: `ZS: keine Netzzeit erhalten`, siehe Fehlersuche.
3. TTN-Konsole → Gerät → Live data:
   - Zu jedem Uplink mit Abfrage gehört ein Ereignis zur Device-Time-Antwort und ein Downlink.
   - Beim Downlink nachsehen, ob er in RX1 oder RX2 geht. Beides ist in Ordnung, wenn die TTN-Einstellungen oben stimmen.
4. Optional `ZEITSYNC_TEST_VERSTELLEN_S 5`: Die Uhr wird absichtlich um 5 s falsch gestellt. Jeder folgende Abgleich muss etwa `-5.0xx s` korrigieren. Das prüft die ganze Messkette.
5. Danach beide Testschalter auf 0 setzen und 24 h normal laufen lassen. Es darf genau eine Abfrage pro Tag kommen.

### Stufe 5 – Feldtest mit mehreren Loggern
- TTN-Konsole, Anwendung → Live data → „Export as JSON“, möglichst über mehrere Tage.
- Alternativ die Storage Integration, wenn sie aktiviert ist.
- Dann: `python tests/ttn_auswertung/ttn_zeitanalyse.py export.json`

Die Auswertung zeigt je Logger:

- Lage im 10-min-Raster, Reihenfolge und Abstand der Slots
- Streuung
- Gang zwischen den Abgleichen (s/Tag)
- erkannte Uhrkorrekturen
- verlorene Pakete (Lücken im Frame-Counter)
- kleinsten Abstand zweier Logger

Ziel: Abstände nie unter 2 s, Reihenfolge = `LOGGER_SLOT`, Gang im Bereich ±4 s/Tag, eine Korrektur pro Tag.

## Fehlersuche, wenn keine Netzzeit kommt
1. Live data: Kommt überhaupt ein Downlink?
   - Nein: LoRaWAN-Version testweise auf 1.0.3 stellen und prüfen, ob das Gateway Downlinks senden darf.
2. Downlink da, Logger meldet trotzdem „keine Netzzeit“: Die Rx1/Rx2-Werte in TTN passen nicht zum Logger (siehe Tabelle).
   - Notlösung: Im Sketch `LMIC.rxDelay = 5;` setzen, in TTN „Rx1 delay 5“ eintragen und `SERVER_TM_OUT` auf 10000 erhöhen. Das kostet bei jedem Senden 4 s mehr Wachzeit.
3. Rückweg jederzeit: `ZEITSYNC_aktiv 0` setzen oder das Original `STM32_LORA_260705` aufspielen.

## Bekannte Grenzen
- **Messdauer:** Gesendet wird nach der Messung. Unterschiede in der Messdauer zwischen den Loggern verschieben die Sendezeit. Prüfen kann man das über „t-on“ (Service-Wert) im beelogger-Server.
- **Schaltsekunden:** fest 18 s, seit 2017 unverändert. Kündigt der IERS eine neue an, `ZS_SCHALTSEKUNDEN` in `beelogger_zeitsync.h` anpassen.
- **Zeitzone:** Die Sommerzeit-Regel gilt nur für die EU.
- **Nicht übernommene Befehle:** Antworten auf MAC-Befehle von TTN gehen weiterhin bei jedem Wecken verloren, wie im Original.
  - Deshalb ist ADR aus (`LORA_ADR_aus 1`).
  - Prüfen: In Live data sollten außer der täglichen Zeitantwort keine weiteren Downlinks auftauchen.
- **Backup-Register 11–16:** Die Testversion nutzt sie, deshalb nur für STM32F4. Beim F103 bricht das Übersetzen mit Meldung ab.
