<?php
// Umwelt-Eingang (Wetterstation, Bodensonden und weitere Umweltsensoren am Stand)
// Vorlage: kopieren nach umwelt_config.php und anpassen. umwelt_config.php wird nicht ins Repo hochgeladen.
return array(
    // Geheimes Wort, gleich wie im TTN-Webhook unter "Additional headers" (mindestens 16 Zeichen, zufällig).
    // Ein eigenes Wort je Eingang ist sicherer als dasselbe wie im Bienen-Eingang.
    'token' => 'HIER-EIN-LANGES-ZUFALLSWORT-EINTRAGEN',
    'header' => 'X-Bienen-Token',

    // Rohprotokoll aller Webhooks (JSON-Zeilen je Monat in UTC). Möglichst außerhalb des Webverzeichnisses;
    // sonst legt der Eingang dort eine .htaccess mit "Require all denied" an (nur Apache).
    // Der Importer liest dieses Verzeichnis (--umwelt) und braucht Leserecht.
    'log_verzeichnis' => __DIR__ . '/umwelt_log',
);
