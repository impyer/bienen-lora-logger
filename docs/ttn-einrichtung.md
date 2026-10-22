# TTN einrichten (The Things Stack, EU868)

## Applikation

- **Application ID:** `beelog-de-sn`. Sie lässt sich später nicht ändern und muss im ganzen TTN eindeutig sein.
- **Eine Applikation für alle Geräte:** Ein Live-data-Export enthält dann alle Logger, ein Webhook genügt, und Logger können ohne Änderung in TTN den Stand wechseln.
- **Payload-Formatter:** an der Applikation der beelogger-Formatter (`payloadformatter_220227.js` aus dem beelogger-Sketchpaket). Die Wetterstation S2120 bekommt aus der Device Repository ihren eigenen Formatter am Gerät.

## Gerätenamen (End device IDs, lassen sich nicht ändern)

| Gerät | End device ID | Firmware |
|---|---|---|
| Logger 1 … 10 | `beelogger-01` … `beelogger-10` | `GERAET 1 … 10`, `LOGGER_SLOT 0 … 9` |
| Wetterstation | `sensecap-s2120-rad` | – |

Logger bekommen keinen Ort im Namen, damit sie wandern können. Welcher Logger an welchem Volk und Stand hängt, steht auf dem Server und in BEEP.

## Registrierung der Logger

- Aktivierung: ABP, LoRaWAN 1.0.2, RP001 1.0.2 rev B, Frequenzplan „Europe 863-870 MHz (SF9 for RX2 - recommended)“ (wie in der beelogger-Anleitung).
- DevEUI, Device address, NwkSKey und AppSKey erzeugen. Die DevEUI braucht man für einen direkten BEEP-Anschluss.
- Die Werte kommen in `firmware/STM32_LORA_261008_ZS/Config_Geraet.h`. Diese Datei wird nicht hochgeladen.

## Geräte: Advanced MAC settings

Ort in der Konsole: End device → Settings → Network layer → Advanced MAC settings.

Gemeint ist die **Geräte-Registrierung im TTN-Netzserver**, also die Funkseite Logger ↔ Gateway ↔ TTN. Der Webhook TTN → beelogger-Webserver, das Gateway und BEEP bleiben unverändert. Die Werte im Sketch sind fest; TTN muss zu ihnen passen:

```
Logger --LoRa--> Gateway --Internet--> TTN-Netzserver --> Webhook --> beelogger-Server --> BEEP
   ^                                        |
   +--------- Downlink (Zeitantwort) -------+   hier wirken die Advanced MAC settings
```

Der Logger empfängt nur in zwei Fenstern: RX1 1 s nach dem Senden (gleiche Frequenz, SF7) und RX2 2 s nach dem Senden (869,525 MHz, SF9). „Rx1 delay“ und „Rx2 data rate index“ sind das, was TTN über das Gerät *annimmt* (Ist). „Desired …“ ist das, was TTN per Stellbefehl einstellen *will* (Soll). Der Logger setzt seinen LoRa-Zustand bei jedem Wecken zurück und übernimmt solche Befehle nie. Ein Soll ungleich Ist führt deshalb zu immer neuen Stellbefehlen. Laut TTS-Quelltext erzeugt TTN einen Downlink, sobald Stellbefehle anstehen.

| Feld | Wert | Grund |
|---|---|---|
| Rx1 delay / Desired Rx1 delay | **1 / 1** | Der Logger öffnet RX1 nach 1 s. Die beelogger-Anleitung hat Desired 5. |
| Rx2 data rate index / Desired | **3 / 3** | SF9, wie `LMIC.dn2Dr = DR_SF9` im Sketch. Mit 0 (SF12, beelogger-Anleitung) sendet TTN im RX2 auf einer Einstellung, auf die der Logger nicht hört. Mit 1 s RX1-Verzögerung schafft TTN RX1 wegen der Internet-Laufzeit oft nicht und weicht auf RX2 aus. |
| Rx2 frequency / Desired | 869,525 MHz | |
| Resets frame counters | an | wie bisher |
| Status count periodicity / Status time periodicity | **0 / 0** (= aus) | Laut TTS-Quelltext verlangt TTN eine Statusabfrage (DevStatusReq) mit eigenem Downlink, solange nie eine Antwort kam. Der Logger beantwortet sie nie. Ohne diese Einstellung ist ein Downlink nach jedem Uplink zu erwarten. Falls die Felder in der Konsole fehlen: CLI `ttn-lw-cli end-devices set <app> <gerät> --mac-settings.status-count-periodicity 0 --mac-settings.status-time-periodicity 0s` (Feldnamen bitte prüfen). |
| Rx1 data rate offset / Desired, Max duty cycle / Desired | jeweils gleich (0 / 0, 100 % / 100 %) | Soll = Ist, sonst Stellbefehle |
| Factory preset frequencies | alle 8 **in dieser Reihenfolge**: 868100000, 868300000, 868500000, 867100000, 867300000, 867500000, 867700000, 867900000 | **Nötig wegen `LORA_CHANNELS 8`, unabhängig vom Zeitabgleich.** TTN kennt ohne Eintrag nur 868,1/868,3/868,5 MHz. Uplinks auf 867,x MHz verwirft TTN dann stillschweigend, also 5 von 8 Paketen (TTS-Quelltext: `searchUplinkChannel`). |
| LoRaWAN-Version | 1.0.2 wie bisher | Laut TTS-Quelltext beantwortet der Server DeviceTimeReq unabhängig von der Version. Kommt keine Antwort, als Versuch 1.0.3 einstellen. |

Fehlen die 867-MHz-Kanäle, will TTN sie per NewChannelReq und LinkADRReq nachtragen. Laut Quelltext schickt TTN LinkADRReq für die Kanalmaske auch bei abgeschaltetem ADR. Auch das ergibt ständige Downlinks. Die Reihenfolge muss zum TTN-Frequenzplan passen.

Neue Logger am besten gleich so registrieren. Bei bereits registrierten Loggern die Werte ändern und danach „Reset session and MAC state“ drücken. Dieser Knopf steht direkt über „Advanced MAC settings“. Wir gehen davon aus, dass TTN geänderte Ist-Werte erst mit dem Reset übernimmt. Mit „Resets frame counters“ ist der Reset für ABP unkritisch.

Kontrolle in Live data:
- Nach einem Uplink mit Zeitabfrage zeigt der Downlink entweder RX1 (Uplink-Frequenz, SF7) oder RX2 (869,525 MHz, SF9).
- Ohne Zeitabfrage sollen keine Downlinks auftauchen.

Hinweis zum NTP des Gateways: TTN nimmt für die Zeitantwort die GPS-Zeit des Gateways, falls vorhanden. Sonst nimmt es die eigene Empfangszeit, korrigiert um die halbe gemessene Laufzeit zum Gateway (im TTS-Quelltext geprüft, Semtech-UDP). Die NTP-Uhr des Gateways fließt **nicht** in die Antwort ein. Sie steht aber im Uplink als `rx_metadata.time` und ist damit eine unabhängige Messlatte für den Feldtest (Stufe 5).



## Webhook zum eigenen beelogger-Server

Ab 08.10.2026 geht der Webhook an den eigenen Eingang, nicht mehr direkt an `beelogger_log.php`; seit 22.10.2026 gibt es genau zwei: **Bienen-Eingang** `server/bienen/bienen_eingang.php` (Logger, eigene Platine, BEEP Base) und **Umwelt-Eingang** `server/umwelt/umwelt_eingang.php` (Wetterstation, Bodensonden).
Einrichtung und Webhook-Einstellungen: [`../server/bienen/README.md`](../server/bienen/README.md), [`../server/umwelt/README.md`](../server/umwelt/README.md).

- Ein Webhook für alle Geräte. Der Eingang ordnet die Geräte über `lora_config.php` den Verzeichnissen `beelogger1` … `beelogger10` zu.
- Die Verzeichnisse behalten die beelogger-Namen. Hinweis zur früheren Empfehlung, die Verzeichnisse wie die Geräte zu benennen (`beelogger-03`): `beelogger_log.php` liest die Nummer aus dem Namen (`intval("-03")` = −3). Davon rate ich ab.
- Das Passwort steht nicht mehr in der URL, sondern als Header `X-Bienen-Token`.

Quellen:
- TTS-Quelltext v3.33 (`pkg/networkserver`)
- [TTS: Webhook path variables](https://www.thethingsindustries.com/docs/integrations/webhooks/path-variables/)
- [beelogger LoRa_Konfig.pdf (Okt. 24)](https://beelogger.de/?ddownload=213050)
