<?php
// LoRa-Eingang für den beelogger-Webserver (Webhook-Ziel für The Things Stack)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Ablauf: TTN-Uplink (JSON) → Gerät zuordnen → Messzeit in UTC bestimmen → EE-Datensatz bauen
//         → beelogger_log.php des Loggers aufrufen → Ergebnis prüfen → Zusatzwerte ablegen (lora_verarbeitung.php).
// Vorübergehende Fehler: Nachricht wird zwischengespeichert (Antwort 202) und mit lora_nachholen.php erneut verarbeitet.
// TTN wiederholt einzelne Webhooks nicht; viele Fehlerantworten können den Webhook dagegen abschalten.
// Einrichtung: server/lora/README.md

error_reporting(E_ALL);
ini_set('display_errors', '0');
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/lora_verarbeitung.php';

function le_ende($code, $text)
{
    http_response_code($code);
    header('Content-Type: text/plain; charset=UTF-8');
    echo $text . "\n";
    exit;
}

$cfg = le_cfg_laden();
if ($cfg === null) le_ende(500, 'lora_config.php fehlt oder ist ungültig (Vorlage: lora_config.beispiel.php)');
if (empty($cfg['token']) || strlen($cfg['token']) < 16) le_ende(500, 'token in lora_config.php fehlt oder ist kürzer als 16 Zeichen');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') le_ende(405, 'nur POST');
$hkey = 'HTTP_' . strtoupper(str_replace('-', '_', $cfg['header']));
$token = isset($_SERVER[$hkey]) ? $_SERVER[$hkey] : '';
if (!is_string($token) || !hash_equals($cfg['token'], $token)) le_ende(401, 'Token falsch');

$roh = file_get_contents('php://input', false, null, 0, 65536);
$msg = json_decode($roh, true);
if (!is_array($msg)) le_ende(400, 'kein JSON');
// In TTN-Live-Data kopierte Events enthalten die ApplicationUp teilweise unter 'data'.
// TTN-Custom-Webhooks senden normalerweise die ApplicationUp direkt.
if (isset($msg['data']['uplink_message']) && is_array($msg['data'])) $msg = $msg['data'];

$geraet = isset($msg['end_device_ids']['device_id']) ? (string)$msg['end_device_ids']['device_id'] : '';
// Rohprotokoll vor jeder Verarbeitung (PLT26-02, R-1). Schlägt es fehl, wird trotzdem verarbeitet,
// damit der Messwert nicht verloren geht; der Fehler steht dann in der Antwort an TTN und im PHP-Fehlerprotokoll (R-2).
$roh_ok = true;
if (isset($msg['uplink_message'])) {
    $roh_ok = le_log($cfg, array('geraet' => $geraet, 'art' => 'uplink', 'id' => le_nachricht_id($msg),
        'roh_sha256' => hash('sha256', $roh), 'nachricht' => $msg));
    if (!$roh_ok) error_log('bienen lora_eingang: Rohprotokoll nicht geschrieben, Kennung ' . le_nachricht_id($msg));
}
$warnung = $roh_ok ? '' : ' | WARNUNG: Rohprotokoll nicht geschrieben';

$e = le_verarbeiten($cfg, $msg);
if (in_array($e['klasse'], array('fehler_endpunkt', 'fehler_einrichtung'), true)) {
    if (le_nachholen_ablegen($cfg, $msg, le_nachricht_id($msg))) {
        le_ende(202, 'zwischengespeichert, wird nachgeholt (' . $e['klasse'] . '): ' . $e['text'] . $warnung);
    }
    le_ende($e['code'], $e['text'] . ' | Zwischenspeichern fehlgeschlagen' . $warnung);
}
le_ende($e['code'], $e['text'] . $warnung);
