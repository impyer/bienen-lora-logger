<?php
// Unit-Tests für server/umwelt/umwelt_funktionen.php. Aufruf: php tests/server/test_umwelt_funktionen.php
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../../server/umwelt/umwelt_funktionen.php';

$anz = 0; $fehler = 0;
function gleich($name, $ist, $soll)
{
    global $anz, $fehler;
    $anz++;
    if ($ist !== $soll) { $fehler++; echo "FEHL - $name\n       soll: " . var_export($soll, true) . "\n       ist:  " . var_export($ist, true) . "\n"; }
}

// Gerätenamen nach den Regeln von The Things Stack
gleich('Gerät ok', ue_geraet_ok('wetterstation-01'), true);
gleich('Gerät Bodensonde', ue_geraet_ok('lsn50v2-d23-boden'), true);
gleich('Gerät eine Ziffer', ue_geraet_ok('1'), true);
gleich('Gerät 36 Zeichen', ue_geraet_ok(str_repeat('a', 36)), true);
gleich('Gerät 37 Zeichen', ue_geraet_ok(str_repeat('a', 37)), false);
gleich('Gerät Großbuchstaben', ue_geraet_ok('Wetter'), false);
gleich('Gerät Unterstrich', ue_geraet_ok('wetter_01'), false);
gleich('Gerät Pfad', ue_geraet_ok('../x'), false);
gleich('Gerät Bindestrich am Anfang', ue_geraet_ok('-x'), false);
gleich('Gerät Bindestrich am Ende', ue_geraet_ok('x-'), false);
gleich('Gerät doppelter Bindestrich', ue_geraet_ok('a--b'), false);
gleich('Gerät leer', ue_geraet_ok(''), false);
gleich('Gerät kein Text', ue_geraet_ok(null), false);

// Messwerte im decoded_payload (gerätunabhängig, auch verschachtelt)
$p = base64_encode("\x01\x02");
gleich('S2120-Werte', ue_ohne_messwerte_grund(array('frm_payload' => $p, 'decoded_payload' => array('t' => 11.0, 'h' => 88))), null);
gleich('LSN50 Zahl als Text', ue_ohne_messwerte_grund(array('frm_payload' => $p, 'decoded_payload' => array('TempC1' => '12.34'))), null);
gleich('verschachtelt', ue_ohne_messwerte_grund(array('frm_payload' => $p, 'decoded_payload' => array('a' => array('b' => array(0))))), null);
gleich('Null ist ein Messwert', ue_ohne_messwerte_grund(array('frm_payload' => $p, 'decoded_payload' => array('rain_mm' => 0))), null);
gleich('ohne frm_payload', ue_ohne_messwerte_grund(array('f_port' => 3)), 'ohne Nutzdaten');
gleich('leeres frm_payload', ue_ohne_messwerte_grund(array('frm_payload' => '')), 'ohne Nutzdaten');
gleich('ohne decoded_payload', ue_ohne_messwerte_grund(array('frm_payload' => $p)), 'kein decoded_payload (Formatter?)');
gleich('nur Texte und Wahrheitswerte', ue_ohne_messwerte_grund(array('frm_payload' => $p,
    'decoded_payload' => array('modell' => 'S2120', 'ok' => true, 'warnungen' => array('x')))), 'keine Messwerte');
gleich('NaN zählt nicht', ue_hat_zahl(array('x' => NAN)), false);
gleich('kein Array', ue_ohne_messwerte_grund('x'), 'ohne Nutzdaten');

echo ($fehler ? "FEHLER" : "OK") . ": Umwelt-Funktionen " . ($anz - $fehler) . " von $anz Prüfungen bestanden\n";
exit($fehler ? 1 : 0);
