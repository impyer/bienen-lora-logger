<?php
// Bienen-Eingang: Webhook-Ziel für The Things Stack für alle Messwerte der Völker (beelogger, eigene Platine, BEEP Base)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Jeder Uplink kommt vor jeder Verarbeitung ins Rohprotokoll (bienen_log/); daraus liest der Importer in die Datenbank.
// Nur Geräte aus bienen_config.php ('geraete') gehen zusätzlich an den beelogger-Webserver M.40:
// TTN-Uplink (JSON) → Gerät zuordnen → Messzeit in UTC bestimmen → EE-Datensatz bauen
//         → beelogger_log.php des Loggers aufrufen → Ergebnis prüfen → Zusatzwerte ablegen (bienen_verarbeitung.php).
// Vorübergehende Fehler: Nachricht wird zwischengespeichert (Antwort 202) und mit bienen_nachholen.php erneut verarbeitet.
// TTN wiederholt einzelne Webhooks nicht; viele Fehlerantworten können den Webhook dagegen abschalten.
// Annahme, Rohprotokoll und Antwort: gemeinsame Eingangsschicht ../eingang/eingang_webhook.php
// Einrichtung: server/bienen/README.md

error_reporting(E_ALL);
ini_set('display_errors', '0');
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../eingang/eingang_webhook.php';
require __DIR__ . '/bienen_verarbeitung.php';

$cfg = le_cfg_laden();
list($roh, $msg) = ein_webhook_annehmen($cfg, 'bienen_config.php');
$id = ein_nachricht_id($msg);
if (isset($msg['uplink_message'])) {
    ein_rohprotokoll($cfg['log_verzeichnis'], array('geraet' => ein_geraet_id($msg)), $roh, $msg, 'bienen_eingang');
}

$e = le_verarbeiten($cfg, $msg);
if (le_nachholen_noetig($e)) {
    if (le_nachholen_ablegen($cfg, $msg, $id)) {
        ein_ende(202, 'zwischengespeichert, wird nachgeholt (' . $e['klasse'] . '): ' . $e['text']);
    }
    ein_ende($e['code'], $e['text'] . ' | Zwischenspeichern fehlgeschlagen');
}
ein_ende($e['code'], $e['text']);
