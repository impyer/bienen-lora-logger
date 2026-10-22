# Umwelt-Eingang

`umwelt_eingang.php` ist das Webhook-Ziel für The Things Stack (TTN) für **alle Umweltsensoren am Stand**: Wetterstation SenseCAP S2120, Bodensonden Dragino LSN50v2-D23 und künftige Geräte. Messwerte der Völker gehen an den [Bienen-Eingang](../bienen/README.md).

Der Eingang kennt **keine Geräte und keine Feldnamen**. Er schreibt jeden Uplink ins Rohprotokoll; Bedeutung, Einheit und Zuordnung zum Stand stehen nur in der Datenbank (Verwaltung: Gerät, Zuordnung, Kanäle). Ein neues Umweltgerät braucht deshalb nur einen Uplink-Formatter in TTN und einen Eintrag in der Verwaltung, keinen Servercode.

| Datei | Zweck |
|---|---|
| `umwelt_eingang.php` | Webhook-Ziel (einzige von außen erreichbare Datei, siehe `.htaccess`) |
| `umwelt_funktionen.php` | Hilfsfunktionen ohne Seiteneffekte (Unit-Tests) |
| `umwelt_config.beispiel.php` | Vorlage für `umwelt_config.php` (Token, Protokollverzeichnis) – `umwelt_config.php` bleibt lokal |

## Was er macht

1. Token im Header `X-Bienen-Token` prüfen (gemeinsame Eingangsschicht [`../eingang/`](../eingang/README.md)).
2. Jeden Uplink **vor** jeder Prüfung ins Rohprotokoll `<log_verzeichnis>/JJJJ-MM.jsonl` schreiben (Herkunftsfeld `geraet`, Kennung, `roh_sha256`; R-1).
3. Uplinks ohne Nutzdaten (die S2120 sendet nach jedem Join einige), ohne `decoded_payload` oder ohne Zahlenwert mit 200 „ignoriert“ beantworten, damit TTN den Webhook nicht abschaltet. Sie stehen trotzdem im Rohprotokoll.
4. Sonst 200 „protokolliert“.

Doppelte Zustellung wird nicht hier, sondern im Importer erkannt (gleiche Kennung → einmal in der Datenbank).
Die Messzeit bestimmt der Importer nach derselben Regel wie beim Bienen-Eingang: Gerätezeit, wenn der Formatter sie als abgeglichen liefert, sonst Empfangszeit `received_at` (Vertrag: [`../datenbank/README.md`](../datenbank/README.md), Abschnitt Messzeit). Stand 22.10.2026: Die S2120 sendet laut offiziellem Seeed-Decoder keinen Zeitstempel. Dragino-Geräte können die Uhr per DeviceTimeReq stellen (SYNCMOD) und gespeicherte Werte mit Unix-Zeitstempel nachsenden (Datalog); ob die vorhandene LSN50v2-D23-Firmware das kann, ist am Gerät zu prüfen **[P]**. Dann muss ihr Formatter die Zeit als `Messzeit_unix` mit `Status.zeit_ok` bzw. die Liste `Eintraege` liefern.

**Rohprotokoll ist der einzige Speicher.** Scheitert das Schreiben, antwortet der Eingang bei Uplinks mit Messwerten **500** „nicht gespeichert | WARNUNG: Rohprotokoll nicht geschrieben“ (sichtbar in der TTN-Konsole) und schreibt die Kennung ins PHP-Fehlerprotokoll (R-2). TTN wiederholt den Webhook nicht; der Wert ist dann verloren.

### Antworten

| Code | Text | Fall |
|---|---|---|
| 200 | `protokolliert: <gerät>` | Uplink mit Messwerten im Rohprotokoll |
| 200 | `ignoriert: …` | keine Uplink-Nachricht, Gerätename ungültig, Uplink ohne Nutzdaten/`decoded_payload`/Zahlenwert |
| 400 | `kein JSON`, `received_at fehlt …` | unbrauchbare Nachricht |
| 401 | `Token falsch` | |
| 405 | `nur POST` | |
| 500 | | `umwelt_config.php` fehlt oder Token zu kurz; Rohprotokoll nicht schreibbar |

## Einrichtung

1. Ordner `eingang/` und `umwelt/` nebeneinander auf den Server kopieren (neben `bienen/`).
2. `umwelt_config.beispiel.php` nach `umwelt_config.php` kopieren, Token eintragen (`openssl rand -hex 24`). `log_verzeichnis` möglichst außerhalb des Webverzeichnisses; der Webserver braucht Schreib-, der Importer Leserecht.
3. TTN-Konsole → Applikation der Umweltgeräte → **Webhooks** → Custom webhook:
   - Format **JSON**, Base URL `https://<dein-server>/<ordner>/umwelt/umwelt_eingang.php`
   - Additional headers: `X-Bienen-Token` = Token aus `umwelt_config.php`
   - nur **Uplink message** anhaken
4. Uplink-Formatter je Gerät in TTN: S2120 `formatter/s2120_beep_formatter.js`; LSN50v2-D23 der Formatter von Dragino (Feldnamen erst an echten Daten prüfen).
5. Nach dem nächsten Uplink: neue Zeile in `<log_verzeichnis>/JJJJ-MM.jsonl`, in TTN kein `as.webhook.fail`. Nach dem nächsten Importer-Lauf erscheinen unbekannte Felder in der Verwaltung als „unbenannt“; dort Kanäle anlegen (S2120: Vorlage `s2120`) und „Werte nachtragen“.

**Altbestand:** Bis 22.10.2026 gab es stattdessen den Wetter-Eingang (`server/wetter/`, nur S2120, CSV je Stand, Protokoll `wetter_log/` mit Herkunftsfeld `station`). Seine Protokolle liest der Importer weiter (`--wetter`); dieselbe Nachricht in `wetter_log/` und `umwelt_log/` kommt nur einmal in die Datenbank. Die Zuordnung Station → Stand aus `wetter_config.php` gibt es nicht mehr; sie steht in der Datenbank (`geraet_zuordnung`).

## Tests

```
php tests/server/test_eingang_funktionen.php
php tests/server/test_umwelt_funktionen.php
bash tests/server/test_umwelt_eingang.sh
```

Geprüft mit PHP-Testserver (kein Apache, kein TTN-Feldtest).

Lizenz: GPL-3.0-or-later.
