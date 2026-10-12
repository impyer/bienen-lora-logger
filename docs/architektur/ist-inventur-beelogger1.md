# Ist-Inventur beelogger1 – Sensorbestückung und Kanalzuordnung

**Stand:** 12.10.2026  
**Fassung:** 0.1, **STATUS: TEILWEISE ERMITTELT – PHYSISCHE SENSORBELEGUNG NOCH UNVERIFIZIERT**  
**Prüfart:** D0 (Dokumentation) / T0 (Quellcodeabgleich); die zugehörige Diagnosesoftware ist ein **separater, noch nicht auf der Produktivinstallation geprüfter Entwurf**.  
**Nicht:** Feld-/HiL-Test, SQL-Migration, Änderungsauftrag für den Logger, Beweis für produktive Sensorwerte.

**Referenz:** [Anforderungen](anforderungen-datenplattform.md) · [Sensor-/Kanalfachentwurf](sensoren-messkanaele-entwurf.md) · [Quellinventar](messgroessen-kanalinventar.md)

## A. Feststehende Ausgangsinformationen

| Aussage | Beleg / Stand |
|---|---|
| `beelogger1` ist als beelogger-Webansicht im bisherigen Projekt behandelt worden. | Projektkontext; **keine** Aussage zur tatsächlich gestarteten physischen Hardware. |
| Ein beelogger-M.40-**Single** schreibt im Pfad des Loggerverzeichnisses unter anderem `beelogger.csv`, `month.csv`, `week.csv`. | [`server/beelogger_eigen/beelogger1/beelogger_log.php`](../../server/beelogger_eigen/beelogger1/beelogger_log.php), Single-Datensatzerzeugung. |
| Der M.40-Single-Datensatz hat 17 kommaseparierte Spalten und enthält je ein separates Feld für serverseitig **korrigiertes** und eingehendes **Gewicht**. | [Serveranalyse M.40](../server-analyse.md); source code `beelogger_log.php`. |
| Ein eigener LoRa-Eingang kann optional zusätzliche technische Informationen in `lora_zusatz.csv` ablegen. | [`server/lora/README.md`](../../server/lora/README.md) und [`lora_funktionen.php`](../../server/lora/lora_funktionen.php). |
| Ein FPort-1-Decoder und ein FPort-2-Decoder sind im Repository vorhanden; daraus ergibt sich **nicht** der an `beelogger1` tatsächlich laufende Formatter/Firmwarestand. | [`formatter/formatter.js`](../../formatter/formatter.js). |
| Die im Repository befindliche `firmware/STM32_LORA_261008_ZS/Config_MULTI.h` ist die Konfiguration eines **Test-/Firmwarepakets**, nicht der Nachweis der bei `beelogger1` geflashten Konfiguration. | [Test-Firmware](../../firmware/STM32_LORA_261008_ZS/Config_MULTI.h), [Firmware-Dokumentation](../../firmware/README.md). |
| In früherer, von Nutzerseite vorgelegter Browserausgabe waren Beispielwerte aus dem Jahr 2022 sichtbar. | Gesprächsstand; **keine** gesicherte zeitgleiche echte beelogger-Messreihe für den Wetterdatenzeitraum 2026. |

## B. Kandidaten für beelogger1 – Belegung noch nicht physisch bestätigt

| CSV-Single-Index (1-basiert) | Technische Rolle im Original-M.40-Schema | Fachliche Interpretation | Status tatsächliches Gerät |
|---:|---|---|---|
| 1 | Zeitangabe | Quell-/Serverzeit, Zeitzone prüfen | offen |
| 2 | `TempIn` | Temperatur innen, Position offen | **offen** |
| 3 | `TempOut` | Außentemperatur bzw. für Gewichtskorrektur genutzter Kanal | **offen** |
| 4 | `FeuchteIn` | Relative Feuchte **oder** zweiter Temperaturfühler (abhängig von Konfiguration) | **offen – nicht blind als Feuchte importieren** |
| 5 | `FeuchteOut` | Relative Feuchte außen | **offen** |
| 6 | `Licht` | Helligkeit | **offen** |
| 7 | `Gewicht korrigiert` | vom beelogger-Server korrigiertes Gewicht | **offen** |
| 8 | `VBatt` bzw. `BienenIn` | Spannung **oder** Bienenzähler | **offen** |
| 9 | `VSolar` bzw. `BienenOut` | Spannung **oder** Bienenzähler | **offen** |
| 10 | `Service` bzw. Zählerinformation | Gerätestatus | **offen** |
| 11 | `Gewicht roh/Quelle` | Eingangswert vor serverseitiger Gewichtskorrektur; nicht automatisch ADC-Rohwert | **offen** |
| 12 | `Aux1` | Konfigurations-/Pfadabhängig, häufig Luftdruck | **offen** |
| 13 | `Aux2` | Konfigurations-/Pfadabhängig; im Original-M.40-LoRa u. a. RSSI | **offen** |
| 14 | `Aux3` | Konfigurations-/Pfadabhängig; u. a. Sketch-ID | **offen** |
| 15–16 | reservierte/leere Felder | Nicht als Sensor deuten | — |
| 17 | Unix-Zeit | technische Zeitreferenz; UTC-Güte prüfen | offen |

**Diese Tabelle ist ein Schemaabgleich, keine Liste bestätigter physischer Sensoren.** Ob die einzelnen Datenfelder ausgefüllt sind, lässt sich nur anhand der echten Datendateien feststellen. Auch ein gefülltes Feld beweist keine intakte Sensorik oder richtige Messposition.

## C. Read-only-Strukturanalyse auf der ThinkStation

Zur sicheren Vorbereitung liegt im Repository ein [Diagnoseskript](../../server/diagnose/beelogger1_inventur.py). Es **führt keine PHP-Dateien aus** und gibt **keine** CSV-Messwerte, Passwörter, Token, Funk-IDs, Originalpayloads oder privaten Gerätekonfigurationsinhalte aus. Es berichtet ausschließlich Dateivorhandensein, grobe Dateistatistik, Schema-Spaltenlängen, Anzahlen nichtleerer Felder und – soweit vorhanden – Zählwerte für Funkformat 1/2.

Auf dem Server **nach Prüfung auf ungesicherte lokale Git-Änderungen**:

```bash
cd /home/impy/bienen-lora-logger
git status --short
git pull --ff-only
python3 server/diagnose/beelogger1_inventur.py \
  --root /var/www/bienen-logger/beelogger1 \
  > /home/impy/beelogger1_strukturinventur.json
```

**Wichtig:** Bitte vor einem `git pull` sicherstellen, dass keine ungesicherten Änderungen im Repository betroffen sind. Falls die CSV-Dateien nicht mit dem Benutzer `impy` lesbar sind, meldet der Aufruf einen Lesefehler; Berechtigungen vor einer weiteren Maßnahme prüfen, nicht pauschal Dateirechte ändern.

Die Ausgabedatei **außerhalb des öffentlich ausgelieferten Webordners** belassen. Sie enthält keine Rohwerte; bei Veröffentlichung dennoch die generelle Freigaberegel des Projekts beachten. **Keine** `beelogger_config.php`, `Config_LORA.h`, `Config_Geraet.h`, LoRa-Schlüssel oder vollständige TTN-/BEEP-API-Antworten teilen.

**Ausgangslage:** Das Skript und die Bestandsaufnahme wurden von hier aus noch **nicht auf deiner ThinkStation ausgeführt**. Die Abfrage der tatsächlich gespeicherten CSV-Zeilen ist daher **OFFEN**.

## D. Physische Sensorinventur – manuell gegen Gerät und geflashte Firmware prüfen

| Sachverhalt | Gesicherte Angabe bisher | Nächster Nachweis |
|---|---|---|
| Exakter `beelogger1`-Gerätetyp und Firmwareversion | unbekannt | Geräteverwaltung / tatsächlich geflashte Build-Zuordnung |
| FPort 1 oder 2 bzw. letzter eingesetzter Formatter | unbekannt | nur Metadaten der TTN-Uplinks und der sichere Diagnosereport |
| Gewichtswandler / HX711 / Tarierung / Kalibrierung | unbekannt für tatsächlich betriebenes Gerät | Aufbau- und Kalibriernachweis |
| Temperatursensor(en), Anbringungsort (Brut/Deckel/Außen/Zelle) | unbekannt | Verdrahtung und tatsächlich geflashte Konfiguration |
| Feuchtesensor(en) | unbekannt | Hardwarebelegung und Quellfeldinterpretation |
| Licht-, Druck-, FFT- oder sonstige Zusatzsensorik | unbekannt | aktivierte Sensoren und Firmware-/Kanalbelegung |
| Sensoraustausch und historischer Gültigkeitsbeginn | unbekannt | Installations-/Wartungsprotokoll |
| Tatsächlich verfügbare aktuelle Messdaten | nicht verifiziert | Strukturreport; für Datenqualität zusätzlich separate, **nicht öffentliche** Prüfung echter Werte |

Bei der **Testkonfiguration** im Repository stehen z. B. `Anzahl_Sensoren_DS18B20=1`, `Anzahl_Sensoren_Gewicht=1`, `Anzahl_Sensoren_BME280=0` und `Aussenwerte=8`. **Dies sind ausschließlich nachgewiesene Test-Compilezeitwerte und dürfen nicht als beelogger1-Istzustand ausgegeben werden.**

### Schema für bestätigte Sensorbelegung (noch leer)

| Sensor-/Hardware-Komponente | Gerät | Kanal am Firmwareeingang | Tatsächliche Messposition | Inbetriebnahme ab | Quelle/Nachweis |
|---|---|---|---|---|---|
| **noch unbekannt** | beelogger1 | **offen** | **offen** | **offen** | echte Hardware-/Konfigprüfung erforderlich |

**Keine geratenen Sensormodelle, Positionen oder Kalibrierwerte eintragen.**

## E. Nächster Entscheidungspunkt

Aus dem auf der ThinkStation erzeugten **Strukturreport** lässt sich zunächst ableiten, welche CSV-Felder tatsächlich Daten enthalten und welcher Zusatzdatenpfad vorkommt. Danach die tatsächliche **Funk-/Firmwarekonfiguration und physische Sensorposition** prüfen und erst die bestätigten Kanal-zu-Messgrößen-Zuordnungen ins zentrale Datenmodell übernehmen.

Eine **automatisierte Analyse oder öffentliche Diagrammausgabe** darf `FeuchteIn` oder `Aux1`–`Aux3` nicht anhand des Namens allein interpretieren. Bis zur Prüfung erhalten solche Felder den Status **unklar/nicht freigegeben**.

**Umsetzung:** keine Datenbankänderung, keine Apache-/Firewalländerung, kein Zugriff auf produktive Geheimnisse.
