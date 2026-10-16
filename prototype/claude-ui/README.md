# Bienenlogger UI – Claude-basierter interaktiver Prototyp

Stand: 16.10.2026 · UI-/Bedienprototyp **ohne Produktionsfreigabe**

## Start

`index.html` direkt im Browser öffnen, oder `python3 -m http.server 8000` und `http://localhost:8000` besuchen. Keine Pakete / kein CDN erforderlich. Auf kleinen Bildschirmen Menü-Symbol verwenden.

## Datenquellen und Grenzen

- Originale Claude-Referenz: `Bienenlogger Weboberfläche.html` des Betreibers; berücksichtigt die vier Ansichten **Bienenstand**, **Volk-Cockpit**, **Umwelt & Tracht** und **Datenquellen & Kanäle** und deren Farb- und Informationskonzept.
- **BEEP**: ergänzte Eingabemaske für Durchsicht/Maßnahme, checklistenartige Merkmale, Königinneninformationen, Beutenzeichnung und zeitliche Änderungen. Alle neuen Einträge sind **ausschließlich lokale Browser-Testentwürfe**; kein BEEP-API-Schreibzugriff. BEEP bleibt vorerst die fachliche Quelle der Beutenkonfiguration.
- **beelogger**: Gewichts- und Temperaturkurven, Nachtmedian **00:00–04:00 Uhr Europe/Berlin**, Tagesbilanz nur bei aufeinanderfolgenden Tagen, Überblick aller gewählten Völker und FFT-Bänder. Keine erfundenen Trends bei nur einem Messpunkt.
- Default: ein realer, kalibrierter Einzelmesspunkt aus dem vom Betreiber gelieferten TTN-Uplink für Volk 8 (16.10.2026); Volk 5 hat ohne Dateiimport keine Messreihe. Zum Test der Diagramme gibt es gesondert gekennzeichnete, synthetische **Musteranalyse**.
- Die Beuten- und Königinnenangaben zu Volk 8 stammen aus der *hochgeladenen Claude-Referenz* und sind nicht selbst aus der BEEP-API verifiziert.
- Boden-Einzelwerte aus dem Projektkontext sind **keine** historische Zeitreihe. GTS und Blütenprognose bleiben ausdrücklich unberechnet.
- JSON-Dateien im Format `{ "devices": [ { "volk": "Volk 8", "rows": [ {"zeit_utc":"...", "gewicht_kg":..., "temperatur_c":..., "fft_baender":[] } ] } ] }` werden im Browser importiert (keine Netzwerkanfrage). Für andere Völker und Standorte muss das später auf ein generisches ID-/Rollenmodell umgestellt werden.

## Architekturbezug

- BEEP Base, klassischer beelogger und Eigenentwicklung sind **alternative Primärgeräte**, maximal eines je Volk zur selben Zeit. Zusatzgeräte können ergänzende Kanäle liefern.
- Physische Beute, Volk, Königin, Standort, Gerät und Kanal sind verschiedene Identitäten. Beutenkonfigurations- und Stockkartenereignisse erhalten einen Gültigkeitszeitpunkt und müssen später BEEP-Provenienz tragen.
- **Persistenz dieser Vorschau = `localStorage`** des Browsers, nicht PostgreSQL und nicht BEEP. Testentwürfe lassen sich als JSON exportieren. Produktionszugriff, Authentifizierung, Eingabevalidierung auf dem Server, revisionssichere Historie und echte BEEP-Synchronisation fehlen noch.
- Gemeinsamer TTN-Empfang/BEEP-Decoder im separaten PR #13 (`server/lora/...`). Die Darstellung kann die API-Antwort manuell als JSON importieren, um die Messdatenanzeige ohne Serverdeploy zu testen.
- Keine DevEUIs, BEEP-Schlüssel, Personenangaben, geografischen Koordinaten oder Kontozugangsdaten sind für den Prototyp notwendig. Ein öffentlicher GitHub-Stand sollte Demo-Völkernamen und Beispiele vor Veröffentlichung prüfen.

## Funktionsprüfung

1. Bienenstand zeigt zwei Karten (Volk 5 ohne Messwert und Volk 8 mit Einzelpunkt).
2. Musteranalyse einschalten: beide Karten mit Kurven und berechenbaren Nachtmedianen, wieder ausschalten: realer Einzelpunkt.
3. Volk-Cockpit Zeitbereiche und Völker wechseln.
4. Unter Stockkarte eine Durchsicht mit Checkliste erfassen; sie erscheint in der Chronik.
5. Beutenkonfiguration testweise ändern; Zeichnung und Historie ändern sich, BEEP nicht.
6. Kanalregister um einen Testkanal ergänzen; JSON-Testdatei importieren und Export prüfen.
7. Browseransicht mobil prüfen.

**Nächste Integrationsstufe:** FastAPI-Lese-API und PostgreSQL-Importer nach `server/datenbank/schema.sql` (Schema derzeit Entwurf), BEEP-Stockkarte read-only importieren, Authentifizierung und Versionshistorie; die Liveanzeige nicht ungeprüft an öffentliches Web anbinden.

### Zusätzliche Interaktionen (Stand 16.10.2026)

- Die Test-Checkliste lässt sich um eigene Merkmale erweitern. Durchsichten speichern die ausgewählten Merkmale im lokalen Entwurf.
- Eine simulierte Beutenänderung erzeugt zugleich einen lokalen Stockkarten-Ereigniseintrag, damit die fachliche Beziehung sichtbar wird.
- In der Gewichtsanalyse werden Entwurfseinträge im betrachteten Zeitraum als **gestrichelte Datumslinien** markiert; bei fehlender Uhrzeit ist dies ausdrücklich keine exakte Zeitzuordnung.
GitHub-Version: Die Standortbezeichnung ist anonymisiert (`Teststand`). Reale Zuordnungen gehören ausschließlich in die geschützte lokale Konfiguration.
