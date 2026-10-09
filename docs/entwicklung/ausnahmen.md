# Ausnahmenregister

**Status:** Vorschlag zu Regelwerk 1.1. Eine Ausnahme ist nur zulässig, wenn sie Scope, Risiko, kompensierende Maßnahmen, Owner, Prüfung und Enddatum bzw. zwingenden Review-Anlass dokumentiert. Keine Freigabe sicherheitsgefährdender Abweichungen.

## EX-01 – Passwort im GET der bestehenden beelogger-Schnittstelle

| Feld | Definition |
|---|---|
| Status | **Dokumentierte Bestandsausnahme; operative Gegenmaßnahmen nicht vollständig nachgewiesen** |
| Regel | [S-05 Nr. 5](software.md): Keine Passwörter in URLs, soweit kontrollierbar |
| Ursprung | Original-`beelogger_log.php?PW=…` erfordert beim übernommenen Alt-API ein Passwort als Queryparameter |
| Umfang | Nur **interner TTN-/LoRa-Eingang → Legacy-beelogger-Endpunkt**, keine Übernahme in neue APIs |
| Gefahr | Access-/Errorlogs, Proxies, Redirects und Diagnosedumps könnten Passwort speichern |
| Pflichtmaßnahmen | TLS-Zertifikatsprüfung/HTTPS (oder gesicherte lokale Verbindung), Zugriffsbegrenzung, URL-/Query-Redaktion in Logs, lokale Secretdatei statt Git, keine unsicheren Weiterleitungen, synthetische Auth-Tests |
| Verantwortung | Maintainer `@impyer`; **kein automatisches Produktiv-Sign-off** |
| Erneute Prüfung | **Vor erstem unbeaufsichtigten Feld-/Produktiv-Deployment**, bei jeder Änderung des Übergangswegs und bei Sicherheitsrelease |
| Ablösung | Internen Übergabepfad ohne Passwort in URL entwickeln, sobald die Alt-API abgelöst werden kann |

**Wichtig:** Dieser Eintrag belegt nur den dokumentierten Bestandspfad. Er bestätigt **nicht**, dass alle operativen Gegenmaßnahmen bereits getestet wurden. Ohne Nachweise keine Freigabe.
