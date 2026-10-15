# BEEP-Ablösung bei laufendem Betrieb – risikominimierte Strategie

**15.10.2026 – Entwurf; keine BEEP-Cloud-Zugänge, API-Ergebnisse, Firmwarestände oder TTN-Umstellung verifiziert.**

## Ziel

BEEP-Oberfläche und Checklistendialoge als **Referenz**, nicht durch ungeprüftes Übernehmen des Altstacks als langfristigen Serverkern benutzen. Die neue Webplattform ersetzt schrittweise die alte beelogger-Webdarstellung und erhält eine eigene Stockkarte **erst nach nachgewiesener Migration**. Es gelten die bisher bestätigten Anforderungen unter `docs/architektur/`.

## Quellenautorität je Phase

1. **Lesender Parallelbetrieb:** BEEP bleibt führend für bestehende Beuten, Völker, Checklisten, Inspektionen und Eingriffe. Lokaler Server führt unabhängige Messwerte sowie Leseprojektionen aus BEEP.
2. **Validierter Import:** BEEP-IDs ↔ eigene IDs, Zeitstempel, Checklisten-Versionssemantik, Medien, Änderungen/Löschungen und unvollständige Fälle prüfen. Kein blindes Überschreiben von Rohhistorie.
3. **Funktionsgleichheit:** Durchsichten und Aufgaben in der neuen UI mit BEEP vergleichen; manuelle Abnahme.
4. **Cutover:** definiertes Schreib-Fenster und Migrationssnapshot, anschließend nur eigene Plattform führend; BEEP schreibgeschützt/Archiv. Rollback vor dem Cutover planen.
5. **Ablösung:** nach Backups, Restore-Test, validiertem Geräteempfang und vollständiger Datennachführung.

**Keine synchrone doppelte schreibende Stockkarte ohne Konfliktmodell.**

## BEEP-Base-Datenweg

BEEP Base → LoRaWAN-Gateway → The Things Stack/TTN → Webhook(s) → eigener Raw-Ingest und optional BEEP. Eine eigene TTN-Anwendung mit BEEP-Weiterleitung ist dokumentiert, aber **nicht** als bereits eingerichtet anzunehmen. Wer TTN-Anwendungsinhaber ist, Firmwareversionen, DevEUIs und Decoder sind offen. Bestehende Base-Konfiguration zuerst auslesen und Pilot **mit einem Gerät** planen. Messwerte aus bestehender BEEP-API können in der Übergangszeit ggf. importiert werden; Zugriff, Vollständigkeit und zulässige Raten sind zu verifizieren.

**Nicht gleichsetzen:** BEEP Base (Stockmessgerät) mit digitaler BEEP Stockkarte (fachlicher Datensatz); beide gehören im bisherigen Quellgruppenmodell zur Gruppe BEEP. Zwei Bases existieren/vorgesehen; konkrete Zuordnung zu Volk/Beute muss historisiert werden. Zusätzlich beelogger und Umweltmessstellen – vgl. bestehende Architektur.

## BEEP-Code, Lizenz und Sicherheit

Die BEEP-Implementierungen aus GitHub haben eigene Abhängigkeiten und Lizenzbedingungen. Vor Copy-Paste oder Fork: Lizenzdateien und Abhängigkeiten **pro Quellbereich** prüfen, Herkunft dokumentieren, Rechtekette klären. UI-Design als konzeptionelle Referenz ist kein Recht, beliebige fremde Assets oder Quelltexte ohne Lizenzprüfung zu übernehmen. API-Tokens ausschließlich serverseitig, kein Secret im Browser, Git oder Testlog. Öffentliche Datenfreigabe **nur serverseitig**.

## Abnahmekriterien Migration

- Stichproben + Vollständigkeitsabgleich aller Beuten/Völker/Inspektionen; fehlende/gelöschte Datensätze gekennzeichnet.
- Alle Checklistenvorlagen, Antworttypen, Vorlagenversionen und zeitlichen Angaben reproduzierbar.
- Mindestens eine BEEP Base liefert im Pilottest zeitlich konsistente Daten an beide Ziele; kein impliziter Anspruch für zweite Base.
- Wiederholte Imports ohne Duplikate, Konflikt- und Ausfalltests, nachvollziehbare Cursor/Importlogs.
- Vergleichbare Funktionen im MVP für Stand-Dashboard und Volk-Cockpit, weiterführende Wetter-/Analysedaten nicht vom BEEP-Cutover abhängig.
- Backup und echter Restore unter Testbedingungen durchgeführt und dokumentiert; kein automatisch behaupteter Feldtest.

## Referenzen

- Bestehende lokale [BEEP-Anbindung](../beep-anbindung.md) und [Server-README](../../server/README.md).
- [BEEP API](https://api.beep.nl/docs/)
- [BEEP Web-App](https://github.com/beepnl/beep-vue-app)
- [BEEP Backend](https://github.com/beepnl/BEEP)
- [TTN HTTP Webhooks](https://www.thethingsindustries.com/docs/integrations/webhooks/)
- BEEP-Unterstützung: eigene TTN-Anwendung für BEEP Base (Details vor praktischer Änderung erneut verifizieren).
