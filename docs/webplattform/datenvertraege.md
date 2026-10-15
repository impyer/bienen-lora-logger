# Erweiterbares Datenmodell und UI-Datenverträge – Arbeitsentwurf

**Stand:** 15.10.2026 · **Keine SQL-/API-Freigabe.** Fachliche Referenz: [Anforderungen Datenplattform](../architektur/anforderungen-datenplattform.md).

## Prinzipien

- Stabile interne IDs für `colony`, `hive`, `apiary`, `device` und `measurement_channel`, externe BEEP-/TTN-Kennungen nur als versionierte Referenzen.
- Volk, physische Beute, Gerät, Stockmesseinheit, Sensor, Messkanal, Messgröße und Umweltmessstelle **nicht** zusammenfallen lassen.
- Primäres Stockmesssystem je Volk im bestätigten Normalfall: beelogger oder BEEP Base oder keines. Zeitliche Historie und optionale Mehrkanalgeräte sind möglich. Umweltfühler gehören zum Standort/Messpunkt.
- Beute kann zeitlich nur 0–1 Volk beherbergen; Ableger mit eigener ID und obligatorischer Herkunft; mehrfache Herkünfte/Vereinigung historisierbar.
- Jeder Kanal ist **datengesteuert**: stabile ID, Menge/Größe, Einheit, Umrechnung, Position/Tiefe, gültiger Zeitraum, Geräte-/Messstellenzuordnung, erlaubte Aggregation und Qualitätsflags.
- Rohpayload **append-only**, Beobachtungen dedupliziert und mit `measured_at` (UTC) plus `received_at`; Qualitätsänderungen nicht still überschreiben.
- Rohsignal, FFT-/Schallmerkmal und analysierter Zustand sind separate Datentypen; FFT-Kennzahlen niemals als behauptetes akustisches Rohsignal darstellen.

## Vorläufige Objektstruktur

`Apiary` – Stand. `Hive` – physische Beute. `Colony` – Volk. `Occupancy` – Belegung/Standhistorie. `ColonyLineage` – Herkunft/Ereignisse.  
`ChecklistTemplateVersion`, `Inspection`, `ColonyEvent` – Checklisten, Einträge, Maßnahmen.  
`Device`, `MeasuringUnit`, `MeasurementChannel`, `ChannelInstallation`, `MeasurementSite` – Messsystem/Umweltmessstelle.  
`RawIngestEvent`, `Observation`, `DerivedMetric`, `SignalFeature`, `AnalysisRun` – Eingang, normalisierte Beobachtung, Berechnung, Analyseversion.

## Unverbindliche API-Kontrakte für UX-Mock / Planung

- `GET /api/v1/apiaries` – nur autorisierte Stände, bewusst ohne öffentliche Präzisionskoordinaten.
- `GET /api/v1/apiaries/{id}/colonies` – Volk-ID, Stand, Beutenprojektion, Stockkartenstatus, letzte Messwertzusammenfassung pro auswählbarem Kanal.
- `GET /api/v1/channels?scope=apiary|colony&owner_id=...` – Katalog verfügbarer Messgrößen samt Kanalmetadaten.
- `GET /api/v1/observations?channel_ids=...&from=...&to=...&aggregation=...` – Messreihen mit Qualität, Zeitstempeln, Lücken.
- `GET /api/v1/colonies/{id}/events?from=...&to=...` – tatsächlich datierte Ereignisse samt Symboltyp, Intervall, BEEP-Referenz.
- `GET /api/v1/apiaries/{id}/environment` – Klima, GTS, Messstellen-/Kanalverweise; Raster-/Kartenquellen getrennt.
- `POST /api/v1/channels` nur für autorisierte Geräteadministration; Registrierung ≠ automatische Existenz echter Messwerte.

Diese Pfade sind **Vorschläge, keine vorhandenen Endpunkte**. BEEP-Import wird durch Adapter mit idempotenter Synchronisation angebunden; kein öffentlicher Browserzugang zu API-Schlüsseln.

## JSON-Beispiel: neuer Bodenfühler (rein schematisch)

```json
{
  "channel_id": "example-soil-03",
  "quantity": "soil_temperature",
  "unit": "Cel",
  "measurement_site_id": "example-site-01",
  "installation": {"depth_cm": null, "position": null, "valid_from": null},
  "display": {"label": "Bodentemperatur 3", "preferred_chart": "line"},
  "quality": {"last_sample_at": null, "state": "no_sample"}
}
```

## Im Frontend

- Channel Registry API bestimmt verfügbare Sensoren, Farbe/Einheit/Name aus Metadaten und bewusst gespeicherten Präferenzen.
- Separat: `quantity` (physikalische Größe), `channel_id` (konkreter Sensor) und `series_id` (Mess-/Analyse-/Aggregatreihe).
- Neue Geräte/Kanäle benötigen keinen SQL-Spalten- und UI-Komponenten-Zuwachs. **Neue Darstellungsarten** (z. B. Spektrum, Windrose, Kartenfläche) können dagegen eine neue Renderer-Implementierung erfordern.
- Messkanäle je Volk werden **zeitabhängig** aufgelöst: Sensor an Beute darf nach Geräte-/Volkwechsel nicht rückwirkend falsche Messungen ergeben.
- Kachelkonfiguration `tile_metrics` enthält Kanalpräferenzen/Fallback nach Messgröße; bei fehlenden Werten weder 0 noch grüne Validierung erfinden.

## Ungeklärte technische Fragen

PostgreSQL-Schema/Indexierung, TimescaleDB, PostGIS, Vue-Version und konkrete API-Namen erst nach ADR/fachlicher Freigabe festlegen. Für die aktuellen drei Bodensensoren fehlen Tiefen/Orte, Hardwaredetails, Rohdaten und die exakten Senderkennungen. Testdaten sind synthetisch zu kennzeichnen.
