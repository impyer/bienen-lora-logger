# Projektentscheidungen und Governance-Register

**Stand:** 09.10.2026 · **Regelwerk 1.0:** ANGENOMMEN · **Version 1.1:** Vorschlag [ADR-0002](entscheidungen/ADR-0002-regelwerk-review.md), bis zum Merge nicht wirksam.  
**Beschluss:** [ADR-0001](entscheidungen/ADR-0001-projektregelwerk.md).

Das Register trennt angenommene Verfahrensregeln von noch offenen Sachentscheidungen. **Offen** bedeutet nicht **bestanden**. Die Projektleitung trifft die formale Entscheidung; eine KI ersetzt weder die nötige unabhängige Sicherheitsprüfung noch einen Labornachweis.

| ID | Stand | Entscheidung bzw. offene Aufgabe |
|---|---|---|
| **GOV-01** | **OFFEN** | Für die Python-Generatoren in `hardware/kicad/` existieren ausdrückliche GPL-3.0-or-later-Dateihinweise, während `LICENSE.md` das Hardwareverzeichnis pauschal CERN-OHL-S-2.0 zuordnet. Rechteinhaber, konkret betroffene Dateien und Lizenzkonzept prüfen; **keine Lizenzhinweise stillschweigend ändern**. Vor einem als vollständig lizenzgeklärt veröffentlichten Open-Hardware-Fertigungsrelease auflösen. |
| **GOV-02** | **1.0 angenommen; Präzisierung 1.1 vorgeschlagen** | Maintainer **@impyer** dokumentiert G0/G1. Für **G2 D3** sind T0-Gefährdungsanalyse, T3-Designchecks und ein sicherer strombegrenzter Versuchsplan mit unabhängiger Plan-Gegenprüfung erforderlich; T4 erst danach. Für **G3/G4 D3** zusätzlich bestandene T4-Prüfungen und schriftliche Bewertung einer vom Entwerfer **unabhängigen, einschlägig fachkundigen Person** (z. B. mit Li-Ion-Ladeschutz-Erfahrung). Kein KI-/CI-Alleinentscheid. |
| **GOV-03** | **ANGENOMMEN – Lieferumfang Hardware** | Ein als **fertigungsreif** bezeichnetes Open-Hardware-Release umfasst die bearbeitbaren Quellen inkl. Generatoren und eigener Bibliotheken, Netzliste/Schaltplan/ERC, PCB/DRC, Gerber/Bohrdaten, BOM/CPL, Montage-/Kabelpläne, Testpunkte und Prüfanweisungen. Unfertige Prototypen sind nur mit deutlicher Kennzeichnung „**experimentell, nicht fertigungsreif**“ zu veröffentlichen. |
| **GOV-04** | **OFFEN** | Konkrete elektrische, thermische, Energie-, Funk- und Messgrenzwerte für die real beschaffte Zell-, Board- und Bauteilrevision im Anforderungs-/Prüfplan aus Herstellerquellen festlegen. Ohne diese dürfen abhängige PCB-/Labor-/Feld-Gates nicht als bestanden gelten. |

## Offene Governance-Fragen und Projektstatus

- **GOV-01:** Rechtekette der Python-Generatoren und Hardware-Quellen klären; Copyright und Dateilizenz bis zur Entscheidung unangetastet lassen.
- **GOV-04:** Tatsächlich gewählte Akku-/Board-/Bauteilgrenzwerte samt Datenblatt-, Toleranz- und Test-IDs festlegen.
- **Aktuelle Befunde:** Nur das [Befundregister](../testberichte/befunde.md) hält den Git-SHA-bezogenen technischen Stand. Dieses Governance-Dokument konserviert keine veraltete Einzelbefundbehauptung.

Grundsatz-/Gate-Änderungen nur mit neuer ADR und dokumentierter Auswirkung. Historische Testberichte bleiben unverändert.
