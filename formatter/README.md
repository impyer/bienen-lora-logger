# TTN-Payload-Formatter

| Datei | Zweck |
|---|---|
| `formatter.js` | lesbarer Quelltext, hier wird bearbeitet |
| `ttn_formatter.min.js` | verkleinerte Fassung zum Einfügen in TTN, erzeugt mit `bauen.sh` |
| `bauen.sh` | erzeugt `ttn_formatter.min.js` (Node.js nötig, terser 5.36.0) und prüft die Größe |
| `s2120_beep_formatter.js` | eigener Formatter für die Wetterstation SenseCAP S2120 (Gerät `wetterstation-01`), nur ASCII, direkt einfügen |

## Was er dekodiert

- **FPort 1:** beelogger-Format (`STM32_LORA_*`). Die Ausgabe gleicht `payloadformatter_220227.js` Wert für Wert; die Tests vergleichen beide an 2000 Zufallspaketen. Neu sind nur:
  - `Format: 1`
  - Fehlermeldungen bei kaputten Paketen statt `NaN`-Werten
- **FPort 2:** Funkformat v2, siehe [`../docs/funkformat-v2.md`](../docs/funkformat-v2.md).

Die Feldnamen entsprechen dem beelogger-Webserver (`beelogger_log.php`, `LORA=1`). Namen für neue Werte stehen oben im Objekt `NAME` und lassen sich dort ändern, z. B. für die zweite Innentemperatur.

## Wetterstation SenseCAP S2120

`s2120_beep_formatter.js` dekodiert die Blöcke 4A/4B/4C (Messwerte) und 03/04 (Batterie, Intervall) nach dem Seeed-Decoder und gibt flache Felder aus: `t`, `h`, `p` (in **Pa**: BEEP zeigt p/100 als hPa), `l` für BEEP, dazu `p_hpa`, `uv`, `wind_ms`, `wind_dir_deg`, `gust_ms`, `rain_mmh`, `rain_mm`, `battery_pct`, `interval_min`. BEEP speichert davon nur `t`, `h`, `p`, `l`; alles geht an den Umwelt-Eingang (`server/umwelt/`). Eintragen beim **Gerät** (Payload formatters → Uplink → Custom Javascript formatter). Tests: `node tests/formatter/test_s2120_formatter.js`, dazu goja mit `VEKTOREN=…`.

## In TTN eintragen

1. TTN-Konsole → Applikation `beelog-de-sn` → **Payload formatters** → **Uplink**.
2. Formatter type: **Custom Javascript formatter**.
3. Den Inhalt von `ttn_formatter.min.js` vollständig einfügen und speichern.
4. Zum Prüfen ein Testpaket eingeben, z. B. FPort 2 mit dem Hexwert aus `docs/funkformat-v2.md` (Abschnitt „Beispiel“).

Eigene Formatter sind bei TTN in der Größe begrenzt. Im Community-Forum steht dazu 4 KB je Applikation bzw. Gerät (Mai 2021, Version 3.13).
Ob die Grenze heute noch genau so gilt, habe ich nicht nachgeprüft. Die verkleinerte Fassung ist auf unter 4096 Byte ausgelegt, und `bauen.sh` prüft das.

## Tests

```
node tests/formatter/test_formatter.js                                 # Quelltext
node tests/formatter/test_formatter.js formatter/ttn_formatter.min.js  # verkleinerte Fassung
```

Zusätzlich läuft in der CI eine Prüfung in **goja**: Das ist die JavaScript-Laufzeit von The Things Stack, in der Version aus deren aktuellem Quelltext (Stand 08.10.2026), mit dem Aufruf-Rahmen von dort (`tests/formatter/goja/`). Welche Version auf den TTN-Servern läuft, kann ich nicht sehen.

## Bodensonde Dragino LSN50v2-D23 (`lsn50v2_d23_formatter.js`)

Eintragen beim **Gerät** (nicht an der Applikation). Gibt `temp_weiss`, `temp_rot`, `temp_schwarz` (°C, `null` bei fehlendem Fühler), `BatV`, `ALARM_status`, `Work_mode` aus.

**Warum ein eigener Formatter:** Der Decoder von Dragino nennt die Bytes 2–3 `Temp_Red` und 7–8 `Temp_White`. Das stimmt nur bei der D20 (ein Fühler). Bei D22/D23 liegt laut Dragino-Handbuch (Abschnitt 2.3.1, „Decode corresponding probe color“) **weiß an C1 (Bytes 2–3)** und **rot an C2 (Bytes 7–8)**. Feldbefund 22.10.2026 am Hauptstand: Der Fühler unter dem Namen `Temp_Red` schwankt am Tag am stärksten, sitzt also in 5 cm – passt zum Handbuch. Eigene Namen statt getauschter Dragino-Namen, damit kein Feldname im Rohprotokoll je zwei Bedeutungen hat. In der Plattform zeigen alte (`Temp_Red` → 5 cm, `Temp_White` → 20 cm, `Temp_Black` → 50 cm) und neue Namen auf dieselben Messstellen.

Quelle nur ASCII (Hinweis oben zur TTN-Konsole). Test: `node tests/formatter/test_lsn50v2_d23_formatter.js` (echter Uplink vom 14.10.2026 als Prüfvektor). Der goja-Vergleich fehlt für diesen Formatter noch.

