# Sicherheitsanalyse Akku und Laden (D3)

- **Dokument:** SAF-AKKU, Fassung 0.1 vom 09.10.2026
- **Änderungsklasse:** D3 (Li-Ion, Ladefreigabe, Tiefentladeschutz)
- **Bezugsstand:** `main` = `2076c20` (Akku-Platine `hardware/kicad/akku_platine.py`, Versorgung `hardware/kicad/hauptplatine.py`, Beschreibung [`versorgung.md`](versorgung.md) 3.2–3.5)
- **Zweck:** Voraussetzung für Gate **G2** (Labormuster) nach [tests-freigaben.md](../docs/entwicklung/tests-freigaben.md) T-05 und [hardware.md](../docs/entwicklung/hardware.md) H-02: Gefährdungsanalyse, Fehler- und Wiederanlaufzustände, sicherer Versuchsplan, Rückverfolgbarkeit (Befunde REG26-06/07).
- **Teststufe dieses Dokuments:** T0 (Analyse aus Schaltplan und Datenblättern). **Keine Messung, kein Muster, kein HiL.**
- **Verfasser:** Claude (Agent). **Gegenlesen durch einen zweiten Prüfweg steht aus**; G2 entscheidet Philipp. G3/G4 brauchen zusätzlich T4-Messungen und das unabhängige fachkundige Review (GOV-02).

Kennzeichnung: **[V]** aus Datenblatt/Quelle belegt, **[A]** eigene Annahme oder Rechnung, **[P]** am Muster zu prüfen.

## 1. Sicherheitsziele

| ID | Ziel | Einzelfehlersicherheit gefordert? |
|---|---|---|
| SZ-1 | Kein Laden über **45 °C** Zelltemperatur (Auslegungsgrenze, solange die Zellvariante unbekannt ist, GOV-04) | **Ja** für Fehler in der Temperaturerfassung und Signalkette (Stufe 1/2). Grenze des Nachweises: Abschnitt 4, H-A |
| SZ-2 | Kein Laden unter **0 °C** | Ja, mit der NTC-Kaltsperre als Rückfall (Reserve knapp, H-D) |
| SZ-3 | Keine Überladung über 4,2 V | Ja: BQ25185 (4,1 V) und HY2111 (4,28 V) sind unabhängig |
| SZ-4 | Keine schädliche Tiefentladung (Zelle bleibt ≥ 2,5 V nach Abschaltung) | Ja: BQ25185 BUVLO 3,0 V und HY2111 2,9 V |
| SZ-5 | Kurzschluss im Kabel, Stecker oder auf der Hauptplatine wird an der Zelle abgeschaltet | Einstufig (HY2111 + FS8205 an der Zelle). Die Strombegrenzung im BQ25185 wirkt nur auf SYS |
| SZ-6 | Wiederanlauf nach jeder Schutzabschaltung bei erlaubten Bedingungen, **ohne** einen Schutz zu umgehen (H-02 Nr. 4) | – (Funktionsziel) |
| SZ-7 | Ladeleistung im Laderegler bleibt unter der thermischen Grenze | Der IC regelt selbst bei 100 °C (TREG) [V] |

Vorschlag zur Entscheidung (Philipp, E-1): **SZ-1 einzelfehlersicher** für die Temperaturerfassung, die Signalkette und alle Stecker- und Leitungsfehler; der Laderegler selbst als gemeinsamer Punkt wird als Restrisiko bewertet (H-A).

## 2. Annahmen und Grenzen

| Nr. | Annahme | Folge, falls falsch |
|---|---|---|
| A-1 | Zelle BAK N18650CP, Variante offen; Laden 0–45 °C (strengere Händlerangabe) [V: versorgung.md 3.3] | Grenzen neu rechnen (GOV-04, REG26-12) |
| A-2 | HY2111-**GB** (2,90 V / 4,28 V, Freigabe nur durch Ladegerät, 0-V-Laden erlaubt) [V: HYCON-Datenblatt] | Wiederanlauf und Tiefentladeschutz neu bewerten |
| A-3 | Solar-Eingang dauerhaft ≤ 12 V, Absolutgrenze BQ25185 25 V, TVS SMAJ12A [V/A] | Eingangsschutz neu auslegen (SCH26-08, Panelmessung offen) |
| A-4 | Gehäuseinnentemperatur im Sommer bis 60 °C, im Winter bis −20 °C [A] | Wärmepfade, Kaltsperre, Selbstentladung neu rechnen (REG26-10) |
| A-5 | Leckströme der Ausgänge und FETs wie im Datenblatt, Platine sauber und trocken (Schutzlack nicht vorgesehen) [A] | Pegel neu rechnen; Feuchte als [P] |

## 3. Gefährdungsliste

| ID | Gefährdung | Ursache | Schwere | Schutz im Entwurf | Restrisiko |
|---|---|---|---|---|---|
| G-01 | Laden bei Übertemperatur → beschleunigte Alterung, im Extrem thermisches Durchgehen | Sommer, Sonne aufs Gehäuse, Ladewärme | hoch | Stufe 1 (U2 42 °C → CE), Stufe 2 (U3 42 °C → TS offen), NTC 59,5 °C | gemeinsamer Punkt BQ25185 (H-A), Wärmeverzug Zelle → Sensor [P] |
| G-02 | Laden unter 0 °C → Lithium-Abscheidung | Winter, Sonne am Morgen | hoch (schleichend) | U2 OUTB +5 °C → CE; NTC +1,7 °C → TS | Reserve NTC zu 0 °C nur ca. 1,7 K (H-D) |
| G-03 | Überladung | Defekt BQ25185, falscher VSET-Widerstand | hoch | BQ25185 4,1 V; HY2111 4,28 V (Lade-FET aus) | HY2111-Toleranz [P] |
| G-04 | Tiefentladung, danach Laden einer zu tief entladenen Zelle → Kupferauflösung, interner Kurzschluss | lange Dunkelphase, Ruhestrom, Defekt | hoch | BUVLO 3,0 V, HY2111 2,9 V und Ruhezustand 0,1 µA | HY2111 erlaubt das Laden ab 0 V; eine monatelang entladene Zelle würde wieder geladen (H-B) |
| G-05 | Kurzschluss in Kabel, Stecker oder Hauptplatine | Quetschung, Feuchte, Bestückung | hoch | HY2111 Überstrom ca. 3 A an der Zelle [A], Kurzschlussabschaltung [V] | Kabelquerschnitt und JST-PH-Strom für 3 A prüfen (H-F) |
| G-06 | Überspannung am Eingang | Panel kalt, unbekannter Paneltyp, Störung auf dem Kabel | mittel | TVS SMAJ12A, BQ25185 OVP 18,5 V, C201 50 V | Ausfall TPS70933 (H-C) |
| G-07 | Überhitzung des Ladereglers | hohe Eingangsspannung, 150 mA | mittel | TREG 100 °C, 150 mA, Abstand zur Zelle | Messung offen (HW26-11) |
| G-08 | Falsch gesteckt oder falsch gecrimpt | Montage, Reparatur | mittel bis hoch | JST PH kodiert, Kabel 1:1, Kabelplan | Adertausch beim Crimpen (H-E) |
| G-09 | Unbeabsichtigter Werksmodus durch TS auf Masse | NTC-Leitung kurz | gering (sicherer Zustand, Akku getrennt) | Stufe 2 öffnet statt zu schließen | Logger steht bis zur nächsten Quelle |
| G-10 | Leckströme durch Feuchte heben die 100-kΩ-Knoten an oder ziehen sie herunter | Kondensat im Bienenstock | mittel | 100 kΩ statt 10 MΩ (SCH26-02) | Rechnung nur mit Datenblattwerten; Feuchte [P] |

## 4. Einzelfehleranalyse der Ladesperre

Zustände: **gesperrt** = sicher; **erlaubt** = Laden möglich; maßgeblich ist, ob nach dem Fehler Laden außerhalb 0–45 °C möglich wird.

| Fehler | Wirkung | Laden außerhalb 0–45 °C möglich? |
|---|---|---|
| U2 OUTA hängt hochohmig (Heißsperre Stufe 1 tot) | Stufe 2 sperrt über 42 °C (≤ 43,5 °C mit Toleranz [V]) | nein |
| U2 OUTB hängt hochohmig (Kaltsperre Stufe 1 tot) | NTC sperrt unter ca. +1,7 °C | nein, Reserve knapp (H-D) |
| U2 Ausgänge dauernd Low | CE High → dauernd gesperrt | nein (Verfügbarkeit leidet) |
| Q2 Drain-Source kurz | CE dauernd Low; Stufe 2 und NTC wirken | nein (heiß: 43,5 °C; kalt: 1,7 °C) |
| Q2 offen | CE High → gesperrt | nein |
| R5 (Gate-Pull-up Q2) offen | Gate driftet; Q2 eher aus → gesperrt; undefiniert bei Feuchte | nein, Stufe 2 wirkt |
| R205 (CE-Pull-up) offen | CE driftet; Verhalten des CE-Eingangs ohne Beschaltung unbekannt (H-G) | nein, Stufe 2 wirkt |
| Ader CE_FREI unterbrochen | CE über R205 High → gesperrt | nein |
| Ader CE_FREI an GND (Kurz) | CE Low → Stufe 1 aus; Stufe 2 wirkt | nein |
| U3 OUTA hochohmig | Q3 leitet dauernd → NTC wirkt, Stufe 1 wirkt | nein |
| U3 Ausgang dauernd Low | Q3 sperrt → TS offen → gesperrt | nein |
| Q3 Drain-Source kurz | NTC wirkt dauernd; Stufe 1 wirkt | nein |
| Q3 offen | TS offen → gesperrt | nein |
| NTC offen (Bauteil oder Ader) | TS offen → gesperrt | nein |
| NTC kurz (Bauteil oder Ader NTC an GND) | TS an Masse → **Werksmodus**, Akku getrennt [V]; Stufe 1 weiter aktiv | nein (sicherer Stillstand) |
| TMP_VCC fehlt (LDO, Ader) | beide TMP390 ohne Versorgung → Q2 aus (CE High), Q3 aus (TS offen) | nein |
| TMP_VCC zu hoch (TPS70933 schlägt IN–OUT durch) | bis zur Panelspannung an TMP390 (Grenze ca. 6 V [A]) und an den Gates (AO3400A ±12 V [A]) → Bauteile können ausfallen, Ausfallart unbekannt | **unbekannt** (H-C) |
| BQ25185 defekt (Lade-FET durchlegiert oder Logik ignoriert CE/TS) | **beide Stufen wirken über denselben IC** → keine Temperatursperre mehr; Überladung begrenzt nur noch HY2111 (4,28 V) | **ja** (H-A) |

**Ergebnis:** Für alle Fehler in Temperaturerfassung, Signalkette, Steckern und Leitungen ist SZ-1 einzelfehlersicher. **Nicht** einzelfehlersicher sind der Ausfall des Ladereglers selbst (H-A) und eine Überspannung auf TMP_VCC (H-C).

## 5. Bewertung der Lücken (Befunde, Stand im Register)

| ID | Lücke | Bewertung | Mögliche Abhilfe (Entscheidung offen) |
|---|---|---|---|
| H-A → **HW26-16** | Gemeinsamer Punkt BQ25185: Stufe 1 (CE) und Stufe 2 (TS) steuern denselben IC | Ausfall eines Linearladers im Ladepfad ist selten, aber nicht ausschließbar; dann lädt er ohne Temperaturgrenze bis zur HY2111-Abschaltung bei 4,28 V | a) als Restrisiko akzeptieren und begründen; b) Stufe 2 trennt zusätzlich den Ladereingang (P-FET in VIN_LADER, angesteuert von U3), damit unabhängig vom BQ25185 |
| H-B → **HW26-17** | HY2111-GB erlaubt das Laden einer Zelle ab 0 V; eine nach der Abschaltung monatelang weiter entladene Zelle würde ohne Prüfung wieder geladen | Nach Abschaltung zieht der Schutz 0,1 µA [V]; der Abfall von 2,9 V auf unter 2,0 V hängt von der Selbstentladung ab und ist nicht bekannt [P] | a) Firmware meldet die Abschaltung (DeviceTimeReq-Neuanlauf erkennbar) → Zelle tauschen; b) Schutz-IC-Variante ohne 0-V-Laden prüfen; c) Vorladestrom des BQ25185 (30 mA) als ausreichend schonend begründen |
| H-C → **HW26-18** | Ausfall des TPS70933 mit Durchschlag legt bis zu 12 V (25 V Störung) auf TMP_VCC | Ausfallart der TMP390 dann unbekannt | Klemmung an TMP_VCC (Z-Diode 5,1 V mit Vorwiderstand oder TVS) auf der Hauptplatine; Rechnung und Bauteilwahl offen |
| H-D → **HW26-19** | Kältereserve: Fällt die Kaltsperre von U2 aus, sperrt erst der NTC bei ca. +1,7 °C; Toleranz von NTC (B 3435, 1 %) und BQ25185-Schwelle ergibt grob ±1 K [A] | Abstand zu 0 °C knapp, aber positiv | Toleranzrechnung mit Datenblattwerten; gegebenenfalls Kaltschwelle über Vorwiderstand anheben (Heißschwelle steigt dabei, Stufe 2 bleibt maßgeblich) |
| H-E → in SCH-T09 | Adertausch im Kabel (z. B. P+ auf TMP_VCC, NTC auf CE_FREI) | Folgen je Vertauschung nicht vollständig untersucht | Kabelprüfung vor dem ersten Anschluss (SCH-T09), vorkonfektionierte Kabel |
| H-F → in SCH-T01 | JST PH ist für ca. 2 A je Kontakt spezifiziert [A]; HY2111-Abschaltung bei ca. 3 A | Kontakte und Kabel könnten bis zur Abschaltung überlastet werden | Nennstrom aus JST-Datenblatt prüfen; Strombegrenzung über den Überstrom-Widerstand oder FET-Wahl anpassen |
| H-G → in SCH-T03 | Verhalten des BQ25185-CE-Eingangs ohne äußere Beschaltung (interner Pull-down?) nicht belegt | Nur relevant, wenn R205 ausfällt; Stufe 2 schützt dann | Datenblatt prüfen, am Muster messen |

## 6. Schutz- und Wiederanlaufzustände

| Zustand | Auslöser | Wirkung | Rückkehr in den Normalbetrieb |
|---|---|---|---|
| Normal, Laden | Quelle da, 5–42 °C, Zelle < 4,1 V | BQ25185 lädt mit 150 mA (Vorladung 30 mA) | – |
| Laden gesperrt (Temperatur) | außerhalb 5–42 °C (Stufe 1) bzw. > 42 °C (Stufe 2) | Laden aus, SYS läuft aus der Quelle | Temperatur zurück im Fenster mit 5 K Hysterese |
| Nacht | keine Quelle | TMP_VCC aus, Sperre stromlos; Logger aus der Zelle | Quelle kommt |
| BUVLO | Zelle < 3,0 V | BQ25185 trennt die Zelle von SYS; Logger aus | Quelle kommt → Laden (bei erlaubter Temperatur) |
| Zellschutz Tiefentladung | Zelle < 2,9 V | HY2111 schaltet den Entlade-FET aus, Ruhezustand 0,1 µA | **nur durch Laden:** Quelle → TMP_VCC → Sperre prüft Temperatur → BQ25185 lädt über die Body-Diode → HY2111 gibt frei [V: HYCON 11.3.1]. Prüfung SCH-T04 |
| Zellschutz Überladung | Zelle > 4,28 V | Lade-FET aus | Zelle < 4,08 V |
| Zellschutz Überstrom/Kurzschluss | > ca. 3 A [A] | Entlade-FET aus | Last entfernt [V, Freigabebedingung im Datenblatt prüfen] |
| Werksmodus | TS länger auf Masse | Akku getrennt | Quelle anlegen [V] |

## 7. Sicherer Versuchsplan (Labormuster)

### 7.1 Grundregeln

1. **Keine echte Zelle** in den Versuchen SCH-T01 bis SCH-T09. Die Zelle kommt erst nach bestandenen Versuchen und nach Philipps G2-Entscheid dazu, zuerst unter Aufsicht und auf nicht brennbarer Unterlage.
2. Jede Quelle ist strombegrenzt. Netzteile bleiben während der Versuche in Reichweite (Not-Aus = Ausgang aus).
3. Erstes Einschalten: Sichtprüfung, Widerstand P+/P− und VIN/GND messen, dann VIN mit **20 mA** Begrenzung, erst danach höher.
4. Messwerte werden mit Gerät, Einstellung und Uhrzeit protokolliert (T-03); erfundene oder geschätzte Messwerte sind unzulässig.

### 7.2 Aufbau

| Teil | Ausführung | Grenzwerte |
|---|---|---|
| Solar-Ersatz | Labornetzteil an VIN | 0–12 V, Strom **200 mA** |
| USB-Ersatz | Labornetzteil an VBUS | 5,0 V, 200 mA |
| Zell-Emulator | **muss Strom aufnehmen können**: 2-Quadranten-Netzteil oder Netzteil mit parallelem Lastwiderstand (z. B. 22 Ω / 2 W, nimmt bei 3,7 V ca. 170 mA auf) [A] | 0–4,3 V, Strom **500 mA** Quelle; Ladestrom muss vollständig in den Emulator fließen können |
| Temperatur | Heizplatte bzw. Kältespray oder Klimaschrank für die Akku-Platine, Referenzthermometer am TMP390; für TS-Versuche Widerstandsdekade statt NTC | 0–60 °C an der Platine |
| Messung | Multimeter an CE, TS, TMP_VCC, SYS; Strommessung in der Messbrücke JP1/J2 | – |

**Abbruchkriterien:** Emulatorspannung > 4,25 V; Ladestrom > 180 mA; Platine > 65 °C; Ladestrom > 1 mA im Zustand „gesperrt“; Geruch, Verfärbung, unerwartete Erwärmung.

### 7.3 Versuche

| Test-ID | Ziel | Durchführung (Kurzform) | Abnahme | Bezug |
|---|---|---|---|---|
| SCH-T01 | Grundfunktion | Emulator 3,2/3,7/4,1 V, VIN 0/6/12 V, VBUS 5 V | Ladeschluss 4,1 V ± Datenblatt; Ladestrom 150 mA (Vorladung 30 mA); SYS und TMP_VCC im Soll; Ruhestrom nachts im Soll der Energiebilanz | LH-V3, SZ-3/7 |
| SCH-T02 | Temperaturfenster | Platine 0/4/5/7/36/37/42/44/45/55/60 °C, steigend und fallend | Laden nur zwischen 5 und 42 °C (Toleranz TMP390 ±1,5 K); Hysterese 5 K; im Zustand „gesperrt“ Ladestrom ≈ 0 | LH-V3, SZ-1/2 |
| SCH-T03 | Einzelfehler | jede Zeile aus Abschnitt 4 einzeln nachbilden (Bauteil auslöten, brücken, Ader trennen), bei 25 °C und bei 45 °C | Zustand wie in Abschnitt 4 vorhergesagt; jede Abweichung ist ein neuer Befund | LH-V3, SZ-1, H-G |
| SCH-T04 | Wiederanlauf nach Tiefentladung | Emulator auf 2,8 V → HY2111 trennt (P− offen messen) → VIN 6 V anlegen; einmal bei 25 °C, einmal bei 50 °C | 25 °C: Laden startet, HY2111 gibt ab ≥ 2,9 V frei; 50 °C: **kein** Laden, kein Freigeben am Temperaturschutz vorbei | LH-V2, SZ-4/6 |
| SCH-T05 | Rückspeisung Sensorschiene | wie Review | wie Review | LH-V5 |
| SCH-T06 | Solar-ADC | wie Review | wie Review | HW26-08 |
| SCH-T09 | Kabel und Stecker | Durchgang 1:1 jeder Ader vor dem ersten Anschluss; Stecker abziehen im Betrieb (Emulator) | gesperrt nach Abziehen; keine Ader vertauscht | LH-V1, H-E |
| SCH-T10 | Überstrom/Kurzschluss | **erst nach G2 und nur mit geeigneter Quelle** (Emulator ≥ 4 A Strombegrenzung, kurze Zeit) | HY2111 schaltet ab, Freigabe nach Entfernen der Last | LH-V2, SZ-5, H-F |
| SCH-T11 | Wärmeverzug | echte Zelle unter Aufsicht, Platine langsam erwärmen, Zellenoberfläche und TMP390 messen | Abstand Zelle → Sensor bei 45 °C dokumentiert | SZ-1 |

SCH-T07 (ERC, Reproduzierbarkeit) und SCH-T08 (Footprints, Layout) sind Entwurfsprüfungen und stehen im Review.

## 8. Rückverfolgbarkeit

| Anforderung | Risiko | Umsetzung (Schaltplan) | Test-ID / Stufe | Status |
|---|---|---|---|---|
| LH-V1 Akku-Platine, Stecker J1/J3 5-polig, Kabel 1:1 | G-05, G-08 | `akku_platine.py` J1; `hauptplatine.py` J203; Kabelplan `anschluesse.md` | `netz_tests.py` / T3; SCH-T09 / T4 | T3 bestanden lokal (`2076c20`); T4 offen |
| LH-V2 Tiefentladeschutz zweistufig, Freigabe nur durch Laden | G-04 | BQ25185 BUVLO; HY2111-GB U1 + FS8205 Q1 | `netz_tests.py` (kein Pfad an U1/Q1 vorbei) / T3; SCH-T04 / T4 | T3 lokal; T4 offen; HW26-17 offen |
| LH-V3 Ladeschluss 4,1 V, 150 mA | G-03, G-07 | R203 (ISET) 2,0 kΩ, R204 (ILIM/VSET) 130 kΩ in `hauptplatine.py` | SCH-T01 / T4 | T4 offen |
| LH-V3 Ladesperre Stufe 1 (+5 … 42 °C) | G-01, G-02 | U2, R3/R4, Q2, R5 → CE_FREI → R205/CE | `netz_tests.py` / T3; SCH-T02/T03 / T4 | T3 lokal; T4 offen |
| LH-V3 Ladesperre Stufe 2 (42 °C, TS offen) | G-01 | U3, R6, Q3, R8, TH1 → TS | `netz_tests.py` / T3; SCH-T02/T03 / T4 | T3 lokal; T4 offen; HW26-16 offen |
| LH-V3 Versorgung aus TMP_VCC | G-04, G-06 | U204 TPS70933 an VIN_LADER, C212 | `netz_tests.py` (TMP_VCC nicht an B+/B−) / T3; SCH-T04 / T4 | T3 lokal; HW26-18 offen |
| LH-V7 Ruhestrom < 20 µA | – | Gesamtschaltung | `energiebilanz.py` / T2; SCH-T01 / T4 | T2; T4 offen |

## 9. Offene Entscheidungen für G2

| Nr. | Frage | Wer |
|---|---|---|
| E-1 | Sicherheitsziel SZ-1 wie in Abschnitt 1 vorgeschlagen festlegen | Philipp |
| E-2 | HW26-16: Restrisiko BQ25185 akzeptieren oder zusätzliche Eingangstrennung vorsehen | Philipp, Reviewer |
| E-3 | HW26-17: Umgang mit dem 0-V-Laden des HY2111 | Philipp, Reviewer |
| E-4 | HW26-18: Klemmung an TMP_VCC vorsehen | Philipp |
| E-5 | Gegenlesen dieses Dokuments (zweiter Prüfweg) | Philipp benennt |

**Freigabestand:** G2 für den Akku-Teil ist **nicht** erteilt. Voraussetzungen fehlen noch: Gegenlesen (E-5), Entscheidungen E-1 bis E-4, Board-Kennung und Umgebungsbereich (REG26-10), Footprints (SCH26-04).
