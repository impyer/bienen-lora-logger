# Projektentscheidungen und Governance-Register

**Stand:** 09.10.2026 · **Entwicklungsregelwerk:** Version 1.0, ANGENOMMEN.  
**Beschluss:** [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md).

Das Register trennt angenommene Verfahrensregeln von noch offenen Sachentscheidungen. **Offen** bedeutet nicht **bestanden**. Die Projektleitung trifft die formale Entscheidung; eine KI ersetzt weder die nötige unabhängige Sicherheitsprüfung noch einen Labornachweis.

| ID | Stand | Entscheidung bzw. offene Aufgabe |
|---|---|---|
| **GOV-01** | **OFFEN** | Für die Python-Generatoren in `hardware/kicad/` existieren ausdrückliche GPL-3.0-or-later-Dateihinweise, während `LICENSE.md` das Hardwareverzeichnis pauschal CERN-OHL-S-2.0 zuordnet. Rechteinhaber, konkret betroffene Dateien und Lizenzkonzept prüfen; **keine Lizenzhinweise stillschweigend ändern**. Vor einem als vollständig lizenzgeklärt veröffentlichten Open-Hardware-Fertigungsrelease auflösen. |
| **GOV-02** | **ANGENOMMEN – vorläufige Zuständigkeit** | Die Projektleitung/Maintainer verantwortet und dokumentiert G0/G1. D3-Sicherheitsänderungen (insbesondere Lithium-Akku, Ladefreigabe, Tiefentladeschutz) dürfen G2–G4 **nicht allein aufgrund von CI, Selbstreview oder KI-Review** passieren. Unabhängige fachkundige Sicherheitsprüfung und geeignete reale bzw. gleichwertige Labornachweise sind nötig. Fehlen diese, bleibt das Gate **OFFEN/BLOCKIERT**. |
| **GOV-03** | **ANGENOMMEN – Lieferumfang Hardware** | Ein als **fertigungsreif** bezeichnetes Open-Hardware-Release umfasst die bearbeitbaren Quellen inkl. Generatoren und eigener Bibliotheken, Netzliste/Schaltplan/ERC, PCB/DRC, Gerber/Bohrdaten, BOM/CPL, Montage-/Kabelpläne, Testpunkte und Prüfanweisungen. Unfertige Prototypen sind nur mit deutlicher Kennzeichnung „**experimentell, nicht fertigungsreif**“ zu veröffentlichen. |
| **GOV-04** | **OFFEN** | Konkrete elektrische, thermische, Energie-, Funk- und Messgrenzwerte für die real beschaffte Zell-, Board- und Bauteilrevision im Anforderungs-/Prüfplan aus Herstellerquellen festlegen. Ohne diese dürfen abhängige PCB-/Labor-/Feld-Gates nicht als bestanden gelten. |

## Konkrete nächste Fachaufgaben

1. **Sicherheit:** `SCH26-01` (potenzieller Wiederlade-Deadlock bei Tiefentladung), `SCH26-02` (hochohmige CE-Kette) und `SCH26-03` (Temperatur-Single-Fault) aus dem [Schaltplan-Review](../testberichte/2026-10-09-schaltplan-v01-review.md) weiter aufklären. **Kein HiL-Ergebnis durch den Beschluss erfunden.**
2. **GOV-01:** Rechtekette mit konkreten Dateinamen und den jeweiligen Autoren abgleichen.
3. **GOV-04:** Für tatsächlich ausgewählte Akkuzelle und PCB alle Soll-/Toleranzgrenzen mit Quellen und Test-IDs definieren.

Grundsatz-/Gate-Änderungen nur mit neuer ADR und dokumentierter Auswirkung. Historische Testberichte bleiben unverändert.
