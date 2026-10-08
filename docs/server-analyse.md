# Analyse beelogger-Webserver M.40: LoRa-Eingang (Stand 08.10.2026)

Grundlage: `M40_261004_ServerSkripte.zip` von beelogger.de (Download `?ddownload=215031`, SHA-256 `fc8fc02b…85de85`),
unverändert abgelegt in `server/beelogger_M40_original/`. Geprüft wurde vor allem `beelogger1/beelogger_log.php`
(Version „M.40 vom 04.10.2026“). Zeilennummern beziehen sich auf diese Datei.

**Wichtig:** Geprüft ist das Paket von beelogger.de, nicht die Fassung auf deinem Server.
Falls du dort etwas angepasst hast, ist das hier nicht berücksichtigt.

## 1. Wie der LoRa-Eingang arbeitet (Z. 82–141)

- TTN schickt den Webhook an `beelogger_log.php?LORA=1&Passwort=…`. Das Passwort steht in der URL.
- Gelesen wird `uplink_message.decoded_payload`, also die Ausgabe des Formatters. Helium wird ebenfalls unterstützt.
- Die Prüfsumme entfällt bei LoRa (Z. 396: `OR $LORA==1`).

| JSON-Feld | Serverwert | Bemerkung |
|---|---|---|
| `TempOut` | Außentemperatur | wird auch als **Wägezellentemperatur** für die Gewichtskorrektur genutzt (Z. 98) |
| `TempIn`, `FeuchteIn`, `FeuchteOut`, `Licht`, `VBatt`, `VSolar`, `Service`, `Gewicht` | wie benannt | |
| `BienenIn`, `BienenOut` | Bienenzähler | vom LoRa-Sketch nicht gesendet |
| `Aux1` | Aux1 | Luftdruck, plus Korrekturwert `KorrPressure` (Z. 507) |
| **`Aux2`** | – | **wird aus dem JSON nicht gelesen.** Aux2 bekommt den **RSSI des ersten Gateways** (`rx_metadata[0].rssi`, Z. 95) |
| **`Aux3`** | Aux3 **und** Sketch-ID | Der Wert wird als Messwert in die CSV-Spalte Aux3 geschrieben **und** als Sketch-ID „LORA_…“ abgelegt (Z. 109) |
| `TempIn2` … `Gewicht6` | nur bei Duo/Triple/…-Verzeichnissen | Single (`beelogger1`, M_Type 1) liest sie nicht (Z. 112 ff.) |

Den Typ legt der **Verzeichnisname** fest (Z. 40–61): `beelogger1` = Single, `Duo1` = Duo (mit Unterverzeichnissen `beeloggerD1_1`, `beeloggerD1_2` je Waage), entsprechend `Triple…`, `Quad…`.

**CSV-Zeile Single** (Z. 771–774), Reihenfolge der Spalten:

1. Zeit
2. TempIn
3. TempOut
4. FeuchteIn
5. FeuchteOut
6. Licht
7. Gewicht korrigiert
8. VBatt
9. VSolar
10. Service
11. Gewicht roh
12. Aux1
13. Aux2
14. Aux3
15. leer
16. leer
17. Unix-Zeit

Eine Spalte für eine zweite Innentemperatur gibt es beim Single nicht.

## 2. Befunde

| Nr. | Befund | Folge | Stelle |
|---|---|---|---|
| B1 | **Zeitstempel = Empfangszeit des Servers** in Ortszeit, Sekunden auf `:00` gesetzt. `received_at` von TTN und ein Messzeitpunkt aus dem Gerät werden nicht genutzt. | Funkverzögerungen und gepufferte Werte bekommen eine falsche Zeit. Den Zeitabgleich im Logger nutzt der Server nicht. | Z. 295, 542 |
| B2 | **Umstellung auf Winterzeit:** Ortszeit-Text → `strtotime()`. PHP deutet die doppelte Stunde 02:00–02:59 als MEZ. Gespeichert wird nur, was mehr als 200 s nach dem letzten Datensatz liegt. | Am 25.10.2026: Die erste Stunde 02:xx (MESZ) wird **60 min zu spät** gespeichert, die zweite Stunde 02:xx (MEZ) wird **verworfen**. Mit einer PHP-Nachbildung von Z. 295, 542 und 761 bei 15-min-Takt nachgerechnet: 4 Datensätze falsch datiert, 4 verloren. Die falsche Zeit geht auch an BEEP (`time=`). | Z. 295, 542, 761 |
| B3 | **Aux2 ist bei LoRa fest mit dem RSSI belegt.** Ein `Aux2` aus dem Formatter wird ignoriert. Der RSSI kommt nur vom ersten Gateway der Liste, nicht vom besten. | Die FFT-Frequenz (bei WLAN in Aux2) lässt sich per LoRa ohne Serveränderung nicht ablegen. | Z. 95 |
| B4 | **Aux3 ist zugleich Messwert und Sketch-ID.** Der LoRa-Sketch schickt die ID (z. B. 260705) im Feld `Aux3`. | In der Spalte Aux3 steht bei LoRa die Sketch-ID als Zahl („260705.0“); das ist kein Messwert. Für den FFT-Pegel (bei WLAN in Aux3) bleibt nichts frei. | Z. 109, 509 |
| B5 | **Single nimmt kein `TempIn2` an.** | Eine zweite Innentemperatur (Deckel) geht beim Single über LoRa verloren. Der beelogger-Sketch weicht deshalb auf `FeuchteIn` aus; das ist ein Byte, also ohne Nachkommastelle und ohne Minuswerte. | Z. 112 ff., 771 |
| B6 | Gewichtskorrektur nutzt bei LoRa `TempOut` als Zellentemperatur. | Bei uns misst `TempOut` der BME280 im Strahlungsschutz, nicht die Zelle. Als Näherung brauchbar, physikalisch aber nicht die Zellentemperatur. | Z. 98, 530 ff. |
| B7 | `error_reporting(0)` | Fehler bleiben unsichtbar. Die Fehlersuche läuft nur über `write_error_file()`. | Z. 25 |
| B8 | Tippfehler `$BeepArrayId` statt `$BeepIdArray` (Single) | Die Zeile setzt eine unbenutzte Variable. Im Betrieb ohne Folge, weil die Zeile danach das richtige Feld beschreibt. | Z. 719 |
| B9 | Triple per LoRa: `ext_M_Type` wird nur dann 3, wenn `Gewicht3` im JSON steht. | Fehlt `Gewicht3` (z. B. Sensorfehler), lehnt der Server das ganze Paket mit „typErr“ ab. | Z. 114, 122, 397 |
| B10 | Passwort im Klartext in der URL | TTN unterstützt eigene Header beim Webhook. Ein Header taucht nicht in Server-Logs mit Abfrage-URL auf. Bei HTTPS ist es auf dem Transportweg ohnehin verschlüsselt. | Z. 79–80 |

B2 habe ich in einer Nachbildung der drei Zeilen nachgerechnet, nicht auf einem laufenden Server.

## 3. Umsetzung: eigener LoRa-Eingang (08.10.2026)

Umgesetzt in `server/lora/` (Beschreibung: `server/lora/README.md`).
Der Eingang gibt jeden Uplink über den **EE-Weg** von `beelogger_log.php` weiter: Dieser Weg kennt einen Zeitstempel je Datensatz (Z. 296 ff.).
`beelogger_log.php` selbst bleibt unverändert.

| Befund | Stand |
|---|---|
| B1 Empfangszeit statt Messzeit | **behoben**: Gerätezeit, sonst `received_at` von TTN |
| B2 Winterzeit | **besteht weiter** im Speichern der Ortszeit: Ende-zu-Ende-Test mit den echten Skripten, 2 von 7 Datensätzen in der Umstellungsnacht verworfen. Folgt in Schritt 4. |
| B3 Aux2 = RSSI | **behoben**: Aux1–3 frei zuordenbar, RSSI in `lora_zusatz.csv` |
| B4 Aux3 = Sketch-ID | **behoben**: Sketch-ID bzw. Firmware-ID in `lora_zusatz.csv` |
| B5 kein TempIn2 bei Einzel | **umgehbar**: über die Aux-Zuordnung oder `lora_zusatz.csv` |
| B9 Triple-Ablehnung | **behoben**: Typ kommt aus dem Verzeichnisnamen |
| B10 Passwort in der URL | **behoben** für TTN → Eingang (Header). Der interne Aufruf an `beelogger_log.php` braucht das Passwort weiterhin in der URL. |
| B6, B7, B8 | unverändert (beelogger-Code) |
