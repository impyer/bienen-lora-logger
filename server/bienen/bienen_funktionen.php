<?php
// Bienen-Eingang für den beelogger-Webserver: Hilfsfunktionen (ohne Seiteneffekte, testbar)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
// Läuft ab PHP 7.4. Allgemeine TTN-Hilfen (Zeit, Zahlen, Funk, Kennung) liegen in server/eingang/eingang_funktionen.php.

require_once __DIR__ . '/../eingang/eingang_funktionen.php';

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

// Wert aus den Formatter-Daten holen; $name leer/null → ''
function le_wert(array $d, $name)
{
    if ($name === null || $name === '' || !array_key_exists($name, $d)) return '';
    return ein_zahl($d[$name]);
}

// Typ (Single=1, Duo=2 …) wie beelogger_log.php aus dem Verzeichnisnamen
function le_logger_typ($verz)
{
    $typ = 1;
    foreach (array('Duo' => 2, 'Triple' => 3, 'Quad' => 4, 'Penta' => 5, 'Hexa' => 6) as $name => $n) {
        if (strpos($verz, 'beelogger') === false && strpos($verz, $name) !== false) $typ = $n;
    }
    return $typ;
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

// Zeile für die Zusatzdatei lora_zusatz.csv
function le_zusatz_kopf()
{
    return array('zeit_utc', 'unix', 'zeitquelle', 'geraet', 'f_cnt', 'f_port', 'rssi', 'snr', 'gateways', 'sf', 'format',
        'firmware_id', 'temp_cpu', 'temp_in2', 'fft_hz', 'fft_db', 'fft_gesamt_db', 'fft_baender_db', 'status', 'neustart',
        'warnungen', 'antwort_beelogger');
}

// Zustandsbits des Funkformats v2 als Zahl (Bit 0 zeit_ok … Bit 6 akku_niedrig), '' ohne Status
function le_statusbits(array $d)
{
    if (!isset($d['Status']) || !is_array($d['Status'])) return '';
    $bits = array('zeit_ok', 'fehler_aussen', 'fehler_ds1', 'fehler_ds2', 'fehler_waage1', 'fehler_waage2', 'akku_niedrig');
    $status = 0;
    foreach ($bits as $k => $name) if (!empty($d['Status'][$name])) $status |= 1 << $k;
    return $status;
}

function le_zusatz_zeile($unix, $quelle, $geraet, array $up, array $d, array $funk, $antwort)
{
    $firmware = isset($d['FirmwareID']) ? $d['FirmwareID'] : (isset($d['Aux3']) && isset($d['Format']) && $d['Format'] == 1 ? $d['Aux3'] : '');
    $baender = '';
    if (isset($d['FFT_Baender_dB']) && is_array($d['FFT_Baender_dB'])) $baender = implode(';', array_map('ein_zahl', $d['FFT_Baender_dB']));
    return array(ein_utc_text($unix), $unix, $quelle, $geraet,
        isset($up['f_cnt']) ? $up['f_cnt'] : '', isset($up['f_port']) ? $up['f_port'] : '',
        $funk['rssi'], $funk['snr'], $funk['gateways'], $funk['sf'],
        isset($d['Format']) ? $d['Format'] : '', $firmware, le_wert($d, 'TempCPU'), le_wert($d, 'TempIn2'),
        le_wert($d, 'FFT_Hz'), le_wert($d, 'FFT_dB'), le_wert($d, 'FFT_Gesamt_dB'), $baender, le_statusbits($d),
        isset($d['Neustart']) ? $d['Neustart'] : '', ein_formatter_warnungen($up), $antwort);
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

// Zeitstempel, den beelogger für diesen Datensatz in week.csv schreiben muss. beelogger setzt die Sekunden auf :00;
// im Ortszeit-Modus rechnet es den Zeittext mit strtotime() in der Zeitzone des Servers zurück.
function le_erwarteter_zeitstempel($unix, $zeit_text, $utc)
{
    if ($utc) return $unix - $unix % 60;
    return strtotime(str_replace('_', ' ', substr($zeit_text, 0, 17) . '00'));
}

// Wurde der Datensatz gespeichert? (CI26-01)
// Nicht über die Dateigröße entscheiden: beelogger_log.php kürzt week.csv in CSVbuilder_log() auf 7 Tage,
// und zwar nur vor 08:00 Uhr Serverzeit (date("G") < 8). Die Datei kann also beim Speichern schrumpfen.
// Maßgeblich ist: Die letzte Zeile trägt danach die erwartete Zeit, vorher nicht (beelogger verwirft gleiche
// oder ältere Zeiten, eine schon vorhandene Zeit wird also nicht ein zweites Mal geschrieben).
function le_speicherung_erkannt($ts_vorher, $ts_nachher, $erwartet)
{
    return $ts_nachher !== null && $ts_nachher === $erwartet && $ts_vorher !== $erwartet;
}

// Nimmt dieser beelogger_log.php UTC=1 an? (eigene Fassung ab eigen-utc-2, Merkmal $BL_UTC_FAEHIG) – SRV26-07
// Geprüft wird je Logger-Verzeichnis, nicht über eine Datei im Hauptordner.
function le_utc_faehig($log_php)
{
    if (!is_file($log_php)) return false;
    $kopf = file_get_contents($log_php, false, null, 0, 8192);
    return is_string($kopf) && strpos($kopf, '$BL_UTC_FAEHIG=1;') !== false;
}

// Zeitbasis für den Ziel-Logger (SRV26-07) aus der Einstellung utc_zeit ('auto', true, false) und der Fähigkeit
// seines beelogger_log.php. Rückgabe: true = UTC, false = Ortszeit, null = UTC verlangt, aber Logger nicht fähig.
function le_zeitbasis($utc_zeit, $faehig)
{
    if ($utc_zeit === true && !$faehig) return null;
    return ($utc_zeit === 'auto') ? $faehig : ($utc_zeit === true);
}
