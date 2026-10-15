# Bienenlogger – Konzeptfortschreibung v0.4

**Stand:** 15. Oktober 2026  
**Status:** Fachkonzept / vorgeschlagene Architektur, keine implementierte Schnittstelle. Die Formulierung zu primären Stockmesssystemen wurde mit den bestätigten Bestandsanforderungen im Repository harmonisiert.

## 1. Ausgangslage und verbindliche Grundsätze

Am 14. Oktober 2026 wurde laut Projektmeldung die Datensammlung von **drei Bodentemperatur-Messungen** erfolgreich gestartet. Noch offen sind Einbauorte und -tiefen, Messintervalle, Sensortypen, Gerätezuordnung und Datenformat. Diese Details dürfen nicht als bekannt vorausgesetzt werden.

Die Plattform enthält vier Bereiche: (A) Bienenstand-Dashboard, (B) Volk-Cockpit mit Stockkarte und Ereignislinien, (C) Wetter, Boden, Tracht und Flugkreise, (D) Vergleich und Analyse. Sie nutzen eine gemeinsame Datenarchitektur.

- **BEEP bleibt bis zum definierten Migrationszeitpunkt führend** für die bestehenden Völker, Beuten, Checklisten, Durchsichten und dokumentierten Eingriffe. Eigene Umweltmessungen werden bereits unabhängig gespeichert.
- Biologisches Volk (`Colony`), physische Beute (`Hive`), Stand/Umweltmessstelle (`Apiary`/`MeasurementSite`) und Messgerät (`Device`) sind getrennte Objekte.
- Ein Volk besitzt eine eigene, bleibende ID; Ableger erhalten neue IDs und eine dokumentierte Herkunft. Eine Beute darf gleichzeitig maximal von einem Volk bewohnt sein.
- Geräte und Messkanäle sind optional. Im bestätigten Normalfall hat ein Volk kein oder genau ein primäres Stockmesssystem (beelogger ODER BEEP Base); Umweltmessquellen bleiben davon unabhängig. Zukunftsfähige Mehrfachsysteme sind nicht Teil des Erstumfangs. Kein Messkanal wird hart als feste Position in der Datenbank codiert.
- Rohmessungen, Qualitätsmerkmale, abgeleitete Kennzahlen und interpretierte Zustände bleiben getrennt und nachvollziehbar.

## 2. Erweiterungen der vier Bereiche

### A. Bienenstand-Dashboard

- Umschaltbar zwischen Kachel- und Listenansicht mit BEEP-inspiriertem Beutensymbol.
- Pro Volk: verfügbare Messwerte (z. B. Gewicht, Gewichtsänderung, Stocktemperatur, Feuchte, Akustik), Bio-Status aus Stockkarte und eigener Technik-/Datenqualitätsstatus.
- Wetter-/Umweltkarte pro Stand: Lufttemperatur, drei Bodentemperaturen, Niederschlag, Wind, Datenaktualität, GTS, optional weitere Kennzahlen.
- Fehlende Messdaten als „nicht verfügbar“, nicht als negatives Volkssignal anzeigen.

### B. Volk-Cockpit

- Synchronisierte Zeitachse für Stockmessungen, Umweltmessungen und BEEP-Stockkartenereignisse.
- Maßnahmen als anklickbare Symbole und senkrechte Referenzlinien; Start/Ende für länger dauernde Ereignisse.
- Unabhängige Skalen oder separate Diagrammspuren für physikalisch verschiedene Messgrößen.
- Vorher-/Nachher-Fenster, Quellen- und Qualitätsindikatoren; keine automatische Kausalitätsbehauptung.
- Zeitaufgelöste Zuordnung von Messwerten zu Volk/Beute anhand der jeweils gültigen Geräte- und Beutenhistorie.

### C. Wetter, Boden, Tracht und Flugkreise

- Drei eigenständige Bodenmesskanäle, ohne Annahme gleicher oder unterschiedlicher Tiefen.
- Kurven in 24-Stunden-, 7-Tage-, 30-Tage- und frei wählbaren Ansichten.
- Tagesminimum/-maximum/-mittel je Kanal; bei ausreichender zeitlicher Auflösung Froststunden und Boden-Luft-Differenzen.
- GTS ausschließlich aus Lufttemperatur nach der gewählten und dokumentierten Konvention. Die Bodenmessungen ergeben **keine klassische GTS**.
- Karte: Standkoordinaten, individuell einstellbare theoretische Flugradien und georeferenzierte potenzielle Trachtflächen. Potenzielle Tracht ist kein Nachweis tatsächlichen Sammelns.
- Phänologische Beobachtungen separat erfassen: Pflanzenart, Zeitpunkt/Zeitraum, Standort, Blühphase, Beobachter/Quelle.

### D. Vergleich und Analyse

- Bodentemperatur-Verläufe zwischen den drei Kanälen (Tiefen- oder Lagevergleich nach bestätigter Montageinformation).
- Vergleich Boden vs. Luft, Wetter vs. Stockgewicht/Flugindikatoren, Vorher-/Nachher-Vergleiche mit Checklistenereignissen.
- Später standortübergreifende Analysen; Konfundierung durch Standort, Vegetation, Messhöhe/-tiefe, Sensordatenqualität berücksichtigen.
- Erst robuste Statistik/Regeln, später bei genügend validierten Daten komplexere Modelle und KI.

## 3. Vorschlag für minimale Entitäten

| Entität | Pflichtinformationen / Zweck |
|---|---|
| `Apiary` | Standort-ID, Koordinaten, Zeitzone, Bezeichnung |
| `MeasurementSite` | Umweltmessplatz, optional verknüpfter Stand, Koordinaten/Mikrostandort |
| `Device` | Stabile interne ID, Hersteller, Modell, externe ID, Transport/Protokoll |
| `MeasurementChannel` | Kanal-ID, Device-ID, Messgröße (`soil_temperature` etc.), Standard-Einheit, physischer Sensor |
| `ChannelInstallation` | Kanal-ID, Messstelle, gültig von/bis, Einbautiefe in cm nullable, Position, Bewuchs, Beschattung, Methode |
| `Observation` | Kanal-ID, `measured_at_utc`, `received_at_utc`, Wert, Einheit, Qualität, Quell-/Nachrichtenkennung |
| `RawIngestEvent` | Unveränderte Payload, Übertragungsmetadaten, Empfangszeit, Parser-/Decoder-Version |
| `DerivedMetric` | Rechenmethode und Version, Zeitraum, Quellenkanäle, Wert, Vollständigkeitsstatus |
| `ColonyEvent` | Volk, Kategorie, tatsächlicher Ereigniszeitpunkt/Intervall, BEEP-Quell-ID, Inspektion/Checkliste |

**Schutz vor Duplikaten:** Eindeutiger Idempotenzschlüssel pro Ursprungspaket oder definierte Kombination aus Kanal, gemessener Zeit und Quellsequenz; Duplikate erkennen, nicht unbemerkt überschreiben.  
**Zeitzonen:** UTC in Speicherung, Anzeige nach Standort-Zeitzone; gemessene und empfangene Zeit getrennt halten.  
**Einheit:** Bodentemperatur standardisiert als °C; Rohwerte und Umrechnung dokumentieren.  
**Datenlücken:** Fehlende Zeitpunkte sind Lücken, nicht automatisch Nullwerte oder interpolierte Messungen.

## 4. Berechnete Umweltgrößen – geplantes Minimum

1. `soil_temperature_daily_mean/min/max` je Kanal; Qualität abhängig von Mindestabdeckung und Intervall.
2. `soil_air_temperature_difference` bei zeitlich sauberer Synchronisierung und dokumentiertem Luftsensorstandort.
3. `soil_temperature_daily_amplitude` = Tagesmaximum – Tagesminimum.
4. `soil_frost_duration` = Zeit unter 0 °C (nur bei genügend hoher und gesicherter zeitlicher Auflösung).
5. `soil_depth_gradient` und zeitlicher Nachlauf **nur**, wenn verschiedene Einbautiefen tatsächlich bestätigt wurden.
6. `GTS` (Grünlandtemperatursumme) aus positiven Tagesmittelwerten der **Lufttemperatur** ab Jahresbeginn, Januar × 0,5, Februar × 0,75, ab März × 1,0; Datenlücken und Messhöhe dokumentieren. Quelle: Forschungszentrum Jülich, https://www.fz-juelich.de/de/gs/ueber-uns/meteo/klimastation/gruenlandtemperatursummen.
7. Optional: Boden-Wärmesumme nach ausdrücklich definierter Basistemperatur und Pflanzen-/Fragestellung, **nicht** als GTS bezeichnen.

## 5. Oberfläche: Wetter-/Bodenmodul

- Kopfzeile: Wetterstation/Umweltmessstelle, Alter letzter Messung, Verbindungs- und Qualitätszustand.
- Kennzahlen: Lufttemperatur, Bodentemperatur Kanal 1/2/3, GTS, Niederschlag.
- Hauptchart: drei Bodenkanäle gleichzeitig in °C; Lufttemperatur optional; gemeinsame Zeitachse, Cursor, Zoom, Datenlücken erkennbar.
- Detail: Installationstiefe/Position und Historie per Klick auf Legende oder Kanal.
- „Vergleichen mit Volk“: Ergänze Gewichtsverlauf eines auswählbaren Volkes mit separater Y-Achse/Spur und Stockkartenereignislinien.
- Karte: Flugkreise und Trachtlayer als unabhängig schaltbare Ebenen.

## 6. Migration und Parallelbetrieb

**Phase 1:** BEEP-Völker, Durchsichten und Checklisten nur lesen; eigene Messwerte von Wetterstation, Bodenfühlern und Loggern direkt speichern.  
**Phase 2:** Historische Daten importieren, Zuordnungen und Zeitstempel prüfen; UI mit echten Daten testen.  
**Phase 3:** BEEP Base testweise über kontrollierte TTN-Anbindung parallel empfangen, Rohdaten und BEEP-Werte abgleichen.  
**Phase 4:** Eigene Checklisten/Stockkarte auf funktionale Gleichwertigkeit prüfen, erst danach führende Quelle umschalten.  
**Phase 5:** BEEP nach Vollständigkeits-, Backup-, Geräteempfangs- und Wiederherstellungstests auslaufen lassen.

## 7. Nächste überprüfbare Arbeitspakete

- [ ] Zu den drei Bodensensoren Tiefe/Position, Sensortyp, Messintervall, Quelle/Übertragungsweg und Beginn dokumentieren.
- [ ] Erste echte Datensätze sicherstellen, Rohformat, Zeitstempel, IDs, Einheiten und fehlende Werte prüfen.
- [ ] Gemeinsames Schema für Messstelle, Geräte, Kanalinstallation und Beobachtungen festlegen.
- [ ] Graph für drei Bodentemperaturen und Lufttemperatur mit gemeinsamen Zeitachsen prototypisch aus Echtdaten aufbauen.
- [ ] GTS-Berechnung separat mit vollständigen Lufttemperatur-Tagesmitteln umsetzen.
- [ ] BEEP-Import-Mapping / Zeitstempel- und Ereignismodell mit dem Messdatenschema verbinden.
- [ ] Backup, Datenvollständigkeit und Wiederherstellung automatisiert prüfen.

## 8. Offene Sachfrage

Sind die drei Bodentemperatur-Messungen an **unterschiedlichen Bodentiefen**, an **verschiedenen Orten** oder in einer **Kombination** davon installiert? Die Datenstruktur unterstützt alle Varianten; erst danach kann die wissenschaftliche Interpretation korrekt festgelegt werden.

## 9. Geltungsbereich des vorhandenen Firmware-Testarchivs

Das bereitgestellte Archiv `ZS_Test_261008.zip` beschreibt einen STM32-LoRa-Zeitsynchronisationstest (08.10.2026), nicht die neue Bodensensorinstallation. In dessen `Config_MULTI.h` ist beispielhaft `Anzahl_Sensoren_DS18B20 1` konfiguriert. Daraus darf weder auf den Sensoraufbau noch auf den Datenempfang der drei nun laufenden Bodentemperaturen geschlossen werden. Die README nennt reale TTN-Hardwaretests als noch offen – Messzeitqualität bleibt deshalb ein expliziter Integrationspunkt.