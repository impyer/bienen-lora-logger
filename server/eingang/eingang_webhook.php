<?php
// Gemeinsame Eingangsschicht: Annahme eines TTN-Webhooks (Konfiguration, Token, JSON), Rohprotokoll, Antwort
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Ablauf in jedem Eingang (lora_eingang.php, wetter_eingang.php, künftig Boden und BEEP Base):
//   $cfg = ein_cfg_laden(<config>, <Vorgaben>);
//   list($roh, $msg) = ein_webhook_annehmen($cfg, '<config-name>');   // 500/405/401/400 beenden die Anfrage
//   ein_rohprotokoll(...);                                             // vor jeder Verarbeitung (PLT26-02, R-1/R-2/R-3)
//   ... eingangsspezifische Verarbeitung ...
//   ein_ende($code, $text);                                            // hängt Warnungen an (R-2)

require_once __DIR__ . '/eingang_funktionen.php';

// Warnung für die Antwort an TTN merken; ohne Argument: alle bisherigen Warnungen als Antwortanhang
function ein_warnung($text = null)
{
    static $warnungen = '';
    if ($text !== null) $warnungen .= ' | WARNUNG: ' . $text;
    return $warnungen;
}

// Antwort an TTN (Text, eine Zeile) und Ende der Anfrage
function ein_ende($code, $text)
{
    http_response_code($code);
    header('Content-Type: text/plain; charset=UTF-8');
    echo $text . ein_warnung() . "\n";
    exit;
}

// Konfiguration, Methode und Token prüfen, Nachricht lesen. Rückgabe: [Rohtext, Nachricht]; beendet bei Fehlern die Anfrage.
function ein_webhook_annehmen($cfg, $cfg_name)
{
    if ($cfg === null) ein_ende(500, $cfg_name . ' fehlt oder ist ungültig (Vorlage: ' . basename($cfg_name, '.php') . '.beispiel.php)');
    $soll = isset($cfg['token']) ? $cfg['token'] : null;
    if (!is_string($soll) || strlen($soll) < 16) ein_ende(500, 'token in ' . $cfg_name . ' fehlt oder ist kürzer als 16 Zeichen');

    if ($_SERVER['REQUEST_METHOD'] !== 'POST') ein_ende(405, 'nur POST');
    $hkey = 'HTTP_' . strtoupper(str_replace('-', '_', $cfg['header']));
    $token = isset($_SERVER[$hkey]) ? $_SERVER[$hkey] : '';
    if (!is_string($token) || !hash_equals($soll, $token)) ein_ende(401, 'Token falsch');

    $roh = file_get_contents('php://input', false, null, 0, 65536);
    $msg = json_decode($roh, true);
    if (!is_array($msg)) ein_ende(400, 'kein JSON');
    return array($roh, $msg);
}

// Rohprotokoll eines Uplinks vor jeder Verarbeitung (PLT26-02, R-1): vollständige Nachricht mit Kennung und SHA-256
// des empfangenen Textes. Scheitert es, läuft die Verarbeitung weiter, damit der Messwert nicht verloren geht;
// der Fehler steht dann in der Antwort an TTN und im PHP-Fehlerprotokoll (R-2).
// $quelle: Feldname und Wert für die Herkunft, z. B. array('geraet' => 'beelogger-01'); $eingang: Name für das Fehlerprotokoll.
function ein_rohprotokoll($dir, array $quelle, $roh, array $msg, $eingang)
{
    $id = ein_nachricht_id($msg);
    $ok = ein_protokoll($dir, $quelle + array('art' => 'uplink', 'id' => $id, 'roh_sha256' => hash('sha256', $roh), 'nachricht' => $msg));
    if (!$ok) {
        ein_warnung('Rohprotokoll nicht geschrieben');
        error_log('bienen ' . $eingang . ': Rohprotokoll nicht geschrieben, Kennung ' . $id);
    }
    return $ok;
}
