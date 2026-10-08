<?php
// LoRa-Eingang für den beelogger-Webserver (Webhook-Ziel für The Things Stack)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Ablauf: TTN-Uplink (JSON) → Gerät zuordnen → Messzeit in UTC bestimmen → EE-Datensatz bauen
//         → beelogger_log.php des Loggers aufrufen (unverändert) → Ergebnis prüfen → Zusatzwerte ablegen.
// Einrichtung: server/lora/README.md

error_reporting(E_ALL);
ini_set('display_errors', '0');
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/lora_funktionen.php';

function le_ende($code, $text)
{
    http_response_code($code);
    header('Content-Type: text/plain; charset=UTF-8');
    echo $text . "\n";
    exit;
}

function le_log($cfg, $eintrag)
{
    $dir = $cfg['log_verzeichnis'];
    if (!is_dir($dir)) {
        if (!@mkdir($dir, 0750, true)) return;
        @file_put_contents($dir . '/.htaccess', "Require all denied\n");
    }
    $eintrag['log_zeit'] = gmdate('Y-m-d\TH:i:s\Z');
    @file_put_contents($dir . '/' . gmdate('Y-m') . '.jsonl', json_encode($eintrag, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n", FILE_APPEND | LOCK_EX);
}

// ---------- Einstellungen ----------
$cfg_datei = __DIR__ . '/lora_config.php';
if (!is_file($cfg_datei)) le_ende(500, 'lora_config.php fehlt (Vorlage: lora_config.beispiel.php)');
$cfg = require $cfg_datei;
$cfg += array(
    'header' => 'X-Bienen-Token',
    'aux' => array(1 => 'Aux1', 2 => 'FFT_Hz', 3 => 'FFT_dB'),
    'waegezellen_temp' => 'TempOut',
    'max_zeitabweichung_s' => 900,
    'log_verzeichnis' => __DIR__ . '/lora_log',
    'beelogger_verzeichnis' => dirname(__DIR__),
    'tls_pruefen' => true,
    'zeitlimit_s' => 20,
    'utc_zeit' => 'auto',   // true: Zeit in UTC an die eigene Server-Fassung (beelogger_zeitzone.php vorhanden), false: Ortszeit wie beim Original
);
if (empty($cfg['token']) || strlen($cfg['token']) < 16) le_ende(500, 'token in lora_config.php fehlt oder ist kürzer als 16 Zeichen');

// ---------- Anfrage prüfen ----------
if ($_SERVER['REQUEST_METHOD'] !== 'POST') le_ende(405, 'nur POST');
$hkey = 'HTTP_' . strtoupper(str_replace('-', '_', $cfg['header']));
$token = isset($_SERVER[$hkey]) ? $_SERVER[$hkey] : '';
if (!is_string($token) || !hash_equals($cfg['token'], $token)) le_ende(401, 'Token falsch');

$roh = file_get_contents('php://input', false, null, 0, 65536);
$msg = json_decode($roh, true);
if (!is_array($msg)) le_ende(400, 'kein JSON');

$geraet = isset($msg['end_device_ids']['device_id']) ? (string)$msg['end_device_ids']['device_id'] : '';
if (!isset($msg['uplink_message'])) {   // Join, Downlink-Meldungen usw.: nur protokollieren
    le_log($cfg, array('geraet' => $geraet, 'art' => 'keine_uplink_nachricht', 'nachricht' => $msg));
    le_ende(200, 'ignoriert: keine Uplink-Nachricht');
}
$up = $msg['uplink_message'];
le_log($cfg, array('geraet' => $geraet, 'art' => 'uplink', 'nachricht' => $msg));

if (!isset($cfg['geraete'][$geraet])) le_ende(200, 'ignoriert: Gerät nicht in lora_config.php: ' . $geraet);
$g = $cfg['geraete'][$geraet];
$verz = $g['verzeichnis'];
if (!preg_match('/^[A-Za-z0-9_]+$/', $verz)) le_ende(500, 'Verzeichnisname ungültig: ' . $verz);
$pfad = rtrim($cfg['beelogger_verzeichnis'], '/') . '/' . $verz;

// Typ (Single=1, Duo=2 …) wie beelogger_log.php aus dem Verzeichnisnamen
$typ = 1;
foreach (array('Duo' => 2, 'Triple' => 3, 'Quad' => 4, 'Penta' => 5, 'Hexa' => 6) as $name => $n) {
    if (strpos($verz, 'beelogger') === false && strpos($verz, $name) !== false) $typ = $n;
}

$daten = isset($up['decoded_payload']) && is_array($up['decoded_payload']) ? $up['decoded_payload'] : null;
if ($daten === null) {
    le_log($cfg, array('geraet' => $geraet, 'art' => 'fehler', 'text' => 'kein decoded_payload (Formatter-Fehler?)'));
    le_ende(200, 'ignoriert: kein decoded_payload');
}

// ---------- Zeit ----------
$empfang = le_ttn_zeit(isset($up['received_at']) ? $up['received_at'] : (isset($msg['received_at']) ? $msg['received_at'] : null));
$mz = le_messzeit($daten, $empfang, (int)$cfg['max_zeitabweichung_s']);
if ($mz === null) le_ende(400, 'received_at fehlt oder ist ungültig');
list($unix, $quelle) = $mz;
// Eigene Server-Fassung (eigen-utc) nimmt die Zeit eindeutig in UTC an; das Original nur als Ortszeit-Text
$utc = ($cfg['utc_zeit'] === 'auto') ? is_file(rtrim($cfg['beelogger_verzeichnis'], '/') . '/beelogger_zeitzone.php') : (bool)$cfg['utc_zeit'];
$zeit_text = $utc ? le_ortszeit_text($unix, 'UTC') : le_ortszeit_text($unix);

// ---------- an beelogger_log.php ----------
$pw = le_log_passwort($pfad . '/beelogger_ini.php');
if ($pw === null) le_ende(500, 'beelogger_ini.php in ' . $verz . ' fehlt oder ohne Log-Passwort');
$ee = le_ee_datensatz($daten, $typ, $zeit_text, $cfg['aux'], $cfg['waegezellen_temp']);
$url = rtrim($cfg['basis_url'], '/') . '/' . $verz . '/beelogger_log.php?' .
    http_build_query(array('PW' => $pw, 'Z' => '0', 'M' . $typ => $ee) + ($utc ? array('UTC' => '1') : array()), '', '&', PHP_QUERY_RFC3986);

$week = $pfad . '/week.csv';
clearstatcache();
$groesse_vorher = is_file($week) ? filesize($week) : 0;

$ch = curl_init($url);
curl_setopt_array($ch, array(
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => (int)$cfg['zeitlimit_s'],
    CURLOPT_SSL_VERIFYPEER => (bool)$cfg['tls_pruefen'],
    CURLOPT_SSL_VERIFYHOST => $cfg['tls_pruefen'] ? 2 : 0,
));
$antwort = curl_exec($ch);
$http = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_fehler = curl_error($ch);
curl_close($ch);
$antwort = ($antwort === false) ? ('curl: ' . $curl_fehler) : trim(strip_tags($antwort));

// Gespeichert? beelogger setzt die Sekunden auf :00 und rechnet die Ortszeit mit strtotime() zurück.
$erwartet = $utc ? ($unix - $unix % 60) : strtotime(str_replace('_', ' ', substr($zeit_text, 0, 17) . '00'));
clearstatcache();
$gespeichert = (is_file($week) && filesize($week) > $groesse_vorher && le_letzter_zeitstempel($week) === $erwartet);

// ---------- Zusatzwerte ----------
$zusatz = $pfad . '/lora_zusatz.csv';
$neu = !is_file($zusatz);
$fp = @fopen($zusatz, 'ab');
if ($fp) {
    flock($fp, LOCK_EX);
    if ($neu) fputcsv($fp, le_zusatz_kopf());
    fputcsv($fp, le_zusatz_zeile($unix, $quelle, $geraet, $up, $daten, le_funk($up),
        ($gespeichert ? 'gespeichert' : 'NICHT gespeichert') . ' | HTTP ' . $http . ' | ' . substr($antwort, 0, 120)));
    flock($fp, LOCK_UN);
    fclose($fp);
}

le_log($cfg, array('geraet' => $geraet, 'art' => 'ergebnis', 'zeit' => $zeit_text, 'zeitquelle' => $quelle,
    'gespeichert' => $gespeichert, 'http' => $http, 'antwort' => substr($antwort, 0, 200)));

if ($http < 200 || $http >= 300 || $antwort === '' || strpos($antwort, 'curl:') === 0) le_ende(502, 'beelogger_log.php nicht erreichbar: ' . $antwort);
le_ende(200, ($gespeichert ? 'gespeichert ' : 'nicht gespeichert (doppelt, zu alt oder abgelehnt) ') . le_ortszeit_text($unix) . ($utc ? ' (UTC-Modus)' : '') . ' | ' . $antwort);
