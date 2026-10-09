# Teststrategie, Nachweise und Freigabe-Gates

**Version 0.1 – Entwurf.** Gilt für Hardware, Mechanik, Firmware, Formatter, Server und das integrierte LoRaWAN-System. **Teststatus ≠ Freigabestatus.** Jeder Test gilt nur für seinen dokumentierten Prüfling und Stand.

## T-01 Testpyramide (ohne Schein-HiL)

| Stufe | Nachweistyp | Beispiele / Beweisgrenze |
|---|---|---|
| **T0** | Anforderungen und statisches Review | Datenblatt-/Quellenkontrolle, Symbol-Pinliste, Architektur, Design-Reviews; sagt nichts über reale Schaltungsfunktion |
| **T1** | Automatischer Host-/Unit-Test | Codec, Zeitmathematik, FFT, Sicherheits-Input-Grenzen, PHP-Funktionen |
| **T2** | SiL/Integration/Modell | TTN-JSON → Formatter → Server, Crash-/Duplikat-/DST-Matrix, analoges/elektrisches/energetisches Rechenmodell; Annahmen explizit |
| **T3** | Build und Design-Checker | MCU-Zielkonfigurationen, Toolchain, C++/Go/PHP/JS, KiCad ERC/DRC (soweit vorhanden), reproduzierbarer Generator/BOM |
| **T4** | HiL/Labortest | reales Board/MCU/Funk/Sensor, elektrische Messinstrumente, Fault-Injection und Power-Cut, Temperatur-/Strom-/Timing-Messung |
| **T5** | kontrollierter Feldtest | definiertes Gehäuse/Solar/Standort, TTN/RX, Wetter, Logging, Laufzeit, Abnahme-/Rückholmöglichkeit |
| **T6** | Release-Reproduktion | unabhängiger Build/Export aus Tag, vollständige Artefakte, Prüfnachweise, bekannte Einschränkungen |

Jede behauptete höhere Stufe benötigt eigenständige Evidenz; ein T1-Signal-Sinus ist keine akustische T4-Kalibrierung und „KiCad ERC 0 Fehler“ beweist keinen fehlersicheren Ladepfad.

## T-02 Welche Tests sind Pflicht?

- **D0:** Textaussagen, Verweise, Versionen prüfen.
- **D1:** betroffene automatisierte T1/T2, Syntax/CI.
- **D2:** D1 + Schnittstellen-Goldenvektoren, Fehler-/Grenzfälle, T3-Build/Design-Check, definierte T4-Nachprüfung für Hardwareabhängigkeiten.
- **D3:** zusätzlich dokumentierte Gefährdungsanalyse, Fehler- und Wiederanlaufzustände, **unabhängige** Datenblatt-/Schaltungsprüfung und reale bzw. gleichwertige sicherheitsgerichtete Laborprüfung vor dem Hardware-/Feld-Gate.

**Nicht implementierte Tests:** `nicht geprüft`. **Übersprungener verpflichtender Test:** Gate rot, außer schriftlich akzeptierter nicht-sicherheitskritischer Ausnahme. Grün bei 5/5 CI-Jobs sagt ausschließlich, dass diese fünf Jobs bestanden wurden.

## T-03 Standardfelder eines Prüfberichts

Jeder eigenständige Testbericht enthält mindestens:

- Test-ID, Zweck, Requirement-/Befund-ID, erwartetes Verhalten / Abnahmegrenze;
- **exakten Git-SHA**, Build-/Artefaktkennung und Zielkonfiguration;
- bei HiL: **Platine und Revision** (Akku-/Hauptplatine getrennt), Seriennummer/Prüfling, tatsächlich bestückte Bauteile, Firmware-/Bootloaderstand;
- Prüfumgebung, UTC-Zeitpunkt, Messgerät-/Softwareversion, Spannungen, Temperatur, Aufbau/Schaltplanrevision, Sicherheitsbedingungen;
- Testschritte mit konkreten Befehlen/Stimuli, Ergebnis, tatsächliche Werte, Fehler-/Log-/Rohdatenablage;
- **Bestanden / fehlgeschlagen / übersprungen / blockiert / nicht ausgeführt** plus Grenzen und Restrisiken;
- verantwortliche prüfende Person, ggf. zweite Prüfung, Gate-Entscheid und Folgemaßnahme.

Ein Screenshot allein oder Aussagen wie „manuell geprüft“ ohne reproduzierbares Verfahren reichen bei D2/D3 nicht. Testberichte als neue Snapshots in [`docs/testberichte/`](../testberichte/README.md) ablegen, Historie nicht rückwirkend schönen. [Berichtsvorlage](vorlagen/pruefbericht.md).

## T-04 Testarten und Grenzfälle

**Firmware/FFT/Zeit:** Unter-/Überlauf, Nullen, Kurzpuffer, reservierte Bits, ADC-Sättigung, Rauschen, 50/59/60/61 Hz und hohe aliasierende Frequenzen, verlorene Samples, Sensorausfall, RTC-Reboot und Schattenregister, Standby nach Fehler, Kaltstart. Messgenauigkeit mit realen Referenzen prüfen.

**LoRa/TTN:** Protokoll FPort1/FPort2, Payload-Kürzung, Reihenfolge, Duplicate FCnt, Session-Recovery, MAC-Downlinks, RX1/RX2, schlechter RSSI/SNR, Duty-Cycle, Recovery nach Gatewayausfall und Energiemessung.

**Server/Anzeige:** Authentisierung, ungültiges JSON, fehlende Gerätezeit, Europe/Berlin DST doppelte 02-Uhr-Stunde, zurückgedrehte Serveruhr, Zeitquellen, mehrere gleichzeitige Webhooks, Crash zwischen CSV/Queue/BEEP, HTTP-Timeout, Schreibrecht entzogen, volle Disk, Queue-Drain, Browser-Zeitachse, Deployment mit alter/neuer Serverversion.

**Hardware/PCB:** Netzliste/Pins, max/min Versorgung, Kurz-/Verpolung mit begrenzter Energie, Sensorvakuum/ESD, thermische Verlustleistung, Load-Switch-Off-State, Schütz- und Lade-Recovery, Testpunkte, Pin1-Steckrichtung, Fertigungsmontage.

## T-05 Freigabe-Gates und Nachweismatrix

| Gate | Muss vorliegen | Sperrt |
|---|---|---|
| **G0 – Anforderung/Entwurf** | Ziel, Risiken/Annahmen, Schnittstellen/Versionsplan, Datenblatt-/Lizenzquellen | unklare oder sicherheitskritisch unbelegte Anforderungen als „abgenommen“ |
| **G1 – Integration in main** | passende Unit-/SiL- und Design-/Buildchecks für Änderungsrisiko; Quellstand, Review und Tests im Commit/PR | kaputte relevante CI, Geheimnisse, fehlende Regression bei nachgewiesenem Fehler |
| **G2 – Labor-/Musterfreigabe** | tatsächliche Board-/Bauteilrevision, relevante ERC/DRC-/Netzchecks, sichere Versuchsfolge, strombegrenzte Versorgung, Rettungsweg, P0-Schutzpfade ausreichend geklärt | unkontrollierter Akku-/Solarbetrieb, ungeklärte Sicherheits-P0 |
| **G3 – Begrenzt überwachter Feldtest** | bestandene zielhardwarebezogene HiL-Prüfung, Fehler-/Timeout-/Energie-/Lade-/Batterieprotokoll, Rückholmöglichkeit, Restrisiken bewusst akzeptiert | unbewiesene Schutzfunktionen, nicht gemessene relevante Strom-/Thermikzustände |
| **G4 – Open-Hardware-/Software-Release** | G0–G3 passend zum Release-Typ, Versions-/Kompatibilitätsmatrix, reproduzierbarer Source-/Build-/Fertigungsstand, Lizenzen/Herkunft, bekannte Grenzen, getrennte rechtliche Markt-Konformitätsprüfung soweit nötig | nicht reproduzierbare Artefakte, Lizenzkonflikte, undokumentierte kritische Risiken |

**Separate Releases sind zulässig:** Ein **Software-/Hosttest-Release** darf ohne neue PCB-Hardware erfolgen, ist aber als solcher gekennzeichnet und beweist keine hardwarebezogene G3-Freigabe. Ein unfertiger KiCad-Entwurf kann mit „experimentell – nicht fertigen“ veröffentlicht werden, nicht als fertiges Open-Hardware-Produkt.

## T-06 Nachweis gegen Anforderungen (Traceability)

Führe je freigaberelevanter Funktion eine kleine Matrix:

| Requirement | Quelle | Risiko | Implementierung/Schaltplan | Test-ID/Tier | Status |
|---|---|---|---|---|---|
| `REQ-HW-CHG-01` (Beispiel-ID) | verifiziertes Zell-Datenblatt | Übertemperatur | Akku-Plan/Sicherheitskette | `SCH-T02` / T4 | **offen, kein HiL** |
| `REQ-DATA-DST-01` (Beispiel-ID) | Datenmodell | Zeitdoppelstunde | Server-UTC-Pfad | `test_lora_eingang.sh` / T2 | Teststandsabhängig |

Die Beispiel-IDs sind **keine nachträglich eingeführten geprüften Anforderungen**. Jede neue echte ID wird im passenden Anforderungsdokument/Issue festgelegt.

## T-07 Release-/HiL-Archivierung

Artefakte eindeutig je `<release>/<board-revision>/<git-sha>/` ablegen: Testprotokolle, Geräte-Konfiguration **ohne Schlüssel**, Firmware-Binärdateien mit Checksummen, Schaltplan/Netzliste/ERC/DRC, KiCad/BOM/CPL/Gerber soweit Release-Typ verlangt, Bilder vom Aufbau, Stromkurven und verwendete Messgeräte. Keine Scheinbeweise. Berichte müssen von einem externen Mitwirkenden ohne private Hardwaredaten soweit möglich nachvollziehbar sein.

**Reviewpflicht für Änderungen am Regelwerk:** Neue Testpflichten brauchen Nachweis, wie sie ausführbar sind. Ein nicht installiertes `kicad-cli` darf nicht als bestandener Design-Check erscheinen.
