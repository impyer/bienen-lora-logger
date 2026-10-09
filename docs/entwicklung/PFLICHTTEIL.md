# Pflichtteil – Bienen-logger Entwicklungsregeln

**Version 1.1 – Vorschlag zur Übernahme von Claudes Review E1–E12.** Bis zum Merge gilt auf `main` das angenommene Regelwerk 1.0. [ADR-0002](entscheidungen/ADR-0002-regelwerk-review.md).

1. **Vor Arbeit synchronisieren:** Eigenen lokalen Stand vor Agent-Wechsel committen/pushen oder als *nicht übergeben* kennzeichnen; aktuellen Zielbranch und dessen Git-SHA nennen. Ungepushte Änderungen nie als Bestandteil von `main` ausgeben.
2. **Änderungsklasse D0–D3 feststellen.** D2/D3 brauchen eine nachvollziehbare Soll-Anforderung und einen Abnahmetest. Bestehende Lastenheft- und Befund-IDs zählen; D1 soll eine Anforderung erhalten.
3. **Führende Quelle ändern:** KiCad-V0.1 per Python-Generator, eigener PHP-Server via `server/eigen_anpassen.py`, Formatter per `formatter/formatter.js`. Exporte synchron halten.
4. **Befund mit Status, SHA, Gate und Nachweis führen:** [Register](../testberichte/befunde.md). Codeänderung T0–T3 ist nicht automatisch Hardware-Nachweis T4/T5 oder Schließung.
5. **Tests korrekt benennen:** T0 Review, T1 Unit, T2 SiL/Integration, T3 Build/KiCad/ERC, T4 HiL, T5 Feld, T6 Release. FAIL/SKIP/NICHT AUSGEFÜHRT niemals als PASS.
6. **G2 D3 = sicherer Laborstart**, mit Gefährdungsanalyse, Netz-/Designcheck, strombegrenztem Zell-Emulator, sicherem Testplan und unabhängiger Gegenprüfung des Plans. T4-Messungen entstehen **erst danach**.
7. **G3/G4 D3** benötigen relevante bestandene T4-Nachweise und unabhängige fachkundige Sicherheitsprüfung (nicht der Schaltungsautor; relevante Li-Ion-/Schutzerfahrung). Kein KI-/CI-Alleinentscheid.
8. **Daten und Zugangsdaten schützen:** UTC-Zeit, FPort1/2-Kompatibilität, keine Phantomwerte; keine LoRaWAN-Schlüssel oder Tokens im Repo. Historischer Passwort-GET nur als dokumentierter [EX-01](ausnahmen.md), kein Freibrief.
9. **Lizenzen achten:** Fremdurheber nicht umdeklarieren. GOV-01 (GPL-KiCad-Werkzeuge vs. CERN-OHL-Hardware) bleibt offen.
10. **Ergebnis abgeben:** Baseline- und Ergebnis-SHA, Tests, Status, Restrisiko, Freigabe-Gate und Übergabezustand im PR. `CLAUDE.md` und `CHANGELOG.md` bei Mehr-Agenten-Arbeit zusammenführen, nicht überschreiben.

[Gesamtregeln](regelwerk.md) · [Hardware](hardware.md) · [Software](software.md) · [Tests und Gates](tests-freigaben.md) · [Claude-Review](../testberichte/2026-10-09-regelwerk-review.md).

**Ein Regelwerksreview behebt keinen Hardwarefehler und gibt keine Platine zur Fertigung frei.**
