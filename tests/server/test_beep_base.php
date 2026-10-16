<?php
// SPDX-License-Identifier: GPL-3.0-or-later
// Anonymisierter Feldpayload, kein DevEUI, kein echter Gerätename im Repo.
require __DIR__ . '/../../server/lora/lora_verarbeitung.php';
$ok = 0;
function bb_check($what, $got, $want) {
    global $ok;
    if ($got !== $want) {
        fwrite(STDERR, "FAIL $what: " . var_export($got, true) . " erwartet " . var_export($want, true) . "\n");
        exit(1);
    }
    $ok++;
}
$base64='GwzNDL5kCgEVV/kEAQczDAoJRgATAAsAEQAHAAYABgAEAAMABAAABwAAAAAAACsAAAAC';
$up=array('f_port'=>3, 'f_cnt'=>29, 'frm_payload'=>$base64,
    'received_at'=>'2026-10-16T00:51:32.772298464Z',
    'rx_metadata'=>array(array('rssi'=>-78,'snr'=>10.75)));
$d=bb_decode($up);
bb_check('Decoder-Objekt', is_array($d), true);
bb_check('VCC', $d['vcc_v'], 3.277);
bb_check('Batterie', $d['batterie_v'], 3.262);
bb_check('Batterieprozent', $d['batterie_prozent'], 100);
bb_check('Gewichtsrohwert', $d['gewichts_rohwerte'], array(1398777));
bb_check('Temperatur', $d['temperaturen_c'], array(18.43));
bb_check('FFT-Bänder', count($d['fft_baender']), 10);
bb_check('FFT erstes Band', $d['fft_baender'][0], array('von_hz'=>71,'bis_hz'=>122,'wert'=>19));
bb_check('FFT letztes Band', $d['fft_baender'][9], array('von_hz'=>532,'bis_hz'=>583,'wert'=>0));
bb_check('BME fehlt', $d['bme280'], null);
bb_check('Reset Grund', $d['reset_grund'], 2);
$cal=array('gewicht_offset'=>101109,'gewicht_faktor'=>0.000024211515512725);
bb_check('Gewicht kg', abs(bb_gewicht_kg(1398777,$cal)-31.418508912366825)<1e-9, true);
bb_check('kein geschätztes Gewicht ohne Kalibrierung', bb_gewicht_kg(1398777,array()), null);
$wrong=$up; $wrong['f_port']=2;
bb_check('kein fremder FPort', bb_decode($wrong), null);
$wrong=$up; $wrong['frm_payload']='AA==';
bb_check('defekter Payload', bb_decode($wrong), null);
$wrong=$up; $wrong['frm_payload']=base64_encode(substr(base64_decode($base64),0,22));
bb_check('abgeschnittener Payload', bb_decode($wrong), null);
$tmp=sys_get_temp_dir().'/bb_test_'.getmypid();
@mkdir($tmp,0700,true);
$cfg=array('beep_geraete'=>array('test-base'=>array('dev_eui'=>'0123456789abcdef')+$cal),
    'log_verzeichnis'=>$tmp);
$msg=array('end_device_ids'=>array('device_id'=>'test-base','dev_eui'=>'0123456789ABCDEF'),'uplink_message'=>$up);
$r=le_verarbeiten($cfg,$msg);
bb_check('Verarbeitung gespeichert', $r['klasse'], 'gespeichert');
$rows=bb_zeilen($cfg,'0123456789abcdef');
bb_check('eine Zeile', count($rows), 1);
bb_check('Zeile Gewicht', abs($rows[0]['gewicht_kg']-31.418508912366825)<1e-9, true);
bb_check('Kalibrierung im Messwert erhalten', $rows[0]['kalibrierung'], array('offset'=>101109.0,'faktor'=>0.000024211515512725));
$r=le_verarbeiten($cfg,$msg);
bb_check('Duplikat erkannt', $r['klasse'], 'doppelt');
bb_check('Duplikat nicht angehängt', count(bb_zeilen($cfg,'0123456789abcdef')), 1);
$mismatch=$msg;$mismatch['end_device_ids']['dev_eui']='ffffffffffffffff';
bb_check('EUI-Mismatch verworfen', le_verarbeiten($cfg,$mismatch)['klasse'], 'ungueltig');
foreach (glob($tmp.'/beep/*/*') as $f) @unlink($f);
foreach (glob($tmp.'/beep/*/.*') as $f) if (is_file($f)) @unlink($f);
foreach (glob($tmp.'/beep/*') as $d) @rmdir($d);
@rmdir($tmp.'/beep');
@unlink($tmp.'/beep/.htaccess');
@rmdir($tmp);
echo "$ok BEEP-Tests bestanden\n";
