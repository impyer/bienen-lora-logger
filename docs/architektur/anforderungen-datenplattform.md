# Bienen-logger / Radeberger Honig – Anforderungen an die Daten- und Analyseplattform

**Dokumentstatus:** Fachliche Anforderungsbasis / Entwurf des Datenmodells (G0, noch keine SQL-Freigabe)  
**Stand:** 12.10.2026  
**Quelle:** Mit dem Projektbetreiber abgestimmte Anforderungen und Korrekturen im Architekturgespräch vom 11.–12.10.2026.  
**Geltungsbereich:** Zukünftige zentrale Datenverwaltung, Analyse-Engine, interne und öffentliche Visualisierung.  
**Änderungsklasse:** D0 (Dokumentation), Nachweis: T0 (Abgleich mit Gespräch und bestehenden Projektunterlagen); kein Laufzeit-, Hardware- oder Feldtest.  
**Wichtig:** Dieses Dokument hält fachliche Entscheidungen fest. Es behauptet weder, dass die neue Datenbank bereits existiert, noch dass BEEP-Import, öffentliche Forschungsseite oder automatische KI-Analysen bereits produktiv laufen.

## 0. Verbindliche Leseregel und Status

Bei allen folgenden Punkten ist der Status explizit ausgewiesen:

- **[BESTÄTIGT]** Vom Betreiber ausdrücklich als Anforderung oder Entscheidung bestätigt.
- **[VORSCHLAG]** Architekturidee, *keine* bestätigte Festlegung; darf nicht stillschweigend implementiert werden.
- **[OFFEN]** Noch zu klärender Sachverhalt. Keine Annahme als Tatsache ausgeben.
- **[BESTAND / BEOBACHTUNG]** Im bisherigen Projektkontext beziehungsweise in vorgelegten Dateien beobachtet; nicht automatisch dauerhaft gültige Systemeigenschaft.

**Verbindliche Regel für weitere Arbeiten:** Bei Widerspruch zwischen einer früheren Assistentenannahme und einer späteren ausdrücklichen Korrektur des Betreibers gilt die Korrektur. Offene Sachverhalte bleiben offen. Keine erfundenen Völker, Standorte, Kennungen, Messwerte, Ergebnisse oder Implementierungsstände in das produktive Modell übernehmen.

## 1. Zielbild

- **[BESTÄTIGT]** Eine zentrale Plattform für die Erfassung, Speicherung, Auswertung und verständliche Darstellung von Daten aus mehreren Völkern an einem oder mehreren Bienenständen.
- **[BESTÄTIGT]** Vergleich einzelner, mehrerer oder aller ausgewählten Bienenvölker – auch **standortübergreifend**.
- **[BESTÄTIGT]** Auf dem Server sollen regelmäßig bzw. automatisiert statistische und modellgestützte Analysen möglich sein: berechnete Kennzahlen, Klassifikationen, Cluster, Anomalien, Vorhersagen; gegebenenfalls Fuzzy-Logik und KI.
- **[BESTÄTIGT]** Berechnete Daten und Modellresultate sind **eigene, auswertbare und visualisierbare Datenobjekte**, nicht nur temporäre Diagramme.
- **[BESTÄTIGT]** Es soll einen **internen** und einen **öffentlichen** Bereich geben. Öffentliche, nachvollziehbare Forschungsanalysen sollen fachliche Rückmeldungen und offene Begutachtung ermöglichen.
- **[BESTÄTIGT]** `radeberger-honig.de` wurde vom Betreiber **beantragt** und soll für die Imkerei sowie den Forschungsbereich dienen. Registrierung, DNS und Hosting sind damit noch nicht als abgeschlossen bestätigt.
- **[BESTÄTIGT]** Bevor Datenbanktabellen/Importer implementiert werden, wird die **Datenbankstruktur gemeinsam fachlich entworfen und geprüft**. Die bisherigen Visualisierungsprototypen ersetzen diesen Schritt nicht.

## 2. Die exakt drei übergeordneten Datenquellengruppen

| Gruppe | Inhalt | Messung und Übertragung | Fachliche Zuordnung |
|---|---|---|---|
| **beelogger** | Stockmesssystem (z. B. Gewicht, Stocktemperatur, weitere beelogger-Kanäle) | Stockmesswerte direkt an den eigenen Server | zeitlich dem Volk zugeordnet |
| **Umweltsensoren** | Wetterstation, Bodentemperatur, später Bodenfeuchte und beliebige weitere Umweltmessstellen | Eigene Sensorik / geeignete Schnittstellen; Übertragungswege können variieren | Messstelle und zeitliche Zuordnung zu einem Stand/Ort |
| **BEEP** | **BEEP Base** (Stockmessgerät) **und** digitale BEEP-Stockkarten | BEEP Base sendet ihre Stockmessdaten **an die BEEP-Plattform, nicht direkt an den eigenen Server**. Stockkarten liegen ebenfalls bei BEEP. | BEEP-Base-Messungen zeitlich dem Volk; Stockkarte unabhängig vom Messgerät dem Volk |

### Zwingende fachliche Abgrenzung

- **[BESTÄTIGT]** Ein **beelogger** und eine **BEEP Base** sind **alternative Formen eines Stockmesssystems**, nicht zwei sich ergänzende Stockmessgeräte desselben Volkes im vorgesehenen Normalfall.
- **[BESTÄTIGT]** Ein Volk verwendet zu einem Zeitpunkt grundsätzlich **entweder einen beelogger oder eine BEEP Base** als primäres Stockmesssystem – oder keines. Ein Wechsel über die Zeit ist möglich; die Historie muss erhalten bleiben.
- **[BESTÄTIGT]** Die **digitale BEEP-Stockkarte ist unabhängig** vom verwendeten Messsystem und kann auch zu einem beelogger-Volk gehören.
- **[BESTÄTIGT]** Wetter-, Boden- und andere Umweltsensoren sind **standort-/messpunktbezogen**, nicht automatisch ein weiteres Stockmesssystem.
- **[BESTÄTIGT]** Zwei BEEP Bases sind vorgesehen; sie sind **keine vierte Datenquellengruppe**, sondern zwei Geräte innerhalb der Gruppe BEEP.
- **[VORSCHLAG]** Für die zentrale Datenverwaltung werden BEEP-Base-Messwerte und Stockkarten **über eine noch zu definierende, autorisierte BEEP-Schnittstelle/Importstrecke** übernommen. Weder API-Verfügbarkeit noch Berechtigungen, Aktualisierungsintervall oder Vollständigkeit sind derzeit bestätigt.
- **[OFFEN]** Falls künftig ausnahmsweise zwei primäre Stockmesssysteme parallel an einem Volk verwendet werden sollen, ist dies eine explizite Regeländerung mit dokumentiertem Datenkonfliktverfahren – **nicht** die Standardannahme.

**Abgrenzung zu [`docs/beep-anbindung.md`](../beep-anbindung.md):** Dort sind auch technische Übertragungsvarianten aus einem früheren Untersuchungsstand beschrieben. Die vorstehende **aktuell bestätigte fachliche Trennung** hat für den *neuen zentralen Datenbankentwurf* Vorrang; technische Varianten aus dem anderen Dokument sind dadurch nicht automatisch umgesetzt oder erforderlich.

## 3. Identitäten und Beziehungen

### 3.1 Bienenstand, Volk und physische Beute

- **[BESTÄTIGT – 12.10.2026]** Die **physische Beute ist eine eigenständige, dauerhaft identifizierbare Entität** mit eigener Historie, unabhängig von Volk, Bienenstand, Sensor und Messgerät. Die Beuten-ID bleibt bei einem gewöhnlichen Volk-/Stand-/Gerätewechsel erhalten. Einzelheiten zu Beutenaufbau und seltenen Sonderfällen sind **noch offen**.
- **[BESTÄTIGT – 12.10.2026]** **Eine physische Beute kann zu einem Zeitpunkt nur von einem einzigen Bienenvolk bewohnt werden** (Kardinalität auf Beutenseite: **0 oder 1 Volk**). Dieselbe Beute darf nacheinander verschiedene Völker beherbergen; die Belegung wird historisiert. Eine Beute kann unbesetzt sein. Fehlender Belegungsnachweis bedeutet jedoch nicht automatisch „nachweislich leer“.
- **[OFFEN]** Ob ein Volk umgekehrt gleichzeitig mehrere Beuten nutzen kann, ist durch diese Aussage **noch nicht ausdrücklich entschieden**. Die im Entwurf genannte Beschränkung auf maximal eine Beute pro Volk bleibt bis zur Bestätigung **ein Vorschlag**.
- **[VORSCHLAG]** Belegungs- und Standortintervalle führen die Beziehungen `Volk ↔ Beute` und `Beute ↔ Bienenstand` historisch. Der Stand eines Volkes kann bei gesicherter Beutenbelegung und Standaufstellung daraus abgeleitet werden; historische Lücken und abweichende Direktangaben sind ausdrücklich zu behandeln. [Fachentwurf Beute–Volk–Stand](beute-volk-stand-beziehungen-v01.md).

- **[BESTÄTIGT]** Ein Bienenvolk erhält eine **dauerhaft eindeutige interne Volk-ID**; diese darf nicht aus der Loggernummer, einer BEEP-ID oder einer Standbezeichnung abgeleitet werden.
- **[BESTÄTIGT]** Ein Volk kann den Bienenstand wechseln; Standort- und Gerätezuteilungen werden **zeitlich historisiert**, damit alte Messungen am damals zutreffenden Stand ausgewertet werden.
- **[BESTÄTIGT]** Mehrere Völker an einem Stand und mehrere Stände pro Auswertung sind ausdrücklich erforderlich.
- **[VORSCHLAG]** Zuordnungen verwenden `valid_from` (einschließlich), `valid_to` (ausschließlich, NULL = offen) und UTC-Zeitpunkte; überlappende aktive Primärzuordnungen eines Volkes werden verhindert.
- **[OFFEN]** Behandlung von vorübergehend unbekanntem Stand, Wanderung über mehrere Teilstandorte und abweichenden Zeitangaben aus externen Quellen.

### 3.2 Geräte, Sensoren und Messstellen

- **[BESTÄTIGT]** Physisches Gerät, Gerätetyp/Datenquellengruppe, Sensor/Kanal und Messgröße sind **verschiedene Konzepte**.
- **[BESTÄTIGT]** Ein beelogger bzw. eine BEEP Base kann ausgewechselt und einem anderen Volk zugeordnet werden, ohne die Volk-ID zu ändern.
- **[BESTÄTIGT]** Umweltmessstellen können an verschiedenen Positionen liegen; Höhe/Tiefe (z. B. Bodentemperatur) müssen modellierbar sein.
- **[VORSCHLAG]** Eine eigene Zuordnung von Sensor/Kanal zu standardisierter Messgröße erlaubt mehrere Kanäle gleichen Typs, Einheitenumrechnung und Geräteversionen.
- **[BESTÄTIGT – ZUKUNFTSFÄHIGKEIT, NICHT GEPLANTER ERSTAUSBAU]** Das fachliche Modell soll beelogger-Duo-/Triple- und andere **Mehrfachsysteme prinzipiell unterstützen können**, bei denen ein physisches Messgerät getrennte Stockmesseinheiten für mehrere Völker bereitstellt. **Solche Mehrfachsysteme sind derzeit nicht vorgesehen** und dürfen nicht als vorhandene Geräte oder als verpflichtende Funktion der ersten Umsetzung behandelt werden.
- **[VORSCHLAG]** Zur Erweiterbarkeit wird zwischen physischem Gerät und ggf. mehreren logischen Stockmesseinheiten/Kanalsätzen unterschieden. Bei Einzelgeräten genügt eine Stockmesseinheit; die konkreten Tabellen, Grenzen und Validierungsregeln bleiben Teil des ER-/SQL-Entwurfs.
- **[OFFEN]** Details der Geokoordinaten, öffentlich zulässige Ortsauflösung, Sensorkalibrierung und exakte Bezeichnungen aller BEEP-/beelogger-Kanäle.

### 3.3 Ableger, Schwarm, Vereinigung, Königin

- **[BESTÄTIGT]** Jeder **Ableger erhält eine neue eigene Volk-ID**; die **Herkunft vom Muttervolk ist zwingend zu dokumentieren**. Das Muttervolk besteht bei gewöhnlicher Ablegerbildung weiter.
- **[BESTÄTIGT]** Die Historie muss mehr als eine einfache Spalte `mother_colony_id` erlauben, insbesondere mehrere Herkunftsvölker bei Vereinigungen.
- **[VORSCHLAG]** Ein versioniertes Volk-Lebenszyklusereignis wird mit einer n:m-Herkunfts-/Nachfolgebeziehung verknüpft; die genaue Ereignissemantik für Schwarm, Teilung, Verlust und Vereinigung wird in der nächsten Entwurfsrunde festgelegt.
- **[VORSCHLAG]** Königinnenwechsel wird als Ereignis dokumentiert, **ohne** automatisch eine neue Volk-ID anzulegen; Königinnenabstammung ist von der organisatorischen Volk-Abstammung zu trennen.
- **[OFFEN]** Wann eine Vereinigung die alte Volk-ID beendet, wann eine neue entsteht und wie unsichere Abstammung erfasst wird.

## 4. Fachliche Datenarten – nicht vermischen

| Art | Beispiel | Verbindliche Anforderung |
|---|---|---|
| **Quell-/Rohdatensatz** | beelogger-Uplink, Wetterstationsdatensatz, BEEP-API-Antwort | **[BESTÄTIGT]** Herkunft nachvollziehen; **[VORSCHLAG]** Original unverändert, Import mehrfach ausführbar und idempotent speichern |
| **Direkte Messung** | Stockgewicht, S2120-Temperatur, Bodentemperatur | **[BESTÄTIGT]** Zeit, Messgröße, Wert, Einheit, Quelle, Gerät/Sensor und räumlich/volkbezogener Kontext |
| **Imkerliches Ereignis** | Durchsicht, Fütterung, Behandlung, Ablegerbildung | **[BESTÄTIGT]** Als eigenes Ereignis, nicht als numerischen Sensorwert behandeln; BEEP-Stockkarte als Quelle dokumentieren |
| **Berechnete Größe / Feature** | Tagesgewichtszunahme, Temperaturdifferenz, Tagesmittel | **[BESTÄTIGT]** Als eigenständig abfragbare abgeleitete Größe samt Berechnungsgrundlage |
| **Modell-/Analyseergebnis** | Clusterzuordnung, Klassifikationswahrscheinlichkeit, Anomalie, Prognose | **[BESTÄTIGT]** Dauerhaft und reproduzierbar mit Bezug zu Analyseverfahren, Zeitraum, Eingaben und Version |

**[VORSCHLAG]** Für Messwerte sind mindestens `event_time_utc`, `received_at_utc`/`imported_at_utc`, Quelle/Originalkennung, Sensor/Messgröße, Originalwert/-einheit, normalisierter Wert/-einheit und Qualitätsmerkmale vorzusehen. Messzeit und Empfangszeit dürfen nicht unbemerkt gleichgesetzt werden. Für fehlende Werte, doppelte Uplinks, verspätete Ankünfte, Zeitzonen-/DST-Probleme und Korrekturen sind explizite Regeln zu entwerfen.

**[OFFEN]** Fachliche Aggregationsregeln je Messgröße: z. B. Mittelwert für Temperaturen, intervallbezogene **Menge** für Regen (mm), **Intensität** für Regen (mm/h), Zählerstände einschließlich möglicher Resets und Windrichtung als zirkuläre Größe. Regenintensität, Intervallmenge und kumulierter Stationszähler sind **nicht** synonym.

## 5. Berechnete Größen, Klassifikation, Clustering und automatisierte Läufe

- **[BESTÄTIGT]** Analysen sollen auf dem Server **automatisiert und wiederholt** laufen können; feste Algorithmen sind noch nicht beschlossen.
- **[BESTÄTIGT]** Kennzahlen und Analyseergebnisse können einzelne Völker, **mehrere ausgewählte Völker aus unterschiedlichen Bienenständen** oder Umweltmessstellen umfassen.
- **[BESTÄTIGT]** Der Nutzer soll sehen können, **welche Cluster entstanden sind**, welche Völker/Beobachtungsfenster zugewiesen wurden und **welche Merkmale die Gruppen charakterisieren**.
- **[BESTÄTIGT]** Eine Clusterkennung ist **keine zeitlich unveränderliche Eigenschaft des Volkes**. Eine Zuordnung gehört zu einem konkreten **Analyselauf und Beobachtungszeitraum**; dieselbe Volk-ID kann in anderen Fenstern/Modellständen anders zugeordnet sein.
- **[VORSCHLAG]** Ein Analyselauf erhält stabile ID, Ausführungsstatus, Zeitfenster, betrachtete Völker/Stände, Dataset-Snapshot/Version, Featuredefinitionen und -versionen, Algorithmus/Codeversion, Hyperparameter, Zufalls-Seed (falls relevant), Laufzeit, Ergebnisversion und Fehlerdiagnostik.
- **[VORSCHLAG]** Für Clusteranalysen werden Feature-Matrix-Definition, Vorverarbeitung/Normierung, Zuordnung je Beobachtungsfenster, Clusterzentren/-profile, Gruppengrößen und Qualitätskennzahlen (z. B. Silhouette bei geeigneter Datenlage) getrennt vorgehalten. Cluster-Labels verschiedener Läufe sind **nicht** automatisch vergleichbar.
- **[VORSCHLAG]** Für Klassifikationen: definierte Klassen, Score/Wahrscheinlichkeit, Schwellwert, Modellversion und ggf. menschliche Bestätigung. Für Prognosen: Vorhersagezeitpunkt, Zielzeitraum, Unsicherheit und spätere tatsächliche Beobachtung.
- **[VORSCHLAG]** Herkunftsbeziehungen (Lineage) vom Ergebnis zu den konkreten Eingangsdaten bzw. Dataset-Versionen; bei korrigierten Rohdaten alte Ergebnisse nicht still überschreiben, sondern als veraltet kennzeichnen und neu berechnen.
- **[OFFEN]** Fachliche Zielgrößen/Labeldefinitionen (z. B. Schwarm), Trainingsdaten, Bewertungsmaßstäbe, Rechenrhythmus, Retention, Rechenbudget und Umgang mit Datenlücken.

**Methodische Schutzregel:** Ein farbiger Cluster oder eine Klassifikation stellt **keinen bestätigten biologischen Befund** dar. Korrelation und Kausalität sind zu unterscheiden; Modellgüte, Grenzen und Unsicherheiten müssen angezeigt werden.

## 6. Darstellung / Apache ECharts

- **[BESTÄTIGT]** **Apache ECharts** wird für die **neue** Analyse- und Forschungsoberfläche verwendet; die laufende beelogger-M.40-Ansicht soll nicht unkontrolliert ersetzt werden.
- **[BESTÄTIGT]** Messgrößen, berechnete Größen und Analyseergebnisse sind gemeinsam auswählbar; Auswahl **keine/eine/mehrere/alle** geeigneten Reihen.
- **[BESTÄTIGT]** Auswahl **mehrerer Völker**, auch aus **mehreren Bienenständen**, mit gemeinsamen Filtern für Stand, Volk, Zeitraum, Datenart, Messgröße und Analyse.
- **[BESTÄTIGT]** Ein **kombiniertes Zeitdiagramm** mit gemeinsamer X-Zeitachse und mehreren Y-Achsen wird benötigt; zusätzlich synchronisierte Einzelspuren für zu viele oder inkompatible Skalen.
- **[BESTÄTIGT]** Die Diagrammform richtet sich nach Messgröße **und Fragestellung**, nicht starr nach dem Datenlieferanten. Beispielsweise Regen als Balken, Gewicht/Temperatur als Linien, Windrichtung als Windrose, Cluster als Scatter-/Dot-Plots, Klassen und Ereignisse als Punkte/Marker, Merkmalsvergleiche und Verteilungen als geeignete Plots.
- **[VORSCHLAG]** Bei Windrichtungen eine **polare Windrose** für Richtungshäufigkeiten nutzen; Radar-/Spinnennetzdiagramme nur für geeignete mehrdimensionale Profile. Die genaue Diagrammkonfiguration ist noch zu entwerfen.
- **[BESTÄTIGT]** Interaktivität: Zoomen/Scrollen, Tooltips mit Zeit und Einheit, klare Legenden, responsive Darstellung sowie sinnvolle Aggregationswahl.
- **[OFFEN]** Verbindlicher Diagramm-Katalog, Achsengrenzen, maximale gleichzeitig lesbare Achsen, Farbleitsystem, Exportformate, Darstellungsregeln für Unsicherheiten.

## 7. Öffentlicher und interner Bereich

- **[BESTÄTIGT]** Interne Datenerhebung, Gerätemanagement, nicht freigegebene Messungen, vollständige Stockkarten und Modellarbeit sind **geschützt**.
- **[BESTÄTIGT]** Öffentliche Imkerei-/Forschungsseite mit **explizit freigegebenen** Daten, Analysen, Methoden und Feedback-/Review-Möglichkeit.
- **[VORSCHLAG]** Veröffentlichung über eine **serverseitige Freigabe-/Exportstrecke** mit festen Dataset-/Analyseversionen. Kein bloßes Verstecken privater Daten im Browser und kein direkter öffentlicher Zugang zu internen Datenbank-/Admin-Endpunkten.
- **[VORSCHLAG]** Für öffentliche Arbeiten Dataset-Version, Abfragekriterien, Methode/Codeversion, Qualitäts-/Unsicherheitshinweise und ggf. DOI/Repository-Referenz veröffentlichen.
- **[OFFEN]** Freigabeprozess, genaue Standortunschärfe, Verzögerung vor Veröffentlichung, Lizenz der Datensätze, personenbezogene Daten in Stockkarten, Rollen, Nutzerverwaltung, Feedbackplattform und Hosting.
- **Sicherheitsgrundsatz:** Keine Zugangstokens, Passwörter, privaten Geokoordinaten oder unveröffentlichten Rohdaten in das öffentliche Git-Repository einchecken.

## 8. Vorläufige fachliche Entitäten (noch **kein** freigegebenes SQL-Schema)

| Kandidat | Zweck | Status |
|---|---|---|
| `apiaries`, `colonies`, `hives` | Drei **bestätigte, getrennte Identitäten** Stand / Volk / physische Beute; englische Tabellennamen sind Vorschläge | [BESTÄTIGT] fachliche Trennung, [VORSCHLAG] Namen |
| `colony_hive_occupancies`, `hive_apiary_placements` | Historische Beziehungen Volk–Beute und Beute–Stand; direkte `colony_placements` nur als zu klärender Ersatznachweis bei unbekannter Beute | [VORSCHLAG], Details offen |
| `colony_lifecycle_events`, `colony_lineage` | Ableger, Herkunft, Teilungen, Vereinigungen | [VORSCHLAG] |
| `data_sources`, `devices`, `device_assignments` | Drei Datenquellengruppen, Geräte, zeitliche Primärmesssystemzuordnung | [VORSCHLAG] |
| `measurement_points`, `sensors`, `measurement_types` | Umweltmesspunkte, Sensorkanäle, Messgrößen | [VORSCHLAG] |
| `raw_records`, `measurements` | Herkunft, deduplizierte und normalisierte Messungen | [VORSCHLAG] |
| `colony_events`, `external_references` | Stockkartenereignisse; BEEP-/beelogger-IDs | [VORSCHLAG] |
| `derived_features`, `feature_definitions` | Berechnete Größen und ihre Definitionen | [VORSCHLAG] |
| `analysis_runs`, `models`, `analysis_results` | Analysepipeline, Modellversion, Resultat | [VORSCHLAG] |
| `cluster_assignments`, `classification_results` | Ergebnisse je Volk/Beobachtungsfenster/Lauf | [VORSCHLAG] |
| `publications`, `dataset_releases` | Geprüfte Veröffentlichung, Versionen und Zugriff | [VORSCHLAG] |

**[VORSCHLAG]** PostgreSQL als zentrale relationale Datenbank (zeitreihenfähig, ohne verpflichtende Erweiterung); ggf. später TimescaleDB. **[OFFEN]** Volumenschätzung, Tabellenpartitionierung, Backup-/Restore-Konzept, API-/Importstrategie, genaue Schlüssel/Fremdschlüssel und Indexierung.

## 9. Verbindliche fachliche Prüfszenarien für den späteren Entwurf

Die folgenden Fälle müssen das ER-Modell abbilden können; sie sind **Akzeptanzszenarien**, keine bestandenen Implementierungstests.

1. **Mehrere Völker, ein Stand:** mehrere beelogger-Völker teilen sich standbezogene Umweltmesswerte, ohne die Umweltmessung als Volk-Messung zu duplizieren.
2. **Alternative Messtechnik:** Volk A mit beelogger, Volk B mit BEEP Base; beide mit eigenständiger BEEP-Stockkarte möglich.
3. **Zwei BEEP Bases:** zwei Geräte können unterschiedlichen Völkern zugeordnet sein; sie senden an BEEP, ein späterer Import erhält die Herkunft.
4. **Volk- und Gerätewechsel:** Beim Wechsel des Standes bzw. beelogger → BEEP Base bleibt die Volk-ID und die historische Datenzuordnung korrekt.
5. **Ableger:** Aus Volk A entsteht Volk B mit neuer ID, Ereignis, Zeitpunkt und dokumentierter Herkunft; Volk A existiert weiter.
6. **Völkervereinigung:** Mehrere Herkunftsvölker und das Ergebnis lassen sich ohne Verlust der alten Historie modellieren.
7. **Mehrere Umweltmessstellen:** Wetterstation und Bodentemperatursensor verschiedener Tiefe/Position sind unterscheidbar und zeitlich dem richtigen Stand zugeordnet.
8. **Standübergreifende Auswertung:** Eine Analyse verarbeitet gezielt Völker aus zwei oder mehr Ständen mit korrekter Zuordnung des jeweiligen Umweltkontextes.
9. **Berechneter Wert:** Tageszunahme kann von seiner Formel/Version und den verwendeten Gewichtsdaten her nachvollzogen werden.
10. **Wiederholte Clusteranalyse:** Dasselbe Volk hat in verschiedenen Fenstern/Analyseläufen unterschiedliche Cluster; alte Zuordnungen bleiben reproduzierbar.
11. **Datenkorrektur:** Eine rückwirkende Korrektur eines Quellwerts ist nachvollziehbar und führt nicht zu unsichtbar veränderten veröffentlichten Ergebnissen.
12. **Öffentlicher Zugriff:** Ein öffentlicher Nutzer sieht ausschließlich explizit freigegebene Daten; Stockkarten-Rohinhalte, private Standorte und Verwaltungszugänge bleiben verborgen.

## 10. Offene Entscheidungen – Reihenfolge der nächsten Architekturgespräche

**Korrigierte Priorität vom 12.10.2026 [BESTÄTIGT]:** Das **allgemeine fachliche Messgrößenmodell** für Gewicht, Temperatur, Luftfeuchte und Schallwellen wird **vor** einer gerätespezifischen Bestandsaufnahme entworfen. Ein einzelner beelogger ist weder Referenzgerät noch Voraussetzung des Schemas. Siehe [Messgrößen am Bienenvolk](messgroessen-am-bienenvolk.md).

1. **Volk- und Stand-Identität:** Identitätsregeln bei Vereinigung, Schwarm, Verkauf/Verlust; Standortwechsel und unvollständige Historiendaten.
2. **Geräte und Sensorik:** Primärmesssystem, Gerätewechsel, Kanal-/Messgrößenkatalog, Umweltmessstellen und Messhöhen/-tiefen.
3. **Messzeit und Rohdaten:** Quellformate, Zeitqualität, Duplikate, Datenlücken, Einheiten, Wetterzähler und Korrekturen.
4. **BEEP-Anbindung:** autorisierte API-/Exportmöglichkeiten für Base und Stockkarten, Referenz-IDs und Synchronisierungsstrategie.
5. **Analysedatenmodell:** Feature-Fenster, Algorithmus-/Modellversionen, Clusterzuordnung, Provenienz, Reproduzierbarkeit und Qualitätsindikatoren.
6. **Freigabe und Datensicherheit:** öffentlicher Dataset-Lebenszyklus, Rechte, Standortschutz und personenbezogene BEEP-Inhalte.
7. **Erst danach:** konkretes ER-Diagramm mit Kardinalitäten und Constraints, PostgreSQL-DDL, Migrations- und Testplan.

## 11. Quellen, verwandte Projektunterlagen und Pflege

- **[Beute–Volk–Stand: Identitäten und zeitliche Beziehungen 0.1](beute-volk-stand-beziehungen-v01.md)** – bestätigte eigenständige Beutenidentität und gesondert gekennzeichnete Vorschläge für Kardinalitäten, Wechsel und historische Zuordnungen.

- **[Fachentwurf Messreihe, Messkontext, Zeit und Datenqualität 0.1](messreihe-messkontext-zeitqualitaet-v01.md)** – volkzentrierte und geräteunabhängige Struktur von Beobachtungen; **nicht freigegeben**.
- **[Biologisch relevante Messgrößen am und im Bienenvolk](messgroessen-am-bienenvolk.md)** – **neue vorrangige Modellperspektive:** Gewicht, Mehrpunkt-Temperatur, Feuchte, Luftschall und optionale Vibration, unabhängig von der tatsächlichen Sensorbelegung eines Geräts.
- [Fachliches ER-Modell der Datenplattform 0.1](er-modell-datenplattform-v01.md) – Identitäten, zeitliche Geräte-/Sensorzuordnungen, Rohdaten, Messwertsemantik und Analyseprovenienz; **noch nicht freigegeben**.
- [Fachentwurf Sensoren und Messkanäle](sensoren-messkanaele-entwurf.md) – **Entwurf 0.1, noch nicht freigegeben**; zeitliche Interpretation von Quellfeldern, Sensorwechsel, Kalibrierung und Qualität.
- [Messgrößen- und Kanal-Inventar 0.1](messgroessen-kanalinventar.md) samt [maschinenlesbarer CSV](messgroessen-kanalinventar.csv) – quellgeprüfte Felder; tatsächliche Sensorbestückung und BEEP-API-Felder bleiben als solche offen.
- [Ist-Inventur beelogger1](ist-inventur-beelogger1.md) – **optionale, nachgeordnete Geräteintegrationshilfe**, einschließlich [read-only Diagnose](../../server/diagnose/README.md); tatsächliche Sensorbestückung noch offen, **kein Architektur-Gate**.
- [Entwicklungsregelwerk](../entwicklung/README.md) – verbindlicher Arbeits-/Prüfprozess.
- [Governance und Ausnahmen](../entwicklung/entscheidungen.md) – beschlossene Projektstandards.
- [BEEP-Anbindung](../beep-anbindung.md) – frühere Untersuchung möglicher BEEP-Schnittstellen; fachliche Abgrenzung siehe Abschnitt 2.
- [Serveranalyse M.40](../server-analyse.md) und [Funk-/TTN-Datenformat](../datenformat.md) – bestehende Schnittstellen und bekannte Einschränkungen.

### Pflege dieses Dokuments
- Dies ist die **fachliche Referenz** für die bisher bestätigten Datenplattform-Anforderungen; diese müssen bei späteren Änderungen mit einer **konkreten Bestätigung des Betreibers** und entsprechendem Versions-/Commitnachweis aktualisiert werden.
- **[VORSCHLAG]** und **[OFFEN]** dürfen nicht durch bloße Wiederholung zu **[BESTÄTIGT]** werden.
- Künftige ADRs/SQL-Schemata sollen auf die jeweiligen Abschnitte dieses Dokuments verweisen und Abweichungen ausdrücklich festhalten.
- Keine Halluzinationsgarantie durch bloße Dokumentation: Aussagen zu aktuellem Betrieb, externen APIs und tatsächlich vorhandenen Daten müssen bei Verwendung **neu verifiziert** werden.
