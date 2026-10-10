<?php
// Vorlage: kopieren nach wetter_config.php und anpassen. wetter_config.php wird nicht ins Repo hochgeladen.
return array(
    // Geheimes Wort, gleich wie im TTN-Webhook unter "Additional headers" (mindestens 16 Zeichen, zufällig).
    // Darf dasselbe sein wie im LoRa-Eingang, ein eigenes ist sicherer.
    'token' => 'HIER-EIN-LANGES-ZUFALLSWORT-EINTRAGEN',
    'header' => 'X-Bienen-Token',

    // Bienenstände. Kennung (Kleinbuchstaben, Ziffern, - und _) => Name und zugehörige beelogger-Verzeichnisse.
    // Die Kennung wird Verzeichnisname unter daten_verzeichnis.
    'staende' => array(
        'hauptstand' => array(
            'name' => 'Hauptstand am Haus',
            'logger' => array('beelogger1', 'beelogger2', 'beelogger3', 'beelogger4', 'beelogger5',
                              'beelogger6', 'beelogger7', 'beelogger8', 'beelogger9', 'beelogger10'),
        ),
    ),

    // TTN-Gerätename der Wetterstation => Bienenstand. Wird die Station umgestellt, hier den Stand ändern;
    // neue Messwerte landen ab dann beim neuen Stand, alte bleiben, wo sie sind.
    'stationen' => array(
        'wetterstation-01' => array('stand' => 'hauptstand'),
    ),

    // Messwerte: <daten_verzeichnis>/<stand>/<station>_<JJJJ-MM>.csv (Monat in UTC) und staende.json.
    // Möglichst außerhalb des Webverzeichnisses; sonst schützt die angelegte .htaccess (Apache).
    'daten_verzeichnis' => __DIR__ . '/wetter_daten',

    // Protokoll aller Webhooks (JSON-Zeilen je Monat), Kennungen gegen Doppelte, Sperrdateien
    'log_verzeichnis' => __DIR__ . '/wetter_log',
);
