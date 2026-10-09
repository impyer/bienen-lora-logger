# Hardware- und Mechanikregeln

**Version 1.1 – Review-Ergänzung als PR-Entwurf; bis zur Annahme bleibt 1.0 maßgeblich.** Gilt für `hardware/` und `mechanik/`, insbesondere eigene Akku-Platine, Hauptplatine mit STM32F411/SX1262 und Außen-Sensoren. Ziel: eine andere Person kann den Schaltplan **aus dem Repository** verstehen, prüfen, bestellen, aufbauen und sicher testen.

## H-01 Architektur / Eingänge

- Jede Platine MUSS eine eindeutige **Board-ID/Revision**, Eingangs-/Ausgangsschienen, maximale und minimale Umgebungs-/Betriebsbedingungen, Anschlussübersicht und Versionsbezug besitzen.
- Jede externe Quelle (PV1/PV2/USB/Akku) MUSS eine definierte **maximale Dauerspannung, Transientengrenze, Polungs-/Rückstrombetrachtung und thermische Grenze** besitzen. Ein TVS-Name oder das absolute IC-Maximum ersetzt keine Schutzrechnung.
- **Netzzuordnung** enthält Pin-Nummer, Pin-Name, Richtung, Versorgung und erlaubten Spannungspegel. Gleiche Namen über mehrere Blätter sind bewusst; digitale und analoge Fehlerpfade ausdrücklich berücksichtigen.
- Sensor-/Versorgungsschnittstellen beschreiben **„abgeschaltet“** (GPIO-Reset/Standby, Bus-Pull-ups, parasitäre Versorgung/ESD-Rückspeisung).

## H-02 Lithium-Zelle und Ladung — D3/Sicherheits-Gate

1. Genaues Zellmodell/Herstellerrevision und Datenblatt freigeben: Ladefenster, Grenzspannungen, empfohlene Ströme, Alterung und Temperaturbereich.
2. Die Ladung MUSS **hardwareseitig** gegen Über-/Untertemperatur und unerlaubte Spannungen geschützt werden. Firmware darf nur zusätzliche Warnung/Abschaltung leisten.
3. Einfache „zweistufige“ Nennung genügt **nicht**: Schaltgrenzen mit Toleranzen, Fehlerfällen und tatsächlicher Unabhängigkeit nachvollziehen. Ob Einzelfehlersicherheit gefordert ist, im Sicherheitsziel explizit festlegen. Nicht „redundant“ nennen, wenn die Ersatzstufe erst jenseits der zulässigen Zellgrenze arbeitet.
4. Überladung, Unterspannung, Kurzschluss/Überstrom, Lade-Recovery nach Abschaltung und Verhalten bei Quellunterbrechung beschreiben. **Fail-safe muss auch Wiederanlauf bei erlaubten Bedingungen ermöglichen**, ohne Schutzfunktionen zu umgehen.
5. Stecker-/Kabelfehler prüfen: Akku getrennt, NTC offen/kurz, CE-Leitung offen/kurz, verdrehter Stecker, Zelle entfernt, Quelle angelegt. Sicherheitsorientierte Leck-/Hochohmigkeitsrechnung über Temperatur/Feuchte.
6. **Keine schädliche Tiefentladung, Kurzschluss- oder Überhitzungsversuche an echten Li-Ion-Zellen** als frühe Diagnose. Zell-Emulator/Strombegrenzung/Fault-Injection und eine sichere Testumgebung verwenden.
7. PCB-/BOM-Freigabe erst nach ausreichenden Datenblatt-/Schaltungs-/Fault-Nachweisen und einem geeigneten sicheren Prüfkonzept.

**Aktuelle Befunde, Codefixes und HiL-Stände** stehen im [Befundregister](../testberichte/befunde.md); dieses normative Hardware-Regelwerk schreibt keinen zeitabhängigen Einzelbefund fest.

## H-03 Versorgung und Low Power

- Für jede Schiene: Spannungstoleranz, Ripple, Spitzenstrom, Start- und Abschaltreihenfolge, Lastkapazität, Rückspeisung, Ruhestrom, LDO-Dropout und thermischer Worst Case.
- Strom- und Energieplan pro Betriebsschritt: Standby, Sensoranlauf, HX711, ADC/FFT, Flash, Funk-TX, RX1/RX2, Fehlermeldung/Retry/Timeout; Sommer- und Winterszenario. **Annahmen** und **Messungen** separat kennzeichnen.
- Bei PV-Ladeschaltung: gemessene Panel-I/V-Kennlinie/Leerlaufspannung inkl. Kälte, Polung, Verpolung, VBUS-Kombination und Schottky-Dioden. ADC-Eingänge dürfen auch bei VDDA=0 nicht unerlaubt über Speisepfade injizieren.
- Abblockkondensatoren physisch am Versorgungs-Pin, Schleifenfläche klein; DC-Bias/Temperatur/ESR/Spannungsderating berücksichtigen. „10 µF“ ohne wirksame Kapazität bei Betriebs-V ist unvollständig.
- Ruhestromziel und Brownout-/Recovery-Werte als messbare Abnahmekriterien je Board-/Firmwareversion hinterlegen, nicht durch ungeprüfte Tabellen „garantieren“.

## H-04 MCU, Funk und digitale Schnittstellen

- STM32: alle VDD/VSS/VDDA/VSSA/VCAP/VBAT/BOOT/NRST/SWD- und Quarz-Pins im vollständigen Schaltplan, mit Datenblatt-Pinprüfbericht; Pin-Multiplex gegen Firmware-Pinmatrix testen.
- Funk: **konkrete** Ra-01SH-Chip-/Modulrevision prüfen (SX1262 vs. LLCC68), Quarz/TCXO, DIO2-RF-Switch, BUSY, NRST, Antennenfeed/Koax, TX-Peakstrom und thermische Reserve. Mechanische Antennen-Freifläche dokumentieren.
- SPI-Flash: Power-loss-Atomicity, CRC/Generation, Wear-Level/Write-Endurance und Schutz beim Standby. Nicht unkalibriert alle ADC-Rohdaten dauerhaft speichern.
- Außenbusse: Pull-up an korrekter Versorgung, I²C-Kapazität/Rise-Time inkl. Kabel, OneWire-Parasitärstrom und ESD-/Injektionsstrom. Sensoren lassen sich im Fehlerfall erkennen; keine fiktiven Werte.
- HF-Betrieb nur im zulässigen regionalen Frequenz-/Leistungs-/Sendezeitrahmen; genaue Rechts-/Netzparameter beim Release aktuell verifizieren. Gateway im Meterabstand beweist keine Link-Budget-Reserve.

## H-05 Analogsensoren, Waage und Mikrofon

- HX711: Spannungs-/Pegelkompatibilität zwischen 5-V-Brücke/Analogteil und 3,3-V-MCU, Wärme-/Einschwingzeit, Kalibrierung, Leitungsbruch, Sättigung, Schirmung und Fehlerstatus.
- ADC/Mikrofon: Verstärker-Aussteuerung und Ruhespannung bei min/max, analoger Anti-Aliasing-Frequenzgang mit Toleranzen, ADC-Quellimpedanz/Abtastzeit, Jitter und Schall-Kalibrierung; dBFS **nicht** als dB-SPL ausgeben.
- Gewicht, Temperatur, Feuchte, Spannung und FFT: Messbereich und Unsicherheit / Wiederholbarkeit im Prüfplan. Ohne gültige Kalibrierung **keinen scheinbar gültigen Ersatzwert** übertragen.

## H-06 KiCad als reproduzierbare Quelle

1. **Führende Quelle** in V0.1: `hardware/kicad/*.py` und `werkzeug/`; generierte `.kicad_sch`/Bibliotheken/`.pdf` gehören nur zum zugehörigen Generatorstand. Änderungen an generierten Schaltungen werden **zuerst** in Python gepflegt. Eine spätere Umstellung auf manuell geführtes KiCad nur via ADR/Freigabe.
2. Generator deterministisch ausführen und **KiCad-Hauptversion 10** als Toolchainvorgabe festlegen; verwendete Unterversion (z. B. 10.0.x) im Review protokollieren. **Deterministische** `.kicad_sch`/`.kicad_sym` und Generatorquellen im sauberen Checkout bytegenau vergleichen. PDFs/Netzlisten mit Datums-/Metadatenfeldern **nicht** auf Bytegleichheit prüfen, sondern semantisch; Quelle, Erzeugungszeit und Toolversion protokollieren. Regeneration bei Toolupdate als nachvollziehbaren separaten Commit ablegen.
3. **ERC aller relevanten Projekte:** 0 ungeklärte elektrische Fehler. Warnungen einzeln begründen, nicht pauschal ignorieren. Kein Ersetzen von Powerquellen durch wahllose `PWR_FLAG`-Symbole, um ERC grün zu färben.
4. **Netlist-/Symbol-Pin-/Footprint-Abgleich** für alle Custom-Symbole gegen Hersteller-Pinzeichnung; Doppel-Gates, Thermal-Pads, No-Connects und Package-Padzahl prüfen. Unvollständige Blätter explizit als unvollständig markieren.
5. Vor PCB-Bestellung: **DRC**, reale Stackup-/Kupfer-/Abstandsregeln, thermische Vias, Rückstrom-/HF-Schleifen, ESD direkt am Eintritt, mechanischer Bauraum, Masseschluss und Testpads bestätigen.
6. Reale Bestückbarkeit gegen gewählten Hersteller bestätigen: finale Footprints, aktuelle BOM/MfrPN/LCSC/Alternativen, Polaritäts-/Pin-1-Bild, DNP, Assembly-Seite, Gerber/Drill/CPL, 3D/STEP, Kabelführung. Platzhalter-Footprints sperren die betreffende Fertigungsfreigabe.

## H-07 Fertigungs- und Labor-Gates

- **Vor erster Platine bzw. G2-Labormuster:** Offene P0-Schutzrisiken mit einem **sicheren, begrenzten Versuchsplan** bearbeitbar machen; D3-Gefahrenanalyse T0, T3/ERC-/Netz-/Footprintprüfung, Strombegrenzung/Zell-Emulator, definierter Rettungsweg und unabhängige Gegenprüfung des Plans. Die eigentlichen T4-Schutzmessungen entstehen erst nach diesem Gate; ohne T4 **keine G3-/Fertigungsfreigabe**.
- **Erster Einschaltversuch:** Netzteil strombegrenzt, keine wertvolle Zelle und keine unkontrollierte Solarquelle, Messung Rail für Rail; Debug-/SWD-Rettungsweg vorbereitet.
- **HiL-Messprotokoll:** Boardrevision, Aufbau/Seriennr., Firmware-SHA, Messgerät/Skalierung, V/T, Originaldaten, erwartete Grenzen, Ergebnis; gezielte Recovery-/Stör-/Stecker-/Sensorfehler.
- **Feldtest:** mechanische Dichtigkeit, Kondensation, Temperaturzyklen, Blitz-/ESD-Risikoabschätzung, Solar-/Akkureserve, Antenne, sichere Befestigung und Rückholmöglichkeit.

Weitere Nachweise/Gates: [tests-freigaben.md](tests-freigaben.md).
