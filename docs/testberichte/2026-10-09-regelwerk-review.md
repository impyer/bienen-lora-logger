# Review Entwicklungsregelwerk 1.0 (Claude), 09.10.2026

**Geprüfter Stand:** `8fc2aa4` („docs: adopt engineering rules v1.0 …“, Vorgänger `72e4f79`).
Gelesen wurden aus den Git-Objekten des lokalen Klons:
- `docs/entwicklung/` (README, regelwerk, hardware, software, tests-freigaben, open-source-releases, entscheidungen, ADR-0001)
- `AGENTS.md`, `CONTRIBUTING.md`, PR-Vorlage
- `CLAUDE.md`, `CHANGELOG.md`
- **Nicht** gelesen: `docs/entwicklung/vorlagen/*` und `SECURITY.md` (in Pack-Dateien, nicht entpackt).

**Art:** statisches Dokumenten-Review (T0). Keine Tests betroffen.

## Gesamturteil

Das Regelwerk ist inhaltlich gut und passt zum Projekt:
- klare Evidenzstufen T0–T6
- Änderungsklassen D0–D3
- Freigabestufen G0–G4
- Grundsätze wie „Quellcode vor Klickzustand“ und „kein HiL behaupten“
- Verbot zerstörender Versuche an echten Zellen
- Uhrzeit-unabhängige Tests

Den Grundsätzen stimme ich zu. **Vor der verbindlichen Annahme** sollten aber vier Punkte geändert werden (E1–E4). E5–E12 sind Verbesserungen.

## Einwände, die vor der Annahme geklärt werden sollten

### E1 – Zirkelschluss bei G2 für D3

- **Fundstellen:** regelwerk R-09; tests-freigaben T-05; GOV-02; ADR-0001 Nr. 3.
- **Was dort steht:** D3-Funktionen dürfen G2 (Labormuster) erst bestehen, wenn „geeignete reale bzw. gleichwertige Labornachweise“ vorliegen.
- **Das Problem:** Labornachweise entstehen erst am Labormuster, also in G2. Wörtlich genommen kann der Akku-/Ladeteil nie ins Labor.
- **Vorschlag:**
  - **G2 (Labor)** bei D3: dokumentierte Gefährdungs-/Fehleranalyse (T0), Netz-/ERC-Prüfung (T3) und ein sicherer Versuchsplan. Das heißt Zell-Emulator, Strombegrenzung, keine echte Zelle für Fehlerversuche. Dazu eine zweite Prüfung des Plans (darf ein anderer Prüfweg sein).
  - **G3/G4 (Feld/Release)** bei D3: zusätzlich bestandene T4-Messungen **und** unabhängige fachkundige Prüfung.

### E2 – „Unabhängig fachkundig“ ist nicht bestimmt

- **Was fehlt:** Wer kann das in einem Ein-Personen-Projekt sein?
- **Warum es zählt:** Ohne Festlegung bleiben G3/G4 dauerhaft blockiert, oder die Regel wird stillschweigend umgangen.
- **Vorschlag:** In GOV-02 konkret festlegen:
  - Qualifikation, z. B. Elektrofachkraft oder Ingenieur mit Erfahrung in Li-Ion-Ladetechnik
  - „unabhängig“ = nicht der Entwerfer der geprüften Änderung
  - zulässige Form: schriftlicher Prüfbericht nach Vorlage
- Den **Maintainer namentlich** nennen (Philipp Schnabel, GitHub `impyer`).

### E3 – Veränderlicher Projektstatus steht in normativen Texten

- **Fundstellen:**
  - `AGENTS.md` Nr. 3: „`SCH26-01` bleibt ein offenes P0“
  - `hardware.md` H-02: „Hypothese“
  - `docs/entwicklung/README.md`, `entscheidungen.md`, ADR-0001
- **Das Problem:** Regeln altern nicht, Befundstände schon.
  - Der Stand ist bereits überholt: `SCH26-01` ist bestätigt und im Schaltplan behoben, siehe [Behebung SCH26](2026-10-09-sch26-behebung.md). Der Nachweis am Muster (T4) ist offen.
  - Das stand bei `8fc2aa4` nur deshalb nicht in GitHub, weil der Stand im Arbeitsverzeichnis noch nicht eingecheckt war.
  - Ein Agent, der `AGENTS.md` wörtlich befolgt, würde einen behobenen Befund erneut „beheben“.
- **Vorschlag:**
  - Ein **zentrales Befundregister** `docs/testberichte/befunde.md` mit ID, Priorität, gesperrtem Gate und Status, siehe E4.
  - Normative Texte verweisen nur darauf und nennen keine einzelnen Befundstände.

### E4 – Statusmodell für Befunde fehlt

- **Das Problem:** „Offen/behoben“ reicht bei D3 nicht. `SCH26-01` ist im Schaltplan behoben, aber nicht nachgewiesen.
- **Vorschlag:** Status nach Evidenzstufe:

| Status | Bedeutung |
|---|---|
| offen | |
| analysiert (bestätigt/verworfen) | |
| im Entwurf behoben (T0–T3) | |
| nachgewiesen (T4/T5) | |
| geschlossen | |

  Dazu je Befund das gesperrte Gate. Beispiel: „SCH26-01: im Entwurf behoben (T3: Netzprüfung + Gegenprobe), sperrt G2 bis Versuchsplan, G3 bis T4 SCH-T04“.

## Weitere Einwände und Verbesserungen

| Nr. | Fundstelle | Einwand | Vorschlag |
|---|---|---|---|
| E5 | R-06, AGENTS.md | **Zusammenarbeit mehrerer Agents ist nicht geregelt.** Genau das ist heute passiert: Claude schreibt ins Arbeitsverzeichnis, ChatGPT committet direkt auf GitHub. `8fc2aa4` baut auf einem Stand ohne die SCH26-Behebung auf. Beide haben `CLAUDE.md` und `CHANGELOG.md` geändert, beim nächsten `git pull` gibt es Konflikte. | Regel „Übergabe“: Vor jedem Wechsel zwischen Agents (oder Agent und Mensch) wird der Stand **committet und gepusht**. Jeder Agent beginnt mit `git pull` und nennt den Ausgangs-SHA. `CHANGELOG.md` nur oben ergänzen, nie umschreiben. `CLAUDE.md`/`AGENTS.md` nur gezielt ändern, nicht neu schreiben. |
| E6 | R-03 | `REQ-…`-Kennungen sind für **jede** neue Funktion und **jede** relevante Fehlerbehebung Pflicht. Das ist für ein Ein-Personen-Projekt viel Aufwand. Zudem gibt es schon Kennungen (Lastenheft F1…, V1…, M1…, A1…; Befund-IDs). | Bestehende Lastenheft-IDs als Anforderungs-IDs anerkennen (`LH-V3` usw.). MUSS nur für D2/D3, SOLL für D1. |
| E7 | H-06 Nr. 2, R-06 Nr. 4 | „Byte-Reproduzierbarkeit“ ist für PDF und Netzlisten unmöglich, weil sie ein Datum enthalten. „KiCad-Version pinnen“: Die PPA hält alte Unterversionen nicht dauerhaft vor. | Reproduzierbar für Quellen und `.kicad_sch`/`.kicad_sym`. Zeitgestempelte Exporte (PDF, Netzliste) sind ausgenommen und werden mitgeliefert. Hauptversion pinnen (KiCad 10), Unterversion im Bericht nennen. Weicht der Diff nach einem KiCad-Update ab: eigener Commit „Neuerzeugung mit 10.0.x“. So ist es in `pruefen.sh` und im CI-Job umgesetzt. |
| E8 | GOV-01 | Der Lizenzkonflikt ist berechtigt. Die Generator-Skripte habe ich mit GPL-Kopfzeile geschrieben; `LICENSE.md` ordnet `hardware/` CERN-OHL-S zu. | Entscheidung Philipp als Rechteinhaber. Vorschlag: Python-Werkzeuge in `hardware/kicad/` sind Software (GPL-3.0-or-later). Schaltpläne, Symbole und Footprints sind Hardware (CERN-OHL-S-2.0). Dazu SPDX-Kopfzeilen und eine Zeile in `LICENSE.md`. |
| E9 | S-05 Nr. 5 | „Keine Passwörter in URLs“: Die beelogger-Schnittstelle verlangt `PW` im GET (`beelogger_log.php?PW=…`). | Als dokumentierte Ausnahme nach R-08 eintragen (EX-01: Altschnittstelle, nur über HTTPS, Server-Logs schützen). |
| E10 | T-03 | Die Pflichtfelder (Messgerät, UTC-Zeitpunkt, Seriennummer …) passen für HiL, nicht für Analyse- und Review-Berichte. | Pflichtfelder je Stufe: T0–T3 (SHA, Gegenstand, Befehle, Ergebnis, Grenzen); T4/T5 zusätzlich Prüfling, Messgeräte, Umgebung. |
| E11 | Umfang | Rund 50 KB Regeltext. Im Alltag liest das niemand vollständig, Menschen nicht und Agents nicht immer. | Eine **Kurzfassung „Pflichtteil“** (1 Seite) als verbindlicher Einstieg; die Detaildokumente als Auslegung. |
| E12 | ADR-0001 | Das ADR ist „ANGENOMMEN“ mit „ausdrücklicher Zustimmung in der Projektunterhaltung“. Philipp will das Regelwerk aber erst nach diesem Review verbindlich machen. | Annahme erst nach Einarbeitung der Einwände; dann ADR mit Datum und Verweis auf dieses Review. |

## Zustimmung ohne Einwand

- R-02 Grundsätze, R-04 D0–D3, R-05 Prioritäten mit gesperrter Stufe, R-08 Ausnahmen mit Liste nicht ausnahmefähiger Punkte
- H-02 (Akku) vollständig, insbesondere Nr. 3 (keine Scheinredundanz), Nr. 4 (Wiederanlauf), Nr. 6 (keine Versuche an echten Zellen)
- S-04 Zeitbehandlung inklusive Uhrzeit-unabhängiger Tests
- O-02 Datenblätter verlinken statt kopieren
- O-06 Geheimnisse
- T-01 Evidenzstufen mit Beweisgrenzen

## Folge für den Arbeitsstand (Git)

Bei `8fc2aa4` liegt im lokalen Arbeitsverzeichnis noch **nicht eingecheckt** die Behebung SCH26 vor (Schaltpläne, Dokumente, `CLAUDE.md`, `CHANGELOG.md`).

Vorgehen:
1. lokal committen
2. `git pull`
3. Konflikte in `CLAUDE.md` und `CHANGELOG.md` zusammenführen: beide Inhalte behalten
4. den Befundstand in den Regeltexten nach E3 bereinigen
