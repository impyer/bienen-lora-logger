<?php
// Umwelt-Eingang: Webhook-Ziel für The Things Stack für alle Umweltsensoren am Stand
// (Wetterstation SenseCAP S2120, Bodensonden Dragino LSN50v2-D23, künftige Geräte)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Der Eingang kennt keine Geräte und keine Felder. Er schreibt jeden Uplink vor jeder Verarbeitung ins Rohprotokoll
// (umwelt_log/JJJJ-MM.jsonl); daraus liest server/datenbank/importer.py in die Datenbank. Welche Werte ein Gerät
// liefert und zu welchem Stand es gehört, steht nur in der Datenbank (Verwaltung: Gerät, Zuordnung, Kanäle).
// Ein neues Gerät braucht also nur einen Uplink-Formatter in TTN, keinen Servercode. Die Messzeit (Gerätezeit oder
// Empfangszeit) bestimmt der Importer nach derselben Regel wie beim Bienen-Eingang.
// Annahme, Token, Rohprotokoll und Antwort: gemeinsame Eingangsschicht ../eingang/eingang_webhook.php
// Einrichtung: server/umwelt/README.md

error_reporting(E_ALL);
ini_set('display_errors', '0');
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../eingang/eingang_webhook.php';
require __DIR__ . '/umwelt_funktionen.php';

$cfg = ein_cfg_laden(__DIR__ . '/umwelt_config.php', array('header' => 'X-Bienen-Token', 'log_verzeichnis' => __DIR__ . '/umwelt_log'));
list($roh, $msg) = ein_webhook_annehmen($cfg, 'umwelt_config.php');

if (!isset($msg['uplink_message']) || !is_array($msg['uplink_message'])) ein_ende(200, 'ignoriert: keine Uplink-Nachricht');
$geraet = ein_geraet_id($msg);
$id = ein_nachricht_id($msg);
$ok = ein_rohprotokoll($cfg['log_verzeichnis'], array('geraet' => $geraet), $roh, $msg, 'umwelt_eingang');

if (!ue_geraet_ok($geraet)) ein_ende(200, 'ignoriert: Gerätename fehlt oder ist ungültig');
if (ein_ttn_zeit(ein_empfangszeit($msg)) === null) ein_ende(400, 'received_at fehlt oder ist ungültig');

$grund = ue_ohne_messwerte_grund($msg['uplink_message']);
if ($grund !== null) {
    // 200, damit TTN den Webhook nicht abschaltet (leere Uplinks nach einem Join)
    ein_protokoll($cfg['log_verzeichnis'], array('geraet' => $geraet, 'art' => 'ignoriert', 'id' => $id, 'text' => $grund));
    ein_ende(200, 'ignoriert: Uplink ' . $grund);
}
// Das Rohprotokoll ist hier der einzige Speicher. Scheitert es, ist der Messwert verloren: als Fehler melden,
// damit es in der TTN-Konsole sichtbar wird (die Eingangsschicht hängt die Warnung zusätzlich an).
if (!$ok) ein_ende(500, 'nicht gespeichert');
ein_ende(200, 'protokolliert: ' . $geraet);
