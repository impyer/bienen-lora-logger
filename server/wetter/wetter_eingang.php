<?php
// Wetter-Eingang für den beelogger-Webserver (Webhook-Ziel für The Things Stack, Wetterstation SenseCAP S2120)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// Ablauf: TTN-Uplink (JSON, Formatter formatter/s2120_beep_formatter.js) → Station einem Bienenstand zuordnen
//         → Doppelte erkennen → Zeile in <daten_verzeichnis>/<stand>/<station>_<JJJJ-MM>.csv anhängen.
// Uplinks ohne Nutzdaten (nach einem Join) werden mit 200 „ignoriert“ beantwortet, damit TTN den Webhook nicht abschaltet.
// Annahme, Rohprotokoll und Antwort: gemeinsame Eingangsschicht ../eingang/eingang_webhook.php
// Einrichtung: server/wetter/README.md

error_reporting(E_ALL);
ini_set('display_errors', '0');
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/../eingang/eingang_webhook.php';
require __DIR__ . '/wetter_funktionen.php';

// Eintrag im Monatsprotokoll des Wetter-Eingangs
function we_log(array $cfg, array $eintrag)
{
    return ein_protokoll($cfg['log_verzeichnis'], $eintrag);
}

// Übersicht der Stände (ohne Token) für die Auswertung neben die Messwerte legen
function we_staende_schreiben(array $cfg)
{
    @file_put_contents($cfg['daten_verzeichnis'] . '/staende.json',
        json_encode(we_staende_uebersicht($cfg), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n", LOCK_EX);
}

// ---------- Konfiguration und Anfrage ----------
$cfg = ein_cfg_laden(__DIR__ . '/wetter_config.php', array('header' => 'X-Bienen-Token', 'daten_verzeichnis' => __DIR__ . '/wetter_daten',
    'log_verzeichnis' => __DIR__ . '/wetter_log', 'staende' => array(), 'stationen' => array()));
list($roh, $msg) = ein_webhook_annehmen($cfg, 'wetter_config.php');

$station = ein_geraet_id($msg);
if (!isset($msg['uplink_message']) || !is_array($msg['uplink_message'])) ein_ende(200, 'ignoriert: keine Uplink-Nachricht');
$up = $msg['uplink_message'];
$id = ein_nachricht_id($msg);
ein_rohprotokoll($cfg['log_verzeichnis'], array('station' => $station), $roh, $msg, 'wetter_eingang');

$stand = we_stand_fuer($cfg, $station);
if ($stand === null) ein_ende(200, 'ignoriert: Station nicht in wetter_config.php: ' . $station);
if ($stand === false) ein_ende(500, 'wetter_config.php: Station ' . $station . ' ohne gültigen Stand');

if (!we_hat_messwerte($up)) {
    $grund = !isset($up['frm_payload']) ? 'ohne Nutzdaten' : (!isset($up['decoded_payload']) ? 'kein decoded_payload (Formatter?)' : 'keine Messwerte');
    we_log($cfg, array('station' => $station, 'art' => 'ignoriert', 'id' => $id, 'text' => $grund));
    ein_ende(200, 'ignoriert: Uplink ' . $grund);
}

$unix = ein_ttn_zeit(ein_empfangszeit($msg));
if ($unix === null) ein_ende(400, 'received_at fehlt oder ist ungültig');

// ---------- Speichern (Sperre je Station: Doppelprüfung und Anhängen gemeinsam; Freigabe mit dem Ende der Anfrage) ----------
if (!ein_verz_sicher($cfg['log_verzeichnis']) || !ein_verz_sicher($cfg['daten_verzeichnis'])
    || !ein_verz_sicher($cfg['daten_verzeichnis'] . '/' . $stand)) {
    ein_ende(500, 'Verzeichnis nicht beschreibbar');
}
$sperre = ein_sperre_holen($cfg['log_verzeichnis'] . '/sperre_' . $station . '.lock');
if (!$sperre) ein_ende(500, 'Sperre nicht möglich');

$ids = $cfg['log_verzeichnis'] . '/ids_' . $station . '.txt';
if (ein_id_bekannt($ids, $id)) ein_ende(200, 'doppelt: schon gespeichert');
if (!empty($cfg['test_pause_ms'])) usleep(1000 * (int)$cfg['test_pause_ms']);   // nur für den Paralleltest

$datei = $cfg['daten_verzeichnis'] . '/' . we_dateiname($stand, $station, $unix);
if (!ein_csv_anhaengen($datei, we_kopf(), we_zeile($unix, $stand, $station, $up), ';')) {
    we_log($cfg, array('station' => $station, 'art' => 'fehler', 'id' => $id, 'text' => 'Schreiben fehlgeschlagen: ' . $datei));
    ein_ende(500, 'Schreiben fehlgeschlagen');
}
ein_id_merken($ids, $id, time());
we_staende_schreiben($cfg);
ein_ende(200, 'gespeichert: ' . we_dateiname($stand, $station, $unix));
