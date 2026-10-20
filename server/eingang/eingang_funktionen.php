<?php
// Gemeinsame Eingangsschicht aller TTN-Webhooks (LoRa-Logger, Wetterstation, künftig Boden und BEEP Base):
// Hilfsfunktionen ohne HTTP-Seiteneffekte (testbar)
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
// Läuft ab PHP 7.4.

// TTN-Zeit "2026-10-08T12:00:03.123456789Z" → Unix-Sekunden, oder null
function ein_ttn_zeit($s)
{
    if (!is_string($s) || !preg_match('/^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?Z$/', $s, $m)) return null;
    $d = DateTime::createFromFormat('Y-m-d\TH:i:s', $m[1], new DateTimeZone('UTC'));
    return $d ? $d->getTimestamp() : null;
}

// Unix-Zeit → "2026-10-08T12:00:00Z"
function ein_utc_text($unix)
{
    return gmdate('Y-m-d\TH:i:s\Z', (int)$unix);
}

// Unix-Zeit → beelogger-Zeittext in Ortszeit "Y/m/d_H:i:s" (wie EE-Datensatz)
function ein_ortszeit_text($unix, $zone = 'Europe/Berlin')
{
    $d = new DateTime('@' . (int)$unix);
    $d->setTimezone(new DateTimeZone($zone));
    return $d->format('Y/m/d_H:i:s');
}

// Zahl für CSV und beelogger-Datensatz: nur Ziffern, '-' und '.'; leer, wenn kein endlicher Zahlenwert
function ein_zahl($v)
{
    if (is_bool($v) || !is_numeric($v)) return '';
    $f = (float)$v;
    if (!is_finite($f)) return '';
    $s = rtrim(rtrim(sprintf('%.3F', $f), '0'), '.');
    return ($s === '-0') ? '0' : $s;
}

// ---------- Felder der TTN-Nachricht ----------

// TTN-Gerätename (end_device_ids.device_id), '' wenn er fehlt
function ein_geraet_id(array $msg)
{
    return isset($msg['end_device_ids']['device_id']) ? (string)$msg['end_device_ids']['device_id'] : '';
}

// uplink_message als Feld, leer bei Join-, Downlink- und sonstigen Meldungen
function ein_uplink(array $msg)
{
    return isset($msg['uplink_message']) && is_array($msg['uplink_message']) ? $msg['uplink_message'] : array();
}

// Empfangszeit wie von TTN geliefert: uplink_message.received_at, sonst received_at der Nachricht, sonst null
function ein_empfangszeit(array $msg)
{
    $up = ein_uplink($msg);
    if (isset($up['received_at'])) return $up['received_at'];
    return isset($msg['received_at']) ? $msg['received_at'] : null;
}

// Funkdaten aus der TTN-Nachricht: bestes Gateway, Anzahl, Spreizfaktor
function ein_funk(array $up)
{
    $r = array('rssi' => '', 'snr' => '', 'gateways' => 0, 'sf' => '');
    if (isset($up['rx_metadata']) && is_array($up['rx_metadata'])) {
        $r['gateways'] = count($up['rx_metadata']);
        foreach ($up['rx_metadata'] as $g) {
            if (!isset($g['rssi']) || !is_numeric($g['rssi'])) continue;
            if ($r['rssi'] === '' || $g['rssi'] > $r['rssi']) {
                $r['rssi'] = $g['rssi'];
                $r['snr'] = isset($g['snr']) ? $g['snr'] : '';
            }
        }
    }
    if (isset($up['settings']['data_rate']['lora']['spreading_factor'])) $r['sf'] = $up['settings']['data_rate']['lora']['spreading_factor'];
    return $r;
}

// Warnungen des TTN-Formatters als Text "w1; w2", '' wenn keine
function ein_formatter_warnungen(array $up)
{
    return isset($up['decoded_payload_warnings']) && is_array($up['decoded_payload_warnings']) ? implode('; ', $up['decoded_payload_warnings']) : '';
}

// Eindeutige Kennung eines Uplinks für die Duplikat-Erkennung (SRV26-03/04/05).
// FCnt allein reicht nicht: der Musterlogger setzt den Zähler bei 16384 bewusst auf 0 zurück (ABP).
// Mit Nutzdaten und received_at ist eine Wiederholung derselben Nachricht eindeutig erkennbar.
function ein_nachricht_id(array $msg)
{
    $up = ein_uplink($msg);
    $teile = array(
        ein_geraet_id($msg),
        isset($up['f_port']) ? (string)$up['f_port'] : '',
        isset($up['f_cnt']) ? (string)$up['f_cnt'] : '',
        isset($up['frm_payload']) ? (string)$up['frm_payload'] : '',
        (string)ein_empfangszeit($msg),
    );
    return sha1(implode('|', $teile));
}

// ---------- Dateien ----------

// Liste verarbeiteter Kennungen: Zeilen "unixzeit kennung"; behält höchstens $max Einträge
function ein_id_bekannt($datei, $id)
{
    if (!is_file($datei)) return false;
    $s = file_get_contents($datei);
    return is_string($s) && strpos($s, ' ' . $id . "\n") !== false;
}

function ein_id_merken($datei, $id, $jetzt, $max = 5000)
{
    $zeilen = is_file($datei) ? file($datei, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) : array();
    if (!is_array($zeilen)) $zeilen = array();
    $zeilen[] = $jetzt . ' ' . $id;
    if (count($zeilen) > $max) $zeilen = array_slice($zeilen, -$max);
    $tmp = $datei . '.tmp';
    if (@file_put_contents($tmp, implode("\n", $zeilen) . "\n") === false) return false;
    return @rename($tmp, $datei);
}

// Verzeichnis anlegen und für Apache sperren (.htaccess), falls es noch fehlt
function ein_verz_sicher($dir)
{
    if (is_dir($dir)) return true;
    if (!@mkdir($dir, 0750, true)) return false;
    @file_put_contents($dir . '/.htaccess', "Require all denied\n");
    return true;
}

// Eine JSON-Zeile an das Monatsprotokoll <dir>/JJJJ-MM.jsonl anhängen (Monat in UTC).
// Rückgabe: true nur, wenn die ganze Zeile geschrieben wurde (PLT26-02). Das Protokoll ist das Rohprotokoll
// der Plattform: Ein Fehler darf nicht unbemerkt bleiben.
function ein_protokoll($dir, array $eintrag)
{
    if (!ein_verz_sicher($dir)) return false;
    $eintrag['log_zeit'] = ein_utc_text(time());
    $json = json_encode($eintrag, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRESERVE_ZERO_FRACTION);
    if ($json === false) return false;
    $zeile = $json . "\n";
    $n = @file_put_contents($dir . '/' . gmdate('Y-m') . '.jsonl', $zeile, FILE_APPEND | LOCK_EX);
    return $n === strlen($zeile);
}

// Zeile an eine CSV-Datei anhängen; Kopfzeile, wenn die Datei neu ist. Rückgabe: true nur, wenn alles geschrieben wurde.
function ein_csv_anhaengen($datei, array $kopf, array $zeile, $trenner)
{
    $neu = !is_file($datei);
    $fp = @fopen($datei, 'ab');
    if (!$fp) return false;
    $ok = !$neu || fputcsv($fp, $kopf, $trenner) !== false;
    $ok = $ok && fputcsv($fp, $zeile, $trenner) !== false;
    $ok = $ok && fflush($fp);
    fclose($fp);
    return $ok;
}

// Exklusive Sperre über eine Sperrdatei; Rückgabe: Handle oder false. Freigeben mit ein_sperre_freigeben().
function ein_sperre_holen($datei)
{
    $fp = @fopen($datei, 'c');
    if (!$fp) return false;
    if (!flock($fp, LOCK_EX)) { fclose($fp); return false; }
    return $fp;
}

function ein_sperre_freigeben($fp)
{
    flock($fp, LOCK_UN);
    fclose($fp);
}
