# Projektentscheidungen, Governance- und Ausnahmeregister

**Stand:** 09.10.2026 · **Entwicklungsregelwerk:** Version 1.1, ANGENOMMEN.
**Beschlüsse:** [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md) (Regelwerk 1.0), [ADR-0002](entscheidungen/ADR-0002-regelwerk-1-1.md) (Fassung 1.1).
**Maintainer:** Philipp Schnabel (GitHub `impyer`).

Das Register trennt angenommene Verfahrensregeln von noch offenen Sachentscheidungen. **Offen** bedeutet nicht **bestanden**. Die Projektleitung trifft die formale Entscheidung; eine KI ersetzt weder die nötige unabhängige Sicherheitsprüfung noch einen Labornachweis. Der Stand einzelner technischer Befunde steht **nur** im [Befundregister](../testberichte/befunde.md).

## Governance

| ID | Stand | Entscheidung bzw. offene Aufgabe |
|---|---|---|
| **GOV-01** | **ENTSCHIEDEN 09.10.2026** | Lizenzaufteilung in `hardware/` und `mechanik/`: **Python- und Shell-Skripte** (`*.py`, `*.sh`) unter **GPL-3.0-or-later**; **Schaltpläne, Symbole, Footprints, Layouts, KiCad-Projektdateien und Exporte** unter **CERN-OHL-S-2.0**, auch wenn sie von einem GPL-Skript erzeugt werden. Umsetzung: `LICENSE.md`, `SPDX-License-Identifier` in den Skripten. Rechteinhaber: Philipp Schnabel. |
| **GOV-02** | **ANGENOMMEN, präzisiert in 1.1** | G0/G1 dokumentiert der Maintainer; er entscheidet G2. **D3-Sicherheitsfunktionen:** G2 (Labormuster) erfordert Gefährdungs-/Fehleranalyse, Netz-/ERC-Prüfung und einen sicheren Versuchsplan (Zell-Emulator, Strombegrenzung, keine Fehlerversuche an echten Zellen), gegengelesen durch einen zweiten Prüfweg. G3/G4 erfordern zusätzlich bestandene T4-Messungen **und** ein **unabhängiges fachkundiges Review**: ein bis zwei befreundete Hardware-Entwickler des Maintainers, die die Änderung nicht selbst entworfen haben, mit schriftlichem Prüfbericht. CI, Selbstreview oder KI-Review allein genügen dafür nicht. |
| **GOV-03** | **ANGENOMMEN – Lieferumfang Hardware** | Ein als **fertigungsreif** bezeichnetes Open-Hardware-Release umfasst die bearbeitbaren Quellen inkl. Generatoren und eigener Bibliotheken, Netzliste/Schaltplan/ERC, PCB/DRC, Gerber/Bohrdaten, BOM/CPL, Montage-/Kabelpläne, Testpunkte und Prüfanweisungen. Unfertige Prototypen sind nur mit deutlicher Kennzeichnung „**experimentell, nicht fertigungsreif**“ zu veröffentlichen. |
| **GOV-04** | **OFFEN** | Konkrete elektrische, thermische, Energie-, Funk- und Messgrenzwerte für die real beschaffte Zell-, Board- und Bauteilrevision im Anforderungs-/Prüfplan aus Herstellerquellen festlegen. Ohne diese dürfen abhängige PCB-/Labor-/Feld-Gates nicht als bestanden gelten. Erster Schritt: Typ und Datenblatt der gekauften 18650-Zelle. |

## Ausnahmen

| ID | Regel | Ursache | Risiko | Zulässig | Ersatzmaßnahme | Owner | Review |
|---|---|---|---|---|---|---|---|
| **EX-01** | [S-05 Nr. 5](software.md) (keine Passwörter in URLs) | Die Altschnittstelle `beelogger_log.php` (beelogger M.40) erwartet das Log-Passwort als GET-Parameter `PW`. Der LoRa-Eingang ruft sie so auf. | Passwort kann in Webserver-Zugriffslogs, Proxys oder Browser-Verläufen landen. | eigener Server, Aufruf serverintern bzw. nur über HTTPS | HTTPS für externe Aufrufe; Zugriffslogs des Webservers für diese Pfade schützen bzw. ohne Query-String protokollieren; eigenes Log-Passwort nur für diesen Zweck; Passwort nie in Projektlogs (`le_log`) schreiben | Philipp Schnabel | bei jeder Änderung an Server/LoRa-Eingang, spätestens vor Feldrelease |

## Konkrete nächste Fachaufgaben

1. **Sicherheit:** offene und „im Entwurf behobene“ D3-Befunde laut [Befundregister](../testberichte/befunde.md) bis G2 führen (Gefährdungsanalyse, sicherer Versuchsplan); danach T4-Messungen und unabhängiges Review für G3.
2. **GOV-04:** Für tatsächlich ausgewählte Akkuzelle und PCB alle Soll-/Toleranzgrenzen mit Quellen und Test-IDs definieren.
3. **GOV-01 umsetzen:** `LICENSE.md` und SPDX-Kopfzeilen (mit Fassung 1.1 erledigt; neue Skripte erhalten die Kopfzeile von Anfang an).

Grundsatz-/Gate-Änderungen nur mit neuer ADR und dokumentierter Auswirkung. Historische Testberichte bleiben unverändert.
