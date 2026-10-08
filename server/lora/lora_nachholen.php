<?php
// LoRa-Eingang: zwischengespeicherte Nachrichten erneut verarbeiten (nur Kommandozeile, z. B. per cron alle 15 min)
//   php lora_nachholen.php
// Verarbeitet die Dateien in <log_verzeichnis>/nachholen/ der Reihe nach (älteste zuerst). Ist das Ergebnis endgültig
// (gespeichert, doppelt, abgelehnt, ignoriert, ungültig), wird die Datei gelöscht; bei erneutem Fehler bleibt sie liegen.
// Doppelte Weitergabe ist ausgeschlossen: Bereits verarbeitete Nachrichten erkennt le_verarbeiten() an ihrer Kennung.
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later

if (PHP_SAPI !== 'cli') { http_response_code(403); exit("nur Kommandozeile\n"); }
error_reporting(E_ALL);
date_default_timezone_set('Europe/Berlin');
require __DIR__ . '/lora_verarbeitung.php';

$cfg = le_cfg_laden();
if ($cfg === null) { fwrite(STDERR, "lora_config.php fehlt oder ist ungültig\n"); exit(2); }
$dateien = glob($cfg['log_verzeichnis'] . '/nachholen/*.json');
sort($dateien);
$fehler = 0;
foreach ($dateien as $datei) {
    $msg = json_decode((string)file_get_contents($datei), true);
    if (!is_array($msg)) { echo basename($datei) . ": unlesbar, verschoben nach .defekt\n"; rename($datei, $datei . '.defekt'); continue; }
    $e = le_verarbeiten($cfg, $msg);
    echo basename($datei) . ': ' . $e['klasse'] . ' – ' . $e['text'] . "\n";
    if (in_array($e['klasse'], array('fehler_endpunkt', 'fehler_einrichtung'), true)) { $fehler++; continue; }
    le_log($cfg, array('art' => 'nachgeholt', 'datei' => basename($datei), 'klasse' => $e['klasse']));
    unlink($datei);
}
echo count($dateien) . " Nachricht(en), davon $fehler weiter offen\n";
exit($fehler ? 1 : 0);
