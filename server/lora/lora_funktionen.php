<?php
// LoRa-Eingang für den beelogger-Webserver: Hilfsfunktionen (ohne Seiteneffekte, testbar)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
// Läuft ab PHP 7.4.

// TTN-Zeit "2026-10-08T12:00:03.123456789Z" → Unix-Sekunden, oder null
function le_ttn_zeit($s)
{
    if (!is_string($s) || !preg_match('/^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?Z$/', $s, $m)) return null;
    $d = DateTime::createFromFormat('Y-m-d\TH:i:s', $m[1], new DateTimeZone('UTC'));
    return $d ? $d->getTimestamp() : null;
}

// Messzeitpunkt wählen: Gerätezeit, wenn abgeglichen und plausibel; sonst Empfangszeit von TTN
// Rückgabe: [unix, 'geraet'|'ttn'] oder null
function le_messzeit(array $daten, $empfang_unix, $max_abweichung_s)
{
    if ($empfang_unix === null) return null;
    if (isset($daten['Messzeit_unix'], $daten['Status']['zeit_ok']) && $daten['Status']['zeit_ok'] === true
        && is_numeric($daten['Messzeit_unix'])) {
        $t = (int)$daten['Messzeit_unix'];
        // Messung liegt vor dem Empfang; kleine Vorgehzeit der Uhr zulassen (30 s)
        if ($t <= $empfang_unix + 30 && $empfang_unix - $t <= $max_abweichung_s) return array($t, 'geraet');
    }
    return array($empfang_unix, 'ttn');
}

// Unix-Zeit → beelogger-Zeittext in Ortszeit "Y/m/d_H:i:s" (wie EE-Datensatz)
function le_ortszeit_text($unix, $zone = 'Europe/Berlin')
{
    $d = new DateTime('@' . (int)$unix);
    $d->setTimezone(new DateTimeZone($zone));
    return $d->format('Y/m/d_H:i:s');
}

// Zahl für den beelogger-Datensatz: nur Ziffern, '-' und '.'; leer, wenn kein endlicher Zahlenwert
function le_zahl($v)
{
    if (is_bool($v) || !is_numeric($v)) return '';
    $f = (float)$v;
    if (!is_finite($f)) return '';
    $s = rtrim(rtrim(sprintf('%.3F', $f), '0'), '.');
    return ($s === '-0') ? '0' : $s;
}

// Wert aus den Formatter-Daten holen; $name leer/null → ''
function le_wert(array $d, $name)
{
    if ($name === null || $name === '' || !array_key_exists($name, $d)) return '';
    return le_zahl($d[$name]);
}

// EE-Datensatz für beelogger_log.php (Schlüssel "M<typ>") bauen.
// Reihenfolge laut beelogger_log.php M.40 (Z. 313–360):
// Zeit, [Wägezellentemp. ab Duo], TempIn1..n, TempOut, FeuchteIn1..n, FeuchteOut, Licht, Gewicht1..n, VBatt, VSolar, Service, Aux1, Aux2, Aux3
function le_ee_datensatz(array $d, $typ, $zeit_text, array $aux, $waegetemp_feld)
{
    $n = (int)$typ;
    if ($n < 1 || $n > 6) return null;
    $suffix = function ($i) { return $i === 1 ? '' : (string)$i; };
    $f = array($zeit_text);
    if ($n > 1) $f[] = le_wert($d, $waegetemp_feld);
    for ($i = 1; $i <= $n; $i++) $f[] = le_wert($d, 'TempIn' . $suffix($i));
    $f[] = le_wert($d, 'TempOut');
    for ($i = 1; $i <= $n; $i++) $f[] = le_wert($d, 'FeuchteIn' . $suffix($i));
    $f[] = le_wert($d, 'FeuchteOut');
    $f[] = le_wert($d, 'Licht');
    for ($i = 1; $i <= $n; $i++) $f[] = le_wert($d, 'Gewicht' . $suffix($i));
    $f[] = le_wert($d, 'VBatt');
    $f[] = le_wert($d, 'VSolar');
    $f[] = le_wert($d, 'Service');
    for ($i = 1; $i <= 3; $i++) $f[] = le_wert($d, isset($aux[$i]) ? $aux[$i] : '');
    return implode(',', $f);
}

// Funkdaten aus der TTN-Nachricht: bestes Gateway, Anzahl, Spreizfaktor
function le_funk(array $up)
{
    $r = array('rssi' => '', 'snr' => '', 'gateways' => 0, 'sf' => '');
    if (isset($up['rx_metadata']) && is_array($up['rx_metadata'])) {
        $r['gateways'] = count($up['rx_metadata']);
        foreach ($up['rx_metadata'] as $g) {
            if (!isset($g['rssi']) || !is_numeric($g['rssi'])) continue;
            if ($r['rssi'] === '' || $g['rssi'] > $r['rssi']) {
                $r['rssi'] = $g['rssi'];
                $r['snr'] = isset($g['snr']) ? $g['snr'] : '';
            }
        }
    }
    if (isset($up['settings']['data_rate']['lora']['spreading_factor'])) $r['sf'] = $up['settings']['data_rate']['lora']['spreading_factor'];
    return $r;
}

// Zeile für die Zusatzdatei lora_zusatz.csv
function le_zusatz_kopf()
{
    return array('zeit_utc', 'unix', 'zeitquelle', 'geraet', 'f_cnt', 'f_port', 'rssi', 'snr', 'gateways', 'sf', 'format',
        'firmware_id', 'temp_cpu', 'temp_in2', 'fft_hz', 'fft_db', 'fft_gesamt_db', 'fft_baender_db', 'status', 'neustart',
        'warnungen', 'antwort_beelogger');
}

function le_zusatz_zeile($unix, $quelle, $geraet, array $up, array $d, array $funk, $antwort)
{
    $status = '';
    if (isset($d['Status']) && is_array($d['Status'])) {
        $bits = array('zeit_ok', 'fehler_aussen', 'fehler_ds1', 'fehler_ds2', 'fehler_waage1', 'fehler_waage2', 'akku_niedrig');
        $status = 0;
        foreach ($bits as $k => $name) if (!empty($d['Status'][$name])) $status |= 1 << $k;
    }
    $firmware = isset($d['FirmwareID']) ? $d['FirmwareID'] : (isset($d['Aux3']) && isset($d['Format']) && $d['Format'] == 1 ? $d['Aux3'] : '');
    $baender = '';
    if (isset($d['FFT_Baender_dB']) && is_array($d['FFT_Baender_dB'])) $baender = implode(';', array_map('le_zahl', $d['FFT_Baender_dB']));
    $warn = isset($up['decoded_payload_warnings']) && is_array($up['decoded_payload_warnings']) ? implode('; ', $up['decoded_payload_warnings']) : '';
    return array(gmdate('Y-m-d\TH:i:s\Z', $unix), $unix, $quelle, $geraet,
        isset($up['f_cnt']) ? $up['f_cnt'] : '', isset($up['f_port']) ? $up['f_port'] : '',
        $funk['rssi'], $funk['snr'], $funk['gateways'], $funk['sf'],
        isset($d['Format']) ? $d['Format'] : '', $firmware, le_wert($d, 'TempCPU'), le_wert($d, 'TempIn2'),
        le_wert($d, 'FFT_Hz'), le_wert($d, 'FFT_dB'), le_wert($d, 'FFT_Gesamt_dB'), $baender, $status,
        isset($d['Neustart']) ? $d['Neustart'] : '', $warn, $antwort);
}

// Log-Passwort aus beelogger_ini.php lesen, ohne die Datei auszuführen
function le_log_passwort($ini_datei)
{
    if (!is_file($ini_datei)) return null;
    $s = file_get_contents($ini_datei);
    if (!preg_match('/\$BeeloggerLogPasswort\s*=\s*"([^"]*)"\s*;/', $s, $m)) return null;
    return $m[1];
}

// Unix-Zeit am Ende der letzten Zeile einer beelogger-CSV (week.csv), oder null.
// beelogger_log.php antwortet auch bei verworfenen Datensätzen mit "...ok *" (z. B. "T20Bok *");
// ob gespeichert wurde, zeigt deshalb nur die Datei.
function le_letzter_zeitstempel($csv)
{
    if (!is_file($csv)) return null;
    $fp = fopen($csv, 'rb');
    if (!$fp) return null;
    $groesse = filesize($csv);
    fseek($fp, max(0, $groesse - 4096));
    $rest = stream_get_contents($fp);
    fclose($fp);
    $zeilen = preg_split('/\r?\n/', trim($rest));
    $letzte = end($zeilen);
    if (!preg_match('/,(\d{9,11})$/', $letzte, $m)) return null;
    return (int)$m[1];
}
