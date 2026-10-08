# BEEP-Anbindung

## Hauptweg: über den eigenen beelogger-Server

TTN → Webhook → eigener beelogger-Server (Verarbeitung) → BEEP-API. Der Server kann:

- Werte prüfen,
- Werte der Wetterstation als Referenz hinterlegen,
- Daten mit dem Messzeitpunkt an BEEP schicken,
- eine eigene Datenkopie behalten.

## Möglich: direkt aus TTN an BEEP

Der BEEP-Quelltext enthält einen Eingang für TTN-v3-Webhooks: `POST https://api.beep.nl/api/lora_sensors_auth`, angemeldet mit dem Header `Authorization: Bearer <BEEP-API-Token>`.
Die Variante `lora_sensors` ohne Anmeldung ist auf 10 Aufrufe pro Minute begrenzt. Diese Grenze gilt vermutlich je IP-Adresse, und alle TTN-Nutzer kommen über dieselben Server.

Bedingungen laut Quelltext:

1. Der Schlüssel des BEEP-Geräts muss die **DevEUI** des TTN-Geräts sein (`end_device_ids.dev_eui`).
2. Der Payload-Formatter muss BEEP-Kürzel liefern, mindestens 3 Felder. Sonst liest BEEP die Bytes als BEEP-Base-Format:

| beelogger-Formatter | BEEP |
|---|---|
| Gewicht | `weight_kg` |
| TempIn / FeuchteIn | `t_i` / `h_i` |
| TempOut / FeuchteOut | `t` / `h` |
| VBatt | `bv` |
| Licht | `l` |
| Aux1 (Luftdruck) | `p` |

Für die Solarspannung gibt es kein BEEP-Feld.

Weitere Folgen:

- Der Formatter gilt für die ganze Applikation. Er müsste beide Namenssätze liefern, damit auch der beelogger-Server weiter versorgt ist.
- Geräte, die BEEP nicht kennt (z. B. die S2120), lehnt BEEP ab. Abhilfe: in BEEP anlegen oder in eine eigene Applikation legen.
- Werte der Wetterstation speichert BEEP nicht als Wetterdaten.

Quellen:
- [BEEP routes/api.php](https://github.com/beepnl/BEEP/blob/master/routes/api.php)
- [BEEP MeasurementLoRaDecoderTrait.php](https://github.com/beepnl/BEEP/blob/master/app/Traits/MeasurementLoRaDecoderTrait.php)
