<?php
// Unit-Tests für server/lora/lora_funktionen.php. Aufruf: php tests/server/test_lora_funktionen.php
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../../server/lora/lora_funktionen.php';

$anz = 0; $fehler = 0;
function gleich($name, $ist, $soll)
{
    global $anz, $fehler;
    $anz++;
    if ($ist !== $soll) { $fehler++; echo "FEHL - $name\n       soll: " . var_export($soll, true) . "\n       ist:  " . var_export($ist, true) . "\n"; }
}

// Zeit von TTN
gleich('TTN-Zeit mit Nanosekunden', le_ttn_zeit('2026-10-08T12:00:03.123456789Z'), 1791460803);
gleich('TTN-Zeit ohne Bruchteil', le_ttn_zeit('2026-10-08T12:00:03Z'), 1791460803);
gleich('TTN-Zeit ungültig', le_ttn_zeit('2026-10-08 12:00:03'), null);
gleich('TTN-Zeit fehlt', le_ttn_zeit(null), null);

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

// Ortszeit
gleich('Ortszeit Sommer', le_ortszeit_text(1791460800), '2026/10/08_14:00:00');
gleich('Ortszeit Winter', le_ortszeit_text(1792891800), '2026/10/25_02:30:00');

// Zahlen
gleich('Zahl ganz', le_zahl(5), '5');
gleich('Zahl Nachkomma', le_zahl(45.678), '45.678');
gleich('Zahl gerundet', le_zahl(1.23456), '1.235');
gleich('Zahl negativ', le_zahl(-23.5), '-23.5');
gleich('Zahl −0', le_zahl(-0.0001), '0');
gleich('Zahl sehr klein (kein Exponent)', le_zahl(1e-7), '0');
gleich('Zahl groß (kein Exponent)', le_zahl(1e7), '10000000');
gleich('Zahl Text', le_zahl('12.5'), '12.5');
gleich('kein Zahlenwert', le_zahl('abc'), '');
gleich('Wahrheitswert', le_zahl(true), '');
gleich('Liste', le_zahl(array(1)), '');
gleich('NaN', le_zahl(NAN), '');

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

// Funk
$up = array('rx_metadata' => array(array('rssi' => -95, 'snr' => 3), array('rssi' => -71, 'snr' => 8.5), array('snr' => 1)),
    'settings' => array('data_rate' => array('lora' => array('spreading_factor' => 9))));
gleich('Funk bestes Gateway', le_funk($up), array('rssi' => -71, 'snr' => 8.5, 'gateways' => 3, 'sf' => 9));
gleich('Funk ohne Metadaten', le_funk(array()), array('rssi' => '', 'snr' => '', 'gateways' => 0, 'sf' => ''));

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

// Kennung der Nachricht (Duplikat-Erkennung)
$m = array('end_device_ids' => array('device_id' => 'b1'), 'uplink_message' => array('f_port' => 2, 'f_cnt' => 5, 'frm_payload' => 'AAE=', 'received_at' => '2026-10-08T12:00:03Z'));
$m2 = $m; $m2['uplink_message']['received_at'] = '2026-10-09T12:00:03Z';   // gleicher FCnt nach Zähler-Rücksprung
$m3 = $m; $m3['uplink_message']['rx_metadata'] = array(array('rssi' => -80));  // andere Metadaten, gleiche Nachricht
gleich('Kennung: 40 Hex-Zeichen', (bool)preg_match('/^[0-9a-f]{40}$/', le_nachricht_id($m)), true);
gleich('Kennung: gleicher FCnt, anderer Empfang → verschieden', le_nachricht_id($m) === le_nachricht_id($m2), false);
gleich('Kennung: Metadaten egal', le_nachricht_id($m) === le_nachricht_id($m3), true);

// Liste verarbeiteter Kennungen
$tmp = sys_get_temp_dir() . '/le_ids_' . getmypid() . '.txt';
@unlink($tmp);
gleich('Kennung unbekannt (keine Datei)', le_id_bekannt($tmp, 'abc'), false);
gleich('Kennung merken', le_id_merken($tmp, 'abc', 1000), true);
gleich('Kennung bekannt', le_id_bekannt($tmp, 'abc'), true);
gleich('Teilstring zählt nicht', le_id_bekannt($tmp, 'ab'), false);
for ($k = 0; $k < 12; $k++) le_id_merken($tmp, 'id' . $k, 1000 + $k, 10);
gleich('Liste begrenzt auf 10 Einträge', count(file($tmp)), 10);
gleich('älteste Kennung verdrängt', le_id_bekannt($tmp, 'abc'), false);
gleich('neueste Kennung vorhanden', le_id_bekannt($tmp, 'id11'), true);
@unlink($tmp);

// UTC-Fähigkeit je beelogger_log.php (SRV26-07)
$repo = __DIR__ . '/../../server';
gleich('UTC-fähig: eigene Fassung', le_utc_faehig($repo . '/beelogger_eigen/beelogger1/beelogger_log.php'), true);
gleich('UTC-fähig: Original M.40 nicht', le_utc_faehig($repo . '/beelogger_M40_original/beelogger1/beelogger_log.php'), false);
gleich('UTC-fähig: Datei fehlt', le_utc_faehig($repo . '/gibt_es_nicht.php'), false);

echo ($anz - $fehler) . " von $anz Tests bestanden\n";
exit($fehler ? 1 : 0);
