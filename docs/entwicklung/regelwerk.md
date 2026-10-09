# Projektregelwerk: Design, Programmierung, Entwicklung, Zusammenarbeit

**Version 1.1 – ANGENOMMEN am 09.10.2026** ([ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md), Änderungen 1.1: [ADR-0002](entscheidungen/ADR-0002-regelwerk-1-1.md)). Gilt als verbindlicher Projektstandard für Repository `impyer/bienen-lora-logger`, seine Software, Hardware, Mechanik, Testdaten, Dokumentation und releasespezifische Artefakte.

## R-01 Sprachregelung

- **MUSS:** verbindliche Bedingung für die betreffende Entwicklungs-/Freigabestufe.
- **SOLL:** Standardweg; Abweichungen sind mit technischem Grund zu dokumentieren.
- **KANN:** freiwillig.
- **BLOCKIERT:** Ohne Korrektur oder explizit definierte, sichere Projektentscheidung wird das angegebene Freigabe-Gate nicht bestanden.
- **Anforderung** beschreibt beobachtbares Sollverhalten, **Annahme** ungeprüfte Grundlage, **Nachweis** tatsächlich ausgeführte Prüfung, **Freigabe** die dokumentierte Entscheidung.

„Pass“, „grün“, „geprüft“ und „freigegeben“ werden immer mit **Prüfstufe und Gegenstand** angegeben. Beispiel: „C++-Hosttests bestanden für Commit X; ADC-HiL offen“, nicht „Firmware vollständig geprüft“.

## R-02 Projektgrundsätze

1. **Sicherheit vor Funktion:** Lithium-Akku, Lade-/Unterspannung, Überspannung, ESD, Hitze, fehlerhafte Verkabelung und unbeaufsichtigter Betrieb haben Vorrang vor Laufzeitoptimierungen.
2. **Quellcode vor Klickzustand:** Die versionierten Originalquellen und die beschriebenen Generatoren müssen Änderungen vollständig reproduzieren; manuelle Änderungen an generierten Dateien sind nicht die führende Quelle.
3. **Belegbare Aussagen:** Jedes Ergebnis hat Commit, Testumgebung, Soll/Ist, Grenzen und Status. Nicht ausgeführt, übersprungen und fehlgeschlagen sind niemals „bestanden“.
4. **Offene Architektur:** Keine Abhängigkeit von nicht freigegebenen fremden PCB-Daten; fremde Texte/Code/Bibliotheken nur mit klarer Herkunft und kompatiblen Rechten.
5. **Kompatibilität:** Legacy FPort 1, V2 FPort 2, bestehende Datenformate, beelogger M.40 und TTN-Geräte werden nicht ohne geplante Migration inkompatibel geändert.
6. **Energie als Systemanforderung:** Jeder stromrelevante Baustein, Timeout, Retry und jedes zusätzliche Funkpaket hat eine begründete Energiewirkung.
7. **Experiment/Release getrennt:** Ein kontrollierter Labortest darf offene Nicht-Sicherheitsrisiken besitzen; diese dürfen nicht unsichtbar in einen Produktivrelease übergehen.

## R-03 Anforderungen und Rückverfolgbarkeit

Für Änderungen der Klassen **D2 und D3 MUSS**, für **D1 SOLL** eine knappe Anforderung vorliegen, vorzugsweise im betroffenen Modul-/Hardwaredokument oder Issue:

- stabile Kennung. **Bestehende Kennungen gelten als Anforderungs-IDs:** Lastenheft-Zeilen werden als `LH-<Zeile>` zitiert (z. B. `LH-V3` Laderegler, `LH-F5` I²C außen, `LH-M4` Klemmen). Neue Kennungen nur, wo es keine passende gibt (z. B. `REQ-FW-017`, `REQ-DATA-006`);
- Zweck, erwartetes Sollverhalten und nachvollziehbare Grenz-/Fehlerfälle;
- betroffene Revisionen/Schnittstellen und Abnahmetest;
- verantwortliche Person, Status `geplant / umgesetzt / testbar / abgenommen / verworfen`.

Prüfberichte referenzieren Anforderungen und **Befund-IDs**. Ein Befund `SCH26-01` ist ein Risiko und **keine** neue Norm oder Messung. Für kleinste Dokumentationskorrekturen reicht der PR-/Committext.

## R-04 Änderungsklassen und Review-Aufwand

| Klasse | Typische Änderung | Minimum vor Integration |
|---|---|---|
| **D0** | Tippfehler, Links, rein redaktionelle Texte | Review der Aussage/Links; keine erfundenen Ergebnisse |
| **D1** | Hostalgorithmus, Dokumenten-/Skriptberechnung, nicht kritische Firmware/Serverfunktion | statische Prüfung, relevante Unit-/Regressionstests, CI |
| **D2** | Funkprotokoll, Zeitstempel, Persistenz, Strom-/Wake-Logik, Bauteilwert/Pin/PCB-Netz | D1 plus Schnittstellen-/Fehlertests, betroffene Simulationen, HiL-Aufgaben für echte Hardware |
| **D3** | Zellschutz, Ladefreigabe, thermische Sicherheit, Spannungslimits, Recovery, gefährliche Fehlermodi | formalisierter Gefährdungs-/Einzelfehlerreview, zweiter unabhängiger Prüfweg, **nicht** zur Fertigung/Feldfreigabe ohne geeignete Hardware- oder gleichwertige Sicherheitsnachweise |

Eine Änderung darf nicht niedriger eingestuft werden, nur weil wenige Quelltextzeilen betroffen sind. Bei Unsicherheit die höhere Klasse wählen.

## R-05 Befund-Prioritäten

| Stufe | Bedeutung | Konsequenz |
|---|---|---|
| **P0** | unmittelbares bzw. plausibles hohes Sicherheits-/Datenintegritätsrisiko, das die benannte Stufe sperrt | verantwortlichen Gate-Owner informieren; keine betroffene Fertigungs-/Feldfreigabe bis Nachweis oder sichere Abhilfe |
| **P1** | wesentlicher funktionaler oder qualitativer Mangel | vor dem betroffenen Release-Gate korrigieren oder begründete, **nicht sicherheitsgefährdende** Ausnahme beschließen |
| **P2** | begrenzter Mangel oder offene Robustheitsprüfung | mit Test-/Maßnahmenplan und Termin/Owner weiterführen |
| **P3** | Verbesserung ohne aktuelle Freigabewirkung | Backlog |

Die Priorität muss zusammen mit der **gesperrten Stufe** stehen: Ein Akku-P0 sperrt Platinenfertigung, aber nicht das Beheben eines README-Tippfehlers. Eine KI-Bewertung ist **kein** alleiniger Sicherheitsfreigabeakt.

### R-05a Befundregister und Statusmodell

Alle Befunde stehen mit Status im **zentralen [Befundregister](../testberichte/befunde.md)**. Es ist die einzige Stelle für den aktuellen Stand eines Befunds. Regeltexte, `AGENTS.md`, `CLAUDE.md` und READMEs nennen **keine** Befundstände, sondern verweisen auf das Register. Prüfberichte bleiben historische Snapshots.

| Status | Bedeutung | Beleg |
|---|---|---|
| **offen** | gemeldet, nicht bewertet | Befundbericht |
| **analysiert – bestätigt / verworfen** | technisch bewertet; bei „verworfen“ mit Begründung | Analyse mit Quellen |
| **im Entwurf behoben** | Änderung umgesetzt und mit T0–T3 geprüft (Review, Host-/SiL-Test, ERC/Netzprüfung) | Behebungsbericht, Commit |
| **nachgewiesen** | mit T4/T5 am realen Prüfling bestätigt | Mess-/Feldbericht nach T-03 |
| **geschlossen** | nachgewiesen bzw. sicher entfallen und vom Maintainer geschlossen | Registereintrag mit Datum |

Je Befund nennt das Register zusätzlich das **gesperrte Gate** (z. B. „sperrt G3 bis SCH-T04“). Ein Befund im Status „im Entwurf behoben“ ist **nicht** nachgewiesen.

## R-06 Git-/Entwicklungsablauf

1. Vor Arbeit aktuellen `main`-SHA, betroffene Dokumente, das [Befundregister](../testberichte/befunde.md) und tatsächlich akzeptierte ADRs prüfen.
2. **Übergabe zwischen Beteiligten (Menschen und Agents):** Vor jedem Wechsel wird der Arbeitsstand **committet und gepusht**. Wer beginnt, holt zuerst den aktuellen Stand (`git pull`) und nennt den Ausgangs-SHA im Ergebnis. Es arbeitet immer nur **ein** Beteiligter gleichzeitig am selben Stand; parallele Arbeit nur auf getrennten Branches. `CHANGELOG.md` wird nur oben ergänzt, nicht umgeschrieben; `CLAUDE.md`, `AGENTS.md` und Regeltexte werden gezielt geändert, nicht neu geschrieben.
3. Änderung in kleinen, thematisch getrennten Schritten entwickeln; D2/D3 bevorzugt mit separatem Branch und Pull Request, auch wenn nur eine Person beiträgt.
4. Für Risiko-/Protokoll-/Schutzänderungen zunächst Sollverhalten und reproduzierbaren roten Regressionstest bzw. dokumentierte Vorher-Messung festhalten; dann Fix und grünen Nachtest.
5. Generatoren **und** notwendige eingecheckte Artefakte aktualisieren. Byte-Reproduzierbarkeit der **Quellen und erzeugten Quelldateien** prüfen (z. B. `.kicad_sch`, `.kicad_sym`, minifizierter Formatter, abgeleiteter Server). **Zeitgestempelte Exporte** (PDF, Netzliste, Berichte mit Datum) sind davon ausgenommen; sie werden mit dem Stand mitgeliefert und vom Diff-Vergleich ausgeschlossen. Unbeabsichtigte Binär- oder Testausgaben nicht committen.
6. CI vollständig ausführen. Rot/übersprungen heißt: den betroffenen Gate-Status nicht freigeben. Ausnahmen nur schriftlich mit Reichweite und Gegenprüfung.
7. Commit/PR-Text enthält **warum, was, betroffene IDs, Tests, Einschränkungen**. Sicherheitskritische Entscheidungen als ADR dokumentieren.
8. Kein Agent und kein Maintainer veröffentlicht Schlüssel oder verschiebt unbeaufsichtigte Releases auf Basis eines bloßen Kompilierlaufs.

## R-07 Architekturentscheidungen

Technisch weitreichende oder schwer rückgängig zu machende Entscheidungen werden als **ADR** dokumentiert (siehe [Vorlage](vorlagen/entscheidung.md)) mit Entscheidung, Alternativen, Auswirkungen, Unsicherheiten und Revisionsmöglichkeit. **Verabschiedete** Entscheidungen ändern sich nur durch eine neue ADR, nicht durch stille Umgestaltung.

Bekannte bestehende Projektentscheidungen, deren Neubeurteilung eine explizite Freigabe benötigt: BlackPill/RFM95 mit LMIC/ABP als Prototyp; bewusst akzeptierte TTN-Framecounter-Konfiguration; 10-s-Slotraster; FPort1-/FPort2-Kompatibilität; eigener SX1262/RadioLib-Strang als separate Firmware; Original beelogger M.40 unangetastet und abgeleitete Serverfassung aus Patch/Generator.

## R-08 Ausnahmeprozess

Ausnahmen stehen im [Entscheidungsregister](entscheidungen.md#ausnahmen) (`EX-…`). Eine Ausnahme enthält **ID, betroffene Regel, fachliche Ursache, Risiko, zulässige Umgebung, Ersatzmaßnahme, Owner, Ablaufdatum/Reviewtermin und Entscheidung**. Ausnahmen sind im PR, ADR oder Testbericht sichtbar. **Nicht ausnahmefähig:** vorsätzlich unsichere elektrische Versuche, Geheimnisveröffentlichung, falsche Testergebnisse, fehlende Lizenzrechte oder stilles Überschreiten verbindlicher Schutzgrenzen. Für P0 im Sicherheitsbereich darf es höchstens einen **separaten, sicheren Laborversuch** geben – keine ungeprüfte Produktivfreigabe.

## R-09 Aufgabenverteilung und KI

- **Maintainer: Philipp Schnabel (GitHub `impyer`).** Er **entscheidet** über Architektur, Risiken, Freigaben und Veröffentlichung. Für G0/G1 ist die dokumentierte Maintainer-Prüfung maßgeblich.
- **D3-Sicherheitsfunktionen** ([GOV-02](entscheidungen.md)):
  - **G2 (Labormuster):** dokumentierte Gefährdungs- und Fehleranalyse (T0), Netz-/ERC-Prüfung (T3) und ein **sicherer Versuchsplan** (Zell-Emulator, strombegrenzte Quellen, keine Fehlerversuche an echten Zellen). Der Versuchsplan wird von einem zweiten Prüfweg gegengelesen (Person oder unabhängiges Werkzeug/Agent).
  - **G3 (Feldtest) und G4 (Release):** zusätzlich bestandene **T4-Messungen** am realen Prüfling **und** ein **unabhängiges fachkundiges Review**.
  - **Unabhängig fachkundig** heißt: Hardware-Entwickler mit Erfahrung in Elektronikentwicklung, der die geprüfte Änderung **nicht** selbst entworfen hat; Ergebnis als schriftlicher Prüfbericht nach [Vorlage](vorlagen/pruefbericht.md). Vorgesehen sind ein bis zwei befreundete Hardware-Entwickler des Maintainers (Namen im jeweiligen Prüfbericht).
- Beitragende **liefern** Quelländerung, Tests, Dokumentation und ihre expliziten Annahmen.
- Reviewer/zweiter Prüfweg **prüft** kritisch und dokumentiert Widerspruch; kann auch unabhängiges Testtool sein, aber eine KI ersetzt keine qualifizierte Sicherheitsbewertung.
- Coding-Agents **lesen zuerst** `CLAUDE.md`, dieses Regelwerk, aktuelle Befunde und den betroffenen Code; keine fiktiven Tool-/Hardwaretests, kein unautorisiertes Umschreiben fremder Lizenzhinweise.
- Bei Ein-Personen-Pflege: dokumentierte Selbstprüfung + getrennte unabhängige Gegenprobe; D3 **nicht** allein aufgrund von Agent + CI über G2 hinaus freigeben.

## R-10 Änderungs- und Reviewrhythmus

Mindestens vor jeder PCB-Bestellung und jedem Feldrelease offene P0/P1 und Ausnahmen durchgehen; Dokumentversion, Datum und Projektstatus aktualisieren. Nach jeder wesentlichen Fehlerbehebung den betreffenden Test sowie das Risiko-/Nachweisregister pflegen. **Alte Berichte bleiben historische Snapshots.**

Spezialregeln: [Hardware](hardware.md) · [Software](software.md) · [Test-Gates](tests-freigaben.md) · [Open Source/Release](open-source-releases.md).

## R-11 Geltung und technische Durchsetzung

Gültig **ab Annahme-Commit zu Version 1.0, in der Fassung 1.1 ab deren Annahme-Commit,** für neue Änderungen, neue Hardwareversuche, PCB-Bestellungen und neue Freigabeentscheidungen. [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md) dokumentiert den Beschluss. Alte Prüfergebnisse bleiben unveränderte historische Snapshots; das Regelwerk wertet diese nicht nachträglich auf.

Bis Branch-Protection/Reviewpflicht **tatsächlich** konfiguriert und überprüft sind, erfolgt die Einhaltung organisatorisch mit dokumentierten Commits/PRs und bestehenden CI-Checks. Offen gebliebene ERC-/HiL-Nachweise sind **nicht bestanden**. Siehe [Entscheidungsregister](entscheidungen.md).
