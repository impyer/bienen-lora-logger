# Regressionstest main 5c1b847 — Firmware 261010 / eigener UTC-Server

- **Datum:** 2026-10-08
- **Geprüfter Commit:** [5c1b847aea789c5aa462e338746773c265020522](https://github.com/impyer/bienen-lora-logger/commit/5c1b847aea789c5aa462e338746773c265020522)
- **Vergleichsbasis:** [de82bcf85998da072619b18be9633452a84f306b](https://github.com/impyer/bienen-lora-logger/commit/de82bcf85998da072619b18be9633452a84f306b)
- **Änderungszweck:** Firmware-Fixes aus dem vorherigen Review, neue UTC-Serverfassung mit Grafikänderungen, Erweiterung der CI-Buildmatrix und der Integrationsprüfungen.
- **Prüfmethode:** GitHub-Diff, statischer Code-/Kontrollfluss-Review, Einsicht in **fertig ausgeführte** GitHub-Actions-Joblogs des geprüften Commits, unabhängiger kleiner PHP-Uhrzeit-Grenzfalltest.
- **Abgrenzung:** Kein eigener vollständiger Checkout/Arduino-Run außerhalb GitHub Actions; keine angeschlossene STM32-Hardware, kein produktives TTN/LoRaWAN, kein Playwright-Browserlauf in der CI, kein aktiviertes BEEP/ThingSpeak-Testkonto. CI-Ausführungen sind ausdrücklich **CI-Nachweis**, der PHP-Grenzfall ist **unabhängiger isolierter Hosttest**, nicht der originale End-to-End-Server.
- **Entscheid:** Host-/SiL-Regression für die getesteten Varianten gut; **kontrollierter HiL-Labortest freigegeben**, Produktiv-Deployment des Servers nur nach abgesicherter Migration; kein unbeaufsichtigter Feldbetrieb ohne erforderliche Hardware- und Integrationsnachweise.

## 1. Nachweisregister — genau dieser Commit

**[GitHub Actions Run 37801281502](https://github.com/impyer/bienen-lora-logger/actions/runs/37801281502): alle 5 Jobs abgeschlossen, erfolgreich.**

| Bereich | Ergebnis im Joblog | Evidenz |
|---|---|---|
| Zeitrechenlogik | 70/70 Hosttests bestanden | [PC-Tests und Simulation](https://github.com/impyer/bienen-lora-logger/actions/runs/37801281502/job/113393859535) |
| C-Funkformat-v2-Kodierer gegen JavaScript-Referenz | 303/303 Vergleichsfälle bestanden | derselbe PC-Job |
| FFT mit künstlichen ADC-Signalen | 32/32 Prüfungen bestanden | derselbe PC-Job |
| FFT-Frequenzlauf | Max. 0,064 Hz Frequenzabweichung und 0,330 dB Pegelabweichung im angegebenen Sinustest | derselbe PC-Job |
| Rauschunterdrückung | 20 Rauschdurchläufe ohne gültige Spitze, höchster gemeldeter SNR 4,9 dB bei Schwelle 10 dB | derselbe PC-Job |
| LoRaWAN-Slot-Modellsimulation | 30-Tage-Modellsimulation im geprüften CI-Szenario erfolgreich | derselbe PC-Job; **Modell, keine Funkevidenz** |
| TTN-Formatter | jeweils 14/14 Tests für Quell- und Minified-Fassung; goja-Prüfung erfolgreich | [Formatter-Job](https://github.com/impyer/bienen-lora-logger/actions/runs/37801281502/job/113393859183) |
| PHP-Hilfsfunktionen | 46/46 bestanden | [Server-Job](https://github.com/impyer/bienen-lora-logger/actions/runs/37801281502/job/113393858826) |
| eigener Server (UTC), Webhook → beelogger M.40 | 26/26 Ende-zu-Ende-Prüfungen bestanden | derselbe Server-Job |
| Originalserver M.40 als Regression | 22/22 bestanden; **bekannter** DST-Fehler absichtlich 5/7 | derselbe Server-Job |
| DST 25.10.2026, neue Fassung | **7/7** Datenpunkte, fortlaufende CSV-Unixzeitstempel im 1800-s-Abstand, getrennte ISO-Zeiten der beiden 02-Uhr-Stunden | §tests/server/test_lora_eingang.sh§ im Server-Job |
| Patch-Reproduzierbarkeit | §eigen_anpassen.py§ regeneriert Server aus Original-ZIP, rekursiver Vergleich im Job erfolgreich | Server-Job |
| PHP-Syntax | CI-Prüfung der LoRa- und eigenen Server-PHP-Dateien erfolgreich | Server-Job |
| BlackPill-Build ohne Audio, V2 | 76.156 Byte Flash, 3.300 Byte globale RAM-Daten | [Firmware-Job](https://github.com/impyer/bienen-lora-logger/actions/runs/37801281502/job/113393859271) |
| BlackPill-Build Audio EIN, 2 × DS18B20, V2 | 86.252 Byte Flash, 41.036 Byte globale RAM-Daten | Firmware-Job |
| BlackPill Legacy FPort 1 mit Audio-Schalter EIN | 75.576 Byte Flash, 3.356 Byte globale RAM-Daten; FFT-Workbuffer entfällt | Firmware-Job |
| Ungültige 3-Waagen-V2-Konfiguration | Kompilierung schlägt **erwartungsgemäß** mit §#error§ fehl, durch CI geprüft | Firmware-Job |
| Hardware-Selbsttest-Sketch | erfolgreich kompiliert | Firmware-Job |
| Playwright-Grafiktest | **nicht ausgeführt** — Job meldet „Playwright fehlt: Browserprüfung übersprungen“ | Server-Job; HTML-ISO-Strings wurden dennoch geprüft |

Warnungen im Firmware-Build stammen nach den gesichteten relevanten Zeilen hauptsächlich aus STM32-HAL/OneWire/HX711-Bibliotheken. Kein fehlgeschlagener Job.

## 2. Vorherige Befunde: aktualisierter Status

| ID | Ergebnis beim Commit 5c1b847 | Einschränkung |
|---|---|---|
| §FW26-01§ — Waage 3/4 in V2 nicht kodierbar | **Behoben als Sicherheitsbarriere:** Compile-Time-§#error§ bei >2 Waagen; negatives Buildkriterium CI-getestet | Protokoll unterstützt weiterhin nur zwei Waagen. |
| §FW26-02§ — Phantomgewicht 0,01 kg, Waage unkalibriert | **Im Code behoben:** §Taragewicht == 10§ führt zum Weglassen des Gewichts ohne falsches Fehlerbit | Integration mit echten HX711 und Sensorfehlern noch nicht HiL-geprüft. |
| §FW26-03§ — ADC-EOC-Endlosschleife | **Im Code behoben:** 50-µs-Zyklenzähler-Timeout, Fehlerflag, Abbruch und leeres FFT-Ergebnis | MCU-spezifischer ADC-Fehlerpfad nicht injiziert; kein Watchdog-/Strommessbeleg. |
| §FW26-04§ — Hosttests und Audio-Build fehlen in CI | **Behoben, CI belegt:** FFT/Codec, Varianten V2+Audio, V1, Negativ-Build | Tests ohne echte Elektronik. |
| §FW26-05§ — Rauschspitze/59 Hz | **Im SiL weitgehend behoben:** 10-dB-Spitzenabstand zum spektralen Median; Testfälle 50–61 Hz | Mikrofon-Frequenzgang, Störgeräusche und ADC-Aliasing offen. |
| §FW26-06§ — FFT läuft unnötig bei FPort 1 | **Behoben:** §V2_FFT_AKTIV§ und Legacy-Flash/RAM-Buildvergleich | HiL-Strommessung ausstehend. |
| §FW26-07§ — DWT/ADC statt Timer+DMA | **Bewusster Prototypen-Unterschied bleibt** | Neue SX1262-Platine getrennt entwickeln. |
| §SRV26-01§ — DST-Datenverlust | **Für §beelogger_eigen§ behoben**, 7/7 CI; **Original weiterhin 5/7** | Nur vollständige eigene Serverinstallation nutzen. |
| §SRV26-02§–§SRV26-05§ — Zustellstatus, Konkurrenz, CSV-Zusatz und BEEP-Duplikate | **Offen, praktisch unverändert** | Siehe Abschnitt 3. |
| §HW26-01§ und weitere Hardware-Punkte | **Offen** | Keine neue Schaltplan-/PCB- oder Batterie-Freigabe. |

## 3. Offene und neue Befunde

### SRV26-07 — P1 — Automatischer UTC-Modus kann bei Teilupdate falsche Zeit senden (NEU)

**Quelle:** §server/lora/lora_eingang.php§ Zeilen 91–100: UTC wird bei §utc_zeit='auto'§ allein durch Vorhandensein von §beelogger_zeitzone.php§ **im Hauptverzeichnis** bestimmt. Es gibt keinen Nachweis, dass das konkret angesprochene §<Logger>/beelogger_log.php§ §UTC=1§ bereits unterstützt.

**Szenario:** Die neue §beelogger_zeitzone.php§ wurde kopiert, aber mindestens ein Logger-Unterverzeichnis hat noch das alte §beelogger_log.php§. Der Eingang sendet in diesem Fall zum Beispiel §M1=2026/10/08_12:00:00§ mit §UTC=1§. Die alte PHP-Fassung ignoriert das Flag und interpretiert die Zeit als Europe/Berlin.

**Unabhängiger PHP-Hosttest:** Für den 08.10.2026 12:00:00Z liefert dieser Weg bei altem Log-Skript 10:00:00Z, also **−7.200 s**. Reproduktion:

§§§sh
php -r '$u=strtotime("2026-10-08T12:00:00Z");date_default_timezone_set("Europe/Berlin");$txt=gmdate("Y/m/d H:i:00",$u);$alt=strtotime(str_replace("/","-",$txt));printf("utc=%s alt=%s delta=%d\n",gmdate("c",$u),gmdate("c",$alt),$alt-$u);'
# erwartet: delta=-7200
§§§

Der vollständig aktualisierte CI-Test hat diesen Fehler nicht; er reproduziert ausschließlich die **Gefahr beim Rollout**.

**Akzeptanz:** UTC-Fähigkeit *pro Ziel-Logger-Endpunkt* über eine verlässliche Marker-/Versionsprüfung oder einen expliziten atomaren Rollout verifizieren. Testmatrix: §(Marker vorhanden/fehlt) × (neuer/alter beelogger_log.php)§, für jedes Logger-Unterverzeichnis. Bei Inkonsistenz lieber hart abbrechen statt still auf eine falsche Zeitbasis schreiben. Deployment-Dokumentation mit Backup und Rollback aktualisieren.

### SRV26-05 — P1 — BEEP/ThingSpeak kann bei nicht gespeichertem Datensatz erneut angestoßen werden (BESTEHEND)

**Fundstellen:** §server/beelogger_eigen/beelogger1/beelogger_log.php§ Zeilen 375–395 (§Auswertung(1)§, danach §ExternDataOut()§), ca. 742–762 (externe Daten vor §$store§ aufbereitet), 770–829 (§$store§ entscheidet nur über CSV), 1265 ff. (§ExternDataOut()§).

**Kontrollflussbeobachtung:** Für den letzten EE-Datensatz wird §ExternDataOut()§ aufgerufen, auch wenn §Auswertung()§ wegen Duplikat/zu altem Timestamp keine CSV-Zeile angelegt hat. Bei **aktivierter** BEEP-/ThingSpeak-Konfiguration besteht somit ein plausibler Weg zu doppelter externer Ausgabe. Eine tatsächliche externe HTTP-Übertragung wurde **nicht** getestet und wird nicht als Messung behauptet.

**Akzeptanz:** Lokalen HTTP-Mock für externe Dienste verwenden, identischen Uplink 2× schicken. Genau eine externe Aktion bei genau einem gespeicherten Datensatz; für abgelehnte Zeitstempel 0. Danach Tests für 502, Timeout, Wiederholung ergänzen. Die aktuell grüne Duplikatprüfung betrachtet nur §week.csv§.

### SRV26-02/03/04 — P1 — Fehlerquittung, Parallelität und Zusatzdaten-Atomizität weiter offen

- LoRa-Eingang antwortet **HTTP 200** auch bei §nicht gespeichert§ und fehlendem §decoded_payload§. Semantik von „gewollt ignoriert“ und „temporärer Schreib-/Verarbeitungsfehler“ trennen.
- Speicherung wird aus §filesize(week.csv)§ und dem Timestamp der **letzten** Zeile abgeleitet. Mit gleichzeitigen Webhooks entstehen Race Conditions. Nicht durch die sequenziellen CI-Tests widerlegt.
- §lora_zusatz.csv§ wird getrennt geschrieben, Fehler bleiben unbehandelt. Haupt-CSV und Zusatzdatei können auseinanderlaufen.
- **Akzeptanz:** Zwei zeitgleiche Uplinks, doppelte Events, beabsichtigt ungültige Werte, Lese-/Schreibrechte entfernen, Platte voll simulieren, HTTP-Timeout und Wiederholung; prüfen: kein Datenverlust, keine doppelten BEEP-Aktionen, klarer Retry-Status.

### SRV26-08 — P2 — Grafische Darstellung ist nicht als Browser-Regression in CI abgesichert (NEU)

**Stand:** §tests/server/test_lora_eingang.sh§ prüft die beiden unterschiedlichen ISO-8601-Offsets im HTML; der Playwright-Teil unter §if node -e "require('playwright')"§ wird im gesichteten Run **übersprungen**. Damit ist zwar der serverseitige Datenaufbau nachgewiesen, nicht jedoch die Darstellung in Chromium bei der doppelten Stunde.

**Akzeptanz:** Playwright als expliziten CI-Dependency installieren und §tests/server/grafik_pruefen.js§ verpflichtend ausführen. Browser-Assertions: streng steigende Zeitachse, beide 02:30-Punkte, keine JS-Fehler, korrekte Zuordnung nach Sommer-/Winterzeit.

### FMT26-01 / FW26-08 — P2 — Offen für spätere Datenintegrität / HiL

- FFT-Bandanzahl und Status/Zeitpunkt-Konsistenz hart validieren, sofern Protokollversion v2 das verlangt.
- Der FFT-SNR-Wert ist Abstand zur Medianleistung einzelner Spektrallinien, **kein kalibrierter akustischer Signal-Rausch-Abstand** und kein dB-SPL-Wert.
- 50-µs-ADC-Timeout und Rechenzeit haben nur Code-/Build-Abdeckung; HAL/ADC-Funktionsausfall, Taktjitter, Standby und 12-V-/Solar-/Ladebedingungen nicht gemessen.
- SMD-Zielplatine (Ra-01SH/SX1262) und die aktuell kompilierte STM32/RFM95-Prototyp-Firmware sind **verschiedene Systemstände**.

## 4. Reproduzierbare Prüfkommandos (Repository-Root)

§§§sh
# Hardwarefreie Tests auf Linux/WSL/macOS:
bash tests/alle_tests_linux.sh

# Gezielte Prüfungen:
node tests/firmware/vektoren_v2.js > tests/firmware/ff2_vektoren.h
g++ -std=c++11 -Wall -Wextra -Werror -O2 -o /tmp/ff2 tests/firmware/test_funkformat_v2.cpp && /tmp/ff2
g++ -std=c++11 -Wall -Wextra -Werror -O2 -o /tmp/fft tests/firmware/test_bee_fft.cpp && /tmp/fft
node tests/formatter/test_formatter.js
php tests/server/test_lora_funktionen.php
VARIANTE=eigen bash tests/server/test_lora_eingang.sh
VARIANTE=original bash tests/server/test_lora_eingang.sh
§§§

**Wichtig:** Das Skript §tests/alle_tests_linux.sh§ und die testgenerierten Header sind nicht mit dem oben verlinkten, erfolgreich protokollierten GitHub-CI-Lauf zu verwechseln. Die beiden Varianten des Server-End-to-End-Tests benötigen die im Skript genannten PHP-/Node-/curl-/unzip-Abhängigkeiten; Browsertests sind separat zu installieren.

## 5. Priorisierte Übergabe an Claude

1. **SRV26-07 zuerst**: sichere, pro Logger geprüfte UTC-Deployment-Erkennung + Testmatrix für Mischinstallationen; **keine falsche Zeitbasis trotz grünem Normal-E2E**.
2. **SRV26-05**: externe Ausgaben an tatsächlich akzeptierte Datensätze koppeln; Mock-HTTP-Test für Duplikate und Retry.
3. **SRV26-02/03/04**: Speichererfolg/Retries/parallel eintreffende Webhooks absichern; eventuelle Idempotenzschlüssel (gerät + FCnt + Sitzung/FPort) nicht mit nur einem Zeitstempel verwechseln.
4. **SRV26-08**: Browser-Test tatsächlich in CI ausführen.
5. Firmware: Versionsstand 261010 mit Audio am echten BlackPill testen; ADC-Timeout, FFT-Rauschen, Quarz-/RTC-Weckzeiten, sensorlose Kanäle, HX711-Fehler, LoRaWAN RX1/RX2 und Stromprofil messen.
6. Hardware: Schutzschaltungen und analoges Anti-Aliasing vor Fertigung separat freigeben; SMD-SX1262 nicht mit dem RFM95-Prototyp gleichsetzen.

**Freigabestatus:** **Host-/SiL-Codelevel akzeptabel, Labor-HiL sinnvoll.** Eigener UTC-Server nur als **vollständige** Migration mit Verifikation einsetzen, nicht blind per Marker-Erkennung. Produktive Feldfreigabe steht aus.
