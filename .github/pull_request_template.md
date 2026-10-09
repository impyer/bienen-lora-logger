**Gültiger Stand auf `main`: Regelwerk 1.0 (Claude hat in `6dbba8d` die PR-Vorlage bereits mit Version 1.1 beschriftet; die Regeltexte sind aber bis zum Merge unverändert 1.0).** Regelwerk 1.1 ist als PR-Entwurf vorgeschlagen. D3-G2 benötigt einen sicheren Laborplan mit unabhängiger Planprüfung; D3-G3/G4 zusätzlich relevante bestandene T4-Messungen und fachkundige unabhängige Bewertung.

## Ziel / Änderung

**Warum ist die Änderung nötig?**  
…

**Was ist geändert?**  
…

**Änderungsklasse:** D0 / D1 / D2 / D3  
**Betroffene Komponenten / Boardrevision / Protokollversion:** …  
**Anforderung / Befund / ADR:** …
**Basis-SHA / Zielbranch:** …
**Lokaler Übergabestand / ungepushte Fremdänderungen:** …

## Nachweis

| Prüfung | Ergebnis (PASS/FAIL/SKIP/NICHT GELAUFEN) | Befehl, CI-URL, SHA oder Bericht |
|---|---|---|
| Statischer Review / Datenblatt / Lizenz | | |
| Unit / Host / SiL / Integration | | |
| Zielbuild / Ressourcen / KiCad ERC/DRC, falls betroffen | | |
| HiL / Feldtest, falls dieser PR eine Freigabe beansprucht | | |

**Was ist ausdrücklich noch nicht geprüft?**  
…

**Neue/geschlossene Risiken:** P0 / P1 / P2 / P3 und betroffene Gate-Stufe  
…

## Checkliste

- [ ] Änderung und Tests gehören zum angegebenen Git-SHA; kein fremdes/erfundenes Testergebnis; Übergabe- und Branchstand synchronisiert.
- [ ] [Befundregister](../docs/testberichte/befunde.md) auf relevante IDs, echten Teststatus und gesperrte Gates geprüft/aktualisiert.
- [ ] Passende Regression/Negativfälle vorhanden oder Ausnahme begründet.
- [ ] Protokoll-, Zeit-, Firmware-/Server- und Hardware-Kompatibilität geprüft oder ausdrücklich nicht betroffen.
- [ ] Bei Boardänderungen: Pin-Netz-/Footprint-Abgleich, ERC-Warnungen, Generator-/Artefaktdiff; offene HiL-Punkte dokumentiert.
- [ ] Bei Lade-/Akku-/Sicherheitsänderungen: Gefährdungs-/Recovery-Prüfung und Gate-Verantwortung dokumentiert; kein Produktionsrelease allein aus CI.
- [ ] Dokumentation, ADR, Testbericht, Changelog und Versionsbezug soweit erforderlich aktualisiert.
- [ ] Keine Schlüssel, echten Passwörter, personenbezogenen Messlogs oder fremde nichtfreigegebene Dateien.
- [ ] Lizenz-/Urheberhinweise und externe Quellen sind korrekt; etwaige Konflikte gemeldet.

**Beanspruchter Freigabestand:** Entwicklung / Labormuster / Feldtest / Release / **keine Freigabe**  
**Maintainer-Entscheidung / offen:** …
