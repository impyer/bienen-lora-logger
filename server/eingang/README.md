# Gemeinsame Eingangsschicht

Alle TTN-Webhooks der Plattform laufen durch dieselbe Annahme und dasselbe Rohprotokoll. Heute nutzen sie `../lora/` (Stockwaagen) und `../wetter/` (SenseCAP S2120); künftige Eingänge für Bodensonden und BEEP Base bauen darauf auf. Das ist die Eingangsschicht aus der Zielarchitektur ([Konzept 0.2, §4 und §4a](../../docs/architektur/konzept-plattform-v02.md)): Die Eingänge schreiben verlustfreie Rohprotokolle, ein späterer Importer liest sie in PostgreSQL.

| Datei | Aufgabe |
|---|---|
| `eingang_funktionen.php` | Hilfsfunktionen ohne HTTP-Seiteneffekte (auch für Kommandozeilenskripte wie `lora_nachholen.php`): Konfiguration laden, TTN-Zeit, Zahlen, Felder der Nachricht, Funkdaten, Kennung gegen Doppelzustellung, Liste verarbeiteter Kennungen, Monatsprotokoll, CSV anhängen, Sperre |
| `eingang_webhook.php` | Annahme eines Webhooks: Konfiguration prüfen, Token und Methode prüfen, JSON lesen, Rohprotokoll vor jeder Verarbeitung, Antwort an TTN mit angehängten Warnungen |
| `.htaccess` | Apache: kein Zugriff von außen; die Dateien werden nur eingebunden |

## Ablauf in einem Eingang

```php
require __DIR__ . '/../eingang/eingang_webhook.php';
$cfg = ein_cfg_laden(__DIR__ . '/x_config.php', array('header' => 'X-Bienen-Token', 'log_verzeichnis' => __DIR__ . '/x_log'));
list($roh, $msg) = ein_webhook_annehmen($cfg, 'x_config.php');      // 500 / 405 / 401 / 400 beenden die Anfrage
ein_rohprotokoll($cfg['log_verzeichnis'], array('geraet' => ein_geraet_id($msg)), $roh, $msg, 'x_eingang');
// … eingangsspezifisch: Gerät zuordnen, Doppelte über ein_nachricht_id() / ein_id_bekannt() erkennen, speichern …
ein_ende(200, 'gespeichert: …');                                    // hängt „| WARNUNG: …“ an, wenn das Rohprotokoll scheiterte
```

## Rohprotokoll (PLT26-02)

- Je Eingang eine Monatsdatei `<log_verzeichnis>/JJJJ-MM.jsonl` (Monat in UTC), eine JSON-Zeile je Eintrag, nur angehängt.
- Uplinks stehen **vor** jeder Verarbeitung vollständig darin: Herkunft (`geraet` bzw. `station`), `art: "uplink"`, Kennung `id`, `roh_sha256` (SHA-256 des empfangenen Textes), `nachricht`, `log_zeit`.
- Scheitert das Schreiben, wird trotzdem verarbeitet; die Antwort an TTN endet auf `| WARNUNG: Rohprotokoll nicht geschrieben`, und im PHP-Fehlerprotokoll steht die Kennung (R-2).
- Die Feldnamen der Herkunft (`geraet`, `station`) sind je Eingang verschieden geblieben, damit vorhandene Protokolle gleich gelesen werden.

## Einspielen

Ordner `eingang/` auf dem Server **neben** `lora/` und `wetter/` ablegen (gleiche Ebene wie `beelogger1` …). Die Eingänge binden ihn über `../eingang/` ein. Auf nginx gilt die `.htaccess` nicht; dort den Ordner per Server-Konfiguration sperren.

## Tests

- `php tests/server/test_eingang_funktionen.php` (Unit-Tests)
- `bash tests/server/test_lora_eingang.sh` und `bash tests/server/test_wetter_eingang.sh` prüfen die Schicht Ende zu Ende mit beiden Eingängen (T2, PHP-Testserver, kein Apache, kein TTN-Feldtest).

Lizenz: GPL-3.0-or-later.
