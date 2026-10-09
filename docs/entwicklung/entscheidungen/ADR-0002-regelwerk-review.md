# ADR-0002 – Unabhängiges Review E1–E12 in den Projektstandard übernehmen

**Status:** VORGESCHLAGEN – Draft-PR, nach Maintainer-Review zu entscheiden.  
**Datum:** 09.10.2026.  
**Grundlage:** [ADR-0001](ADR-0001-projektregelwerk.md), verbindliches Regelwerk 1.0 bei Commit `8fc2aa4`.  
**Review:** [Claude-Review zu E1–E12](../../testberichte/2026-10-09-regelwerk-review.md), Stand `428d101`.  
**Zielversion:** 1.1, wirksam **erst nach Merge/Annahme**.

## Ausgangslage

Das Regelwerk 1.0 wurde bereits mit ausdrücklicher Zustimmung des Projektverantwortlichen angenommen. E12 fordert fälschlich eine spätere Erstanahme. Die technisch berechtigten Hinweise sollen **als Revision**, nicht durch Umschreiben der historischen ADR-0001, umgesetzt werden.

## Reviewentscheidungen

| Punkt | Vorschlag | Begründung |
|---|---|---|
| **E1** | **Übernehmen:** G2 ist sichere *Zulassung zum Laborversuch* mit T0-/T3-Befund und sicherem Testplan; T4-Messung folgt **erst danach**. G3/G4 D3 erfordern T4. | Behebt zeitlichen Zirkelschluss |
| **E2** | **Übernehmen:** Maintainer `@impyer`; unabhängiger fachkundiger Prüfer ist **nicht** der Autor der Änderung, besitzt belegte Erfahrung etwa mit Li-Ion-Lade-/Schutztechnik und unterschreibt Prüfdokument. | Klare Rollen ohne Schein-Unabhängigkeit |
| **E3** | **Übernehmen:** Normative Regeln enthalten keine wechselnden Git-/Befundstände. | Verhindert veraltete Agentanweisungen |
| **E4** | **Übernehmen:** Zentrales [Befundregister](../../testberichte/befunde.md) mit getrenntem Status, SHA, Beweisstufe und Sperr-Gate. | T3-Fix ist nicht T4-Nachweis |
| **E5** | **Übernehmen:** Commit/Push vor Agent-Übergabe; dieser Änderungsstand bleibt **separater Draft-PR**, damit Claudes noch ungepushter SCH26-Fix nicht überspielt wird. `CLAUDE.md`/`CHANGELOG.md` bewusst nicht geändert. | Vermeidet Git-Konflikte/Verlust |
| **E6** | **Übernehmen:** D2/D3 eindeutige Anforderung; bestehende Lastenheft-IDs gültig, D1 als Soll. | Aufwand verhältnismäßig |
| **E7** | **Übernehmen:** KiCad-10-Hauptversion, Unterversion im Bericht; bytegenauer Vergleich deterministischer Schaltplandateien, nicht zeitgestempelter PDF-/Netzlisten. | Reproduzierbarkeit realistisch |
| **E8** | **Teilweise:** GPL-Generatoren/CERN-OHL-Design als Lösungskandidat; [GOV-01](../entscheidungen.md) bleibt bis zur Autorentscheidung offen. | Keine stille Umlizenzierung |
| **E9** | **Übernehmen:** [EX-01](../ausnahmen.md) für Legacy-Passwort-GET mit Nachweispflicht. | Kompatibilität ohne Sicherheitsdispens |
| **E10** | **Übernehmen:** T0–T3-Berichte mit SHA, Verfahren, Ergebnis, Grenzen; T4/T5 mit Prüfling/Messgerät/Umgebung. | Keine fiktiven Labordaten |
| **E11** | **Übernehmen:** [Pflichtteil](../PFLICHTTEIL.md) als einseitige Einstiegsversion. | Alltagstauglichkeit |
| **E12** | **Nicht als Neuannahme:** 1.0 ist bereits angenommen, Ergänzung erhält diese eigene ADR. | Historisch korrekt |

## Bedingungen vor Merge

1. Der SCH26-Fix wurde in [Commit `6dbba8d`](https://github.com/impyer/bienen-lora-logger/commit/6dbba8d6bd5d255b94fc4c396584508698f3100d) **nur teilweise** übernommen: generierte KiCad-Schaltungen und neue Prüfwerkzeuge ja, **führende Python-Generatoren und `pruefen.sh` nein**. [Issue #2](https://github.com/impyer/bienen-lora-logger/issues/2) dokumentiert die nachgewiesene CI-Regression. **Vor G1-Freigabe der Akku-Schaltplanänderung Generatoren und CI wieder konsistent machen**; aktueller Status im [Befundregister](../../testberichte/befunde.md).
2. Eventuelle Konflikte in `CLAUDE.md` und `CHANGELOG.md` **unter Erhalt beider Änderungslinien** lösen.
3. E8/GOV-01 und tatsächliche Zell-/Boardgrenzwerte GOV-04 separat verbindlich entscheiden. **Kein** Safety-Sign-off allein durch diese ADR.
4. KiCad/ERC-CI bei Warnungen und Footprints weiterentwickeln; gegenwärtig bestandener KiCad-Job ist nicht mit PCB-Fertigungsfreigabe gleichzusetzen.

**Nicht geändert:** Firmware-, Server- und KiCad-Quellen sowie ADR-0001-Historie.
