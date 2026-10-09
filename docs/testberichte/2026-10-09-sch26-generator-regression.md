# Integrationsprüfung SCH26 / KiCad-Generatoren nach Claude-Commit 6dbba8d

- **Prüfdatum:** 09.10.2026 (MESZ)
- **Geprüfter GitHub-main:** [`6dbba8d6bd5d255b94fc4c396584508698f3100d`](https://github.com/impyer/bienen-lora-logger/commit/6dbba8d6bd5d255b94fc4c396584508698f3100d)
- **Vergleichsbasis:** [`428d1014305b27c4daf7c3f72946ea86e6d04735`](https://github.com/impyer/bienen-lora-logger/commit/428d1014305b27c4daf7c3f72946ea86e6d04735)
- **Methode / Teststufe:** T0 GitHub-Commit-Diff, Datei- und Generator-Kontrollfluss, T3 **bereits ausgeführte GitHub Actions Logs**. **Kein eigener KiCad-Aufruf, kein HiL, keine SPICE-Simulation oder reale Li-Ion-Messung.**
- **Prozessbezug:** [Regelwerk-PR #1](https://github.com/impyer/bienen-lora-logger/pull/1) / Befund `REG26-13`, [GitHub Issue #2](https://github.com/impyer/bienen-lora-logger/issues/2)

## Nachweise

1. Commit-Diff `428d101..6dbba8d`: **Geändert:** `hardware/kicad/hauptplatine/versorgung.kicad_sch` und `bienen.kicad_sym`; **hinzugefügt:** `erc_erwartet.json`, `netz_tests.py`, `erc_pruefen.py`, exportierte Netzlisten und PDF. **Nicht geändert:** `hardware/kicad/akku_platine.py`, `hardware/kicad/hauptplatine.py`, `hardware/kicad/werkzeug/symbole.py`, `hardware/kicad/pruefen.sh` sowie insbesondere `akku-platine/akku.kicad_sch` (siehe Diff).
2. Die führenden Generatoren spezifizieren weiterhin z. B. `R205=10M`, `R208=1M` und `J203=4-polig`; der neue Entwurf bzw. das Berichtsziel lautet **100k / 100k / 5-polig**. Der Generator erzeugt beim Aufruf wieder ältere Schaltpläne. **Der neue Akku-Schaltplan `akku.kicad_sch` wurde im Commit nicht einmal geändert.** Dies ist neben dem Generatorbruch ein zusätzlicher harter Inkonsistenzbeleg.
3. `pruefen.sh` generiert den Schaltplan mit den alten Python-Dateien neu, prüft nur `kicad-cli sch erc --severity-error` und ruft **weder** `erc_pruefen.py` **noch** `netz_tests.py` auf. Die zusätzlichen Sicherheitschecks sind vorhanden, aber nicht in den freigaberelevanten CI-Pfad eingebunden.
4. **CI-Lauf [37881512633](https://github.com/impyer/bienen-lora-logger/actions/runs/37881512633), Ergebnis: 6/7 Jobs PASS, KiCad FAIL.** KiCad-Job: `git diff --exit-code -- hardware/kicad ':!hardware/kicad/pdf' ':!hardware/kicad/netzliste'` meldet Unterschiede nach Regeneration. Log zeigt einen sehr umfangreichen Diff der erzeugten Schaltung; dies widerspricht deterministischer Quellenidentität.
5. Das Dokument [`2026-10-09-sch26-behebung.md`](2026-10-09-sch26-behebung.md) beschreibt eine **lokal getestete Arbeitskopie** (42/42 Netztests, ERC nur erwartete Warnungen), aber der beschriebene vollständige Generator-/Skriptestand ist **nicht** in diesem GitHub-Commit enthalten. Diese historischen Angaben sind nicht als erfolgreiches CI-Resultat von `6dbba8d` anzusehen.

## Statusentscheid (Evidenz und Gates)

| Befund | Bewertung am geprüften Commit | Nötiger Nachweis |
|---|---|---|
| **REG26-13** | **BESTÄTIGT, P0/G1–G2 für Akku-Entwurf** | Generator-/Artefakt-/CI-Konsistenz, neuer vollständiger SHA |
| **SCH26-01** | Als Fehler durch Schaltungs-/Datenblattreview bestätigt; Abhilfe wird nur in einem **unvollständigen Paket** beschrieben; **nicht T3-reproduziert**, **nicht T4-geprüft** | Python-Generatoren, neue KiCad-Ausgaben, T3-Checks und G2-Sicherheitsplan; danach SCH-T04 am Zell-Emulator |
| **SCH26-02/03** | Beabsichtigte 100-kΩ-Freigabekette / zweiter TMP390 nur teilweise im Projekt abgebildet; Sicherheitsvalidierung ausstehend | Generator-/Netztests und D3-Einzelfehler-Prüfplan; T4 an sicherem Emulator |
| **SCH26-04** | **CI regressiert**, neue Prüfskripte werden nicht aufgerufen | `pruefen.sh` als reale Sicherheits-Gate-Kette, ERC-Liste inkl. Warnungen, Netzprüfung verpflichtend |
| **Firmware/Server/Formatter** | Die jeweils zugehörigen 6 bestehenden CI-Jobs sind auf `6dbba8d` PASS | **Keine** Folgerung auf SX1262-Zielhardware oder PCB-Freigabe |

**Wichtig:** Das gelungene Einchecken eines Schaltplanfragments ist **keine erfolgreiche Integration der sicherheitsrelevanten D3-Entwurfsänderung**, solange dessen Generator die alte Logik wieder einsetzt. Dies ist ein Problem der Quellwahrheit (R-02) und Quell-/Test-Reproduzierbarkeit (H-06).

## Reproduzierbarer Nachtest nach Behebung (noch NICHT durchgeführt)

```bash
# in sauberem Checkout des Folge-Commits, KiCad 10 installiert:
bash hardware/kicad/pruefen.sh
# Pflicht: Generator zweimal deterministisch, KiCad ERC alle Schweregrade,
# beide Netzlisten neu exportieren, 42 Netztests durchführen
git diff --exit-code -- hardware/kicad ':!hardware/kicad/pdf' ':!hardware/kicad/netzliste'
```

Außerdem im Testzweig eine **negative Gegenprobe**: Den TMP390-Eingang gezielt zurück auf geschütztes Akku-Plus verdrahten, die Netzprüfung muss dann fehlschlagen; Änderung nicht committen.

## Freigabe

- **G1 betroffene D3-KiCad-Änderung:** **NICHT BESTANDEN** (`6dbba8d`, KiCad CI rot).
- **G2 sicherer Laborversuch:** **NICHT FREIGEGEBEN**; detaillierter sicherer Versuchsplan und dessen Gegenprüfung fehlen.
- **G3/G4:** keine HiL-Messung/keine Fachfreigabe/kein fertigungstaugliches Board; **NICHT FREIGEGEBEN**.
- **Dokumentations-Regelwerk PR #1:** kann getrennt reviewed werden; Merge nicht als Schaltplan-Fix deklarieren. Die gemeinsame CI braucht dennoch für G1 vollständige Nachweise; deshalb vor finalem Projekt-Merge zunächst Issue #2 beheben.

**Übergabe an Claude:** [Issue #2](https://github.com/impyer/bienen-lora-logger/issues/2) enthält konkrete zu bearbeitende Generatoren, Skriptprüfungen und Akzeptanzschritte. Keine eigenmächtige Neuauslegung der Schutzschaltung.
