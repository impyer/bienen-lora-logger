# Hardware

Hier entsteht eine **eigene, offene Logger-Platine** (KiCad, CERN-OHL-S-2.0), die JLCPCB weitgehend bestückt
mit Funkmodul Ai-Thinker Ra-01SH (SX1262). Dafür entsteht eine neue Firmware mit RadioLib
(siehe Lastenheft, Abschnitt 6); Musterlogger mit beelogger-Platine und RFM95 laufen weiter mit `firmware/STM32_LORA_261008_ZS`.

- Anforderungen: [`LASTENHEFT.md`](LASTENHEFT.md) und die Blöcke [`versorgung.md`](versorgung.md), [`mcu-funk.md`](mcu-funk.md), [`waage.md`](waage.md), [`mikrofon.md`](mikrofon.md), [`anschluesse.md`](anschluesse.md).
- **Unabhängige Prüfung Hardware 0.4:** [`docs/testberichte/2026-10-09-hardware-04-review.md`](../docs/testberichte/2026-10-09-hardware-04-review.md). **Vor PCB-Freigabe P0 HW26-07 (Ladesperre bei Übertemperatur) und die P1-Spezifikationsprobleme beheben.**
- KiCad-Projekt: folgt in `hardware/logger-platine/`
- Fertigungsdaten für JLCPCB (Gerber, BOM, CPL): folgen je Version in `hardware/logger-platine/production/`

Die Platinen von beelogger.de gehören nicht hierher, weil ihre Fertigungsdaten nicht offen lizenziert sind.
