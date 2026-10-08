# Hardware

Hier entsteht eine **eigene, offene Logger-Platine** (KiCad, CERN-OHL-S-2.0), die JLCPCB weitgehend bestückt
mit Funkmodul SX1262. Die Firmware aus `firmware/` erhält dafür eine Anbindung an RadioLib
(siehe Lastenheft, Abschnitt 6); Musterlogger mit RFM95 laufen weiter mit MCCI LMIC.

- Anforderungen: [`LASTENHEFT.md`](LASTENHEFT.md)
- KiCad-Projekt: folgt in `hardware/logger-platine/`
- Fertigungsdaten für JLCPCB (Gerber, BOM, CPL): folgen je Version in `hardware/logger-platine/production/`

Die Platinen von beelogger.de gehören nicht hierher, weil ihre Fertigungsdaten nicht offen lizenziert sind.
