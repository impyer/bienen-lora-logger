<?php
// Wetter-Eingang für den beelogger-Webserver (Webhook-Ziel für The Things Stack, Wetterstation SenseCAP S2120)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Ablauf: TTN-Uplink (JSON, Formatter formatter/s2120_beep_formatter.js) → Station einem Bienenstand zuordnen
//         → Doppelte erkennen → Zeile in <daten_verzeichnis>/<stand>/<station>_<JJJJ-MM>.csv anhängen.
// Uplinks ohne Nutzdaten (nach einem Join) werden mit 200 „ignoriert“ beantwortet, damit TTN den Webhook nicht abschaltet.
// Einrichtung: server/wetter/README.md

error_reporting(E_ALL);
ini_set('display_errors', '0');
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/wetter_funktionen.php';

function we_ende($code, $text)
{
    http_response_code($code);
    header('Content-Type: text/plain; charset=UTF-8');
    echo $text . "\n";
    exit;
}

function we_verz_sicher($dir)
{
    if (is_dir($dir)) return true;
    if (!@mkdir($dir, 0750, true)) return false;
    @file_put_contents($dir . '/.htaccess', "Require all denied\n");
    return true;
}

function we_log($cfg, $eintrag)
{
    if (!we_verz_sicher($cfg['log_verzeichnis'])) return;
    $eintrag['log_zeit'] = gmdate('Y-m-d\TH:i:s\Z');
    @file_put_contents($cfg['log_verzeichnis'] . '/' . gmdate('Y-m') . '.jsonl',
        json_encode($eintrag, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n", FILE_APPEND | LOCK_EX);
}

// ---------- Konfiguration ----------
$cfg_datei = __DIR__ . '/wetter_config.php';
$cfg = is_file($cfg_datei) ? require $cfg_datei : null;
if (!is_array($cfg)) we_ende(500, 'wetter_config.php fehlt oder ist ungültig (Vorlage: wetter_config.beispiel.php)');
$cfg += array('header' => 'X-Bienen-Token', 'daten_verzeichnis' => __DIR__ . '/wetter_daten',
    'log_verzeichnis' => __DIR__ . '/wetter_log', 'staende' => array(), 'stationen' => array());
if (empty($cfg['token']) || !is_string($cfg['token']) || strlen($cfg['token']) < 16) we_ende(500, 'token in wetter_config.php fehlt oder ist kürzer als 16 Zeichen');

// ---------- Anfrage prüfen ----------
if ($_SERVER['REQUEST_METHOD'] !== 'POST') we_ende(405, 'nur POST');
$hkey = 'HTTP_' . strtoupper(str_replace('-', '_', $cfg['header']));
$token = isset($_SERVER[$hkey]) ? $_SERVER[$hkey] : '';
if (!is_string($token) || !hash_equals($cfg['token'], $token)) we_ende(401, 'Token falsch');

$msg = json_decode(file_get_contents('php://input', false, null, 0, 65536), true);
if (!is_array($msg)) we_ende(400, 'kein JSON');

$station = isset($msg['end_device_ids']['device_id']) ? (string)$msg['end_device_ids']['device_id'] : '';
if (!isset($msg['uplink_message']) || !is_array($msg['uplink_message'])) we_ende(200, 'ignoriert: keine Uplink-Nachricht');
$up = $msg['uplink_message'];
$id = le_nachricht_id($msg);
we_log($cfg, array('station' => $station, 'art' => 'uplink', 'id' => $id, 'nachricht' => $msg));

$stand = we_stand_fuer($cfg, $station);
if ($stand === null) we_ende(200, 'ignoriert: Station nicht in wetter_config.php: ' . $station);
if ($stand === false) we_ende(500, 'wetter_config.php: Station ' . $station . ' ohne gültigen Stand');

if (!we_hat_messwerte($up)) {
    $grund = !isset($up['frm_payload']) ? 'ohne Nutzdaten' : (!isset($up['decoded_payload']) ? 'kein decoded_payload (Formatter?)' : 'keine Messwerte');
    we_log($cfg, array('station' => $station, 'art' => 'ignoriert', 'id' => $id, 'text' => $grund));
    we_ende(200, 'ignoriert: Uplink ' . $grund);
}

$unix = le_ttn_zeit(isset($up['received_at']) ? $up['received_at'] : (isset($msg['received_at']) ? $msg['received_at'] : null));
if ($unix === null) we_ende(400, 'received_at fehlt oder ist ungültig');

// ---------- Speichern (Sperre je Station: Doppelprüfung und Anhängen gemeinsam) ----------
if (!we_verz_sicher($cfg['log_verzeichnis']) || !we_verz_sicher($cfg['daten_verzeichnis'])
    || !we_verz_sicher($cfg['daten_verzeichnis'] . '/' . $stand)) {
    we_ende(500, 'Verzeichnis nicht beschreibbar');
}
$sperre = fopen($cfg['log_verzeichnis'] . '/sperre_' . $station . '.lock', 'c');
if (!$sperre || !flock($sperre, LOCK_EX)) we_ende(500, 'Sperre nicht möglich');

$ids = $cfg['log_verzeichnis'] . '/ids_' . $station . '.txt';
if (le_id_bekannt($ids, $id)) we_ende(200, 'doppelt: schon gespeichert');
if (!empty($cfg['test_pause_ms'])) usleep(1000 * (int)$cfg['test_pause_ms']);   // nur für den Paralleltest

$datei = $cfg['daten_verzeichnis'] . '/' . we_dateiname($stand, $station, $unix);
$neu = !is_file($datei);
$fp = @fopen($datei, 'ab');
$ok = $fp !== false;
if ($ok && $neu) $ok = fputcsv($fp, we_kopf(), ';') !== false;
if ($ok) $ok = fputcsv($fp, we_zeile($unix, $stand, $station, $up), ';') !== false;
if ($fp) fclose($fp);
if (!$ok) {
    we_log($cfg, array('station' => $station, 'art' => 'fehler', 'id' => $id, 'text' => 'Schreiben fehlgeschlagen: ' . $datei));
    we_ende(500, 'Schreiben fehlgeschlagen');
}
le_id_merken($ids, $id, time());
@file_put_contents($cfg['daten_verzeichnis'] . '/staende.json',
    json_encode(we_staende_uebersicht($cfg), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n", LOCK_EX);
we_ende(200, 'gespeichert: ' . we_dateiname($stand, $station, $unix));
