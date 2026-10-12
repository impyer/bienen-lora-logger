# Fachentwurf: Sensoren, Messkanäle und Messgrößen

**Projekt:** Bienen-logger / Radeberger Honig  
**Fassung:** 0.1 · **Stand:** 12.10.2026  
**Status:** **ENTWURF – nicht fachlich freigegeben**, keine SQL-Migration  
**Änderungsklasse / Prüfung:** D0 (Dokumentation), T0 (Abgleich mit Quellunterlagen); keine Laufzeit- oder Feldprüfung  
**Grundlage:** [bestätigte Anforderungen](anforderungen-datenplattform.md), [beelogger-Datenformat](../datenformat.md), [Serveranalyse M.40](../server-analyse.md), [Funkformat v2](../funkformat-v2.md), [LoRa-Eingang](../../server/lora/README.md).

**Statuslegende:** **[BESTÄTIGT]** = im Architekturgespräch bestätigte Anforderung; **[QUELLBEFUND]** = in den genannten Projektunterlagen dokumentiert (ggf. abhängig von Software-/Übertragungsweg); **[VORSCHLAG]** = noch nicht bestätigtes Datenbankdesign; **[OFFEN]** = fachlich/technisch zu klären.

## 1. Leitidee

**[BESTÄTIGT]** Die Plattform unterscheidet **Datenquellengruppe, physisches Gerät, Sensor bzw. Messwandler, technischen Kanal, Messgröße, Messposition und zeitlich gültige Konfiguration**. Sie muss mehrere Völker und Bienenstände sowie beelogger, Umweltsensorik (Wetter, Boden usw.) und BEEP integrieren.

**[VORSCHLAG]** Ein eingehender Wert erhält **nicht** allein aufgrund seines Feldnamens seine physikalische Bedeutung. Eine **versionierte Kanalinterpretation**, die zum Messzeitpunkt gilt, ordnet ihn einer Messgröße, Einheit, Position und ggf. einem physischen Sensor zu.

**[BESTÄTIGT]** beelogger und BEEP Base sind **alternative** primäre Stockmesssysteme; die digitale BEEP-Stockkarte ist eine davon unabhängige Ereignis-/Dokumentationsquelle. Mehrfachlogger sollen **architektonisch möglich**, aber **nicht für den Erstausbau eingeplant** sein.

## 2. Begriffe strikt trennen

| Begriff | Beispiel | Nicht verwechseln mit |
|---|---|---|
| **Datenquellengruppe** | beelogger, Umweltsensoren, BEEP | Gerät oder Protokoll |
| **Gerät** | beelogger-Hardware, SenseCAP-Wetterstation, BEEP Base | Sensor oder Volk |
| **Physischer Sensor / Messwandler** | DS18B20, Wägezelle, integrierter Temperaturfühler | Feldname `TempIn` |
| **Technischer Kanal** | `TempIn`, `FeuchteIn`, `Aux2`, S2120-Payloadfeld | Physikalische Messgröße |
| **Kanalinterpretation** | `FeuchteIn` bedeutet in *dieser Konfiguration* Deckeltemperatur in °C | Generelle Definition aller `FeuchteIn`-Daten |
| **Messgröße** | Temperatur, rel. Feuchte, Gewicht/Masse, Windrichtung, RSSI | Displayname / Kanal |
| **Messposition** | Brutraum, Beutendeckel, Strahlungsschutz, Boden in 10 cm Tiefe | Übertragungskanal |
| **Messwert** | Zahl bzw. Rohinformation + Zeitstempel und Provenienz | Berechnungsergebnis |
| **Berechnete Größe** | korrigiertes Gewicht, Tageszunahme, Mittelwert | vom Sensor unverändert gelieferter Wert |
| **Imkerliches Ereignis** | Durchsicht oder Fütterung aus BEEP-Stockkarte | Messkanal |

**[VORSCHLAG]** Sensoren können als **austauschbare Einzelkomponenten** oder **integrierte und nicht einzeln identifizierbare Baugruppen** geführt werden. Wenn BEEP/API/Logger keine physische Sensor-ID liefern, bleibt diese Information **unbekannt**; keine erfundenen Sensor-IDs erzeugen.

## 3. Fachliche Tabellenkandidaten und Beziehungen

Die Namen sind Arbeitstitel, die Attribute exemplarisch. Bestehende Tabellen `apiaries`, `colonies`, `devices` und zeitliche Geräte-/Standzuordnungen stammen aus dem übergeordneten Entwurf.

| Tabelle (Vorschlag) | Schlüssel und wichtige Felder | Verantwortlichkeit |
|---|---|---|
| `devices` | `device_id`, `device_type`, `source_group`, `external_device_key?` | Physische/logische Geräteidentität, keine fest eingebaute Volk-ID |
| `sensor_components` | `sensor_id`, `device_id?`, `sensor_model?`, `serial_number?`, `replaceable` | Optional identifizierbare physische Sensoren/Messwandler; bei integriertem unbekanntem Sensor optional |
| `device_channels` | `channel_id`, `device_id`, `source_field_path`, `source_protocol`, `channel_key` | Technischer, im Eingang vorkommender Kanal – stabiler Anker für Rohwerte |
| `measurement_quantities` | `quantity_id`, `code`, `dimension`, `canonical_unit`, `value_kind` | Fachlicher Messgrößenkatalog; `value_kind` z. B. kontinuierlich, Winkel, Zähler, Ereignisindikator |
| `measurement_positions` | `position_id`, `apiary_id?`, `colony_id?`, `zone`, `depth_cm?`, `height_cm?`, `description` | Räumliche/biologische Messposition; Standort- oder Volkbezug mit Historie |
| `sensor_installations` | `installation_id`, `sensor_id`, `device_id`, `position_id?`, `valid_from`, `valid_to` | Physischer Sensor an Ort/Gerät im Gültigkeitsintervall; Austausch ohne Überschreiben |
| `channel_mappings` | `mapping_id`, `channel_id`, `quantity_id?`, `position_id?`, `sensor_id?`, `unit_in?`, `converter_version?`, `valid_from`, `valid_to`, `confidence/status` | Zeitlich gültige Interpretation: Feld `AuxX` bzw. `FeuchteIn` kann seine Bedeutung wechseln |
| `raw_records` | `raw_id`, `source_group`, `device_id?`, `external_event_id?`, `received_at`, `payload_ref/hash`, `import_batch_id` | Original-Quelle, unveränderter Eingang, Nachweis bei Duplikaten/Korrekturen |
| `raw_channel_values` | `raw_value_id`, `raw_id`, `channel_id?`, `field_path`, `literal_value`, `original_unit?` | Vor der Interpretation gespeicherter einzelner Quellkanal |
| `measurements` | `measurement_id`, `raw_value_id?`, `mapping_id`, `quantity_id`, `timestamp_utc`, `numeric_value?`, `unit`, `quality_status` | Normalisierter, nachvollziehbarer Wert; keine stillen Änderungen |
| `calibrations` | `calibration_id`, `sensor_id?`, `channel_id?`, `algorithm_version`, `parameters_ref`, `valid_from`, `valid_to` | Kalibrier- und Korrekturregel samt Gültigkeitszeit und Version |
| `derived_values` / `feature_values` | `derived_id`, `feature_definition_version`, `time_window`, `value`, `analysis_run_id?`, `input_ref` | Berechnete Werte separat von direkt gemessenen Werten speichern |

**[VORSCHLAG]** Fachliche Kardinalitäten: ein Gerät hat 0..n Kanäle und 0..n bekannte Sensor-Komponenten; ein Kanal hat über die Zeit 0..n **nicht überlappende** Mappings; ein Sensor kann im Lauf der Zeit mehrere Installationen besitzen. Ein Rohdatensatz enthält 0..n Rohkanalwerte; aus einem Rohwert können mehrere **versionierte** Auswertungen entstehen. `raw_channel_values` und `measurements` müssen auch unbekannte/nichtnumerische oder fehlerhafte Eingänge nachvollziehbar behandeln können.

**Offene Normalisierungsentscheidung:** Soll eine Interpretation *zwingend* genau eine Messgröße liefern, oder dürfen Quellfelder (z. B. Statusbits) fachlich mehrere interpretierte Ergebnisse erzeugen? Der Vorschlag nutzt eine eigene Interpretation/Transformationsschicht und erlaubt damit spätere Aufspaltung.

## 4. Beispiele aus dem bestehenden Projekt, die das Modell begründen

| Eingang/Fall | Tatsächlich dokumentiert | Konsequenz fürs Modell |
|---|---|---|
| LoRa-Single `FeuchteIn` | **[QUELLBEFUND]** Bei einer bekannten beelogger-Konfiguration wird ein zweiter DS18B20 über den Feuchtekanal übertragen; das LoRa-Feld ist `uint8` und verliert Nachkommastellen/negative Werte ([Datenformat](../datenformat.md)) | `source_field=FeuchteIn` bleibt erhalten; `quantity=temperature` nur bei passender, gültiger Gerätekonfiguration; Präzisionsverlust als Qualitäts-/Transformationshinweis |
| LoRa-M.40 `Aux2` | **[QUELLBEFUND]** Der Standard-LoRa-Weg des M.40 setzt die CSV-Spalte `Aux2` auf RSSI statt das gleichnamige JSON-Feld durchzureichen ([Serveranalyse](../server-analyse.md)) | Technischer **Verarbeitungspfad** und Kanalversion gehören zur Provenienz; CSV-Spaltenname allein ist unzureichend |
| LoRa-M.40 `Aux3` | **[QUELLBEFUND]** Derselbe Pfad vermischt Sketch-ID und Hilfskanal; eigener LoRa-Eingang legt Sketch-ID separat in `lora_zusatz.csv` ab ([Serveranalyse](../server-analyse.md), [LoRa-Eingang](../../server/lora/README.md)) | Sketch-/Firmwarekennung nicht als physikalischen Messwert klassifizieren |
| `Gewicht` roh/korrigiert | **[QUELLBEFUND]** In der M.40-Single-CSV existieren getrennte Spalten für korrigiertes und rohes Gewicht ([Serveranalyse](../server-analyse.md)) | Werte getrennt führen; Korrektur-/Algorithmusprovenienz nach Möglichkeit erfassen, nicht unbemerkt denselben Datenpunkt überschreiben |
| `TempOut` und Gewichtskorrektur | **[QUELLBEFUND]** M.40 nutzt bei LoRa `TempOut` als Näherung für Wägezellentemperatur; im dokumentierten Aufbau ist es die BME280-Außentemperatur ([Serveranalyse](../server-analyse.md)) | Sensorposition, tatsächliche Messgröße und verwendete Näherung dokumentieren; keine „Wägezellentemperatur“ aus der Quellenfeldbezeichnung behaupten |
| Neue v2-Funkfelder | **[QUELLBEFUND]** Format v2 kann `TempIn2` und mehrere Gewichtskanäle mit eigenen Bitpositionen abbilden ([Funkformat v2](../funkformat-v2.md)) | Mapper nach Payload-/Formatter-/Serverversion; nicht pauschal aus dem Single-M.40-Verhalten extrapolieren |
| Wetterstation | **[BESTÄTIGT]** Umweltquelle mit Temperatur, Windrichtung, Regen usw. | Ein Gerät kann viele Messkanäle haben; Messposition/-höhe pro Messgröße ggf. verschieden |
| Bodentemperatur | **[BESTÄTIGT]** Als weiterer Umwelt-Sensortyp gewünscht | `position=soil`, `depth_cm` sowie ggf. horizontale Lage und Standort-Zeithistorie |
| BEEP Base | **[BESTÄTIGT]** Alternative Stockmesstechnik; Daten liegen bei BEEP | Herkunft `BEEP` erhalten; Feldabbildung der BEEP-API erst nach Zugriff/Prüfung definieren, **nicht** aus beelogger-Namen ableiten |

**Wichtig:** Aussagen zum beelogger-M.40-Standardweg gelten nicht automatisch für den eigenen `server/lora/`-Eingang. Die Dokumente beschreiben verschiedene Verarbeitungspfade und teils noch offene Feldprüfungen. Das produktiv eingesetzte Mapping ist später gegen echte Konfiguration/Daten zu prüfen.

## 5. Zeitmodell, Sensorwechsel und Kalibrierung

1. **[VORSCHLAG]** Alle Gültigkeitsintervalle als `[valid_from, valid_to)` in UTC; `valid_to = NULL` bedeutet offene Installation/Konfiguration. Der **Messzeitpunkt** entscheidet, welche Interpretation anzuwenden ist – nicht der Zeitpunkt des Imports.
2. **[VORSCHLAG]** Externe Daten erhalten gesondert Quellzeit (`source_time`), empfangene Zeit (`received_at`), importierte Zeit (`imported_at`) und Qualität/Unsicherheit des Zeitstempels. Bekannte Sommer-/Winterzeit-Probleme in M.40 nicht durch bloße UTC-Umbenennung kaschieren.
3. **[VORSCHLAG]** Sensortausch schließt die alte `sensor_installations`-Zuordnung und eröffnet eine neue; bisherige Messwerte werden nicht auf den Ersatzsensor umgebucht.
4. **[VORSCHLAG]** Änderungen von Kanalbedeutung, Messposition, Skalierung, Firmware-/Formatter-Zuordnung und Kalibrierung werden **versioniert**, nicht rückwirkend überschrieben. Neue Interpretationen dürfen als neue Revisionen alter Daten entstehen.
5. **[VORSCHLAG]** Kalibrierung und Messwertkorrektur unterscheiden zwischen Rohwert, *auf Geräteebene bereits korrigiertem Quellenwert* und zusätzlicher eigener Korrektur. Der Ursprung jeder Stufe muss erkennbar sein.
6. **[VORSCHLAG]** Fehlende, abgeschnittene, unplausible, gesättigte oder falsch skalierte Werte erhalten Qualitätshinweise; `0` ist nicht Ersatz für „kein Messwert“.

## 6. Besonderheiten physikalischer Messgrößen

- **Temperatur:** Messposition, Sensortyp, Medium (Stockluft, Außenluft, Boden), Tiefe/Höhe, °C; ein Kanalname wie „innen“ genügt nicht.
- **Stockgewicht:** Roh-/korrigierter Wert, Tarierung, Nullpunkt, Gerätewechsel und ggf. Position/Anzahl Wägezellen; absolute Masse nicht mit Tagesänderung verwechseln.
- **Luftfeuchtigkeit:** Relative Feuchte (%) ist eigene Messgröße; beelogger-`FeuchteIn` darf aufgrund dokumentierter Umnutzung nicht blind so interpretiert werden.
- **Niederschlag:** Intensität (mm/h), Intervallmenge (mm) und kumulierter Zählerstand sind unterschiedliche Größen mit unterschiedlichen Aggregationsregeln; Zählerreset beachten.
- **Wind:** Richtung (Grad, zirkulär), Geschwindigkeit (m/s) und Böe (m/s) getrennt; Windrichtungen nicht unbesehen arithmetisch mitteln, Windrose aus sektorisierten Häufigkeiten.
- **Bodenmessungen:** Tiefe und räumliche Position sind Teil des Messkontexts; Sensoren können am gleichen Stand in mehreren Tiefen vorkommen.
- **Telemetrie:** RSSI, SNR, Batteriespannung, Firmwarekennung und Statusbits werden als **technische Zustands-/Metadaten** eingeordnet, nicht als biologische Beobachtung. Einige technische Größen sind numerisch und zeitabhängig, aber keine Umwelt-/Stockmessung.

## 7. Verbindung zu Analyse und öffentlicher Visualisierung

**[BESTÄTIGT]** Ein- und mehrvolkige, auch standübergreifende Analysen benötigen korrekt zugeordnete Messgrößen; berechnete Kennzahlen und Modelloutputs sind eigenständige Datenobjekte. Apache ECharts ist für die neue Visualisierung gewählt.

**[VORSCHLAG]** Die Analyse-Engine fragt standardisierte `quantity_id`/Einheiten und zulässige Positionen ab, nicht `FeuchteIn`/`Aux2` als vermeintlich fachliche Namen. Für jeden Feature-Wert werden Input-Versionen, Qualitätsfilter, Fenster, Berechnungsversion und betroffene Völker/Stände verzeichnet.

**[VORSCHLAG]** Der öffentliche Bereich erhält ausschließlich **freigegebene** Reihen/Features mit erklärter Herkunft und Qualität; sensible Sensor-/Standortkoordinaten bleiben intern.

## 8. Prüfszenarien vor Umsetzung (Akzeptanzfälle, noch nicht ausgeführt)

1. Ein physischer beelogger liefert `TempIn` und `FeuchteIn`; letztere wird in einem Zeitraum als **Temperatur** dekodiert, in einem anderen (nur wenn wirklich konfiguriert) als **relative Feuchte**. Beide Historien bleiben korrekt.
2. Ein physischer DS18B20 wird ersetzt, derselbe logische Kanal bleibt; Messwerte vor/nach Wechsel bleiben den richtigen Sensoren zugeordnet.
3. Eine Wetterstation liefert Temperatur, Feuchte, Windrichtung, Windgeschwindigkeit und Regen mit unterschiedlichen Aggregationssemantiken; ein Gerätesatz ergibt mehrere Messreihen.
4. Eine Bodenstation liefert zwei Tiefen, z. B. 5 cm und 20 cm; beide werden getrennt gefunden und visualisiert.
5. Ein beelogger-Feld `Aux2` wird unter M.40-Standard-LoRa als RSSI interpretiert; unter dokumentiertem eigenen Eingangsweg als konfigurierte andere Größe – abhängig von Pfad und Gültigkeitszeit.
6. Rohes und bereits serverseitig korrigiertes Stockgewicht werden **nicht** unter derselben „Roh“-Semantik zusammengeworfen.
7. Ein Datenwert trifft nach einem Sensorwechsel verspätet ein; Zuordnung geschieht anhand des **tatsächlichen Messzeitpunkts** (bei zweifelhafter Zeit mit Qualitätskennzeichen), nicht der Importzeit.
8. Eine BEEP Base liefert Werte mit zunächst unklarer physischer Sensoridentität; Import bewahrt die BEEP-Kennungen, ohne Hardwaredetails zu erfinden.
9. Eine Clusteranalyse über Völker aus verschiedenen Ständen bezieht nur fachlich kompatible normalisierte Größen ein; Features behalten ihre Eingangszuordnung und Versionsinformation.
10. Ein als privat markierter Umweltmesspunkt erscheint weder mit Koordinaten noch mit Roh-Metadaten im öffentlichen Export.

## 9. Offene Entscheidungen, die *vor* SQL geklärt werden müssen

1. **[OFFEN]** Welche beelogger-Sensoren/Kanalbelegungen sind in den konkret eingesetzten Loggern tatsächlich konfiguriert? (Firmwarestände, Aux-Zuordnung und Ein-/Duo-Typ nicht aus Beispielen ableiten.)
2. **[OFFEN]** Wie wird die tatsächliche **Konfiguration zum Messzeitpunkt** dokumentiert oder bei fehlender Historie rekonstruiert?
3. **[OFFEN]** Welche Sensoren sind einzeln identifizierbar, welche integrierte/undurchsichtige Gerätekanäle? (BEEP-API-Feldkatalog noch zu prüfen.)
4. **[OFFEN]** Sollen Positionen (Brut/Deckel/Boden) als freie Taxonomie, standardisierte Codes oder eine Kombination geführt werden?
5. **[OFFEN]** Wie werden Kalibrierung, Tara, Messunsicherheit und Korrekturformeln je Sensortyp versioniert und geprüft?
6. **[OFFEN]** Welche Quellzeiten und Zeitqualitäten sind pro Datenweg verfügbar? (M.40-DST-Fall beachten.)
7. **[OFFEN]** Welche fachlichen Mengen-/Zählerkonventionen und Aggregationen sind je Umweltsensor gültig?
8. **[OFFEN]** Technische Wahl: eigenständige Tabellen für `sensor_components` und `channel_mappings` im ersten SQL-Schema oder schrittweise Einführung – ohne Verlust an Semantik und Rückverfolgbarkeit.
9. **[OFFEN]** Der spätere Mehrfachloggerfall bleibt **nur Erweiterungsfähigkeit** und wird nicht als aktiver Betriebsfall behauptet.

## 10. Quellengeprüfter Kanal-Inventarstand

Die erste Schnittstellen-Bestandsaufnahme wurde in [**Messgrößen- und Kanal-Inventar 0.1**](messgroessen-kanalinventar.md) und [**maschinenlesbarer CSV**](messgroessen-kanalinventar.csv) dokumentiert. Die vollständige tatsächliche Belegung der produktiven Hardware ist **noch nicht verifiziert**; BEEP-Base-Exportfelder sind bewusst **nicht erfunden** worden.

## 10. Nächster Architektur-Schritt

Vor Datenbank-Installation oder Migration: aus diesem Konzept ein **konkretes Kanal-Inventar je vorhandener Geräte- und Softwarekonfiguration** erzeugen und die Abbildung `Quellfeld → Kanal → Messgröße → Messposition → Einheit → Zeitgültigkeit` durchgehen. Erst danach das ER-Diagramm mit Kardinalitäten/Constraints und die SQL-DDL entwerfen.

**Kein** Produktiveingriff, **kein** Laufzeittest, **keine** BEEP-Schnittstelle implementiert und **keine** allgemeine Verifikation aller Sensorfelder beansprucht.
