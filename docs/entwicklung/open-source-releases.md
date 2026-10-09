# Open Source, Provenienz, Sicherheit und Releases

**Version 1.1 – Entwurf nach Claude-Review; bis zur Annahme gilt 1.0.** Der öffentlich nutzbare Zustand ist nicht nur eine Lizenzdatei: Dritte sollen Herkunft, Quellen, Änderungen, Reproduktionsverfahren und Einschränkungen verstehen können.

## O-01 Vorhandene Lizenzstruktur bewahren

Die Repository-Datei [`LICENSE.md`](../../LICENSE.md) unterscheidet:

| Inhalt | Bisher in `LICENSE.md` zugeordnet |
|---|---|
| `firmware/`, `formatter/`, `tests/`, `server/` | GPL-3.0-or-later |
| `hardware/`, `mechanik/` | CERN-OHL-S-2.0 |
| `docs/` und README-Dateien | CC BY-SA 4.0 |

**Dieses Regelwerk ändert keine Lizenz.** Der jeweilige urheberrechtliche Hinweis, Quellbezug und Rechteinhaber haben Vorrang. Bei neuen Dateien `SPDX-License-Identifier` nur entsprechend der **tatsächlich geklärten** Lizenz setzen.

**Weiterhin OFFEN GOV-01 (siehe [Register](entscheidungen.md)):** Python-Generatoren in `hardware/kicad/` führen teils explizite GPL-3.0-or-later-Copyright-/Lizenzhinweise, obwohl die Ordnerlizenz pauschal CERN-OHL-S-2.0 sagt. Dies bleibt ein **Klärungsbedarf**, keine automatische Doppel-Lizenzierung und keine Aufforderung zum Entfernen alter Header. [Claude E8](../testberichte/2026-10-09-regelwerk-review.md) schlägt GPL für Generatorsoftware und CERN-OHL für Schaltpläne, Symbole und Footprints vor; diese Zuordnung ist ohne dokumentierte Entscheidung der Rechteinhaber **nicht angenommen**. Vor Veröffentlichung als fertig lizenziertes PCB-Source-Paket Urheber/Umfang prüfen und eine dokumentierte Entscheidung herbeiführen.

## O-02 Fremdquellen, Forks, Attribution

- Code/PCB/Fotos/Texte nur hinzufügen, wenn die Rechte dazu bekannt und kompatibel sind. Herkunft, Version, Download-/Commit-URL, Originalcopyright, Dateiumfang und Änderungen dokumentieren.
- Das ursprüngliche beelogger-Serverpaket, seine Lizenztexte und das Originalverzeichnis **unverändert** erhalten; eigene Anpassung separat als Patch/Generator. Keine übernommenen geschlossenen beelogger-PCB-Layouts/Footprints ohne nachgewiesene Erlaubnis.
- Dritthersteller-Datenblätter **verlinken**, statt ungefragt ganze PDFs ins Repository zu kopieren. Eigenen Schaltplan/Footprint nach nachvollziehbaren Herstellermaßen erstellen und eigene Lizenz ausdrücklich nennen.
- Lizenz- und Urheberhinweise werden nicht aus Platzgründen entfernt oder durch fremde pauschale Header ersetzt. Abhängigkeiten und deren Lizenz im Release aufführen.

## O-03 Was zur offenen Hardware gehört

Je tatsächlich veröffentlichter Boardrevision sollten verfügbar sein: editierbare KiCad-Quelldaten (und bei Generator-Workflow auch der Generator), eigene Symbole/Footprints, Netzliste, Schaltplan-PDF als Ergänzung, Leiterplattenlayout und zur Fertigung nötige Gerber/Drill/BOM/CPL, mechanische STEP/DXF, Assembly-Zeichnung, Testpunkte, Stücklistenrevision und bekannte Fertigungs-/Bestückungsgrenzen. **Eine Schaltplan-PDF allein ist kein reproduzierbarer Fertigungsstand.**

Kennzeichnung: `V0.1 – experimenteller Teilentwurf` ist möglich; keine „fertige Hardware“ behaupten, solange MCU/SX1262/etc. noch fehlen.

## O-04 Beitragende, Qualität und Lizenzen

- Neue Beiträge erfolgen über Issue/PR mit Zweck, Tests, Herkunft und Lizenz. Externe Originalbeiträge müssen rechtmäßig unter einer kompatiblen Lizenz zur Verfügung gestellt werden können.
- Bei Lizenzkonflikten nicht ungefragt umschreiben, sondern als Issue an Maintainer melden.
- Abhängigkeiten beim Release mit genauer Version/Quelle dokumentieren; automatisierte Updates nicht blind mergen.
- Feedback/Bugs sind willkommen; Sicherheitshinweise möglichst **vertraulich** melden (siehe [`SECURITY.md`](../../SECURITY.md)), niemals Netzwerkschlüssel oder private Standorte als öffentliche Issue-Daten.

## O-05 Versions- und Releasepaket

**Versionen separat führen**, z. B. `FW-261010`, `PCB-MAIN-0.1`, `PCB-AKKU-0.1`, `SRV-eigen-utc-2`, `PROTO-FPort2-v2`. Ein identisches Datum ist keine Kompatibilitätsgarantie. Für ein Release:

1. Git-Tag auf **genau einem Commit**, Vorab-/Freigabestatus klar benannt (z. B. `hw-main-0.1-draft` oder `fw-261010-lab`).
2. `CHANGELOG.md` mit sichtbaren Änderungen/Breaking Changes und Migrationshinweisen.
3. Software: Zielboard/FQBN, Quellcode, Compiler/Core, Pinned Dependencies, Bild-/Binärhash, Konfigurationsvorlage ohne Schlüssel, kompatible TTN-Formatter-/Serverversion.
4. Hardware: exakte PCB-Revisionen und Akku-/Zellvariante, Editierquellen, ERC/DRC-Stände, Produktionsdateien **nur wenn fertigungstauglich**, BOM einschließlich Alternativen/DNP, Prüflingsbericht.
5. Tests: Gegenstands-/Commit-SHA, Gate-Status, Blocker/P0/P1/Restrictions und **welche HiL-/Feldprüfungen nicht erfolgt sind**.
6. Herkunft/Attribution/Lizenz pro Teil plus fremde Lizenztexte nach vorhandener Quelle.
7. Falls Geräte verkauft/in Verkehr gebracht werden: einschlägige EU-Anforderungen (etwa Funk, EMV, Batteriesicherheit, Stoff-/Entsorgungsvorgaben) im konkreten Vertriebs-/Verwendungsfall prüfen und die Verantwortlichkeit festhalten. Ein Open-Source-Repo oder ein ERC-Report ist **keine Konformitätsbescheinigung**.

**GOV-03 ANGENOMMEN:** Fertigungsreife Open-Hardware-Pakete müssen die O-03-Artefakte einschließlich Originalquellen, Produktions-/Montagedaten und Testnachweisen enthalten. Unfertige Versionen deutlich „experimentell, nicht fertigungsreif“ kennzeichnen. Siehe [Register](entscheidungen.md).

## O-06 Sicherheits- und Geheimnisregeln

- Reale ABP-/TTN-Schlüssel, Webhook-Token, Passwörter, private IPs und sensible Geräte-/Standorteinstellungen gehören nicht in Versionsverwaltung, Tickets, Screenshots oder öffentliches Debuglogging.
- Nur `*.beispiel.*`-Dateien mit synthetischen Werten veröffentlichen, *.env/`Config_Geraet.h`/`lora_config.php` und persönliche Messlogs ignorieren. Vor jedem Release auf versehentliche Geheimnisse und enthaltene personenbezogene Daten prüfen.
- Bei geleaktem Schlüssel **zuerst widerrufen/rotieren**, nicht bloß aus dem letzten Commit löschen; Freigabe-/Kommunikationsplan separat.
- Webhook-/Server-Hardening, Dateisystemrechte, TLS, erwartete Retry-Semantik und veraltete Abhängigkeiten gehören zur Sicherheitsprüfung. Anfällige Geräte nicht mit unbekannten Schlüsseln ins Feld schicken.

## O-07 Release-Archiv und Langzeitpflege

Ein veröffentlichter Freigabestand bleibt mit Quellen, Prüfbericht und eindeutigen Revisionen auffindbar. Nachträgliche Korrekturen **als neue Version** veröffentlichen, nicht alte Testergebnisse still umschreiben. Verantwortung für bekannte Sicherheitsrisiken, abgekündigte Bauteile und ungepflegte Abhängigkeiten explizit benennen.
