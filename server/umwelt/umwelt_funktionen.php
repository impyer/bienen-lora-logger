<?php
// Umwelt-Eingang: Hilfsfunktionen (ohne Seiteneffekte, testbar)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
// Läuft ab PHP 7.4. Allgemeine TTN-Hilfen (Zeit, Zahlen, Kennung, Protokoll) liegen in server/eingang/eingang_funktionen.php.

require_once __DIR__ . '/../eingang/eingang_funktionen.php';

// TTN-Gerätename (end_device_ids.device_id): Kleinbuchstaben, Ziffern und '-', 1–36 Zeichen (Regel von The Things Stack)
function ue_geraet_ok($s)
{
    return is_string($s) && preg_match('/^[a-z0-9](?:[-]?[a-z0-9]){0,35}$/', $s) === 1;
}

// Enthält ein (verschachtelter) decoded_payload mindestens eine Zahl? Texte und Wahrheitswerte zählen nicht.
function ue_hat_zahl($d, $tiefe = 0)
{
    if ($tiefe > 8) return false;
    if (is_array($d)) {
        foreach ($d as $v) if (ue_hat_zahl($v, $tiefe + 1)) return true;
        return false;
    }
    return ein_zahl($d) !== '';
}

// Grund, warum ein Uplink keine Messwerte trägt, oder null, wenn er welche hat.
// Nach einem Join senden manche Geräte (z. B. die S2120) Uplinks ohne Nutzdaten.
function ue_ohne_messwerte_grund($up)
{
    if (!is_array($up) || !isset($up['frm_payload']) || $up['frm_payload'] === '') return 'ohne Nutzdaten';
    if (!isset($up['decoded_payload']) || !is_array($up['decoded_payload'])) return 'kein decoded_payload (Formatter?)';
    if (!ue_hat_zahl($up['decoded_payload'])) return 'keine Messwerte';
    return null;
}
