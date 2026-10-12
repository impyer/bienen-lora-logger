# Fachmodell: biologisch relevante Messgrößen am und im Bienenvolk

**Stand:** 12.10.2026 · **Version:** 0.1 · **Status:** FACHLICHER ENTWURF – nicht als SQL-Schema freigegeben  
**D0 / T0:** Dokumentationsentwurf auf Basis der Betreiberkorrektur und zitierter Fachliteratur; keine Firmware-, Hardware-, Datenbank- oder Feldtests.  
**Maßgebliche Richtungsentscheidung:** **[BESTÄTIGT]** Die Datenbank ist **allgemeingültig nach Messgrößen, Messkontext, Zeit und biologischen Fragestellungen** zu gestalten. Die konkrete Sensorbelegung von `beelogger1` oder irgendeinem anderen Gerät ist **keine Voraussetzung und kein Entwurfstreiber**. Sie kann sich jederzeit ändern.

**Quelle der Korrektur (12.10.2026):** „Die Sensorbelegung von beelogger1 ist nicht relevant, es sollte allgemeingültig gebaut sein, da es sich auch ändern kann. Betrachte besser, welche Messwerte am und im Bienenvolk wichtig sind. Also z.B. Gewicht, Temperatur, Feuchte und Schallwellen.“

**Leseregel:** [BESTÄTIGT] Betreiberanforderung; [VORSCHLAG] fachlicher/technischer Architekturvorschlag; [FORSCHUNG] methodisch gestütztes Untersuchungsfeld **ohne** garantierte Diagnosesicherheit; [OFFEN] weitere gemeinsame Entscheidung. Angaben über einen tatsächlich verbauten Sensor, verfügbaren Kanal oder bereits laufende Analyse sind **nicht** aus diesem Dokument abzuleiten.

## 1. Leitmodell: Vom biologischen Untersuchungsgegenstand zur Quelle

```text
Bienenvolk (biologische Identität und Lebenszyklus)
    ↕ gültige Zeitbeziehungen zu Beute, Bienenstand und Gerätezuordnungen
Beute / Messumgebung (physische Konstruktion und Einbau-/Messposition)
    ↓
Biologisch relevante Messgröße + Messkontext (Ort, Medium, Höhe/Tiefe)
    ↓
Messreihe / Beobachtungsfenster (Zeitpunkt, Zeitspanne, Methode, Einheit, Qualität)
    ↓
Quellabbildung (beelogger, BEEP Base, unabhängiger Sensor oder andere Geräte)
    ↓
Rohdatensatz → standardisierter Wert / Signal → abgeleitetes Feature
    ↓
Analyselauf → vorsichtig formulierte biologische Interpretation / Hypothese
```

**[VORSCHLAG]** Die Datenbank sollte die physische **Beute** optional von der biologischen **Volk-Identität** trennen. Eine Stockwaage wiegt normalerweise **Beute samt Material, Bienen, Brut, Vorräten und ggf. wetterbedingten Zusatzlasten**, nicht die reine Bienenmasse; ein Volk kann außerdem umziehen, aufgeteilt oder vereinigt werden. `hives` / `colony_hive_assignments` sind daher **zu prüfende zusätzliche Entitäten**, kein bereits beschlossener Ausbau.

**[BESTÄTIGT]** Die drei Datenquellengruppen bleiben unverändert: beelogger; Umweltsensoren; BEEP (BEEP Base als Alternative zu beelogger und digitale Stockkarte als unabhängige Dokumentationsquelle). Sie sind **Lieferwege**, nicht die fachliche Definition der Messgröße.

## 2. Kernbereiche der Beobachtung

| Prioritätsbereich | Primäre Größe | Einheiten | Relevanter Kontext | Anregungen für wissenschaftlich prüfbare Features |
|---|---|---|---|---|
| **Gewicht / Masse** | Masse der gesamten bewohnten Beute | kg | Welche Beute und Volk-Zuordnung? Tara, Waagenmontage, Gerätewechsel, Witterung, imkerlicher Eingriff | Nettoänderung je Zeitfenster, Tagesamplitude, Trends, sprunghafte Änderungen, Verhältnis zu Wetter und Stockkartenereignissen |
| **Temperatur** | Lokale Temperatur im Brutbereich / Brutraum / Deckel / an der Außenwand / außen | °C | Exakte Position, Höhe, Abstand zur Brut, Medium, Saison, Aufstellung | zeitliche Mittel und Extrema, Amplitude, Trend, Innen–Außen-Differenz, Gradienten zwischen Positionen, Stabilität, zeitliche Änderungsrate |
| **Relative Luftfeuchte** | Relative Feuchte im Innenraum oder an weiteren Punkten | % RH | Temperatur am selben Ort, Messposition, möglicher Kondensationsbereich, Sensorfehler | Innen–Außen-Differenz, Tagesgang, Feuchtetrends, zusammen mit Temperatur berechneter Taupunkt / Wasserdampfdruck |
| **Luftschall / akustische Wellen** | Mikrofon-Zeitsignal oder definiertes kurzes Aufnahmesegment | z. B. digitale Samples; nach Kalibrierung ggf. Pa oder dB SPL | innen/außen, Mikrofonposition, Frequenzgang, Pegelkalibrierung, Abtastrate, Aufnahmedauer, Störquellen | Signal-RMS, Bandenergien, dominierende Frequenz, Spektralform, zeitliche Entwicklung, Erkennung *hypothetischer* Ereignismuster |
| **Körperschall / Vibration** | Vibration einer Wabe, eines Rähmchens oder der Beutenstruktur | z. B. m/s²; Spektralgrößen | Achse, Sensorankopplung, Befestigungsposition, Beschleunigungssensor und Frequenzgang | Spektralbandenergien, frequenzabhängige Vibration, zeitliche Signatur, mögliche Schwarm-/Königinnen-bezogene Muster |

**[BESTÄTIGT]** Gewicht, Temperatur, Feuchte und Schallwellen sollen als **fachlich bedeutende Grundgrößen** im allgemeinen Datenmodell berücksichtigt werden. **[VORSCHLAG]** Die gesonderte Klasse `vibration` wird als Erweiterung von „Schallwellen“ berücksichtigt: Mikrofone und Beschleunigungssensoren sind physikalisch nicht gleichwertige Quellen.

Die genannten **Features sind mögliche Forschungsfragen, nicht gemessene Diagnosen**. Temperatur allein beweist beispielsweise weder vorhandene Brut noch fehlende Königin; akustische Signale allein belegen nicht zuverlässig, dass ein Schwarm unmittelbar bevorsteht. Modelle brauchen validierte Labels, Vergleichsdaten, jahreszeitliche Einordnung und unabhängige Evaluierung.

## 3. Tiefe je Kernbereich

### 3.1 Gewicht: die physikalische Basis sauber definieren

- **Primärer Messwert:** `hive_mass_total` als kg, gemessen an einer Waage **unter einer konkreten Beute**; zur späteren Zuordnung wird geprüft, welches Volk zum Messzeitpunkt darin war.
- **Kein unzulässiger Schluss:** `hive_mass_total` ist **weder** Honigvorrat noch Futtermenge, Bienenmasse oder Trachteintrag. Solche Größen lassen sich höchstens mittels Zusatzinformationen/Modellen **schätzen**.
- **Kontext:** Waagentyp, Belastungs-/Kalibrierstatus, Tara, Wägezellentemperatur, Beute-/Zargenkonfiguration, Austausch und Zeitpunkte von Honigernte, Fütterung, Umstellen/Zargenwechsel aus der Stockkarte.
- **Rechenwerte:** `mass_delta_1h`, `mass_delta_24h`, `intraday_amplitude`, `mass_change_rate`, saisonaler Trend usw. jeweils **definierte Funktion** von Zeit, Datenqualität und Zustand.
- **FORSCHUNG:** Trachtphasen und unterschiedliche tageszeitliche Gewichtsverläufe lassen sich unter Umständen erkennen; Wind/Regen, Eingriffe und Aus-/Einflugbewegungen beeinflussen die Messkurve. Quelle: Meikle & Holst (2015), Liu & Lin (2025).

### 3.2 Temperatur: mehrere Positionen sind unterschiedliche Beobachtungen

- **Ein physikalischer Messgrößentyp `temperature`,** aber Messreihen mit eigener `position` (Brutraum, zwischen Rähmchen, Deckelraum, Beutenwand, Außenluft, optional Wägezelle/Elektronik).
- **Brutnest-Temperatur ≠ beliebige „Innentemperatur“:** Für die biologische Interpretation muss bekannt sein, **wo** der Sensor liegt; ein Sensor im Deckelbereich hat andere Aussagekraft als ein Sensor im Brutnest.
- **Rechenwerte:** `temperature_delta_inside_outside`, `temperature_gradient_by_position`, Tagesvariabilität und zeitliche Stabilität; Klima-/Standkontext über Umweltmessstellen.
- **FORSCHUNG:** Temperaturmuster können über Brutaktivität, Jahresphase und Thermoregulation informieren; ohne Position und weitere Daten sind Schlussfolgerungen unsicher. Quellen: Meikle & Holst (2015), Meikle et al. (2016), Deutscher Datensatz 2019–2022.

### 3.3 Luftfeuchtigkeit: Kopplung an Temperatur erhalten

- **Messgröße `relative_humidity` (% RH)** mit Messposition/Medium, Messgenauigkeit und Zeit. Ein Quellfeld namens `FeuchteIn` ist **nicht** per se ein Feuchtesensor.
- **Wichtig:** Relative Feuchte ist temperaturabhängig. Taupunkt bzw. absolute Feuchte sind **abgeleitete Größen** und brauchen zeitlich/räumlich passende Temperatur- und Feuchtemessungen sowie eine Berechnungsdefinition.
- **FORSCHUNG:** Feuchtigkeitsregulation und Feuchteverläufe im Stock lassen sich explorativ untersuchen; aus relativer Feuchte allein keine Diagnosen zu Brut, Krankheit oder Honigreife ableiten.

### 3.4 Schallwellen: ein eigener Signal-Datentyp ist erforderlich

Ein **digitalisiertes Mikrofonsignal** ist **keine** gewöhnliche numerische Messreihe mit einem Wert je 15 Minuten. Wir unterscheiden daher:

| Ebene | Beispiele | Erforderliche Metadaten |
|---|---|---|
| **Signalquelle** | Mikrofon innen / Mikrofon am Flugloch | Sensorart, Position, Schallpfad, Frequenzgang, Verstärkung |
| **Messsegment** | Signal über 2 s oder 30 s | Beginn/Ende, Samplezahl, Hz-Abtastrate, Anzahl Kanäle, Bitauflösung, Kalibrierzustand |
| **Signalverarbeitung** | Vorfilter, Fensterung, FFT/STFT, Spektrogramm | Algorithmus-/Codeversion, Filterbänder, Fensterlänge, Überlappung, Skalierung, Normalisierung |
| **Spektral-/Zeitmerkmale** | RMS, Peakfrequenz Hz, spektrale Energie in Hz-Bändern, ZCR, spektraler Schwerpunkt | Merkmalsdefinition, Frequenzgrenzen, Einheiten, Zeitfenster, Provenienz |
| **Biologisches Analyseergebnis** | „Muster ähnlich dokumentierter Schwarmphase“ | Modellversion, Zielklasse, Score/Konfidenz, Labelgrundlage, Fehlerrate, Validierung |

**Akustik ≠ Vibration:** Luftschall kann mit Mikrofonen, Strukturvibration mit Accelerometern erfasst werden. Bei einem 2020 publizierten Schwarmprädiktionsansatz wurden **Beschleunigungssensoren** im Stock eingesetzt; Resultate sind nicht 1:1 auf einen Mikrofonkanal übertragbar.

**Pegel korrekt benennen:** Ein FFT-Merkmal in **dBFS** (digitaler Vollaussteuerungsbezug) ist nicht automatisch Schalldruckpegel in **dB SPL**, und ein **relativer** Peakwert ist keine kalibrierte physikalische Lautstärke. Einheit und Verarbeitungsmethode sind obligatorisch; Schallleistung/RMS und FFT-Amplitude dürfen nicht miteinander verwechselt werden.

**Abtastphysik:** Samplerate, nutzbare Bandbreite, Anti-Aliasing, FFT-Auflösung und Segmentlänge müssen explizit gespeichert werden. Eine Peakfrequenz ohne diese Informationen kann nicht belastbar verglichen werden.

**Speicherung:** **[VORSCHLAG]** Spektral-/Statistikfeatures als strukturierte Zeitreihen in PostgreSQL; **optionale Roh-Audiosegmente** als referenzierte, integritätsgeprüfte Binärartefakte/Objekte – nicht automatisch riesige Audioarrays in jede Messwertzeile kopieren. Aufnahmeintervalle und Speicherstrategie erst mit tatsächlichen Datenmengen/Energiebudget abstimmen. Bei akustischer Außenaufnahme mögliche Drittpersonen-/Sprachaufzeichnung und Veröffentlichung gesondert datenschutzrechtlich prüfen.

**Präzise Abgrenzung zum Repository:** FPort 2 beschreibt `FFT_Hz`, `FFT_dB`, `FFT_Gesamt_dB` und Bandpegel als **vorverarbeitete Merkmale**; daraus folgt **keine** gespeicherte Roh-Tonaufnahme. Ältere beelogger-Firmware hat teilweise nur einen relativen FFT-Pegel, **nicht dBFS**. Diese Verfahren dürfen nur bei vergleichbaren Definitionen statistisch zusammengeführt werden. Der vorhandene Funkformat-/Formatterkatalog belegt die Kanalformate, **nicht** einen heute vorhandenen, aufgezeichneten Schallkanal eines bestimmten Volks.

### 3.5 Vibration als eigenständige Modalität

- Separate physikalische Größe (Beschleunigung bzw. Schwingung), Sensorschnittstelle und Messposition.
- Bei mehrachsiger Sensorik Achsrichtung bzw. Vektorbetrag dokumentieren.
- Gleiche Signal-/Fensterarchitektur möglich, aber keine Vermischung von Mikrofon-/Beschleunigungsdaten als identische „Schallwerte“.

## 4. Ergänzende Messgrößen und Fachinformationen (nur Möglichkeiten)

| Bereich | Mögliche Größe | Status / Nutzen |
|---|---|---|
| **Gasaustausch** | CO₂-Konzentration im Stock (ppm) | [VORSCHLAG] Mikroklima und Ventilationsverhalten untersuchen |
| **Flugverkehr** | Einflüge/Ausflüge, Zählintervalle | [VORSCHLAG] Flugaktivität, Tagesrhythmik |
| **Licht** | Beleuchtungsstärke am Stock/Flugloch (lx) | [VORSCHLAG] Kontext / Tageszeiten |
| **Standortwetter** | Außentemperatur, Luftfeuchte, Niederschlag, Wind, UV, Strahlung | [BESTÄTIGT] **Umweltsensor-Gruppe**, zeitlich und räumlich dem Bienenstand zuordnen; nicht einfach je Volk duplizieren |
| **Imkerliche Beobachtung** | Brutstatus, Königin, Futter, Behandlung, Ableger, Fütterung, Ernte | [BESTÄTIGT] Digitales BEEP-Stockkarten-/Ereignismodell als wichtiger Kontext bzw. potenzielle validierte Labels |
| **Gerätetechnik** | Akku, Firmware, RSSI, SNR, MCU-Temperatur | [VORSCHLAG] Telemetrie separat als Gerätegesundheit führen, nicht als Volkszustand |

CO₂-, Flug- und Vibrationskanäle sind **keine** Behauptung über vorhandene Ausrüstung. Ihre Unterstützung soll das Datenmodell auf lange Sicht nicht sprengen; der Erstumfang wird separat festgelegt.

## 5. Empfohlenes allgemeines Datenmodell, nicht gerätezentriert

### 5.1 Messgröße und Position definieren den fachlichen Zusammenhang

```text
measurement_quantities
  quantity_id, code, physical_dimension, canonical_unit, modality,
  semantics (instantaneous | rate | interval_total | spectrum | signal | status ...)
measurement_contexts
  context_id, target_kind, target_ref, position_code, medium, depth_or_height,
  valid_from, valid_to, context_quality
observation_series
  series_id, quantity_id, context_id, source_mapping_id, unit_id,
  device_assignment_id, valid_from, valid_to
observations
  observation_id, series_id, observed_at / window_start + window_end,
  value, unit, quality, source_record_id, mapping_version, revision
signal_segments
  signal_id, context_id, modality (airborne_sound | structural_vibration),
  start_utc, end_utc, sample_rate_hz, axes, encoding, calibration_id,
  artifact_uri?, content_hash?, source_record_id
signal_features
  feature_id, signal_id?, context_id, feature_definition_version,
  window_start, window_end, quantity_id, value/array_or_artifact, unit, quality
feature_definitions
  feature_code, version, input_types, processing_params, required_metadata
biological_interpretations
  interpretation_id, feature_set_id, analysis_run_id,
  hypothesis_or_class, score, evidence_status, validated_label_reference?
```

Die Feldnamen sind **Arbeitsbegriffe**; Constraints und FK-Modell noch nicht verabschiedet. Das Modell erlaubt, **ohne einen vorhandenen Sensor** eine Messgröße zu definieren. Eine Messung entsteht erst, wenn tatsächlich ein entsprechender Quellwert nachgewiesen ist.

### 5.2 Identität der Beute prüfen

**OFFEN / fachlich wichtig:** Wird **Beute** als eigenständiges Objekt (`hives`) historisiert? Empfehlung: **Ja, prüfen und sehr wahrscheinlich getrennt modellieren**, weil Stockgewicht immer auch Beuten-/Zargenmasse ist, Sensorpositionen physisch an der Beute liegen und ein Volk in eine andere Beute umgesetzt werden kann. Eine Beute kann wiederum ohne Volk oder mit einem anderen Volk genutzt werden. Die eigentliche Auswertung erfolgt weiterhin volkzentriert über die **zeitliche Zuordnung** `colony ↔ hive ↔ stand`.

**Wichtig:** Das ist **keine** Aussage, dass der Betreiber einen solchen Umzug bereits gemeldet hat. Dies ist ein robuster fachlicher Vorschlag, bevor wir FK-Constraints festlegen.

### 5.3 Keine falsche Gleichsetzung verschiedener Datenebenen

- Direkt gemessen: Stockmasse, Temperatur, relative Feuchte, digitalisiertes Luftschallsignal, Beschleunigung.
- Messwertaufbereitung: kalibrierte Masse, gefilterte Zeitreihe, normalisierte Temperatur.
- Signalfeatures: FFT-Peak, Bandpegel, RMS oder spektraler Schwerpunkt.
- Biologisches Feature: 24-h-Massenverlauf, Brutraumtemperatur-Stabilität, akustische Änderung relativ zum eigenen Volk-Baselinefenster.
- Interpretation / Modellresultat: „möglicher Schwarmindikator“, „mögliche reduzierte Brutaktivität“ usw. **niemals als direkte Messung ausgeben**.
- Manuell bestätigter Zustand: Stockkartenbeobachtung oder imkerliche Diagnose mit Zeit/Gültigkeit, Qualität und Herkunft.

## 6. Vergleichbarkeit über Völker und Standorte

Zwei Messwerte sind erst nach **semantischer Prüfung** zusammen vergleichbar:

1. **Dasselbe physikalische Merkmal** und dieselbe oder umrechenbare Einheit.
2. **Vergleichbarer Messort**: Brutnest vs. Deckel, Innen- vs. Außenschall nicht unkommentiert vermischen.
3. **Vergleichbare Zeitaggregation**: 1-s-Signalmerkmale vs. 15-min-Mittelwerte vs. Tagesdifferenz.
4. **Ähnliche oder modelliert unterschiedliche Messqualität**: Kalibrierung, fehlende Sensoren, Drift, Tausch, Firmware.
5. **Stimmige biologische Kontexte**: Jahreszeit, Volksentwicklung, Maßnahmen aus Stockkarten, Standwetter und Standortwechsel.
6. Für Akustik zusätzlich **kompatible Abtast-/Fenster-/Band-/Pegeldefinitionen**.
7. **Kein Ausfüllen fehlender Kanäle mit Nullen** oder ungeprüfte Substitution anderer Sensorpositionen. Analysen dürfen je Volk unterschiedliche Datenverfügbarkeit ausweisen.

**VORSCHLAG:** Automatische Merkmalsgruppen für spätere Cluster/KI:
- `weight_dynamics`
- `thermal_profile`
- `humidity_regulation`
- `acoustic_signature`
- `vibration_signature`
- `environmental_context`
- `hive_management_context`

Eine Merkmalsgruppe darf „nicht verfügbar“ sein. Die Anzahl verfügbarer Sensorarten darf nicht unbemerkt selbst zum künstlichen Clustertreiber werden.

## 7. Priorisierung des weiteren Architekturentwurfs

**[BESTÄTIGT]** Vorrang hat **nicht** die tatsächliche Sensorbelegung eines bestimmten beelogger.

**Empfohlene Reihenfolge:**

1. Fachliche Messgrößen-Ontologie und ihre Untertypen (insb. Gewicht, Temperatur, Feuchte, Luftschall, Vibration).
2. Physische Messkontexte, ggf. Beute als eigenständiges Objekt; wechselnde Volk-/Beuten-/Standbeziehungen.
3. Allgemeine Zeitreihen- **und** Signal-/Spektrendatenmodellierung (Skalar vs. segmentierter Signalstrom).
4. Unterschied gemessen – korrigiert – abgeleitet – biologisch interpretiert; gemeinsame Provenienz und Qualitätsregeln.
5. Analysetauglichkeit für mehrere Völker und Stände, Labels durch BEEP-Stockkarte, Reproduzierbarkeit.
6. Erst anschließend **gerätebezogene Mappings**, tatsächliche Sensorinventur (wenn verfügbar), BEEP-Importformate und SQL-DDL. Geräteinventur ist **Integrationsarbeit, kein Architekturgate**.

## 8. Fachliche Prüfszenarien

- Ein Volk besitzt Gewicht und Stocktemperatur, aber kein Mikrofon; keine künstlichen Nullwerte für Schall erzeugen.
- Zwei Völker haben Temperaturfühler an **verschiedenen Positionen**; eine Vergleichsanalyse darf sie nicht ohne Kennzeichnung als identisch behandeln.
- Ein Temperatursensor wird ersetzt, dieselbe Messgröße bleibt vorhanden; Sensorwechsel ist historisch abgrenzbar.
- Ein Volk wechselt die **Beute**: Gesamtmasse kann sich sprunghaft durch die Beutenmasse ändern; die biologische Volk-ID bleibt.
- Eine Wind-/Regenmessung am Stand darf mehreren Völkern für die Analyse als Kontext dienen, ohne ihre Rohreihe physisch zu vervielfachen.
- Ein beelogger liefert ausschließlich **FFT-Merkmale** und eine Forschungsaufnahme optional ein **Roh-Audiosignal**: beide nutzen passende Teilmodelle, ohne vorgetäuschte Vergleichbarkeit.
- Eine BEEP Base liefert unbekannte Kanäle: Werte bleiben quellseitig nachvollziehbar, bis die tatsächliche Bedeutung belegt ist.
- Eine akustische Anomalie wird erkannt: das Analyseergebnis ist eine **Hypothese**, kein bewiesener Schwarm-/Königinnenzustand.
- Stockkartenereignisse wie Fütterung und Honigernte markieren Gewichtszeitreihen als mögliche Eingriffsartefakte.
- Mehrere Völker an mehreren Ständen können nach **gleichen semantischen Messgrößen und definierten Zeitfenstern** verglichen werden.

## 9. Literatur / Herkunft der Forschungsoptionen

Die folgenden Quellen unterstützen die **Relevanz** dieser Messbereiche, **nicht** eine diagnostische Garantie für das konkrete Projekt:

1. Meikle, W. G. & Holst, N. (2015), *Application of continuous monitoring of honeybee colonies*. Apidologie. https://link.springer.com/article/10.1007/s13592-014-0298-x
2. Meikle et al. (2016), *Monitoring colony phenology using within-day variability in continuous weight and temperature of honey bee hives*. Apidologie. https://link.springer.com/article/10.1007/s13592-015-0370-1
3. Ramsey et al. (2020), *The prediction of swarming in honeybee colonies using vibrational spectra*. Scientific Reports. https://www.nature.com/articles/s41598-020-66115-5
4. Uthoff, Homsi & von Bergen (2023), *Acoustic and vibration monitoring of honeybee colonies for beekeeping-relevant aspects of presence of queen bee and swarming*. Computers and Electronics in Agriculture. https://www.sciencedirect.com/science/article/pii/S0168169922008973
5. *Weight, temperature and humidity sensor data of honey bee colonies in Germany, 2019–2022* (2024), Datensatz mit unterschiedlichen Messpositionen. https://pmc.ncbi.nlm.nih.gov/articles/PMC10809063/
6. Liu & Lin (2025), *Pattern analysis of daily beehive weight variation for colony health assessment*. Computers and Electronics in Agriculture. https://www.sciencedirect.com/science/article/pii/S0168169925011226

**Abgrenzung zur technischen Bestandsaufnahme:** [Ist-Inventur beelogger1](ist-inventur-beelogger1.md) und [Kanalinventar](messgroessen-kanalinventar.md) bleiben als **separate Implementierungs-/Integrationsunterlagen** bestehen, sind aber **kein erforderlicher nächster Schritt** für die fachliche Datenbankarchitektur.
