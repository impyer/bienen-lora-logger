<?php
// Vorlage: kopieren nach lora_config.php und anpassen. lora_config.php wird nicht ins Repo hochgeladen.
return array(
    // Geheimes Wort, gleich wie im TTN-Webhook unter "Additional headers" (mindestens 16 Zeichen, zufällig)
    'token' => 'HIER-EIN-LANGES-ZUFALLSWORT-EINTRAGEN',
    'header' => 'X-Bienen-Token',

    // Adresse des Ordners, in dem beelogger1, beelogger2 … liegen (mit https)
    'basis_url' => 'https://example.org/beelogger',

    // TTN-Gerätename => beelogger-Verzeichnis. Der Verzeichnisname bestimmt den Typ wie beim beelogger:
    // beelogger1 = Einzel, Duo1 = zwei Waagen usw.
    'geraete' => array(
        'beelogger-01' => array('verzeichnis' => 'beelogger1'),
        'beelogger-02' => array('verzeichnis' => 'beelogger2'),
        'beelogger-03' => array('verzeichnis' => 'beelogger3'),
        'beelogger-04' => array('verzeichnis' => 'beelogger4'),
        'beelogger-05' => array('verzeichnis' => 'beelogger5'),
        'beelogger-06' => array('verzeichnis' => 'beelogger6'),
        'beelogger-07' => array('verzeichnis' => 'beelogger7'),
        'beelogger-08' => array('verzeichnis' => 'beelogger8'),
        'beelogger-09' => array('verzeichnis' => 'beelogger9'),
        'beelogger-10' => array('verzeichnis' => 'beelogger10'),
    ),

    // BEEP Bases: gleiche Eingangs-URL wie der klassische beelogger, aber interner Base-Decoder.
    // Echte DevEUIs/Kalibrierwerte nur in die lokale, nicht versionierte lora_config.php schreiben!
    // Beispiel (NICHT aktiv): 'my-beep-base-2' => array('dev_eui'=>'...', 'volk'=>'Volk 8',
    //    'name'=>'BEEPBASE-5A76', 'stand'=>'Hauptstand', 'gewicht_offset'=>..., 'gewicht_faktor'=>...)
    'beep_geraete' => array(),

    // Passwort-Hash für die interne Vorschau /lora/beep_dashboard.php.
    // Erzeugen: php -r 'echo password_hash("EIN-STARKES-PASSWORT", PASSWORD_DEFAULT), PHP_EOL;'
    // In der lokalen lora_config.php ersetzen; keinesfalls Klartext-Passwort eintragen.
    'dashboard_passwort_hash' => '',

    // Welche Formatter-Werte in die beelogger-Spalten Aux1, Aux2, Aux3 kommen ('' = leer lassen).
    // Vorgabe wie beim WLAN-beelogger: Aux1 Luftdruck, Aux2 FFT-Frequenz, Aux3 FFT-Pegel.
    // Beispiel für die Deckeltemperatur bei Einzel-Loggern: 3 => 'TempIn2'
    'aux' => array(1 => 'Aux1', 2 => 'FFT_Hz', 3 => 'FFT_dB'),

    // Nur für Duo usw.: Formatter-Wert, der als Wägezellentemperatur gilt
    'waegezellen_temp' => 'TempOut',

    // Gerätezeit nur übernehmen, wenn sie höchstens so viele Sekunden vor dem Empfang liegt
    'max_zeitabweichung_s' => 900,

    // Protokoll aller Webhooks (JSON-Zeilen je Monat). Möglichst außerhalb des Webverzeichnisses.
    'log_verzeichnis' => __DIR__ . '/lora_log',

    // Ordner mit beelogger1, beelogger2 … auf dem Server (Dateisystem). Vorgabe: eine Ebene über diesem Ordner.
    'beelogger_verzeichnis' => dirname(__DIR__),

    // Zeitbasis je Logger: 'auto' = UTC, wenn das beelogger_log.php des Loggers die eigene Fassung ist
    // (Merkmal $BL_UTC_FAEHIG), sonst Ortszeit; true = eigene Fassung verlangen (sonst zurückstellen); false = immer Ortszeit
    'utc_zeit' => 'auto',

    'tls_pruefen' => true,
    'zeitlimit_s' => 20,
);
