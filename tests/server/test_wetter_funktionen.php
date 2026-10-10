<?php
// Unit-Tests für server/wetter/wetter_funktionen.php. Aufruf: php tests/server/test_wetter_funktionen.php
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../../server/wetter/wetter_funktionen.php';

$anz = 0; $fehler = 0;
function gleich($name, $ist, $soll)
{
    global $anz, $fehler;
    $anz++;
    if ($ist !== $soll) { $fehler++; echo "FEHL - $name\n       soll: " . var_export($soll, true) . "\n       ist:  " . var_export($ist, true) . "\n"; }
}

// Kennungen
gleich('Kennung ok', we_kennung_ok('hauptstand'), true);
gleich('Kennung mit Bindestrich', we_kennung_ok('wetterstation-01'), true);
gleich('Kennung Großbuchstaben', we_kennung_ok('Hauptstand'), false);
gleich('Kennung Pfad', we_kennung_ok('../x'), false);
gleich('Kennung leer', we_kennung_ok(''), false);
gleich('Kennung keine Zeichenkette', we_kennung_ok(null), false);
gleich('Kennung zu lang (37)', we_kennung_ok(str_repeat('a', 37)), false);

// Zuordnung Station → Stand
$cfg = array(
    'staende' => array('hauptstand' => array('name' => 'Hauptstand am Haus', 'logger' => array('beelogger1', 'beelogger2')),
                       'wiese' => array('name' => 'Wiese')),
    'stationen' => array('wetterstation-01' => array('stand' => 'hauptstand'),
                         'station-ohne-stand' => array(),
                         'station-falscher-stand' => array('stand' => 'gibtsnicht'),
                         'Station-Gross' => array('stand' => 'hauptstand')),
);
gleich('Stand bekannt', we_stand_fuer($cfg, 'wetterstation-01'), 'hauptstand');
gleich('Station unbekannt', we_stand_fuer($cfg, 'wetterstation-02'), null);
gleich('Station ohne Stand', we_stand_fuer($cfg, 'station-ohne-stand'), false);
gleich('Station mit unbekanntem Stand', we_stand_fuer($cfg, 'station-falscher-stand'), false);
gleich('Stationsname ungültig', we_stand_fuer($cfg, 'Station-Gross'), false);

// Übersicht ohne Token
gleich('Übersicht', we_staende_uebersicht($cfg + array('token' => 'geheim')), array(
    'hauptstand' => array('name' => 'Hauptstand am Haus', 'logger' => array('beelogger1', 'beelogger2'), 'stationen' => array('wetterstation-01', 'Station-Gross')),
    'wiese' => array('name' => 'Wiese', 'logger' => array(), 'stationen' => array()),
));

// Messwerte vorhanden?
$voll = array('t' => 11, 'h' => 88, 'p' => 98170, 'p_hpa' => 981.7, 'l' => 0, 'uv' => 0, 'wind_ms' => 0, 'wind_dir_deg' => 72,
              'gust_ms' => 1, 'rain_mmh' => 0, 'rain_mm' => 4.064);
gleich('Uplink mit Messwerten', we_hat_messwerte(array('frm_payload' => 'SgBu', 'decoded_payload' => $voll)), true);
gleich('Uplink ohne Nutzdaten (nach Join)', we_hat_messwerte(array('f_cnt' => 1)), false);
gleich('Uplink mit leerem frm_payload', we_hat_messwerte(array('frm_payload' => '', 'decoded_payload' => $voll)), false);
gleich('Uplink ohne decoded_payload', we_hat_messwerte(array('frm_payload' => 'SgBu')), false);
gleich('decoded_payload ohne bekannte Felder', we_hat_messwerte(array('frm_payload' => 'AA==', 'decoded_payload' => array('x' => 1))), false);
gleich('decoded_payload mit Text statt Zahl', we_hat_messwerte(array('frm_payload' => 'AA==', 'decoded_payload' => array('t' => 'abc'))), false);
gleich('nur Batterie (Block 03)', we_hat_messwerte(array('frm_payload' => 'A2Q=', 'decoded_payload' => array('battery_pct' => 100))), true);
gleich('kein Feld', we_hat_messwerte(null), false);

// Dateiname: Monat in UTC
gleich('Dateiname', we_dateiname('hauptstand', 'wetterstation-01', 1791602508), 'hauptstand/wetterstation-01_2026-10.csv');
gleich('Dateiname Monatswechsel UTC (Ortszeit schon November)', we_dateiname('h', 's', 1793491199), 'h/s_2026-10.csv');

// Zeile
$up = array('f_cnt' => 7, 'f_port' => 3, 'frm_payload' => 'SgBuWAAAAAAAAABLAEgAAAAAJllMAAoAAA/g', 'decoded_payload' => $voll,
    'rx_metadata' => array(array('rssi' => -66, 'snr' => 14.75)),
    'settings' => array('data_rate' => array('lora' => array('spreading_factor' => 7))));
$z = we_zeile(1791602508, 'hauptstand', 'wetterstation-01', $up);
gleich('Zeile Spaltenzahl = Kopf', count($z), count(we_kopf()));
$k = array_combine(we_kopf(), $z);
gleich('Zeile Zeit UTC', $k['zeit_utc'], '2026-10-10T03:21:48Z');
gleich('Zeile Ortszeit', $k['ortszeit'], '2026/10/10_05:21:48');
gleich('Zeile t', $k['t'], '11');
gleich('Zeile Luftdruck hPa', $k['p_hpa'], '981.7');
gleich('keine Spalte p (Pa nur für BEEP)', array_key_exists('p', $k), false);
gleich('Zeile Regensumme', $k['rain_mm'], '4.064');
gleich('Zeile Böe', $k['gust_ms'], '1');
gleich('Zeile Batterie leer', $k['battery_pct'], '');
gleich('Zeile RSSI', $k['rssi'], -66);
gleich('Zeile SF', $k['sf'], 7);
gleich('Zeile Rohdaten hex', $k['payload_hex'], '4A006E58000000000000004B00480000000026594C000A00000FE0');
gleich('Zeile Stand/Station', array($k['stand'], $k['station']), array('hauptstand', 'wetterstation-01'));
$z2 = array_combine(we_kopf(), we_zeile(1791602508, 'h', 's', array('frm_payload' => 'BGQ=', 'decoded_payload' => array('battery_pct' => 100, 'interval_min' => 5, 't' => -0.1),
    'decoded_payload_warnings' => array('w1', 'w2'))));
gleich('Zeile negative Temperatur', $z2['t'], '-0.1');
gleich('Zeile fehlender Wert leer', $z2['h'], '');
gleich('Zeile Batterie', $z2['battery_pct'], '100');
gleich('Zeile Intervall', $z2['interval_min'], '5');
gleich('Zeile Warnungen', $z2['warnungen'], 'w1; w2');

echo ($fehler ? "FEHLER" : "OK") . ": Wetter-Funktionen " . ($anz - $fehler) . " von $anz Prüfungen bestanden\n";
exit($fehler ? 1 : 0);
