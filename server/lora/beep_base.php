<?php
// SPDX-License-Identifier: GPL-3.0-or-later
// BEEP Base FPort 3: interner Decoder des gemeinsamen LoRa-Eingangs.
// Format nach beepnl/BEEP: ttn-payload-decoder.js und MeasurementLoRaDecoderTrait.php.
// Keine Rückübertragung an BEEP und kein direkter Eingriff in die M.40-CSV.

function bb_unsigned(array $b, $pos, $size)
{
    $v = 0;
    for ($i = 0; $i < $size; $i++) $v = $v * 256 + $b[$pos + $i];
    return $v;
}

function bb_signed($value, $bits)
{
    return $value >= pow(2, $bits - 1) ? $value - pow(2, $bits) : $value;
}

// Liefert null bei fremdem/defektem Payload. Insbesondere keine Zahlen aus zu kurzen Frames erraten.
function bb_decode(array $up)
{
    if (!isset($up['f_port']) || (int)$up['f_port'] !== 3 || !isset($up['frm_payload'])) return null;
    $raw = base64_decode($up['frm_payload'], true);
    if ($raw === false || strlen($raw) < 15 || strlen($raw) > 255) return null;
    $b = array_values(unpack('C*', $raw));
    $n = count($b);
    if ($b[0] !== 0x1B || $b[6] !== 0x0A) return null;

    $countW = $b[7];
    if ($countW > 2 || 8 + 3 * $countW + 2 > $n) return null;
    $p = 8;
    $weights = array();
    for ($i = 0; $i < $countW; $i++) {
        $weights[] = bb_signed(bb_unsigned($b, $p, 3), 24);
        $p += 3;
    }

    if ($b[$p] !== 0x04) return null;
    $countT = $b[$p + 1];
    $p += 2;
    if ($countT > 10 || $p + 2 * $countT + 4 > $n) return null;
    $temps = array();
    for ($i = 0; $i < $countT; $i++) {
        $v = bb_signed(bb_unsigned($b, $p, 2), 16);
        $temps[] = ($v <= -9900) ? null : ($v / 100);
        $p += 2;
    }

    if ($b[$p] !== 0x0C) return null;
    $nfft = $b[$p + 1];
    $start = $b[$p + 2];
    $stop = $b[$p + 3];
    $p += 4;
    if ($nfft > 12 || $p + 2 * $nfft > $n || ($nfft > 0 && $stop <= $start)) return null;
    $fft = array();
    if ($nfft > 0) {
        $step = (int)ceil(($stop - $start) * 2 / $nfft);
        $binFreq = 3.937752016; // BEEP-Referenzdecoder
        for ($i = 0; $i < $nfft; $i++) {
            $from = (int)round(($start * 2 + $i * $step) * $binFreq);
            $to = (int)round(($start * 2 + ($i + 1) * $step) * $binFreq);
            $fft[] = array('von_hz' => $from, 'bis_hz' => $to, 'wert' => bb_unsigned($b, $p, 2));
            $p += 2;
        }
    }

    // BME280 optional, nur Werte ungleich Null als echte Messungen interpretieren.
    $bme = null;
    if ($p + 7 <= $n && $b[$p] === 0x07) {
        $temp = bb_signed(bb_unsigned($b, $p + 1, 2), 16);
        $humidity = bb_unsigned($b, $p + 3, 2);
        $pressure = bb_unsigned($b, $p + 5, 2);
        if ($temp !== 0 || $humidity !== 0 || $pressure !== 0) {
            $bme = array('temp_c' => $temp / 100, 'feuchte_pct' => $humidity / 100, 'druck_hpa' => $pressure);
        }
        $p += 7;
    }
    $reset = null;
    if ($p + 5 <= $n && $b[$p] === 0x2B) $reset = bb_unsigned($b, $p + 1, 4);

    return array(
        'vcc_v' => bb_unsigned($b, 1, 2) / 1000,
        'batterie_v' => bb_unsigned($b, 3, 2) / 1000,
        'batterie_prozent' => $b[5],
        'gewichts_rohwerte' => $weights,
        'temperaturen_c' => $temps,
        'fft_baender' => $fft,
        'bme280' => $bme,
        'reset_grund' => $reset,
    );
}

function bb_gewicht_kg($roh, array $geraet)
{
    if ($roh === null || !isset($geraet['gewicht_offset'], $geraet['gewicht_faktor'])
        || !is_numeric($geraet['gewicht_offset']) || !is_numeric($geraet['gewicht_faktor'])) return null;
    $offset = (float)$geraet['gewicht_offset'];
    $faktor = (float)$geraet['gewicht_faktor'];
    if (!is_finite($offset) || !is_finite($faktor) || $faktor <= 0) return null;
    return ($roh - $offset) * $faktor;
}

function bb_speichern(array $cfg, array $msg)
{
    $ids = isset($msg['end_device_ids']) ? $msg['end_device_ids'] : array();
    $device = isset($ids['device_id']) ? (string)$ids['device_id'] : '';
    $geraet = $cfg['beep_geraete'][$device];
    $expectedEui = isset($geraet['dev_eui']) ? strtolower((string)$geraet['dev_eui']) : '';
    $actualEui = isset($ids['dev_eui']) ? strtolower((string)$ids['dev_eui']) : '';
    if (!preg_match('/^[0-9a-f]{16}$/', $expectedEui) || $expectedEui !== $actualEui)
        return le_ergebnis(400, 'ungueltig', 'BEEP: DevEUI passt nicht zur Zuordnung');

    $up = $msg['uplink_message'];
    $decoded = bb_decode($up);
    if ($decoded === null) return le_ergebnis(200, 'ignoriert', 'BEEP: Kein unterstützter FPort-3-Messframe');
    $recv = isset($up['received_at']) ? $up['received_at'] : (isset($msg['received_at']) ? $msg['received_at'] : null);
    $unix = le_ttn_zeit($recv);
    if ($unix === null) return le_ergebnis(400, 'ungueltig', 'BEEP: ungültige Empfangszeit');
    $gewicht = count($decoded['gewichts_rohwerte']) === 1 ? $decoded['gewichts_rohwerte'][0] : null;
    $kg = bb_gewicht_kg($gewicht, $geraet); // niemals Rohzähler als kg anzeigen
    $funk = le_funk($up);
    $id = le_nachricht_id($msg);

    $base = rtrim($cfg['log_verzeichnis'], '/') . '/beep';
    $dir = $base . '/' . hash('sha256', strtolower($actualEui));
    if (!le_verz_sicher($dir)) return le_ergebnis(500, 'fehler_einrichtung', 'BEEP: Datenordner nicht beschreibbar');
    $lock = @fopen($dir . '/.lock', 'c');
    if (!$lock || !flock($lock, LOCK_EX)) return le_ergebnis(500, 'fehler_einrichtung', 'BEEP: Sperre nicht verfügbar');
    try {
        $index = $dir . '/ids.txt';
        if (le_id_bekannt($index, $id)) return le_ergebnis(200, 'doppelt', 'BEEP: bereits gespeichert');
        $row = array(
            'id' => $id, 'zeit_utc' => $recv, 'unix' => $unix,
            'quelle' => 'beep_base', 'device_id' => $device,
            'f_cnt' => isset($up['f_cnt']) ? $up['f_cnt'] : null,
            'gewicht_roh' => $gewicht, 'gewicht_kg' => $kg,
            'temperatur_c' => count($decoded['temperaturen_c']) ? $decoded['temperaturen_c'][0] : null,
            'temperaturen_c' => $decoded['temperaturen_c'],
            'fft_baender' => $decoded['fft_baender'],
            'batterie_v' => $decoded['batterie_v'],
            'vcc_v' => $decoded['vcc_v'], 'batterie_prozent' => $decoded['batterie_prozent'],
            'rssi' => $funk['rssi'], 'snr' => $funk['snr'],
            'reset_grund' => $decoded['reset_grund'],
            'bme280' => $decoded['bme280'],
        );
        $payload = json_encode($row, JSON_UNESCAPED_SLASHES | JSON_PRESERVE_ZERO_FRACTION);
        if ($payload === false) return le_ergebnis(500, 'fehler_einrichtung', 'BEEP: JSON-Fehler');
        $file = $dir . '/' . gmdate('Y-m', $unix) . '.jsonl';
        $line = $payload . "\n";
        $written = @file_put_contents($file, $line, FILE_APPEND | LOCK_EX);
        if ($written !== strlen($line)) return le_ergebnis(500, 'fehler_einrichtung', 'BEEP: Speicherung fehlgeschlagen');
        if (!le_id_merken($index, $id, time(), 20000))
            return le_ergebnis(500, 'fehler_einrichtung', 'BEEP: Duplikatindex nicht aktualisiert');
        return le_ergebnis(200, 'gespeichert', 'BEEP: Gewicht/Temperatur/FFT gespeichert');
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}

function bb_zeilen(array $cfg, $devEui, $max = 2000)
{
    $dir = rtrim($cfg['log_verzeichnis'], '/') . '/beep/' . hash('sha256', strtolower($devEui));
    $files = glob($dir . '/????-??.jsonl');
    if (!$files) return array();
    rsort($files);
    $rows = array();
    foreach ($files as $file) {
        $lines = @file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if (!is_array($lines)) continue;
        for ($i = count($lines) - 1; $i >= 0 && count($rows) < $max; $i--) {
            $row = json_decode($lines[$i], true);
            if (is_array($row) && isset($row['zeit_utc'])) $rows[] = $row;
        }
        if (count($rows) >= $max) break;
    }
    return array_reverse($rows);
}
