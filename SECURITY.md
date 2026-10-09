# Sicherheitsmeldungen

Vielen Dank für Hinweise zu Fehlern in Firmware, Server, LoRaWAN-Datenverarbeitung oder der Akku-/Ladeelektronik.

**Bitte keine ungepatchten Schwachstellen mit ausnutzbaren Details, Schlüssel, Zugangsdaten, reale Geräte-/Standortdaten oder personenbezogene Messungen öffentlich in ein Issue kopieren.**

Wenn im Repository die private Funktion **„Report a vulnerability“ / Private vulnerability reporting** aktiviert ist, nutze diese für vertrauliche Meldungen. Falls sie nicht aktiviert ist, kontaktiere die Projektverantwortlichen zunächst über einen geeigneten **nichtöffentlichen Kontaktweg**, ohne öffentliche Exploit- oder Schlüsselangaben zu hinterlassen. In diesem Repository ist aktuell keine besondere Reaktionsfrist oder 24/7-Bereitschaft zugesagt.

Beschreibe soweit möglich:
- betroffenen Commit/Tag, Hardware- und Firmware-Revision;
- erwartetes und tatsächliches Verhalten, Reichweite und Schadensszenario;
- reproduzierbare **sichere** Testschritte mit synthetischen Daten;
- ob bereits ein reales Gerät, ein Akku, ein Webserver oder ein echter Schlüssel betroffen ist.

Bei möglicher Akkusicherheitsgefährdung keine unkontrollierten Feldversuche durchführen und keinen sicherheitskritischen Test an absichtlich tiefentladenen oder überhitzten echten Li-Ion-Zellen starten. Fehlerfälle zunächst in einer sicheren, strombegrenzten Laborumgebung analysieren.

Siehe [Projektregelwerk](docs/entwicklung/regelwerk.md) und [Test-/Freigabegates](docs/entwicklung/tests-freigaben.md).
