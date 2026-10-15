# Weboberfläche – fachliche Anforderungen (Entwurf v0.4)

**Stand:** 15.10.2026. Kennzeichnung: [B] Betreiber bestätigt / [V] Vorschlag / [O] offen. Keine erfundenen Live-Daten.

## A – Bienenstand-Dashboard

- [B] Startansicht zeigt den gewählten Bienenstand. Umschalten **Kacheln/Liste**; ein Volk hat ein BEEP-artiges Symbol mit Beutenaufbau/Farben und wichtige verfügbare Messwerte.
- [B] Keine festen Sensorfelder voraussetzen: Gewicht, Stocktemperatur, relative Feuchte, Schall und andere verfügbare Kanäle auswählbar; dynamische Registrierung zusätzlicher Kanäle.
- [V] Gewicht + Trend besonders prominent; optional konfigurierbare zweite/dritte Kennzahl. Listenansicht suchen/filtern/sortieren.
- [V] Drei getrennte Indikatoren: **Stockkarten-/Biologie-Eindruck**, **technische Verfügbarkeit/Datenqualität**, **offene Aufgaben**. Nicht aus Sensorfehler auf Volkszustand schließen.
- [B] Völker ohne Stockmesssystem bleiben sichtbar; „keine Daten“ statt 0 oder Warnsignal.
- [V] Kartenbild zeigt Konfiguration aus BEEP als abgeleitete Darstellung; nicht parallel von eigener UI frei bearbeiten, solange BEEP führend ist.

## B – Volk-Cockpit + Stockkarte

- [B] Ereignisse aus Stockkarte als **Symbole und vertikale Hilfslinien senkrecht zur Zeitachse** über allen relevanten Kurven.
- [B] Synchronisierte Zeitachse, wählbare Messreihen, Zoom/Zeitraum, Überlagerung von Witterung, Volk und Eingriffen.
- [V] Für Ereignisintervalle Beginn und Ende sowie farblich zurückhaltendes Intervallband; Detailpanel mit Quelle, Originalzeit, Beschreibung und BEEP-Referenz.
- [B] Gewicht, Temperatur, Feuchte, Schall **auf korrekten Einheiten-/Y-Achsen** oder getrennten, zeitsynchronen Spuren; fehlende Daten nicht verbinden oder mit 0 auffüllen.
- [V] Maßnahmen auswählen, Vorher-/Nachher-Fenster vergleichen, Änderungen als Beobachtung und **nicht als Kausalitätsbeweis** markieren.
- [B] BEEP-Checklisten/Durchsichten zunächst lesend integrieren; eigene Eingabe erst nach validierter Migration.

## C – Wetter, Boden, Tracht, Flugkreise

- [B] Eigene Wetter- und Trachtansicht mit theoretischen **Flugkreisen je Bienenstand** sowie Wetter-, Pollen-/Tracht- und Phänologiedaten.
- [B] Drei unabhängige Bodentemperaturkanäle (Messbeginn laut Betreiber 14.10.2026); Tiefen/Positionen/Sensortypen unbekannt, nicht ableiten.
- [V] Umweltwerte am Bienenstand sichtbar: Luft, Boden 1–3, Wind, Niederschlag, Datenalter, GTS.
- [V] Schaltbare Kartenebenen: 1/3/5 km konfigurierbare Radien, Landnutzung, potenzielle Tracht, Wasser, Wetter, Blühbeobachtung. Radius garantiert keine tatsächliche Sammelaktivität.
- [B] GTS aus **Lufttemperatur**, Bodenwärmekennzahlen separat; Algorithmen und Datenlücken dokumentieren.

## D – Vergleiche & Analysen

- [B] Vergleich eines/mehrerer Völker auch standortübergreifend und über verschiedene Perioden.
- [B] Zeitreihen, berechnete Größen, Analysen und Ereignisse gemeinsam auswählbar, abhängig vom Datentyp geeignete Chartformen; ECharts für neue Ansicht vorgesehen.
- [V] Kurven (absolute Werte, Differenzen, tägliche Änderungsraten), Korrelationen, Qualitäts-/Unsicherheitsanzeige; später Modellergebnisse mit Version und erklärbarem Befund.

## UX-Kriterien für den ersten nutzbaren MVP

1. [V] Mobil und Desktop sinnvoll nutzbar, Tastaturbedienung und lesbare Kontraste.
2. [V] Startseite lädt Völker und verfügbaren Messkanalkatalog **ohne pro Sensortyp angepassten View-Code**.
3. [V] „Kacheln/Liste“ merkt sich die Auswahl in privaten UI-Einstellungen (Implementierung noch offen).
4. [V] Messkanal hinzufügen: Datenbank/API-Metadaten verarbeiten, danach Kanal in Auswahl und passenden Charts sichtbar, auch neue Größenarten; kein UI-Deploy nur für neue Kanal-Instanz.
5. [V] Lade-/Leer-/Fehlerzustände sowie Quelle und letzter gültiger Messzeitpunkt in jedem Wertebereich.
6. [V] Klick auf BEEP-Ereignis hebt Linie bei tatsächlichem Ereigniszeitpunkt hervor; selbst nachträglich erfasste Ereignisse landen beim Durchsichtszeitpunkt, nicht bei der Eingabezeit.
7. [V] UI bietet sichere Nutzung von Live-Daten nur authentifiziert; öffentliche Ansicht ausschließlich nach serverseitiger Freigabe.

## Abgrenzung des vorhandenen Prototyps

`web/prototypes/Bienenlogger_UI_MVP_v0_3.html` ist statisch und verwendet synthetische Beispielvölker, Beispielereignisse und simulierte Sensorkanäle; keine echte Persistenz, BEEP-API, TTN-Anbindung, Geokarte oder Authentifizierung. Es ist UX-Referenz, **kein produktionsreifes Frontend**.
