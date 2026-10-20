<?php
// LoRa-Eingang für den beelogger-Webserver (Webhook-Ziel für The Things Stack)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Ablauf: TTN-Uplink (JSON) → Gerät zuordnen → Messzeit in UTC bestimmen → EE-Datensatz bauen
//         → beelogger_log.php des Loggers aufrufen → Ergebnis prüfen → Zusatzwerte ablegen (lora_verarbeitung.php).
// Vorübergehende Fehler: Nachricht wird zwischengespeichert (Antwort 202) und mit lora_nachholen.php erneut verarbeitet.
// TTN wiederholt einzelne Webhooks nicht; viele Fehlerantworten können den Webhook dagegen abschalten.
// Annahme, Rohprotokoll und Antwort: gemeinsame Eingangsschicht ../eingang/eingang_webhook.php
// Einrichtung: server/lora/README.md

error_reporting(E_ALL);
ini_set('display_errors', '0');
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../eingang/eingang_webhook.php';
require __DIR__ . '/lora_verarbeitung.php';

$cfg = le_cfg_laden();
list($roh, $msg) = ein_webhook_annehmen($cfg, 'lora_config.php');
$id = ein_nachricht_id($msg);
if (isset($msg['uplink_message'])) {
    ein_rohprotokoll($cfg['log_verzeichnis'], array('geraet' => ein_geraet_id($msg)), $roh, $msg, 'lora_eingang');
}

$e = le_verarbeiten($cfg, $msg);
if (le_nachholen_noetig($e)) {
    if (le_nachholen_ablegen($cfg, $msg, $id)) {
        ein_ende(202, 'zwischengespeichert, wird nachgeholt (' . $e['klasse'] . '): ' . $e['text']);
    }
    ein_ende($e['code'], $e['text'] . ' | Zwischenspeichern fehlgeschlagen');
}
ein_ende($e['code'], $e['text']);
