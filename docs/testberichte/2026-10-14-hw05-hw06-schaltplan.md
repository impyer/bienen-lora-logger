# Prüfbericht: HW-05 (USB mit VBUS-Erkennung) und HW-06 (eine Platine, Akku auf der Hauptplatine)

- **Prüfbericht-ID:** SCH-2026-10-14-HW05-HW06
- **Prüfdatum (UTC):** 14.10.2026
- **Bezug:** Entscheidungen HW-05 und HW-06 (Philipp, 14.10.2026); Befunde SCH26-10 und SCH26-06; Lastenheft K5, F9, V1, M3; `sicherheit-akku.md` Abschnitt 10
- **Ausgangs-SHA:** `bbabcd4` + gelieferter, noch nicht gepushter Routing-Stand
- **Artefakte:**
  - `hardware/kicad/hauptplatine.py`: neues Blatt „Akku“; J203 entfernt; R307/R308; J704 Pin 11 frei
  - entfernt: `akku_platine.py`, `akku-platine/`, `netzliste/akku.net`, `pdf/akku.pdf`
  - Prüfwerkzeuge: `netz_tests.py`, `pin_footprint.py`, `pruefen.sh`, `erc_erwartet.json`
  - Platzierung: `werkzeug/platine_bestuecken.py`, `platine_fein.py`, `platine_start.py`
  - Dokumente: Lastenheft, `versorgung.md`, `mcu-funk.md`, `anschluesse.md`, `sicherheit-akku.md`, Entscheidungsregister, Befundregister, READMEs, `CLAUDE.md`
- **Änderungsklasse:** **D3** (HW-06: Li-Ion, Zellschutz, Ladesperre – Schaltung unverändert, Ort geändert) und D2 (HW-05: USB)
- **Teststufe:** T3 (KiCad 10.0.6: ERC, Netzprüfung, Pin-/Footprint-Abgleich, DRC mit Schaltplanabgleich). Keine Messung, kein Muster. **G2 bleibt offen.**

## HW-06: Akku auf der Hauptplatine

- Die Schaltung der früheren Akku-Platine ist unverändert übernommen, als Blatt „Akku“ mit Bauteilen 8xx: Halter BT801 (Keystone 1042), Messbrücke JP801 und J801 (DNP), HY2111 U801 mit R801/C801/R802, FS8205 Q801, Ladesperre Stufe 1 (U802, Q802, R803–R805, C802) und Stufe 2 (U803, Q803, R806–R808, C803, NTC TH801).
- Die Kabelnetze sind jetzt direkt verbunden: P+ → VBAT, CE_FREI → CE_LADEN, NTC und TMP_VCC als globale Netze zum Blatt Versorgung. Die Stecker J1 (Akku) und J203 (Haupt) entfallen; ebenso die PWR_FLAGs, die nur wegen des zweiten Projekts nötig waren.
- **Sicherheitsrelevant:** B− (Zelle bis Schutz-FET) bleibt ein eigenes Netz und ist nicht GND. Die Netzprüfung prüft das ausdrücklich, ebenso wie bisher „Ladesperre ohne Verbindung zu B+/B−/VBAT“.

## HW-05: USB mit VBUS-Erkennung

- Teiler **R307 33 kΩ / R308 82 kΩ** von VBUS an **PB13** (ST AN4879). J704 Pin 11 (bisher EXT_PB13) ist frei.
- Firmware-Anforderungen (USB-CDC, Pull-up nur bei VBUS, 48-MHz-PLL) stehen in `mcu-funk.md` 1.3.

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Erzeugung zweimal identisch, Gegenprobe | bestanden |
| ERC Hauptplatine (alle Schweregrade) | **0 Meldungen** |
| Netzprüfung | **168/168** (Akku-Prüfungen auf das Blatt Akku umgestellt; neu: B− ≠ GND, VBUS_SENSE, J704 Pin 11 frei; entfallen: Kabelprüfung J1 ↔ J203) |
| Pin-/Footprint-Abgleich | 161 Bauteile, 0 Abweichungen |
| `tests/alle_tests_linux.sh` | rc = 0 |
| Platine neu erzeugt (start → bestücken → fein → Lagen → Fanout) | DRC 0 Verstöße (nur Bestückungsdruck und Ausbruchstiche), Schaltplanabgleich 0; **ohne Routing** |

## Platine (Platzierungsvorschlag für den Layouter)

- Der Halter BT801 (Courtyard 88 × 22 mm) liegt waagerecht unter dem Funkmodul, mit Abstand zur Funkkante und zum Laderegler. B+ liegt links, B− rechts.
- Zellschutz und Ladesperre sitzen am rechten Halterende (B−-Insel klein). Der STM32 ist 3 mm nach unten gerückt.
- Die Platine ist **nicht geroutet**: Das Routing vom 13.10.2026 passte nicht mehr zum Schaltplan. Das Layout übernimmt der beauftragte Layouter (Fiverr), siehe Pflichtenheft.
- **Aufgabe für den Layouter [P]:** TH801, U802 und U803 unter die Zelle mit Wärmeleitpad. Im Vorschlag liegen sie neben dem Halter, weil KiCad sonst Courtyard-Überlappungen meldet. Außerdem prüfen, ob der Halter unten offen ist.

## Grenzen

- Nur T3. Die D3-Änderung braucht vor G2 das Gegenlesen nach `sicherheit-akku.md` Abschnitt 10 und die Versuche am Muster.
- Firmware für USB-CDC und VBUS-Erkennung ist nicht Teil dieses Stands.
