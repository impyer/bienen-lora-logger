# Software- und Schnittstellenregeln

**Version 1.1 – am 09.10.2026 angenommen** (Änderungen: [ADR-0002](entscheidungen/ADR-0002-regelwerk-1-1.md)). Für STM32-Firmware, LoRaWAN-Stack, FFT/Codec, TTN-Formatter, PHP-LoRa-Eingang, beelogger-Integration, Python-Werkzeuge und Buildskripte.

## S-01 Führende Quellen, Toolchain, Architektur

- Jede Firmwarevariante besitzt **Zielhardware**, Boardrevision, Pinmatrix, MCU-Core-/Bibliotheksversionen und benannte Buildkonfiguration. BlackPill+RFM95/LMIC und zukünftige SMD-Platine+SX1262/RadioLib sind getrennte Targets; **ein erfolgreicher BlackPill-Build beweist nichts über die SX1262-Hardware**.
- Compiler, Core/SDK, wichtige Bibliotheken, Region, Frequenzband, Board-ID und Protokollversion sind reproduzierbar festgelegt. Änderungen an Toolchain als D2 behandeln, bei schutzrelevantem Treiber D3.
- Änderungen am Original-beelogger-Code dokumentieren; fremdes Original erhalten. Eigene PHP-Version **nur** aus `server/eigen_anpassen.py` regenerieren, nicht im generierten Ordner heimlich patchen. Formatter-Quelle `formatter.js` führt; minifizierte Fassung reproduzierbar generieren.
- Konfiguration mit ungefährlichen Beispieldaten, echte Schlüssel nur lokal/Secret Store; **kein** Gerätetoken in Testlog, Debugdump, Git-Verlauf oder Screenshot.

## S-02 MCU-Laufzeit, Energie und Fehlertoleranz

1. **Keine unbeschränkten Wartepfade** in ADC, I²C, OneWire, HX711, Radio, Flash, Netzwerk oder RTC; Timeouts und Fehlerfolgen samt geordnetem Schlaf-/Recovery-Pfad.
2. Sensorfehler, fehlende Kalibrierung, Timeout, ungültige RTC und ungültige FFT dürfen **keinen plausibel aussehenden Normalmesswert** erzeugen. Gültigkeits- und Statusfelder konsistent senden.
3. Vor jedem Speicher-/Funk- oder Schlafübergang sichere Zustände herstellen (ADC/DMA/IRQ/Power-Gates, Chip-Select, Watchdog). Fehlerbehandlung darf Energie nicht unbegrenzt verbrauchen.
4. RAM/Flash/Stack mit realer Buildvariante bilanzieren, besonders FFT-Puffer und Stackreserve. Keine unbegründete dynamische Speicher-/Stringnutzung im zeitkritischen Embedded-Pfad.
5. Zähler-/RTC-/LoRaWAN-Sitzungsstände crash-konsistent und gegen Unterspannungsabbruch abgesichert; Journal, Generation und CRC nach definiertem Verhalten. Funk- und Speicherfrequenz entsprechend Energiebudget begrenzen.
6. Watchdog, Brownout, Standby-Wakeup und Resetursache explizit testen; ein Softwarereset ersetzt keine sichere Hardwareabschaltung.

## S-03 Funk-/Datenformat als API

- `FPort 1` (legacy) und `FPort 2` (v2) besitzen eigene dokumentierte, versionierte Verträge. Byteoffsets, Endianness, Wertebereiche, Signierung, Skalierung, optionale Felder und ungültige Zustände sind in [Funkformat v2](../funkformat-v2.md) spezifiziert.
- Codecänderungen **atomar über** Encoder (C/C++), Formatter (JS und minifiziert), Serverfeldmapping und C-vs-JS-Goldenvektoren durchführen. Keine stillen semantischen Feldumdeutungen.
- Paketlänge/EU-Funkzeit/Duty-Cycle/ADR-/RX-Fenster mit reales Zielmodul und Datenrate prüfen. Regionale Grenzwerte nicht aus einem Laborlink ableiten.
- Kompatibilitätsverhalten für unbekannte Version, reservierte Bits, ungültige Länge, fehlende optionale Sensoren und Paketzähler festlegen.
- Bestehende ABP-/Framecounter- und RTC-/Slotraster-Entscheidungen sind dokumentierte Projektannahmen, keine Einladung zu stiller Protokollmigration; eine Änderung braucht ADR, Migration und Regression.

## S-04 Zeitbehandlung und Reproduzierbarkeit

- Intern und zwischen Geräten/Servern **UTC bzw. eindeutigen Unix-Timestamp** verwenden; Zeitzone nur für Anzeige (z. B. Europe/Berlin). Datum und Messzeit vs. Servereingangszeit unterscheiden.
- Gerätzeit nur bei validierter Synchronisationsfrische/Qualität verwenden, sonst explizit annotierten TTN-Fallback. Nie die DST-Doppelstunde als lokalen Text zur eindeutigen Speicherung verwenden.
- Regressionen: Sommer-/Winterzeit, Tages-/Monats-/Jahresgrenzen, ungültige UTC, Zeitrücksprung, getrennte Mess-/Empfangszeit, Reboot ohne RTC, Gerätezeit > zulässiger Drift, TTN-DeviceTimeReq/Ans.
- Tests dürfen **nicht** von der zufälligen Uhrzeit des CI-Runners abhängen: feste Zeitbasis/Clock-Injection oder dokumentiertes `libfaketime` wie beim bekannten beelogger-Speicherfehler.

## S-05 Server, Datenintegrität und Verfügbarkeit

1. Eingehende Webhooks/Dateien strikt validieren: Authentisierung, Gerätezuordnung, JSON-Limits, erlaubte Feld-/Wertebereiche, kein Pfad-/Codeinjektionspfad. Fehlerklassen für temporär/permanent/dupliziert unterscheiden.
2. **Idempotenz:** Eventkennung und Zeitstempelstrategie müssen Duplikate, parallele Verarbeitung und Retries unterscheiden. Test für Crash vor/nach Hauptspeicherung, Zusatzzeile, Acknowledge, BEEP/ThingSpeak.
3. Hauptdaten und Zusatz-/Rohdaten besitzen ein dokumentiertes Konsistenzmodell. Keine Erfolgsbehauptung allein aufgrund einer Dateigrößenänderung; alte/unvollständige Installation gesondert behandeln.
4. LoRa-Uplink-Retry/`nachholen` darf Ereignisse nicht ungesehen verlieren; auch „HTTP 202“ braucht lokales **dauerhaftes** Queueing und eine beobachtbare Wiederherstellung bei Dateisystemausfall.
5. Keine Passwörter in URLs, Protokollen oder HTTP-GETs, soweit Schnittstelle kontrolliert wird; wo eine Alt-Schnittstelle das erfordert, Risiko sichtbar machen und Zugriffslogs/HTTPS/Deployment absichern. Bekannte Ausnahme: beelogger-`PW` im GET ([EX-01](entscheidungen.md#ausnahmen)).
6. Abhängigkeiten (PHP-Erweiterungen, Browser-/goja-Version, TTN-Formatter) in CI pinnen oder bewusst aktualisieren; die vorhandene Anwendungslogik gegen neue Laufzeiten prüfen.
7. Externe Weitergabe (BEEP/ThingSpeak) nur für **wirklich akzeptierte** Daten und mit eindeutiger Duplikat-/Fehlerpolitik; kein Doppelsenden bei Timeouts ohne messbaren Nachtest.

## S-06 Review und Codequalität

- Funktionen mit klarer Verantwortung; Zustand/Seiteneffekte benennen; untrusted Inputs und Hardwarezugriffe von rein mathematischen Routinen trennen, damit Host-SiL möglich ist.
- Einheitliche Namen, Einheiten und Datentypen; physikalische Einheiten in Bezeichnern/Kommentaren (mV, mA, °C, Hz, dBFS, Unix-Sekunden) nennen. Integeroverflow/Signedness, Rundung und NaN prüfen.
- Für jede Fehlerbehebung ein konkreter Regressionstest mit alter Fehlersequenz; kritische Grenzfälle und Negativtests zählen mehr als nur hohe Coverage-Prozentzahl.
- Kein ungeprüftes Update von Bibliotheken; Toolchain-Buildvarianten und Speicherbericht vergleichen. Kommentare beschreiben **warum** und Annahmen, nicht nur die offensichtliche Syntax.
- Sicheres Logging: keine Secrets, keine persönlichen Standortdaten, begrenzte Loggröße, unverwechselbare Errorcodes. Genaue Testreproduktion ohne private Echtdaten ermöglichen.

## S-07 Minimalmatrix je Änderung

| Änderung | Mindesttests |
|---|---|
| V2-Feld/FFT | Host-Unit + Golden C/JS + Formatter-Mini/goja + betroffene STM32-Buildvarianten |
| Zeit-/Slot-/RTC-Code | Hostgrenzen + Simulationsregression + RTC-HiL als offene Aufgabe |
| Funk-/Power-Gate-/Watchdog | Kompilierung + Zeit-/Energiebudget + gezieltes MCU-HiL |
| Server-/Webhook-Logik | PHP-Unit + End-to-End mit eigener/Originalfassung, Retry/Parallelität + Zeit-Browser-Test soweit relevant |
| Sicherheit/Datenschutz/Token | negative Auth-/Format-/Berechtigungstests; keine vertraulichen Daten |
| Neuer SX1262-Treiber | eigener Toolchain-Build **und** tatsächliches DIO/BUSY/Reset/RX/TX/Sleep-HiL |

Vollständige Stufendefinition: [tests-freigaben.md](tests-freigaben.md).
