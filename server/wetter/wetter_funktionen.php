<?php
// Wetter-Eingang: Hilfsfunktionen (ohne Seiteneffekte, testbar)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
// Läuft ab PHP 7.4. Allgemeine TTN-Hilfen (Zeit, Zahlen, Funk, Kennung) liegen in server/eingang/eingang_funktionen.php.

require_once __DIR__ . '/../eingang/eingang_funktionen.php';

// Messwerte aus dem Formatter (formatter/s2120_beep_formatter.js) in fester Spaltenreihenfolge
function we_messfelder()
{
    return array('t', 'h', 'p_hpa', 'l', 'uv', 'wind_ms', 'wind_dir_deg', 'gust_ms', 'rain_mmh', 'rain_mm');
}

// Gerätewerte (nur nach Join bzw. einmal täglich): Batterie in % (laut Seeed-Handbuch nur 0 oder 100), Intervall in min
function we_geraetefelder()
{
    return array('battery_pct', 'interval_min');
}

function we_kopf()
{
    return array_merge(array('zeit_utc', 'unix', 'ortszeit', 'stand', 'station'), we_messfelder(), we_geraetefelder(),
        array('f_cnt', 'f_port', 'rssi', 'snr', 'gateways', 'sf', 'payload_hex', 'warnungen'));
}

// Kennung für Stand und Station: nur Kleinbuchstaben, Ziffern, '-' und '_' (wird Verzeichnis- bzw. Dateiname)
function we_kennung_ok($s)
{
    return is_string($s) && preg_match('/^[a-z0-9][a-z0-9_-]{0,35}$/', $s) === 1;
}

// Stand einer Station aus der Konfiguration. Rückgabe: Kennung, null (Station unbekannt) oder false (Konfiguration fehlerhaft)
function we_stand_fuer(array $cfg, $station)
{
    if (!isset($cfg['stationen'][$station])) return null;
    $s = $cfg['stationen'][$station];
    $stand = is_array($s) && isset($s['stand']) ? $s['stand'] : null;
    if (!we_kennung_ok($station) || !we_kennung_ok($stand) || !isset($cfg['staende'][$stand])) return false;
    return $stand;
}

// Hat der Uplink Mess- oder Gerätewerte? Nach einem Join sendet die S2120 Uplinks ohne Nutzdaten; die werden nicht gespeichert.
function we_hat_messwerte($up)
{
    if (!is_array($up) || !isset($up['frm_payload']) || $up['frm_payload'] === '') return false;
    if (!isset($up['decoded_payload']) || !is_array($up['decoded_payload'])) return false;
    foreach (array_merge(we_messfelder(), we_geraetefelder()) as $f) {
        if (array_key_exists($f, $up['decoded_payload']) && ein_zahl($up['decoded_payload'][$f]) !== '') return true;
    }
    return false;
}

// Datei für Stand, Station und Monat (UTC): <stand>/<station>_<JJJJ-MM>.csv
function we_dateiname($stand, $station, $unix)
{
    return $stand . '/' . $station . '_' . gmdate('Y-m', (int)$unix) . '.csv';
}

function we_zeile($unix, $stand, $station, array $up)
{
    $d = isset($up['decoded_payload']) && is_array($up['decoded_payload']) ? $up['decoded_payload'] : array();
    $z = array(ein_utc_text($unix), $unix, ein_ortszeit_text($unix), $stand, $station);
    foreach (array_merge(we_messfelder(), we_geraetefelder()) as $f) $z[] = array_key_exists($f, $d) ? ein_zahl($d[$f]) : '';
    $funk = ein_funk($up);
    $hex = isset($up['frm_payload']) ? bin2hex((string)base64_decode((string)$up['frm_payload'], true)) : '';
    return array_merge($z, array(
        isset($up['f_cnt']) ? $up['f_cnt'] : '', isset($up['f_port']) ? $up['f_port'] : '',
        $funk['rssi'], $funk['snr'], $funk['gateways'], $funk['sf'], strtoupper($hex), ein_formatter_warnungen($up)));
}

// Übersicht der Stände für die Auswertung (ohne Token): Name, zugehörige Logger und Stationen
function we_staende_uebersicht(array $cfg)
{
    $r = array();
    foreach ((array)(isset($cfg['staende']) ? $cfg['staende'] : array()) as $id => $s) {
        $r[$id] = array(
            'name' => isset($s['name']) ? (string)$s['name'] : (string)$id,
            'logger' => isset($s['logger']) && is_array($s['logger']) ? array_values($s['logger']) : array(),
            'stationen' => array(),
        );
    }
    foreach ((array)(isset($cfg['stationen']) ? $cfg['stationen'] : array()) as $st => $s) {
        if (is_array($s) && isset($s['stand'], $r[$s['stand']])) $r[$s['stand']]['stationen'][] = (string)$st;
    }
    return $r;
}
