# Messgrößen- und Kanal-Inventar – Bestandsaufnahme 0.1

**Projekt:** Bienen-logger / Radeberger Honig  
**Stand:** 12.10.2026 · **Status:** FACHLICHER ENTWURF / QUELLINVENTUR; **keine Abnahme der tatsächlichen Sensorbelegung**  
**Änderungsklasse:** D0, Prüfung: T0 (Code- und Dokumentenabgleich); **keine** Prüfung an der produktiven ThinkStation/TTN/BEEP-API.  
**Maschinenlesbarer Begleiter:** [`messgroessen-kanalinventar.csv`](messgroessen-kanalinventar.csv).  
**Übergeordnete Anforderungen:** [Anforderungsbasis](anforderungen-datenplattform.md) · [Fachentwurf Sensoren/Kanäle](sensoren-messkanaele-entwurf.md).

## 1. Beweisniveau und verbindliche Unterscheidungen

| Kürzel | Bedeutung |
|---|---|
| **Q** | Feld/Konvertierung aus Repository-Quellcode bzw. vorhandener Projektdokumentation **nachgewiesen**. Beweist **nicht**, dass es am konkreten physischen Gerät aktiv ist. |
| **K** | Fachliche Feldinterpretation hängt von tatsächlicher Hardware, Loggerkonfiguration, Übertragungsweg, Firmware oder Messposition ab; **vorerst keine automatische Festlegung**. |
| **B** | Aus dem bisherigen Projektgespräch bzw. der Datenaufbereitung **als Betriebsbeobachtung berichtet**, in dieser Bestandsaufnahme **nicht live verifiziert**. |
| **P** | Vom Betreiber **als Zukunftsfunktion geplant**; keine konkrete Hardware-/API-Belegung nachgewiesen. |
| **U** | Unbekannt/offen; nicht durch Vermutungen auffüllen. |

**[BESTÄTIGT]** Drei Datenquellengruppen: (1) beelogger, (2) Umweltsensoren, (3) BEEP mit BEEP Base **als Alternative** zu beelogger sowie unabhängiger digitaler BEEP-Stockkarte. Zwei BEEP Bases sind vorgesehen. Mehrfachlogger werden im **Modell ermöglicht**, sind aber **nicht als aktueller Ausbau geplant**.

**Kritische Unterscheidung:** Quellfeld ≠ Sensor ≠ physikalische Messgröße ≠ Messposition ≠ Rohwert ≠ bereits korrigierter Quellenwert ≠ später abgeleiteter Analysewert. Ein Feldname im JSON, ein CSV-Spaltenname und der physische Sensor können unterschiedlich sein.

## 2. Bestand vs. Schnittstellen – was tatsächlich bekannt ist

| Komponente | Bestandsaussage | Sicherheit |
|---|---|---|
| beelogger-Single / beelogger1 | `beelogger1` ist aus der bisherigen Bereitstellung als Webansicht bekannt. `beelogger2`–`beelogger10` erscheinen in der früheren Standzuordnung, **nicht** als Nachweis zehn aktiver Geräte oder echter Messwerte. | **B** |
| LoRa-Formatter FPort 1 / 2 | Feldnamen, Kodierung und Decoder in `formatter/formatter.js`; v2-Spezifikation dokumentiert. Ob jeder Kanal an einem konkreten Gerät aktiviert ist, bleibt offen. | **Q/K** |
| SenseCAP S2120, Wetterstation | Wetter-Ingestionscode und zehn definierte Umweltdatenfelder. Für den Hauptstand wurde in früheren Gesprächen die Station `wetterstation-01` mit echten Daten genannt, ohne erneuten produktiven Zugriff in dieser Inventur. | **Q/B** |
| Bodentemperatursensoren und weitere Umweltgeräte | Als unterstützte Erweiterung gefordert; **kein konkreter Kanal/Hersteller/Datentransport nachgewiesen**. | **P/U** |
| BEEP Base 1 und 2 | Als alternative Stockmesssysteme vorgesehen; Daten werden an BEEP übertragen. **Konkrete API-Ausgabefelder, Sensoren, Abtastraten und Einheiten sind noch nicht überprüft.** | **P/U** |
| Digitale BEEP-Stockkarte | Fachliche Ereignis-/Dokumentationsquelle, kein Sensorgerät; genaue Ereignistypen/externes Schema noch zu erfassen. | **BESTÄTIGT/U** |
| `ZS_Test_261008.zip` | Vorliegendes **Firmware-Testpaket**, kein belastbares Inventar der produktiven Hardware. Die darin gezeigte `Config_MULTI.h` ist eine **Testkonfiguration**, nicht automatisch das aktuell eingesetzte Sensorlayout. | **Q für Testpaket; U für Betrieb** |

## 3. beelogger – FPort 1, klassisches Format (Q/K)

**Quelle:** [`formatter/formatter.js`](../../formatter/formatter.js), Funktion `dekodiereV1` und `V1`; [`docs/datenformat.md`](../datenformat.md).

| Bit | Quellfeld (JSON) | Kodierte / formatierte Einheit | Vorläufige fachliche Interpretation | Status |
|---:|---|---|---|---|
| 0 | `TempOut` | °C | Außentemperatur; konkrete Position/ggf. Korrekturrelevanz prüfen | Q/K |
| 1 | `FeuchteOut` | % | relative Feuchte außen | Q/K |
| 2 | `VBatt` | V | Batteriespannung; technische Telemetrie | Q |
| 3 | `VSolar` | V | Solarspannung; technische Telemetrie | Q |
| 4 | `Licht` | lx | Beleuchtungsstärke; Sensor/Position prüfen | Q/K |
| 5 | `Gewicht` | kg | Stockgewicht, **nicht** automatisch unkorrigiertes Rohgewicht | Q/K |
| 6 | `TempIn` | °C | Innentemperatur; räumliche Position prüfen | Q/K |
| 7 | `FeuchteIn` | Quellformat: ganze Zahl, formal % | **Entweder Feuchte oder umgenutzter Temperaturkanal**; bei umgenutztem DS18B20 im LoRa-Format Präzisions-/Vorzeichenproblem | **Q/K, KEIN Standardmapping** |
| 8 | `Gewicht2` | kg | zweite Messeinheit / Mehrfachsystem; aktuell nicht vorgesehen | Q/P |
| 9 | `TempIn2` | °C | zweiter Temperaturkanal bei Mehrfachsystem; nicht automatisch beim Single verfügbar | Q/P |
| 10 | `FeuchteIn2` | % im Format | weiterer Mehrfachkanal; tatsächliche Bedeutung prüfen | Q/P/K |
| 11 | `Gewicht3` | kg | dritter Gewichts-/Mehrfachkanal | Q/P |
| 12 | `Gewicht4` | kg | vierter Gewichts-/Mehrfachkanal | Q/P |
| 13 | `Aux1` | Decoder: ein Zehntel pro Einheit | Hilfskanal, häufig Luftdruck in hPa; **konfigurationsabhängig** | Q/K |
| 14 | `Service` | ganzzahlig | Status/Servicecode, kein Umweltmesswert | Q/K |
| 15 | `Aux3` | ganzzahlig | im dokumentierten LoRa-v1-Formatter **Sketch-/Firmwarekennung**, nicht pauschal Sensormessung | Q/K |

**Wichtige Verarbeitungsschicht:** [`docs/server-analyse.md`](../server-analyse.md) beschreibt beim **originalen M.40-LoRa-Pfad** `Aux2` in der CSV als RSSI und `Aux3` als gleichzeitig hilfskanal-/Sketch-ID-belegt. Der **eigene** LoRa-Eingang dokumentiert dagegen konfigurierbare `Aux1`–`Aux3` und separate technische Werte in `lora_zusatz.csv` ([`server/lora/README.md`](../../server/lora/README.md)). **Diese beiden Pfade nicht gleichsetzen.** In jedem importierten Datensatz muss nachvollziehbar sein, welchen Pfad und welche Mappings er durchlaufen hat.

## 4. beelogger – FPort 2 / Funkformat v2 (Q, Aktivierung offen)

**Quellen:** [`docs/funkformat-v2.md`](../funkformat-v2.md), [`formatter/formatter.js`](../../formatter/formatter.js). FPort 2 ist eine dokumentierte Format-/Decoderfähigkeit, **kein Nachweis sämtlicher installierter Sensoren**.

| Bit | Vom Formatter erzeugtes Feld | Semantik / Einheit | Datenart / besondere Vorsicht |
|---:|---|---|---|
| 0 | `TempOut` | Temperatur außen, °C | Messung; Position prüfen |
| 1 | `FeuchteOut` | relative Feuchte außen, % | Messung |
| 2 | `Aux1` | Luftdruck, hPa | Messung gemäß v2-Spezifikation |
| 3 | `TempIn` | Innentemperatur 1, °C | Messung; im v2-Entwurf DS18B20 für Brut |
| 4 | `TempIn2` | Innentemperatur 2, °C; Name konfigurierbar | Messung; tatsächliche Position unbekannt |
| 5 | `Gewicht` | Gewicht 1, kg | Messung bzw. geräteseitig verarbeitet; Tara/Korrektur klären |
| 6 | `Gewicht2` | Gewicht 2, kg | optionaler Mehrfachkanal |
| 7 | `VBatt` | Batteriespannung, V | Telemetrie |
| 8 | `VSolar` | Solarspannung, V | Telemetrie |
| 9 | `Licht` | Beleuchtungsstärke, lx | Messung |
| 10 | `FeuchteIn` | relative Innenfeuchte, % | **v2-Felddefinition**, nicht auf v1-Daten übertragen |
| 11 | `FFT_Hz`, `FFT_dB` | dominante FFT-Frequenz, Hz; Peakpegel, dBFS | **abgeleitete Signalmerkmale**, kein Audio-Rohsignal |
| 12 | `FFT_Gesamt_dB` | Gesamtpegel, dBFS | abgeleitetes FFT-Merkmal |
| 13 | `FFT_Baender_dB` | Liste von Bandpegeln, dBFS | **Array mit noch zu klärender Banddefinition**, nicht ein skalierbarer Einzelwert |
| 14 | `Service` | ganzzahliger Servicecode | Gerätestatus |
| 15 | `Status.*`, `Neustart` | Statusbits und Neustartgrund | technische Ereignisse/Flags, **keine** biologischen Messwerte |
| 16 | `Messzeit_unix`, `Messzeit` | Unix-UTC-Sekunden und ISO-UTC | Zeitmetadaten; nur mit gültiger Gerätesynchronisierung vertrauen |
| 17 | `FirmwareID` | Ganzzahl | Versionsmetadatum, keine Messgröße |
| 18 | `TempCPU` | CPU-Temperatur, °C | Gerätetelemetrie, **nicht** Stock-/Außentemperatur |

Der Decoder ergänzt `Format: 2` als Metadatum. Die Statusstruktur enthält die Flags `zeit_ok`, `fehler_aussen`, `fehler_ds1`, `fehler_ds2`, `fehler_waage1`, `fehler_waage2` und `akku_niedrig`; `Neustart` ist als Code abgelegt. Die dokumentierte Frequenz-/Pegel-FFT des alten LoRa-Sketches ist **nicht** vorhanden; die v2-Spezifikation beschreibt eine zusätzliche zukünftige Formatfähigkeit. **Nicht** fälschlich behaupten, dass aktuelle LoRa-Musterlogger FFT-Werte liefern.

Der Code kann `NAME.tIn2` und weitere neue Feldnamen umbenennen. **Das Quellprofil muss deshalb sowohl Parser-Version als auch tatsächliche Feldnamenkonfiguration referenzieren.**

## 5. SenseCAP S2120 – Umweltkanäle (Q/B)

**Quellen:** [`formatter/s2120_beep_formatter.js`](../../formatter/s2120_beep_formatter.js), [`server/wetter/wetter_funktionen.php`](../../server/wetter/wetter_funktionen.php), [`server/wetter/README.md`](../../server/wetter/README.md).

| Feld im gespeicherten CSV | Bedeutung | Einheit | Datenmodell-Hinweis |
|---|---|---|---|
| `t` | Lufttemperatur | °C | Umweltmessgröße; Sensorhöhe/Position noch offen |
| `h` | relative Luftfeuchtigkeit | % | Umweltmessgröße |
| `p_hpa` | Luftdruck | hPa | Druckwert; vor der Aggregation Einheit normieren |
| `l` | Licht | lx | Beleuchtungsstärke |
| `uv` | UV-Index | Index (dimensionslos) | eigenständige Größe, nicht lx |
| `wind_ms` | Windgeschwindigkeit | m/s | Zeitverlauf/Verteilung |
| `wind_dir_deg` | Windrichtung | Grad | **zirkulärer Winkel**; Windrose/vektorielle Statistik |
| `gust_ms` | Windböe | m/s | Spitzenwert; Aggregationsregel ggf. Maximum |
| `rain_mmh` | höchste Regenintensität im Übertragungsintervall | mm/h | **Intensität**, keine Menge |
| `rain_mm` | vom Gerät gelieferte Regensumme | mm | **Rücksetz-/Bezugszeitpunkt offen**: nicht ohne Prüfung als Intervallmenge oder Tagesregen ausgeben |
| `battery_pct` | Batteriekennwert | % | nur gelegentlich; Dokumentation nennt häufig 0/100, **kein sicherer kontinuierlicher Ladezustand** |
| `interval_min` | Sendeintervall | min | Geräte-/Konfigurationsmetadatum, keine Umweltgröße |

**Dekodierbesonderheit:** Derselbe S2120-Formatter erzeugt zusätzlich `p` in **Pa** für den BEEP-kompatiblen Feldsatz und `p_hpa` in **hPa** für den eigenen Wetter-Eingang. Das sind **zwei Repräsentationen derselben Druckmessung**, kein zweiter Drucksensor und keine zwei unabhängigen Beobachtungen.

**Getrennt zu führende technische Uplink-Daten:** `f_cnt`, `f_port`, `rssi`, `snr`, `gateways`, `sf`, `payload_hex`, `warnungen`, außerdem `zeit_utc`, `unix`, `ortszeit`, `stand`, `station`. Diese Felder sind wichtig für Provenienz, Funkdiagnose und Zeit-/Standzuordnung; sie sind **nicht** zwölf zusätzliche Umweltmessgrößen. Die S2120-Dokumentation nennt `received_at` von TTN als Zeitquelle und keine geräteseitige Messzeit: Empfangszeit ist daher mit entsprechender Zeitqualitätsinformation zu speichern.

## 6. Weitere Umweltmessstellen – noch kein Kanalkatalog (P/U)

- **Bodentemperatur**: fachlich `temperature`, °C, `medium=soil` und eine **messpunktspezifische Tiefe**; tatsächliches Gerät, Schnittstelle, Anzahl und Messintervalle offen.
- Weitere Bodensensorik wie **Bodenfeuchte** ist als Erweiterungsmöglichkeit genannt, jedoch weder aktiv noch hinsichtlich Messverfahren/Einheit (z. B. volumetrisch vs. relativ) spezifiziert.
- Weitere Wetter-/Mikroklimasensoren werden durch denselben Messstellen-/Kanalmechanismus unterstützt, **ohne** ihnen bereits Gerätekennungen zuzuweisen.

## 7. BEEP – bewusst unbestätigter Eingabekatalog (P/U)

- **BEEP Base** ist ein **alternatives** Stockmesssystem; Messdaten gehen an die BEEP-Plattform. **Zwei Geräte vorgesehen**, keine zu diesem Zeitpunkt bestätigten kanalweisen API-Antworten, Einheitendefinitionen, Sensorkonfigurationen, Historien oder Zugriffsmöglichkeiten.
- Die digitale BEEP-Stockkarte ist **keine Messkanalquelle**, sondern liefert strukturierte imkerliche **Ereignisse und Beobachtungen**. Hierfür braucht es einen gesonderten Ereigniskatalog und externe Referenzen zur richtigen Volk-ID.
- Die technischen Kürzel `weight_kg`, `t_i`, `h_i`, `t`, `h`, `bv`, `l`, `p` in [`docs/beep-anbindung.md`](../beep-anbindung.md) dokumentieren eine **mögliche beelogger-/TTN-zu-BEEP-Eingabe**, **nicht** verifizierte Messfelder eines BEEP-Base-Datenexports. **Nicht** aus dieser Liste die BEEP-Base-Hardware oder einen fertigen Import ableiten.
- **Noch zu prüfen:** Authentifizierte BEEP-Export-/API-Berechtigung, Objektkennungen (Volk/Base/Stockkarte), Feldkatalog, Zeitstempel, Einheiten, mögliche Korrekturen, Änderungs-/Löschereignisse und Sync-Semantik.

## 8. Fachlicher Zielkatalog: Größen und Aggregationssemantik (VORSCHLAG)

| Standardgröße / Arbeitscode | Einheit | Klasse | Zulässige/zu prüfende Aggregation |
|---|---|---|---|
| `temperature` | °C | Messwert, kontinuierlich | Mittel/Min/Max, **mit Positionskontext** |
| `relative_humidity` | % | Messwert, kontinuierlich | Mittel/Min/Max |
| `pressure` | hPa | Messwert, kontinuierlich | Mittel/Min/Max; Pa vorab konvertieren |
| `hive_mass` | kg | Messwert bzw. vom Quellsystem korrigiert | Zeitverlauf; Tagesdifferenz **separates berechnetes Feature** |
| `illuminance` | lx | Messwert, kontinuierlich | Mittel/Max unter Angabe der Zeitauflösung |
| `uv_index` | 1 | Index | Mittel/Max, mit Definition |
| `wind_speed` / `wind_gust` | m/s | kontinuierlich / Spitze | Mittel bzw. Maximum |
| `wind_direction` | ° | zirkulär | Windrose und zirkuläre/vektorielle Statistik, **kein naives arithmetisches Mittel** |
| `rain_intensity` | mm/h | Rate / Intervallspitze | Max/Verlauf; keine direkte Mengen-Summation |
| `rain_total_reported` | mm | Zähler/Summe unbekannter Basis | **keine Summation**, bevor Reset-/Bezugsregel geklärt ist |
| `battery_voltage` / `solar_voltage` | V | Gerätetelemetrie | Verlauf/Min/Max |
| `rssi` / `snr` | dBm / dB | Funktelemetrie | getrennt von biologischer Analyse |
| `fft_peak_frequency` / `fft_level` | Hz / dBFS | Signalmerkmal | nur mit dokumentierter DSP-Methode/Bandgrenzen |
| `cpu_temperature` | °C | Gerätetelemetrie | **nicht** als Bienenstocktemperatur verwenden |

**Wichtig:** Arbeitscodes sind **Vorschläge**, keine bereits vergebenen Datenbank-IDs. FFT-Bandpegel werden erst nach Banddefinition, Quelle und Kalibrierstatus als interpretierbare Mehrkanalmerkmale geführt.

## 9. Konsequenzen für die spätere SQL-Modellierung

**Vorschlag** eines importierbaren, versionierten Mappings:

```text
raw_record (Originalnachricht, Zeitquellen, Gerät, Verarbeitungspfad)
  └─ raw_channel_value (exakter Quellpfad, Rohwert, Quellformat)
        └─ channel_mapping (gültige Zeit, Format-/Konfigversion)
             ├─ measurement_quantity (physikalische Größe und Einheit)
             ├─ sensor_installation (falls bekannt)
             └─ measurement_position (Volk/Brutraum/Deckel oder Umweltstandort/Tiefe)
                   └─ normalized_measurement (Wert, Qualität, Mapping-/Quellreferenz)
                        └─ feature_definition + analysis_run → abgeleitete Daten
```

Es sollen **keine** technischen Feldnamen als fachliche Schlüssel missbraucht werden. Vor allem müssen `FeuchteIn`, `Aux1`–`Aux3`, Gewichts-/Kalibrierstatus und BEEP-Felder im konkreten Betrieb validiert werden.

## 10. Gerätespezifischer Abgleich begonnen

Für den Logger `beelogger1` existiert eine [Ist-Inventur 0.1](ist-inventur-beelogger1.md) mit Quellenstand, noch ungeprüften Hardwaredetails und einer nur lesenden [Diagnose](../../server/diagnose/README.md). Die tatsächlichen Messdateien wurden von dieser Umgebung **noch nicht gelesen**.

## 11. Nächste Arbeitsschritte und noch fehlende Nachweise

1. **Ist-Belegung beelogger:** Für jedes tatsächlich installierte Gerät Firmware/FPort, Sensorbestückung, logische Beute-/Kanalzuordnung, DS18B20-Positionen, Aux-Mapping, Tara/Kalibrierung und Änderungen über die Zeit bestätigen; **keine geheimen Konfigurationswerte öffentlich einchecken**.
2. **S2120-Kontext ergänzen:** Installationshöhe/-position, dokumentierte Bedeutung und Resetzeitpunkt von `rain_mm`, zeitlicher Standwechsel und Datenqualität.
3. **Boden-/weitere Umweltsensoren:** Konkrete Modelle/Schnittstellen erst nach Festlegung in das Quellprofil aufnehmen.
4. **BEEP Base / Stockkarte:** Autorisierten API-/Export-Beispieldatensatz **ohne Zugangsdaten oder private Angaben** prüfen und dann den tatsächlichen Feldkatalog erstellen; kein erfundener API-Vertrag.
5. **Entscheidungen bestätigen:** Einheitencodes, Messpositionstaxonomie, Mapping-Versionierung, Sensorinstallation/Kalibrierung und Rohdaten-Erhaltung als verbindliches Schema abnehmen.
6. **Erst anschließend:** ER-Diagramm, PostgreSQL-Constraints/DDL und Migration/Importtests.

**Grenze der Bestandsaufnahme:** Dies ist ein nach Quellen belegter **Schnittstellen- und Begriffskatalog**, **keine vollständige inventarisierte Liste aller produktiv installierten Sensoren**. Sie kann erst durch Abgleich mit der tatsächlichen Hardware-/Gerätekonfiguration vollständig werden.
