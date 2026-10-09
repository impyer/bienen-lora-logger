**Gültiger Standard:** [Regelwerk 1.0](../docs/entwicklung/README.md). D3-Sicherheitsprüfungen nicht durch grüne CI oder KI-Review ersetzen.

## Ziel / Änderung

**Warum ist die Änderung nötig?**  
…

**Was ist geändert?**  
…

**Änderungsklasse:** D0 / D1 / D2 / D3  
**Betroffene Komponenten / Boardrevision / Protokollversion:** …  
**Anforderung / Befund / ADR:** …

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

- [ ] Änderung und Tests gehören zum angegebenen Git-SHA; kein fremdes/erfundenes Testergebnis.
- [ ] Passende Regression/Negativfälle vorhanden oder Ausnahme begründet.
- [ ] Protokoll-, Zeit-, Firmware-/Server- und Hardware-Kompatibilität geprüft oder ausdrücklich nicht betroffen.
- [ ] Bei Boardänderungen: Pin-Netz-/Footprint-Abgleich, ERC-Warnungen, Generator-/Artefaktdiff; offene HiL-Punkte dokumentiert.
- [ ] Bei Lade-/Akku-/Sicherheitsänderungen: Gefährdungs-/Recovery-Prüfung und Gate-Verantwortung dokumentiert; kein Produktionsrelease allein aus CI.
- [ ] Dokumentation, ADR, Testbericht, Changelog und Versionsbezug soweit erforderlich aktualisiert.
- [ ] Keine Schlüssel, echten Passwörter, personenbezogenen Messlogs oder fremde nichtfreigegebene Dateien.
- [ ] Lizenz-/Urheberhinweise und externe Quellen sind korrekt; etwaige Konflikte gemeldet.

**Beanspruchter Freigabestand:** Entwicklung / Labormuster / Feldtest / Release / **keine Freigabe**  
**Maintainer-Entscheidung / offen:** …
