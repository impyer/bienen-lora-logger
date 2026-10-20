<?php
// Unit-Tests für die gemeinsame Eingangsschicht server/eingang/. Aufruf: php tests/server/test_eingang_funktionen.php
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../../server/eingang/eingang_webhook.php';

$anz = 0; $fehler = 0;
function gleich($name, $ist, $soll)
{
    global $anz, $fehler;
    $anz++;
    if ($ist !== $soll) { $fehler++; echo "FEHL - $name\n       soll: " . var_export($soll, true) . "\n       ist:  " . var_export($ist, true) . "\n"; }
}

// Zeit von TTN
gleich('TTN-Zeit mit Nanosekunden', ein_ttn_zeit('2026-10-08T12:00:03.123456789Z'), 1791460803);
gleich('TTN-Zeit ohne Bruchteil', ein_ttn_zeit('2026-10-08T12:00:03Z'), 1791460803);
gleich('TTN-Zeit ungültig', ein_ttn_zeit('2026-10-08 12:00:03'), null);
gleich('TTN-Zeit fehlt', ein_ttn_zeit(null), null);

// Ortszeit
gleich('Ortszeit Sommer', ein_ortszeit_text(1791460800), '2026/10/08_14:00:00');
gleich('Ortszeit Winter', ein_ortszeit_text(1792891800), '2026/10/25_02:30:00');

// Zahlen
gleich('Zahl ganz', ein_zahl(5), '5');
gleich('Zahl Nachkomma', ein_zahl(45.678), '45.678');
gleich('Zahl gerundet', ein_zahl(1.23456), '1.235');
gleich('Zahl negativ', ein_zahl(-23.5), '-23.5');
gleich('Zahl −0', ein_zahl(-0.0001), '0');
gleich('Zahl sehr klein (kein Exponent)', ein_zahl(1e-7), '0');
gleich('Zahl groß (kein Exponent)', ein_zahl(1e7), '10000000');
gleich('Zahl Text', ein_zahl('12.5'), '12.5');
gleich('kein Zahlenwert', ein_zahl('abc'), '');
gleich('Wahrheitswert', ein_zahl(true), '');
gleich('Liste', ein_zahl(array(1)), '');
gleich('NaN', ein_zahl(NAN), '');

// Funk
$up = array('rx_metadata' => array(array('rssi' => -95, 'snr' => 3), array('rssi' => -71, 'snr' => 8.5), array('snr' => 1)),
    'settings' => array('data_rate' => array('lora' => array('spreading_factor' => 9))));
gleich('Funk bestes Gateway', ein_funk($up), array('rssi' => -71, 'snr' => 8.5, 'gateways' => 3, 'sf' => 9));
gleich('Funk ohne Metadaten', ein_funk(array()), array('rssi' => '', 'snr' => '', 'gateways' => 0, 'sf' => ''));

// Kennung der Nachricht (Duplikat-Erkennung)
$m = array('end_device_ids' => array('device_id' => 'b1'), 'uplink_message' => array('f_port' => 2, 'f_cnt' => 5, 'frm_payload' => 'AAE=', 'received_at' => '2026-10-08T12:00:03Z'));
$m2 = $m; $m2['uplink_message']['received_at'] = '2026-10-09T12:00:03Z';   // gleicher FCnt nach Zähler-Rücksprung
$m3 = $m; $m3['uplink_message']['rx_metadata'] = array(array('rssi' => -80));  // andere Metadaten, gleiche Nachricht
gleich('Kennung: 40 Hex-Zeichen', (bool)preg_match('/^[0-9a-f]{40}$/', ein_nachricht_id($m)), true);
gleich('Kennung: gleicher FCnt, anderer Empfang → verschieden', ein_nachricht_id($m) === ein_nachricht_id($m2), false);
gleich('Kennung: Metadaten egal', ein_nachricht_id($m) === ein_nachricht_id($m3), true);

// Liste verarbeiteter Kennungen
$tmp = sys_get_temp_dir() . '/ein_ids_' . getmypid() . '.txt';
@unlink($tmp);
gleich('Kennung unbekannt (keine Datei)', ein_id_bekannt($tmp, 'abc'), false);
gleich('Kennung merken', ein_id_merken($tmp, 'abc', 1000), true);
gleich('Kennung bekannt', ein_id_bekannt($tmp, 'abc'), true);
gleich('Teilstring zählt nicht', ein_id_bekannt($tmp, 'ab'), false);
for ($k = 0; $k < 12; $k++) ein_id_merken($tmp, 'id' . $k, 1000 + $k, 10);
gleich('Liste begrenzt auf 10 Einträge', count(file($tmp)), 10);
gleich('älteste Kennung verdrängt', ein_id_bekannt($tmp, 'abc'), false);
gleich('neueste Kennung vorhanden', ein_id_bekannt($tmp, 'id11'), true);
@unlink($tmp);

// UTC-Text
gleich('UTC-Text', ein_utc_text(1791460800), '2026-10-08T12:00:00Z');

// Felder der TTN-Nachricht
$m = array('end_device_ids' => array('device_id' => 'b1'), 'received_at' => '2026-10-08T12:00:09Z',
    'uplink_message' => array('received_at' => '2026-10-08T12:00:03Z', 'decoded_payload_warnings' => array('w1', 'w2')));
gleich('Gerätename', ein_geraet_id($m), 'b1');
gleich('Gerätename fehlt', ein_geraet_id(array()), '');
gleich('Uplink vorhanden', ein_uplink($m)['received_at'], '2026-10-08T12:00:03Z');
gleich('Uplink kein Feld (Join-Meldung)', ein_uplink(array('uplink_message' => 'x')), array());
gleich('Empfangszeit aus uplink_message', ein_empfangszeit($m), '2026-10-08T12:00:03Z');
$m4 = $m; unset($m4['uplink_message']['received_at']);
gleich('Empfangszeit aus der Nachricht', ein_empfangszeit($m4), '2026-10-08T12:00:09Z');
gleich('Empfangszeit fehlt', ein_empfangszeit(array()), null);
gleich('Formatter-Warnungen', ein_formatter_warnungen($m['uplink_message']), 'w1; w2');
gleich('Formatter-Warnungen fehlen', ein_formatter_warnungen(array()), '');
gleich('Kennung ohne Uplink: Empfangszeit der Nachricht zählt', ein_nachricht_id($m4) === ein_nachricht_id(array('end_device_ids' => array('device_id' => 'b1'), 'received_at' => '2026-10-08T12:00:09Z')), true);

// Protokoll, CSV, Sperre
$t = sys_get_temp_dir() . '/ein_test_' . getmypid();
gleich('Verzeichnis anlegen', ein_verz_sicher("$t/log"), true);
gleich('Verzeichnis gesperrt (.htaccess)', file_get_contents("$t/log/.htaccess"), "Require all denied\n");
gleich('Protokollzeile geschrieben', ein_protokoll("$t/log", array('art' => 'uplink', 'wert' => 1.0)), true);
$z = json_decode(trim(file_get_contents("$t/log/" . gmdate('Y-m') . '.jsonl')), true);
gleich('Protokollzeile mit log_zeit', array_keys($z), array('art', 'wert', 'log_zeit'));
mkdir("$t/blockiert/" . gmdate('Y-m') . '.jsonl', 0750, true);   // Monatsdatei als Verzeichnis: Schreiben scheitert (wie im E2E-Test R-2)
gleich('Protokolldatei ist Verzeichnis → false', ein_protokoll("$t/blockiert", array('a' => 1)), false);
gleich('CSV neu mit Kopf', ein_csv_anhaengen("$t/a.csv", array('k1', 'k2'), array(1, 'x'), ';'), true);
gleich('CSV angehängt ohne zweiten Kopf', ein_csv_anhaengen("$t/a.csv", array('k1', 'k2'), array(2, 'y'), ';'), true);
gleich('CSV Inhalt', file_get_contents("$t/a.csv"), "k1;k2\n1;x\n2;y\n");
mkdir("$t/b.csv");
gleich('CSV nicht schreibbar → false', ein_csv_anhaengen("$t/b.csv", array('k'), array(1), ','), false);
$s = ein_sperre_holen("$t/x.lock");
gleich('Sperre geholt', is_resource($s), true);
ein_sperre_freigeben($s);
gleich('Sperre im fehlenden Verzeichnis → false', ein_sperre_holen("$t/fehlt/x.lock"), false);
@unlink("$t/log/.htaccess"); array_map('unlink', glob("$t/log/*")); rmdir("$t/log");
rmdir("$t/blockiert/" . gmdate('Y-m') . '.jsonl'); rmdir("$t/blockiert"); rmdir("$t/b.csv");
array_map('unlink', glob("$t/*")); rmdir($t);

// Konfiguration und Warnungen
$c = sys_get_temp_dir() . '/ein_cfg_' . getmypid() . '.php';
file_put_contents($c, "<?php\nreturn array('token' => 'abc', 'header' => 'X-Eigen');\n");
gleich('Konfiguration mit Vorgaben', ein_cfg_laden($c, array('header' => 'X-Bienen-Token', 'log' => 'l')), array('token' => 'abc', 'header' => 'X-Eigen', 'log' => 'l'));
file_put_contents($c, "<?php\nreturn 5;\n");
gleich('Konfiguration kein Feld → null', ein_cfg_laden($c, array()), null);
@unlink($c);
gleich('Konfiguration fehlt → null', ein_cfg_laden($c, array()), null);
gleich('keine Warnung', ein_warnung(), '');
ein_warnung('eins'); ein_warnung('zwei');
gleich('Warnungen als Antwortanhang', ein_warnung(), ' | WARNUNG: eins | WARNUNG: zwei');

echo ($anz - $fehler) . " von $anz Tests bestanden\n";
exit($fehler ? 1 : 0);
