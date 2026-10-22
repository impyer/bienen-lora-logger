<?php
// Unit-Tests für server/bienen/bienen_funktionen.php und die Hilfen in bienen_verarbeitung.php. Aufruf: php tests/server/test_bienen_funktionen.php
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../../server/bienen/bienen_verarbeitung.php';

$anz = 0; $fehler = 0;
function gleich($name, $ist, $soll)
{
    global $anz, $fehler;
    $anz++;
    if ($ist !== $soll) { $fehler++; echo "FEHL - $name\n       soll: " . var_export($soll, true) . "\n       ist:  " . var_export($ist, true) . "\n"; }
}

// Messzeit
$ok = array('zeit_ok' => true);
gleich('Gerätezeit gültig', le_messzeit(array('Messzeit_unix' => 1000, 'Status' => $ok), 1100, 900), array(1000, 'geraet'));
gleich('Gerätezeit genau an der Grenze', le_messzeit(array('Messzeit_unix' => 200, 'Status' => $ok), 1100, 900), array(200, 'geraet'));
gleich('Gerätezeit zu alt', le_messzeit(array('Messzeit_unix' => 199, 'Status' => $ok), 1100, 900), array(1100, 'ttn'));
gleich('Gerätezeit 30 s voraus erlaubt', le_messzeit(array('Messzeit_unix' => 1130, 'Status' => $ok), 1100, 900), array(1130, 'geraet'));
gleich('Gerätezeit 31 s voraus', le_messzeit(array('Messzeit_unix' => 1131, 'Status' => $ok), 1100, 900), array(1100, 'ttn'));
gleich('Uhr nicht abgeglichen', le_messzeit(array('Messzeit_unix' => 1000, 'Status' => array('zeit_ok' => false)), 1100, 900), array(1100, 'ttn'));
gleich('ohne Status', le_messzeit(array('Messzeit_unix' => 1000), 1100, 900), array(1100, 'ttn'));
gleich('ohne Empfangszeit', le_messzeit(array(), null, 900), null);

// EE-Datensatz: Feldzahl wie beelogger_log.php M.40 erwartet (13 + (n−1)·3, ab Duo +1)
for ($n = 1; $n <= 6; $n++) {
    $soll = 13 + ($n - 1) * 3 + ($n > 1 ? 1 : 0);
    gleich("EE-Feldzahl Typ $n", count(explode(',', le_ee_datensatz(array(), $n, '2026/10/08_14:00:00', array(), 'TempOut'))), $soll);
}
$d = array('TempIn' => 34.56, 'TempIn2' => 18.07, 'TempOut' => 12.34, 'FeuchteIn' => 55.5, 'FeuchteOut' => 67, 'Licht' => 100,
    'Gewicht' => 45.678, 'Gewicht2' => -0.123, 'VBatt' => 3.912, 'VSolar' => 5.1, 'Service' => 0, 'Aux1' => 1013.2,
    'FFT_Hz' => 247.3, 'FFT_dB' => -23.5, 'Aux3' => 260705);
$aux = array(1 => 'Aux1', 2 => 'FFT_Hz', 3 => 'FFT_dB');
gleich('EE Einzel', le_ee_datensatz($d, 1, 'Z', $aux, 'TempOut'), 'Z,34.56,12.34,55.5,67,100,45.678,3.912,5.1,0,1013.2,247.3,-23.5');
gleich('EE Duo', le_ee_datensatz($d, 2, 'Z', $aux, 'TempOut'), 'Z,12.34,34.56,18.07,12.34,55.5,,67,100,45.678,-0.123,3.912,5.1,0,1013.2,247.3,-23.5');
gleich('EE Aux-Zuordnung frei (Deckeltemperatur in Aux3)', le_ee_datensatz($d, 1, 'Z', array(1 => 'Aux1', 3 => 'TempIn2'), 'TempOut'),
    'Z,34.56,12.34,55.5,67,100,45.678,3.912,5.1,0,1013.2,,18.07');
gleich('EE ungültiger Typ', le_ee_datensatz($d, 7, 'Z', $aux, 'TempOut'), null);
gleich('EE nur erlaubte Zeichen (beelogger-Prüfung)', preg_match('#^[0-9\/\_\-\:\,\.]*$#', le_ee_datensatz($d, 2, '2026/10/08_14:00:00', $aux, 'TempOut')), 1);

// Passwort und CSV
$t = sys_get_temp_dir() . '/le_test_' . getmypid();
@mkdir($t);
file_put_contents("$t/ini.php", "<?php\n\$BeeloggerShowPasswort=\"Show\";\n\$BeeloggerLogPasswort=\"Ge!heim*1\";\n");
gleich('Log-Passwort lesen', le_log_passwort("$t/ini.php"), 'Ge!heim*1');
gleich('Log-Passwort fehlt', le_log_passwort("$t/fehlt.php"), null);
file_put_contents("$t/week.csv", "2026/10/08 14:00:00,1,2,,,1791460800\r\n2026/10/08 14:15:00,1,2,,,1791461700\r\n");
gleich('letzter Zeitstempel', le_letzter_zeitstempel("$t/week.csv"), 1791461700);
file_put_contents("$t/leer.csv", "");
gleich('letzter Zeitstempel leer', le_letzter_zeitstempel("$t/leer.csv"), null);
array_map('unlink', glob("$t/*"));
rmdir($t);

// Zusatzzeile
$z = le_zusatz_zeile(1791460800, 'geraet', 'beelogger-01', array('f_cnt' => 5, 'f_port' => 2),
    array('Format' => 2, 'Status' => array('zeit_ok' => true, 'akku_niedrig' => true), 'FFT_Baender_dB' => array(-40, -22.5)),
    array('rssi' => -71, 'snr' => 8.5, 'gateways' => 1, 'sf' => 7), 'ok');
gleich('Zusatz Spaltenzahl', count($z), count(le_zusatz_kopf()));
gleich('Zusatz Statusbits', $z[18], 65);
gleich('Zusatz Bänder', $z[17], '-40;-22.5');

// Speicherung erkennen (CI26-01): unabhängig von der Dateigröße
gleich('Speicherung: neue Zeit als letzte Zeile', le_speicherung_erkannt(1000, 1060, 1060), true);
gleich('Speicherung: erste Zeile (Datei fehlte)', le_speicherung_erkannt(null, 1060, 1060), true);
gleich('Speicherung: Zeit war schon letzte Zeile (abgelehnt)', le_speicherung_erkannt(1060, 1060, 1060), false);
gleich('Speicherung: ältere Zeit verworfen', le_speicherung_erkannt(2000, 2000, 1060), false);
gleich('Speicherung: keine Zeile danach', le_speicherung_erkannt(null, null, 1060), false);
// Kürzung auf 7 Tage beim Speichern: Datei schrumpft, Zeile ist trotzdem neu
$k = sys_get_temp_dir() . '/le_kurz_' . getmypid() . '.csv';
file_put_contents($k, "a,1792000000\r\nb,1792001800\r\n");
$vor = le_letzter_zeitstempel($k); $g_vor = filesize($k);
file_put_contents($k, "c,1792886400\r\n");   // beelogger schreibt neu und kürzt
clearstatcache();
gleich('Kürzung: Datei kleiner als vorher', filesize($k) < $g_vor, true);
gleich('Kürzung: trotzdem als gespeichert erkannt', le_speicherung_erkannt($vor, le_letzter_zeitstempel($k), 1792886400), true);
@unlink($k);

// UTC-Fähigkeit je beelogger_log.php (SRV26-07)
$repo = __DIR__ . '/../../server';
gleich('UTC-fähig: eigene Fassung', le_utc_faehig($repo . '/beelogger_eigen/beelogger1/beelogger_log.php'), true);
gleich('UTC-fähig: Original M.40 nicht', le_utc_faehig($repo . '/beelogger_M40_original/beelogger1/beelogger_log.php'), false);
gleich('UTC-fähig: Datei fehlt', le_utc_faehig($repo . '/gibt_es_nicht.php'), false);

// Zeitbasis je Ziel-Logger (SRV26-07): Einstellung utc_zeit × Fähigkeit von beelogger_log.php
gleich('Zeitbasis auto, fähig → UTC', le_zeitbasis('auto', true), true);
gleich('Zeitbasis auto, alt → Ortszeit', le_zeitbasis('auto', false), false);
gleich('Zeitbasis true, fähig → UTC', le_zeitbasis(true, true), true);
gleich('Zeitbasis true, alt → nicht möglich', le_zeitbasis(true, false), null);
gleich('Zeitbasis false, fähig → Ortszeit', le_zeitbasis(false, true), false);

// Erwarteter Zeitstempel in week.csv (Sekunden auf :00)
gleich('Erwartet UTC-Modus', le_erwarteter_zeitstempel(1791460809, '2026/10/08_12:00:09', true), 1791460800);
gleich('Erwartet Ortszeit-Modus', le_erwarteter_zeitstempel(1791460809, '2026/10/08_14:00:09', false), 1791460800);

// Logger-Typ aus dem Verzeichnisnamen (wie beelogger_log.php)
gleich('Typ beelogger1', le_logger_typ('beelogger1'), 1);
gleich('Typ Duo1', le_logger_typ('Duo1'), 2);
gleich('Typ Hexa2', le_logger_typ('Hexa2'), 6);
gleich('Typ beeloggerDuo zählt als Einzel', le_logger_typ('beeloggerDuo'), 1);

// Zustandsbits
gleich('Statusbits ohne Status', le_statusbits(array()), '');
gleich('Statusbits zeit_ok + fehler_waage1', le_statusbits(array('Status' => array('zeit_ok' => true, 'fehler_waage1' => true))), 17);

// Aufruf-Adresse von beelogger_log.php und Nachholklassen (bienen_verarbeitung.php)
$cfg_t = array('basis_url' => 'https://example.org/beelogger/', 'aux' => array(), 'waegezellen_temp' => 'TempOut');
$a_t = array('daten' => array('TempIn' => 34.5), 'typ' => 1, 'zeit_text' => '2026/10/08_12:00:00', 'pw' => 'P W', 'verz' => 'beelogger1', 'utc' => true);
gleich('URL UTC-Modus', le_beelogger_url($cfg_t, $a_t),
    'https://example.org/beelogger/beelogger1/beelogger_log.php?PW=P%20W&Z=0&M1=2026%2F10%2F08_12%3A00%3A00%2C34.5%2C%2C%2C%2C%2C%2C%2C%2C%2C%2C%2C&UTC=1');
$a_t['utc'] = false;
gleich('URL Ortszeit-Modus ohne UTC', strpos(le_beelogger_url($cfg_t, $a_t), 'UTC='), false);
gleich('Nachholen bei fehler_endpunkt', le_nachholen_noetig(le_ergebnis(502, 'fehler_endpunkt', '')), true);
gleich('Nachholen bei fehler_einrichtung', le_nachholen_noetig(le_ergebnis(500, 'fehler_einrichtung', '')), true);
gleich('kein Nachholen bei abgelehnt', le_nachholen_noetig(le_ergebnis(200, 'abgelehnt', '')), false);

echo ($anz - $fehler) . " von $anz Tests bestanden\n";
exit($fehler ? 1 : 0);
