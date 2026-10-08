# Hardware

Hier entsteht eine **eigene, offene Logger-Platine** (KiCad, CERN-OHL-S-2.0), die JLCPCB weitgehend bestückt
mit Funkmodul Ai-Thinker Ra-01SH (SX1262). Dafür entsteht eine neue Firmware mit RadioLib
(siehe Lastenheft, Abschnitt 6); Musterlogger mit beelogger-Platine und RFM95 laufen weiter mit `firmware/STM32_LORA_261008_ZS`.

- Anforderungen: [`LASTENHEFT.md`](LASTENHEFT.md)
- KiCad-Projekt: folgt in `hardware/logger-platine/`
- Fertigungsdaten für JLCPCB (Gerber, BOM, CPL): folgen je Version in `hardware/logger-platine/production/`

Die Platinen von beelogger.de gehören nicht hierher, weil ihre Fertigungsdaten nicht offen lizenziert sind.
