<?php
// Bienen-Eingang: Verarbeitung eines TTN-Uplinks (gemeinsam für bienen_eingang.php und bienen_nachholen.php)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Ergebnisklassen (SRV26-02):
//   gespeichert        Datensatz in week.csv angelegt                                    → 200
//   doppelt            dieselbe Nachricht wurde schon verarbeitet (Kennung bekannt)      → 200, beelogger nicht aufgerufen
//   abgelehnt          beelogger hat geantwortet, aber nicht gespeichert (Zeit doppelt/zu alt) → 200
//   ignoriert          keine Uplink-Nachricht, unbekanntes Gerät, kein decoded_payload   → 200
//   ungueltig          Nachricht unbrauchbar (z. B. ohne received_at)                    → 400
//   fehler_einrichtung Konfiguration/Installation passt nicht (vorübergehend behebbar)   → nachholen
//   fehler_endpunkt    beelogger_log.php nicht erreichbar oder Fehlerantwort             → nachholen
// "nachholen": Die Nachricht wird zwischengespeichert und von bienen_nachholen.php erneut verarbeitet.
//
// Ablauf von le_verarbeiten():
//   1. le_auftrag()        Nachricht prüfen, Ziel-Logger, Messzeit und Zeitbasis bestimmen (ohne Schreibzugriff auf beelogger)
//   2. le_weitergeben()    unter der Sperre je Logger: Duplikat, Aufruf von beelogger_log.php, Speicherprüfung, Zusatzdatei

require_once __DIR__ . '/bienen_funktionen.php';

// Klassen, bei denen die Nachricht zwischengespeichert und später nachgeholt wird
const LE_KLASSEN_NACHHOLEN = array('fehler_endpunkt', 'fehler_einrichtung');

function le_cfg_laden()
{
    return ein_cfg_laden(__DIR__ . '/bienen_config.php', array(
        'header' => 'X-Bienen-Token',
        'aux' => array(1 => 'Aux1', 2 => 'FFT_Hz', 3 => 'FFT_dB'),
        'waegezellen_temp' => 'TempOut',
        'max_zeitabweichung_s' => 900,
        'log_verzeichnis' => __DIR__ . '/bienen_log',
        'beelogger_verzeichnis' => dirname(__DIR__),
        'tls_pruefen' => true,
        'zeitlimit_s' => 20,
        // 'auto': UTC, wenn das beelogger_log.php des Ziel-Loggers die eigene Fassung ist (Merkmal $BL_UTC_FAEHIG);
        // true: UTC verlangen (alte Fassung → Fehler, Nachricht wird nachgeholt); false: immer Ortszeit wie beim Original
        'utc_zeit' => 'auto',
    ));
}

// Eintrag im Monatsprotokoll des Bienen-Eingangs
function le_log(array $cfg, array $eintrag)
{
    return ein_protokoll($cfg['log_verzeichnis'], $eintrag);
}

function le_ergebnis($code, $klasse, $text)
{
    return array('code' => $code, 'klasse' => $klasse, 'text' => $text);
}

function le_nachholen_noetig(array $e)
{
    return in_array($e['klasse'], LE_KLASSEN_NACHHOLEN, true);
}

// Nachricht zum Nachholen ablegen (Dateiname = Kennung, eine Datei je Nachricht)
function le_nachholen_ablegen($cfg, array $msg, $id)
{
    $dir = $cfg['log_verzeichnis'] . '/nachholen';
    if (!ein_verz_sicher($dir)) return false;
    $datei = $dir . '/' . gmdate('Ymd\THis') . '_' . $id . '.json';
    foreach ((array)glob($dir . '/*_' . $id . '.json') as $vorhanden) if ($vorhanden) return true;   // liegt schon da
    return @file_put_contents($datei, json_encode($msg, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), LOCK_EX) !== false;
}

function le_verarbeiten(array $cfg, array $msg)
{
    $a = le_auftrag($cfg, $msg);
    if (isset($a['ergebnis'])) return $a['ergebnis'];
    return le_weitergeben($cfg, $a);
}

// Schritt 1: Auftrag für die Weitergabe an beelogger. Rückgabe: Auftrag oder array('ergebnis' => …), wenn hier schon Schluss ist.
function le_auftrag(array $cfg, array $msg)
{
    $geraet = ein_geraet_id($msg);
    if (!isset($msg['uplink_message']) || !is_array($msg['uplink_message'])) {   // Join, Downlink-Meldungen usw.
        le_log($cfg, array('geraet' => $geraet, 'art' => 'keine_uplink_nachricht', 'nachricht' => $msg));
        return array('ergebnis' => le_ergebnis(200, 'ignoriert', 'ignoriert: keine Uplink-Nachricht'));
    }
    $up = $msg['uplink_message'];
    $id = ein_nachricht_id($msg);

    // ---------- Ziel-Logger ----------
    if (!isset($cfg['geraete'][$geraet])) {
        return array('ergebnis' => le_ergebnis(200, 'ignoriert', 'protokolliert, ohne beelogger-Weiterleitung (Gerät nicht in bienen_config.php): ' . $geraet));
    }
    $verz = (string)$cfg['geraete'][$geraet]['verzeichnis'];
    if (!preg_match('/^[A-Za-z0-9_]+$/', $verz)) {
        return array('ergebnis' => le_ergebnis(500, 'fehler_einrichtung', 'Verzeichnisname ungültig: ' . $verz));
    }
    $basis = rtrim($cfg['beelogger_verzeichnis'], '/');
    $pfad = $basis . '/' . $verz;

    $daten = isset($up['decoded_payload']) && is_array($up['decoded_payload']) ? $up['decoded_payload'] : null;
    if ($daten === null) {
        le_log($cfg, array('geraet' => $geraet, 'art' => 'fehler', 'id' => $id, 'text' => 'kein decoded_payload (Formatter-Fehler?)'));
        return array('ergebnis' => le_ergebnis(200, 'ignoriert', 'ignoriert: kein decoded_payload'));
    }

    // ---------- Zeit ----------
    $mz = le_messzeit($daten, ein_ttn_zeit(ein_empfangszeit($msg)), (int)$cfg['max_zeitabweichung_s']);
    if ($mz === null) return array('ergebnis' => le_ergebnis(400, 'ungueltig', 'received_at fehlt oder ist ungültig'));
    list($unix, $quelle) = $mz;

    // ---------- Zeitbasis je Ziel-Logger (SRV26-07) ----------
    $faehig = le_utc_faehig($pfad . '/beelogger_log.php');
    $utc = le_zeitbasis($cfg['utc_zeit'], $faehig);
    if ($utc === null) {
        return array('ergebnis' => le_ergebnis(500, 'fehler_einrichtung',
            'UTC verlangt, aber ' . $verz . '/beelogger_log.php ist nicht die eigene Fassung (Merkmal $BL_UTC_FAEHIG fehlt)'));
    }
    if (!$faehig && is_file($basis . '/beelogger_zeitzone.php')) {
        // Hauptordner schon eigene Fassung, dieser Logger noch nicht: sicher in Ortszeit senden und melden
        le_log($cfg, array('geraet' => $geraet, 'art' => 'warnung', 'id' => $id,
            'text' => 'Mischinstallation: ' . $verz . '/beelogger_log.php ist nicht die eigene Fassung, Ortszeit-Modus'));
    }

    $pw = le_log_passwort($pfad . '/beelogger_ini.php');
    if ($pw === null) return array('ergebnis' => le_ergebnis(500, 'fehler_einrichtung', 'beelogger_ini.php in ' . $verz . ' fehlt oder ohne Log-Passwort'));

    return array('geraet' => $geraet, 'id' => $id, 'up' => $up, 'daten' => $daten, 'verz' => $verz, 'pfad' => $pfad,
        'typ' => le_logger_typ($verz), 'unix' => $unix, 'quelle' => $quelle, 'utc' => $utc,
        'zeit_text' => $utc ? ein_ortszeit_text($unix, 'UTC') : ein_ortszeit_text($unix), 'pw' => $pw);
}

// Schritt 2: unter der Sperre je Logger (SRV26-03) Duplikat prüfen, beelogger aufrufen, Speicherung prüfen, Zusatzdatei schreiben
function le_weitergeben(array $cfg, array $a)
{
    if (!ein_verz_sicher($cfg['log_verzeichnis'])) return le_ergebnis(500, 'fehler_einrichtung', 'Protokollordner nicht anlegbar');
    $sperre = ein_sperre_holen($cfg['log_verzeichnis'] . '/sperre_' . $a['verz'] . '.lock');
    if (!$sperre) return le_ergebnis(500, 'fehler_einrichtung', 'Sperre für ' . $a['verz'] . ' nicht möglich');
    $ids = $cfg['log_verzeichnis'] . '/ids_' . $a['verz'] . '.txt';
    try {
        if (ein_id_bekannt($ids, $a['id'])) {
            le_log($cfg, array('geraet' => $a['geraet'], 'art' => 'ergebnis', 'klasse' => 'doppelt', 'id' => $a['id']));
            return le_ergebnis(200, 'doppelt', 'doppelt: Nachricht schon verarbeitet, nicht erneut weitergegeben');
        }

        // Gespeichert? Unter der Sperre schreibt nur dieser Aufruf in week.csv.
        // Keine Prüfung der Dateigröße: beelogger kürzt week.csv vor 08:00 Uhr (CI26-01, le_speicherung_erkannt).
        $week = $a['pfad'] . '/week.csv';
        clearstatcache();
        $ts_vorher = le_letzter_zeitstempel($week);
        $r = le_beelogger_aufrufen($cfg, le_beelogger_url($cfg, $a));
        clearstatcache();
        $gespeichert = le_speicherung_erkannt($ts_vorher, le_letzter_zeitstempel($week),
            le_erwarteter_zeitstempel($a['unix'], $a['zeit_text'], $a['utc']));

        if (!$r['erreicht'] && !$gespeichert) {
            le_log($cfg, array('geraet' => $a['geraet'], 'art' => 'ergebnis', 'klasse' => 'fehler_endpunkt', 'id' => $a['id'],
                'http' => $r['http'], 'antwort' => substr($r['antwort'], 0, 200)));
            return le_ergebnis(502, 'fehler_endpunkt', 'beelogger_log.php nicht erreichbar: ' . substr($r['antwort'], 0, 200));
        }
        $klasse = $gespeichert ? 'gespeichert' : 'abgelehnt';
        $zusatz_ok = le_zusatz_schreiben($cfg, $a, ($gespeichert ? 'gespeichert' : 'NICHT gespeichert') . ' | HTTP ' . $r['http'] . ' | ' . substr($r['antwort'], 0, 120));

        // Kennung erst merken, wenn beelogger geantwortet hat: dann bringt eine Wiederholung nichts Neues
        if (!ein_id_merken($ids, $a['id'], time())) {
            le_log($cfg, array('geraet' => $a['geraet'], 'art' => 'fehler', 'id' => $a['id'], 'text' => 'Kennung nicht gespeichert: ' . $ids));
        }
        le_log($cfg, array('geraet' => $a['geraet'], 'art' => 'ergebnis', 'klasse' => $klasse, 'id' => $a['id'], 'zeit' => $a['zeit_text'],
            'zeitquelle' => $a['quelle'], 'utc' => $a['utc'], 'zusatz_ok' => $zusatz_ok, 'http' => $r['http'], 'antwort' => substr($r['antwort'], 0, 200)));

        $text = ($gespeichert ? 'gespeichert ' : 'abgelehnt: nicht gespeichert (Zeit doppelt oder zu alt) ') . ein_ortszeit_text($a['unix'])
            . ($a['utc'] ? ' (UTC-Modus)' : ' (Ortszeit-Modus)') . ($zusatz_ok ? '' : ' | WARNUNG: lora_zusatz.csv nicht geschrieben')
            . ' | ' . $r['antwort'];
        return le_ergebnis(200, $klasse, $text);
    } finally {
        ein_sperre_freigeben($sperre);
    }
}

// Aufruf-Adresse von beelogger_log.php mit EE-Datensatz (Passwort im GET: Ausnahme EX-01)
function le_beelogger_url(array $cfg, array $a)
{
    $ee = le_ee_datensatz($a['daten'], $a['typ'], $a['zeit_text'], $cfg['aux'], $cfg['waegezellen_temp']);
    $parameter = array('PW' => $a['pw'], 'Z' => '0', 'M' . $a['typ'] => $ee) + ($a['utc'] ? array('UTC' => '1') : array());
    return rtrim($cfg['basis_url'], '/') . '/' . $a['verz'] . '/beelogger_log.php?' . http_build_query($parameter, '', '&', PHP_QUERY_RFC3986);
}

// beelogger_log.php aufrufen. Rückgabe: antwort (Text ohne HTML), http (Statuscode), erreicht (gültige Antwort erhalten)
function le_beelogger_aufrufen(array $cfg, $url)
{
    $ch = curl_init($url);
    curl_setopt_array($ch, array(
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => (int)$cfg['zeitlimit_s'],
        CURLOPT_SSL_VERIFYPEER => (bool)$cfg['tls_pruefen'],
        CURLOPT_SSL_VERIFYHOST => $cfg['tls_pruefen'] ? 2 : 0,
    ));
    $antwort = curl_exec($ch);
    $http = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_fehler = curl_error($ch);
    curl_close($ch);
    $antwort = ($antwort === false) ? ('curl: ' . $curl_fehler) : trim(strip_tags($antwort));
    $erreicht = !($http < 200 || $http >= 300 || $antwort === '' || strpos($antwort, 'curl:') === 0);
    return array('antwort' => $antwort, 'http' => $http, 'erreicht' => $erreicht);
}

// Zusatzwerte in lora_zusatz.csv des Loggers (SRV26-04): Fehler erkennen und mit der Zeile im Protokoll melden
function le_zusatz_schreiben(array $cfg, array $a, $antwort)
{
    $zeile = le_zusatz_zeile($a['unix'], $a['quelle'], $a['geraet'], $a['up'], $a['daten'], ein_funk($a['up']), $antwort);
    $ok = ein_csv_anhaengen($a['pfad'] . '/lora_zusatz.csv', le_zusatz_kopf(), $zeile, ',');
    if (!$ok) {
        le_log($cfg, array('geraet' => $a['geraet'], 'art' => 'fehler', 'klasse' => 'zusatz_fehler', 'id' => $a['id'],
            'text' => 'lora_zusatz.csv nicht geschrieben', 'zeile' => $zeile));
    }
    return $ok;
}
