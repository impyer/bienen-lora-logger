# Behebung Schaltplan-Review V0.1 (SCH26-01 … SCH26-08), 09.10.2026

**Bezug:** [Schaltplan-Review V0.1](2026-10-09-schaltplan-v01-review.md) zu `fcd18fe`.
**Stand:** Arbeitsstand nach `fcd18fe`; vollständig eingecheckt als `2076c20` (nachgetragen 09.10.2026, REG26-05/REG26-13; der Zwischenstand `6dbba8d` enthielt nur einen Teil).

**Art des Nachweises:**
- Schaltungsanalyse mit Datenblattwerten.
- KiCad 10.0.6: Erzeugung, ERC mit allen Schweregraden gegen eine Liste begründeter Warnungen, Netzprüfungen an den **von KiCad exportierten Netzlisten**, eine Gegenprobe.
- **Nicht vorhanden:** Simulation (SPICE), Muster, Messung, CI-Lauf mit dem neuen KiCad-Job.

Entscheidung Philipp (09.10.2026): Die Ladesperre soll auch bei einem Einzelfehler unter 45 °C bleiben (SCH26-03, zweiter TMP390).

## Bewertung der Befunde

| Befund | Bewertung | Begründung |
|---|---|---|
| SCH26-01 P0 | **bestätigt, war ein echter Entwurfsfehler** | Ablauf siehe unten, mit HYCON-Datenblatt 11.3.1 und BQ25185-CE-Logik nachvollzogen. |
| SCH26-02 P1 | **bestätigt** | TMP390-Leckstrom ±0,1 µA [V: TI, ILKG]. Kritischer als im Review genannt: Der Leckstrom von Q2 (AO3400A, im heißen Fall µA-Bereich) hätte an 10 MΩ den CE-Pegel unter VIH ziehen und **Laden trotz Sperre erlauben** können. |
| SCH26-03 P1 | **bestätigt** | Einzelfehler in Stufe 1 hätte erst bei ca. 59,5 °C gesperrt. |
| SCH26-04 P1 | **bestätigt** | Kein ERC in der CI; Warnungen nicht bewertet; DLH-Footprint fehlt. |
| SCH26-05 P2 | **bestätigt** | R208 = 1 MΩ widersprach `versorgung.md` (100 kΩ). Meine Abweichung war nicht dokumentiert. |
| SCH26-06 P2 | **berechtigt** | Kabelplan fehlte. |
| SCH26-07 P2 | Stand der Arbeit | Blätter MCU, Funk, Waage, Mikrofon, Anschlüsse folgen. |
| SCH26-08 P2 | **teilweise** | C201 25 V war zu knapp: berechtigt. ADC ohne Versorgung kann praktisch nicht auftreten (siehe unten). |

### SCH26-01: Ablauf des Fehlers (nachvollzogen)

1. Der HY2111 schaltet bei Tiefentladung nur den **Entlade-FET** ab. Der Lade-FET bleibt an [V: HYCON 11.3.1].
2. Ohne Sonne fließt dann kein Strom zwischen P− und B−; P+ und die Masse der Hauptplatine nähern sich an. Der TMP390 an P+/P− ist ohne Versorgung, Q2 sperrt.
3. Kommt Sonne, versorgt der BQ25185 SYS über den Power-Path. R205 zieht CE auf High → **kein Laden**.
4. Der HY2111-GB gibt die Zelle nur frei, wenn ein Ladegerät den CS-Pin unter VCIP zieht [V: 11.3.1 Fall 1/2]. Das geschieht nur, wenn der BQ25185 lädt.
5. Ergebnis: dauerhafter Stillstand. Der Logger wäre nach einer einzigen Tiefentladung ohne Eingriff tot geblieben.

Eine Versorgung des TMP390 direkt aus der Zelle (B+/B−) habe ich verworfen. Q2 hätte dann über die Masse der Hauptplatine einen Strompfad **am Zellschutz vorbei** geöffnet. Bei 100 kΩ Vorwiderstand wären das grob 10 µA aus der tiefentladenen Zelle gewesen.

## Änderungen

| Befund | Änderung | Nachweis |
|---|---|---|
| SCH26-01 | **TMP_VCC**: LDO TPS70933 (2,7–30 V Eingang, 1 µA) am Ladereingang VIN_LADER versorgt beide TMP390, alle Gate-Pull-ups und speist den CE-Pull-up-Pfad. Die Ladesperre arbeitet, sobald eine Ladequelle da ist, unabhängig vom Zustand des Zellschutzes. Keine Verbindung der Sperre zu B+/B−. J3 5-polig. | Netzprüfung `netz_tests.py`: „U2/U3/Q2/Q3/R5/R8 ohne Verbindung zu B+/B−/P+“. **Gegenprobe:** U2 testweise wieder an P+ gelegt → 40/42, beide Prüfungen schlagen an. **[P]** Wiederanlauf mit strombegrenztem Zell-Emulator (SCH-T04). |
| SCH26-02 | R5/R8 100 kΩ nach TMP_VCC; R205 100 kΩ nach SYS. Rechnung: Gate 3,29 V; CE gesperrt ≥ 4,0 V auch bei 5 µA Leckstrom; CE erlaubt < 0,05 V. Pull-up-Ströme nur bei Sonne. | `versorgung.md` 3.3 (Tabelle Pegel) |
| SCH26-03 | **Stufe 2:** zweiter TMP390 U3 (42 °C) öffnet mit Q3 den NTC-Kreis → TS offen → BQ25185 sperrt, unabhängig vom CE-Pfad. TS wird nie auf Masse gezogen (Werksmodus). | Netzprüfung GATE_NTC, NTC_FUSS; Fehlertabelle `versorgung.md` 3.3 |
| SCH26-04 | `pruefen.sh`: zweimal erzeugen und vergleichen (identisch), ERC **mit allen Schweregraden** gegen `erc_erwartet.json` (jede neue Meldung = Fehler), Netzlisten- und PDF-Export, `netz_tests.py` (42 Prüfungen). Neuer CI-Job `kicad-schaltplan` mit KiCad 10 aus der offiziellen PPA, danach `git diff --exit-code`. | lokal: reproduzierbar, ERC OK (2 begründete Warnungen), 42/42. **CI-Lauf offen.** Footprint BQ25185 DLH: weiter offen, vor dem Layout. |
| SCH26-05 | R208 = 100 kΩ | Netzprüfung „Wert R208 = 100k“ |
| SCH26-06 | Kabelplan mit Pin-Tabelle, Crimpgehäuse PHR-5, Hinweis „gleichsinnig“, Prüfablauf mit strombegrenztem Netzteil (`anschluesse.md` 1.1) | Netzprüfung „Kabel Pin 1–5“ vergleicht beide Stecker |
| SCH26-07 | offen, nächste Blätter | – |
| SCH26-08 | C201 4,7 µF **50 V** X7R. ADC unversorgt: +3V3 kommt aus SYS, das bei Eingangsspannung immer versorgt ist; zudem begrenzt 3,3 MΩ den Strom auf unter 8 µA. Panel-Werte messen bleibt offen. | `versorgung.md` 3.1 |

**Ruhestrom:** 16,6 → **15,7 µA**. Die Ladesperre zieht nachts nichts mehr aus der Zelle. Reichweite ohne Laden 128–454 Tage.

## ERC-Stand (KiCad 10.0.6, alle Schweregrade)

| Projekt | Meldungen | davon erwartet |
|---|---|---|
| Akku-Platine | 0 | – |
| Hauptplatine | 2 | Footprint-Bibliothek „Bienen“ (BQ25185 DLH) fehlt; VBUS hat erst ein Ende |

## Offen

- **[P] Muster:** SCH-T01 … T08 aus dem Review, insbesondere T04 (Wiederanlauf) und T03 (Einzelfehler).
- AO3400A: VGS(th) und IDSS beim Bestellen am Datenblatt der gelieferten Variante prüfen.
- TPS70933DBVR: LCSC-Nummer und Bestand.
- KiCad-Version: Die CI installiert die jeweils aktuelle 10.0.x. Ändert ein Update das Dateiformat, schlägt der Diff-Vergleich an; dann neu erzeugen und einchecken.
