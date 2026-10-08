<?php
// LoRa-Eingang: Verarbeitung eines TTN-Uplinks (gemeinsam für lora_eingang.php und lora_nachholen.php)
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
// "nachholen": Die Nachricht wird zwischengespeichert und von lora_nachholen.php erneut verarbeitet.

require_once __DIR__ . '/lora_funktionen.php';

function le_cfg_laden()
{
    $cfg_datei = __DIR__ . '/lora_config.php';
    if (!is_file($cfg_datei)) return null;
    $cfg = require $cfg_datei;
    if (!is_array($cfg)) return null;
    $cfg += array(
        'header' => 'X-Bienen-Token',
        'aux' => array(1 => 'Aux1', 2 => 'FFT_Hz', 3 => 'FFT_dB'),
        'waegezellen_temp' => 'TempOut',
        'max_zeitabweichung_s' => 900,
        'log_verzeichnis' => __DIR__ . '/lora_log',
        'beelogger_verzeichnis' => dirname(__DIR__),
        'tls_pruefen' => true,
        'zeitlimit_s' => 20,
        // 'auto': UTC, wenn das beelogger_log.php des Ziel-Loggers die eigene Fassung ist (Merkmal $BL_UTC_FAEHIG);
        // true: UTC verlangen (alte Fassung → Fehler, Nachricht wird nachgeholt); false: immer Ortszeit wie beim Original
        'utc_zeit' => 'auto',
    );
    return $cfg;
}

function le_verz_sicher($dir)
{
    if (is_dir($dir)) return true;
    if (!@mkdir($dir, 0750, true)) return false;
    @file_put_contents($dir . '/.htaccess', "Require all denied\n");
    return true;
}

function le_log($cfg, $eintrag)
{
    $dir = $cfg['log_verzeichnis'];
    if (!le_verz_sicher($dir)) return;
    $eintrag['log_zeit'] = gmdate('Y-m-d\TH:i:s\Z');
    @file_put_contents($dir . '/' . gmdate('Y-m') . '.jsonl', json_encode($eintrag, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n", FILE_APPEND | LOCK_EX);
}

function le_ergebnis($code, $klasse, $text)
{
    return array('code' => $code, 'klasse' => $klasse, 'text' => $text);
}

// Nachricht zum Nachholen ablegen (Dateiname = Kennung, eine Datei je Nachricht)
function le_nachholen_ablegen($cfg, array $msg, $id)
{
    $dir = $cfg['log_verzeichnis'] . '/nachholen';
    if (!le_verz_sicher($dir)) return false;
    $datei = $dir . '/' . gmdate('Ymd\THis') . '_' . $id . '.json';
    foreach ((array)glob($dir . '/*_' . $id . '.json') as $vorhanden) if ($vorhanden) return true;   // liegt schon da
    return @file_put_contents($datei, json_encode($msg, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), LOCK_EX) !== false;
}

function le_verarbeiten(array $cfg, array $msg)
{
    $geraet = isset($msg['end_device_ids']['device_id']) ? (string)$msg['end_device_ids']['device_id'] : '';
    if (!isset($msg['uplink_message']) || !is_array($msg['uplink_message'])) {   // Join, Downlink-Meldungen usw.
        le_log($cfg, array('geraet' => $geraet, 'art' => 'keine_uplink_nachricht', 'nachricht' => $msg));
        return le_ergebnis(200, 'ignoriert', 'ignoriert: keine Uplink-Nachricht');
    }
    $up = $msg['uplink_message'];
    $id = le_nachricht_id($msg);

    if (!isset($cfg['geraete'][$geraet])) return le_ergebnis(200, 'ignoriert', 'ignoriert: Gerät nicht in lora_config.php: ' . $geraet);
    $verz = (string)$cfg['geraete'][$geraet]['verzeichnis'];
    if (!preg_match('/^[A-Za-z0-9_]+$/', $verz)) return le_ergebnis(500, 'fehler_einrichtung', 'Verzeichnisname ungültig: ' . $verz);
    $basis = rtrim($cfg['beelogger_verzeichnis'], '/');
    $pfad = $basis . '/' . $verz;

    // Typ (Single=1, Duo=2 …) wie beelogger_log.php aus dem Verzeichnisnamen
    $typ = 1;
    foreach (array('Duo' => 2, 'Triple' => 3, 'Quad' => 4, 'Penta' => 5, 'Hexa' => 6) as $name => $n) {
        if (strpos($verz, 'beelogger') === false && strpos($verz, $name) !== false) $typ = $n;
    }

    $daten = isset($up['decoded_payload']) && is_array($up['decoded_payload']) ? $up['decoded_payload'] : null;
    if ($daten === null) {
        le_log($cfg, array('geraet' => $geraet, 'art' => 'fehler', 'id' => $id, 'text' => 'kein decoded_payload (Formatter-Fehler?)'));
        return le_ergebnis(200, 'ignoriert', 'ignoriert: kein decoded_payload');
    }

    // ---------- Zeit ----------
    $empfang = le_ttn_zeit(isset($up['received_at']) ? $up['received_at'] : (isset($msg['received_at']) ? $msg['received_at'] : null));
    $mz = le_messzeit($daten, $empfang, (int)$cfg['max_zeitabweichung_s']);
    if ($mz === null) return le_ergebnis(400, 'ungueltig', 'received_at fehlt oder ist ungültig');
    list($unix, $quelle) = $mz;

    // ---------- Zeitbasis je Ziel-Logger (SRV26-07) ----------
    $faehig = le_utc_faehig($pfad . '/beelogger_log.php');
    if ($cfg['utc_zeit'] === true && !$faehig) {
        return le_ergebnis(500, 'fehler_einrichtung', 'UTC verlangt, aber ' . $verz . '/beelogger_log.php ist nicht die eigene Fassung (Merkmal $BL_UTC_FAEHIG fehlt)');
    }
    $utc = ($cfg['utc_zeit'] === 'auto') ? $faehig : ($cfg['utc_zeit'] === true);
    if (!$faehig && is_file($basis . '/beelogger_zeitzone.php')) {
        // Hauptordner schon eigene Fassung, dieser Logger noch nicht: sicher in Ortszeit senden und melden
        le_log($cfg, array('geraet' => $geraet, 'art' => 'warnung', 'id' => $id,
            'text' => 'Mischinstallation: ' . $verz . '/beelogger_log.php ist nicht die eigene Fassung, Ortszeit-Modus'));
    }
    $zeit_text = $utc ? le_ortszeit_text($unix, 'UTC') : le_ortszeit_text($unix);

    $pw = le_log_passwort($pfad . '/beelogger_ini.php');
    if ($pw === null) return le_ergebnis(500, 'fehler_einrichtung', 'beelogger_ini.php in ' . $verz . ' fehlt oder ohne Log-Passwort');

    // ---------- Sperre je Logger (SRV26-03): Duplikatprüfung, Aufruf, Speicherprüfung, Zusatzdatei ----------
    if (!le_verz_sicher($cfg['log_verzeichnis'])) return le_ergebnis(500, 'fehler_einrichtung', 'Protokollordner nicht anlegbar');
    $sperre = @fopen($cfg['log_verzeichnis'] . '/sperre_' . $verz . '.lock', 'c');
    if (!$sperre || !flock($sperre, LOCK_EX)) return le_ergebnis(500, 'fehler_einrichtung', 'Sperre für ' . $verz . ' nicht möglich');
    $ids = $cfg['log_verzeichnis'] . '/ids_' . $verz . '.txt';
    try {
        if (le_id_bekannt($ids, $id)) {
            le_log($cfg, array('geraet' => $geraet, 'art' => 'ergebnis', 'klasse' => 'doppelt', 'id' => $id));
            return le_ergebnis(200, 'doppelt', 'doppelt: Nachricht schon verarbeitet, nicht erneut weitergegeben');
        }

        $ee = le_ee_datensatz($daten, $typ, $zeit_text, $cfg['aux'], $cfg['waegezellen_temp']);
        $url = rtrim($cfg['basis_url'], '/') . '/' . $verz . '/beelogger_log.php?' .
            http_build_query(array('PW' => $pw, 'Z' => '0', 'M' . $typ => $ee) + ($utc ? array('UTC' => '1') : array()), '', '&', PHP_QUERY_RFC3986);

        $week = $pfad . '/week.csv';
        clearstatcache();
        $ts_vorher = le_letzter_zeitstempel($week);

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

        // Gespeichert? Unter der Sperre schreibt nur dieser Aufruf in week.csv; beelogger setzt die Sekunden auf :00.
        // Keine Prüfung der Dateigröße: beelogger kürzt week.csv vor 08:00 Uhr (CI26-01, le_speicherung_erkannt).
        $erwartet = $utc ? ($unix - $unix % 60) : strtotime(str_replace('_', ' ', substr($zeit_text, 0, 17) . '00'));
        clearstatcache();
        $gespeichert = le_speicherung_erkannt($ts_vorher, le_letzter_zeitstempel($week), $erwartet);

        if (!$erreicht && !$gespeichert) {
            le_log($cfg, array('geraet' => $geraet, 'art' => 'ergebnis', 'klasse' => 'fehler_endpunkt', 'id' => $id,
                'http' => $http, 'antwort' => substr($antwort, 0, 200)));
            return le_ergebnis(502, 'fehler_endpunkt', 'beelogger_log.php nicht erreichbar: ' . substr($antwort, 0, 200));
        }
        $klasse = $gespeichert ? 'gespeichert' : 'abgelehnt';

        // ---------- Zusatzwerte (SRV26-04): Fehler erkennen und melden ----------
        $zusatz = $pfad . '/lora_zusatz.csv';
        $zeile = le_zusatz_zeile($unix, $quelle, $geraet, $up, $daten, le_funk($up),
            ($gespeichert ? 'gespeichert' : 'NICHT gespeichert') . ' | HTTP ' . $http . ' | ' . substr($antwort, 0, 120));
        $zusatz_ok = false;
        $neu = !is_file($zusatz);
        $fp = @fopen($zusatz, 'ab');
        if ($fp) {
            $zusatz_ok = true;
            if ($neu && fputcsv($fp, le_zusatz_kopf()) === false) $zusatz_ok = false;
            if (fputcsv($fp, $zeile) === false) $zusatz_ok = false;
            if (!fflush($fp)) $zusatz_ok = false;
            fclose($fp);
        }
        if (!$zusatz_ok) {
            le_log($cfg, array('geraet' => $geraet, 'art' => 'fehler', 'klasse' => 'zusatz_fehler', 'id' => $id,
                'text' => 'lora_zusatz.csv nicht geschrieben', 'zeile' => $zeile));
        }

        // Kennung erst merken, wenn beelogger geantwortet hat: dann bringt eine Wiederholung nichts Neues
        if (!le_id_merken($ids, $id, time())) {
            le_log($cfg, array('geraet' => $geraet, 'art' => 'fehler', 'id' => $id, 'text' => 'Kennung nicht gespeichert: ' . $ids));
        }
        le_log($cfg, array('geraet' => $geraet, 'art' => 'ergebnis', 'klasse' => $klasse, 'id' => $id, 'zeit' => $zeit_text,
            'zeitquelle' => $quelle, 'utc' => $utc, 'zusatz_ok' => $zusatz_ok, 'http' => $http, 'antwort' => substr($antwort, 0, 200)));

        $text = ($gespeichert ? 'gespeichert ' : 'abgelehnt: nicht gespeichert (Zeit doppelt oder zu alt) ') . le_ortszeit_text($unix)
            . ($utc ? ' (UTC-Modus)' : ' (Ortszeit-Modus)') . ($zusatz_ok ? '' : ' | WARNUNG: lora_zusatz.csv nicht geschrieben')
            . ' | ' . $antwort;
        return le_ergebnis(200, $klasse, $text);
    } finally {
        flock($sperre, LOCK_UN);
        fclose($sperre);
    }
}
