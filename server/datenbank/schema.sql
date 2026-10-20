-- SPDX-License-Identifier: GPL-3.0-or-later
-- Bienen-Plattform – Datenbankschema 0.4 (PostgreSQL 16)
-- 0.4 (20.10.2026): Tabelle import_position für den Importer (PLT26-02, R-5)
-- 0.3 (15.10.2026): Review Issue #11 – Zeitgenauigkeit, Kalibrierreferenz, Berechnungsversionen, Zuordnungsprüfung
-- Grundlage: docs/architektur/konzept-plattform-v02.md (Fassung 0.2.5), Abschnitt 5
-- Status: ENTWURF, D0/T1 (Tests gegen PostgreSQL 16 in tests/datenbank/). Keine Produktivfreigabe.
--
-- Regeln:
--   * Alle Zeitpunkte timestamptz (UTC gespeichert). Zeiträume als tstzrange '[von,bis)', bis offen = NULL.
--   * Historie wird nie überschrieben: neue Zeile mit neuem Zeitraum.
--   * Zeitangaben beim Schreiben immer mit Zeitzone (z. B. '2026-10-15 07:00+00'); ohne Angabe gilt
--     die Zeitzone der Sitzung.
--   * Überlappungen verhindert PostgreSQL selbst (EXCLUDE ... WITH &&), keine Trigger nötig.

CREATE EXTENSION IF NOT EXISTS btree_gist;

DROP SCHEMA IF EXISTS bienen CASCADE;
CREATE SCHEMA bienen;
SET search_path = bienen, public;

-- Hilfsdomain: Zeitraum mit bekanntem Beginn, halb offen
CREATE DOMAIN zeitraum AS tstzrange
  CHECK (NOT isempty(VALUE) AND lower(VALUE) IS NOT NULL
         AND lower_inc(VALUE) AND NOT upper_inc(VALUE));

-- =====================================================================
-- Modul A – Stammdaten
-- =====================================================================

CREATE TABLE stand (
  id              serial PRIMARY KEY,
  name            text NOT NULL UNIQUE,
  lage            point,                        -- genaue Lage, nie öffentlich
  ort_oeffentlich text                          -- z. B. 'Radeberg'
);

CREATE TABLE volk (
  id            serial PRIMARY KEY,
  name          text NOT NULL,                  -- z. B. 'Volk 8'
  entstanden_am timestamptz,
  aufgeloest_am timestamptz,
  notiz         text,
  CHECK (aufgeloest_am IS NULL OR entstanden_am IS NULL OR aufgeloest_am > entstanden_am)
);

CREATE TABLE beute (
  id          serial PRIMARY KEY,
  bezeichnung text NOT NULL,
  beutentyp   text,                             -- z. B. 'Segeberger 1,5', 'Einraumbeute DNM'
  rahmenmass  text,
  notiz       text
);

CREATE TABLE beute_konfiguration (
  id          serial PRIMARY KEY,
  beute_id    int NOT NULL REFERENCES beute,
  gueltig     zeitraum NOT NULL,
  brutzargen  smallint CHECK (brutzargen >= 0),
  honigzargen smallint CHECK (honigzargen >= 0),
  rahmen      smallint CHECK (rahmen >= 0),
  notiz       text,
  EXCLUDE USING gist (beute_id WITH =, gueltig WITH &&)
);

-- Beute = Volk: zu jedem Zeitpunkt 1:1 (bestätigt 15.10.2026)
CREATE TABLE belegung (
  id       serial PRIMARY KEY,
  volk_id  int NOT NULL REFERENCES volk,
  beute_id int NOT NULL REFERENCES beute,
  gueltig  zeitraum NOT NULL,
  EXCLUDE USING gist (beute_id WITH =, gueltig WITH &&),
  EXCLUDE USING gist (volk_id  WITH =, gueltig WITH &&)
);

CREATE TABLE aufstellung (
  id       serial PRIMARY KEY,
  beute_id int NOT NULL REFERENCES beute,
  stand_id int NOT NULL REFERENCES stand,
  gueltig  zeitraum NOT NULL,
  platz    smallint,                            -- Reihenfolge am Stand
  EXCLUDE USING gist (beute_id WITH =, gueltig WITH &&)
);

CREATE TABLE volk_ereignis (
  id    serial PRIMARY KEY,
  art   text NOT NULL CHECK (art IN ('ableger','vereinigung','schwarm','aufloesung')),
  zeit  timestamptz NOT NULL,
  notiz text
);

CREATE TABLE volk_ereignis_teil (
  ereignis_id int  NOT NULL REFERENCES volk_ereignis ON DELETE CASCADE,
  volk_id     int  NOT NULL REFERENCES volk,
  rolle       text NOT NULL CHECK (rolle IN ('quelle','ergebnis','bleibt')),
  PRIMARY KEY (ereignis_id, volk_id)
);

CREATE TABLE koenigin (
  id             serial PRIMARY KEY,
  jahrgang       smallint,
  farbe          text,
  rasse          text,
  begattet       boolean,
  gezeichnet     boolean,
  geschnitten    boolean,
  herkunft       text,
  mutter_volk_id int REFERENCES volk
);

CREATE TABLE koenigin_volk (
  koenigin_id int NOT NULL REFERENCES koenigin,
  volk_id     int NOT NULL REFERENCES volk,
  gueltig     zeitraum NOT NULL,
  grund       text,
  EXCLUDE USING gist (volk_id     WITH =, gueltig WITH &&),
  EXCLUDE USING gist (koenigin_id WITH =, gueltig WITH &&)
);

-- Externe Kennungen (BEEP-Hive-ID → Volk, TTN-Gerätename → Gerät …)
CREATE TABLE extern_ref (
  system     text NOT NULL,                     -- 'beep', 'ttn'
  typ        text NOT NULL,                     -- 'hive', 'inspection', 'device' …
  extern_id  text NOT NULL,
  intern_typ text NOT NULL,                     -- 'volk', 'durchsicht', 'geraet' …
  intern_id  int  NOT NULL,
  PRIMARY KEY (system, typ, extern_id)
);

-- =====================================================================
-- Modul B – Stockkarte
-- =====================================================================

CREATE TABLE merkmal (
  id        serial PRIMARY KEY,
  code      text NOT NULL UNIQUE,               -- stabil, z. B. 'brutwaben'
  name      text NOT NULL,
  eltern_id int REFERENCES merkmal,
  eingabetyp text NOT NULL CHECK (eingabetyp IN
             ('janein','zahl','ganzzahl','liste','text','datum','bewertung','gruppe')),
  einheit   text,
  optionen  jsonb                               -- Listenwerte
);

CREATE TABLE checkliste (
  id   serial PRIMARY KEY,
  name text NOT NULL UNIQUE
);

CREATE TABLE checkliste_version (
  id            serial PRIMARY KEY,
  checkliste_id int NOT NULL REFERENCES checkliste,
  version       int NOT NULL CHECK (version >= 1),
  gueltig_ab    timestamptz NOT NULL,
  UNIQUE (checkliste_id, version)
);

CREATE TABLE checkliste_merkmal (
  version_id  int NOT NULL REFERENCES checkliste_version,
  merkmal_id  int NOT NULL REFERENCES merkmal,
  reihenfolge int NOT NULL,
  pflicht     boolean NOT NULL DEFAULT false,
  PRIMARY KEY (version_id, merkmal_id)
);

CREATE TABLE durchsicht (
  id                    serial PRIMARY KEY,
  volk_id               int NOT NULL REFERENCES volk,
  zeit                  timestamptz NOT NULL,
  erfasst_am            timestamptz NOT NULL DEFAULT now(),
  zeitgenauigkeit       text NOT NULL DEFAULT 'exakt' CHECK (zeitgenauigkeit IN ('exakt','geschaetzt','nur_datum')),
  checkliste_version_id int REFERENCES checkliste_version,
  notiz                 text,
  quelle                text NOT NULL DEFAULT 'eigen' CHECK (quelle IN ('eigen','beep_import'))
);
CREATE INDEX ON durchsicht (volk_id, zeit);

CREATE TABLE durchsicht_wert (
  durchsicht_id int NOT NULL REFERENCES durchsicht ON DELETE CASCADE,
  merkmal_id    int NOT NULL REFERENCES merkmal,
  wert_zahl     numeric,
  wert_text     text,
  wert_bool     boolean,
  PRIMARY KEY (durchsicht_id, merkmal_id),
  CHECK (num_nonnulls(wert_zahl, wert_text, wert_bool) = 1)
);

-- Maßnahmen mit Zeitraum (z. B. Behandlung 01.–11.10.). Ein Zeitpunkt wird als kurzer Zeitraum erfasst, z. B. [t, t+1 min)
CREATE TABLE massnahme (
  id            serial PRIMARY KEY,
  volk_id       int NOT NULL REFERENCES volk,
  art           text NOT NULL CHECK (art IN ('behandlung','fuetterung','ernte','zarge_auf','zarge_ab',
                                             'umsetzen','tarieren','sonstiges')),
  zeitraum      zeitraum NOT NULL,
  zeitgenauigkeit text NOT NULL DEFAULT 'exakt' CHECK (zeitgenauigkeit IN ('exakt','geschaetzt','nur_datum')),
  menge         numeric,
  einheit       text,
  mittel        text,                           -- z. B. 'Ameisensäure 60 %'
  notiz         text,
  durchsicht_id int REFERENCES durchsicht,
  quelle        text NOT NULL DEFAULT 'eigen' CHECK (quelle IN ('eigen','beep_import'))
);
CREATE INDEX ON massnahme USING gist (volk_id, zeitraum);

CREATE TABLE varroa_messung (
  id        serial PRIMARY KEY,
  volk_id   int NOT NULL REFERENCES volk,
  zeitraum  zeitraum NOT NULL,                  -- Windel: Einlegen bis Auszählen
  zeitgenauigkeit text NOT NULL DEFAULT 'exakt' CHECK (zeitgenauigkeit IN ('exakt','geschaetzt','nur_datum')),
  methode   text NOT NULL CHECK (methode IN ('windel','puderzucker','auswaschung')),
  milben    int  NOT NULL CHECK (milben >= 0),
  anmerkung text,
  quelle    text NOT NULL DEFAULT 'eigen' CHECK (quelle IN ('eigen','beep_import'))
);

CREATE TABLE aufgabe (
  id          serial PRIMARY KEY,
  volk_id     int REFERENCES volk,
  stand_id    int REFERENCES stand,
  faellig_am  date NOT NULL,
  text        text NOT NULL,
  erledigt_am timestamptz,
  durchsicht_id int REFERENCES durchsicht,
  CHECK (num_nonnulls(volk_id, stand_id) = 1)
);

CREATE TABLE anhang (
  id             serial PRIMARY KEY,
  durchsicht_id  int REFERENCES durchsicht,
  massnahme_id   int REFERENCES massnahme,
  pfad           text NOT NULL,
  sha256         text NOT NULL,
  aufgenommen_am timestamptz,
  CHECK (num_nonnulls(durchsicht_id, massnahme_id) = 1)
);

-- =====================================================================
-- Modul C – Messdaten
-- =====================================================================

-- Katalog der Messgrößen = Register der Oberfläche
CREATE TABLE messgroesse (
  code        text PRIMARY KEY,                 -- z. B. 'gewicht', 'temperatur', 'regen_summe'
  name        text NOT NULL,
  einheit     text NOT NULL,
  semantik    text NOT NULL CHECK (semantik IN
              ('momentan','intervallsumme','spitze','zaehler','zirkulaer','status','unbekannte_summe')),
  verdichtung text NOT NULL CHECK (verdichtung IN
              ('mittel','median','summe','max','min','letzter','vektor','keine')),
  achse       text NOT NULL,                    -- gleiche Achse = gleiche Einheit
  darstellung text NOT NULL DEFAULT 'linie' CHECK (darstellung IN ('linie','balken','punkte','stufe','pfeile')),
  farbe       text,
  oeffentlich boolean NOT NULL DEFAULT false    -- darf in die öffentliche Übersicht
);

CREATE TABLE geraet (
  id        serial PRIMARY KEY,
  dev_eui   text UNIQUE,
  name      text NOT NULL UNIQUE,               -- TTN-Gerätename
  art       text NOT NULL CHECK (art IN ('stockwaage','beep_base','wetter','boden','sonstiges')),
  modell    text,
  firmware  text
);

-- Waage am Volk (bestätigt 15.10.2026); Umweltgeräte am Stand
CREATE TABLE geraet_zuordnung (
  id        serial PRIMARY KEY,
  geraet_id int NOT NULL REFERENCES geraet,
  volk_id   int REFERENCES volk,
  stand_id  int REFERENCES stand,
  gueltig   zeitraum NOT NULL,
  notiz     text,
  CHECK (num_nonnulls(volk_id, stand_id) = 1),
  EXCLUDE USING gist (geraet_id WITH =, gueltig WITH &&),
  -- höchstens ein Stockmesssystem je Volk zur selben Zeit
  EXCLUDE USING gist (volk_id WITH =, gueltig WITH &&) WHERE (volk_id IS NOT NULL)
);

CREATE TABLE messstelle (
  id          serial PRIMARY KEY,
  volk_id     int REFERENCES volk,
  stand_id    int REFERENCES stand,
  zone        text NOT NULL CHECK (zone IN ('brutnest','deckel','aussen','waage','flugloch',
                                            'boden','luft_stand','elektronik','funk')),
  hoehe_cm    numeric,
  tiefe_cm    numeric,
  bezeichnung text,
  CHECK (num_nonnulls(volk_id, stand_id) = 1),
  CHECK (zone <> 'boden' OR tiefe_cm IS NOT NULL OR bezeichnung IS NOT NULL)
);

-- Deutung eines Quellfelds eines Geräts für einen Zeitraum
CREATE TABLE kanal (
  id               serial PRIMARY KEY,
  geraet_id        int  NOT NULL REFERENCES geraet,
  quellfeld        text NOT NULL,               -- Feldname im Formatter-JSON, z. B. 'TempIn2'
  messgroesse_code text NOT NULL REFERENCES messgroesse,
  messstelle_id    int  REFERENCES messstelle,
  faktor           double precision NOT NULL DEFAULT 1,
  versatz          double precision NOT NULL DEFAULT 0,
  gueltig          zeitraum NOT NULL,
  status           text NOT NULL DEFAULT 'ungeprueft' CHECK (status IN ('geprueft','ungeprueft')),
  kalibriert_am    timestamptz,                -- letzte Kalibrierung, die für diesen Zeitraum gilt
  kalibrierung     text,                       -- Verfahren und Referenz, z. B. 'Prüfgewicht 10,00 kg, Firmware-Faktor 21,43'
  sensor           text,                       -- Bauteil/Seriennr., falls bekannt, z. B. 'DS18B20 28-0316…'
  EXCLUDE USING gist (geraet_id WITH =, quellfeld WITH =, gueltig WITH &&)
);

-- Verweis auf die unveränderten Protokollzeilen der PHP-Eingänge
CREATE TABLE rohnachricht (
  id              text PRIMARY KEY,             -- Kennung des Eingangs (Gerät, FPort, FCnt, Nutzdaten, received_at)
  geraet_id       int  NOT NULL REFERENCES geraet,
  empfangen       timestamptz NOT NULL,
  messzeit_quelle timestamptz,                  -- Gerätezeit, falls gesendet
  datei           text NOT NULL,
  zeile           int  NOT NULL,
  sha256          text NOT NULL
);

CREATE TABLE messwert (
  kanal_id     int NOT NULL REFERENCES kanal,
  zeit         timestamptz NOT NULL,
  wert         double precision NOT NULL,
  qualitaet    text NOT NULL DEFAULT 'ok' CHECK (qualitaet IN ('ok','verdaechtig','ungueltig')),
  zeitqualitaet text NOT NULL CHECK (zeitqualitaet IN ('geraet','empfang','unbekannt')),
  roh_id       text REFERENCES rohnachricht,
  PRIMARY KEY (kanal_id, zeit)
);

-- Felder ohne Kanal: gespeichert als Hinweis, nicht als Messwert
CREATE TABLE quellfeld_ohne_kanal (
  geraet_id int  NOT NULL REFERENCES geraet,
  quellfeld text NOT NULL,
  zuerst    timestamptz NOT NULL,
  zuletzt   timestamptz NOT NULL,
  anzahl    int NOT NULL DEFAULT 1,
  PRIMARY KEY (geraet_id, quellfeld)
);

-- Leseposition des Importers je Protokolldatei (Konzept §4a R-5). Bis 'bytes' ist alles eingelesen;
-- 'sha256' ist die Prüfsumme dieser ersten Bytes. Weicht sie ab, wurde die Datei umgeschrieben (R-4).
CREATE TABLE import_position (
  datei        text PRIMARY KEY,                -- z. B. 'lora_log/2026-10.jsonl'
  bytes        bigint NOT NULL CHECK (bytes >= 0),
  zeilen       int    NOT NULL CHECK (zeilen >= 0),
  sha256       text   NOT NULL,
  aktualisiert timestamptz NOT NULL DEFAULT now()
);

-- Versionen der Berechnungen (Provenienz abgeleiteter Werte)
CREATE TABLE berechnung (
  code         text NOT NULL,
  version      int  NOT NULL,
  beschreibung text NOT NULL,                   -- Formel, Fenster, Filter
  quelle       text,                            -- z. B. 'Grundgerüst 3.4 Nr. 1'
  gueltig_ab   date NOT NULL,
  PRIMARY KEY (code, version)
);
INSERT INTO berechnung VALUES
 ('gewicht_tagesreferenz', 1, 'Median aller Gewichtswerte mit qualitaet=ok von 00:00 bis 04:00 Ortszeit Europe/Berlin je Volk und Tag', 'beelogger-datenanalyse-grundgeruest 3.4 Nr. 1', '2026-10-15'),
 ('gewicht_tagesbilanz',   1, 'Tagesreferenz(t) − Tagesreferenz(t−1); mit_eingriff = Maßnahme zwischen 00:00 (t−1) und 04:00 (t)', 'beelogger-datenanalyse-grundgeruest 3.4 Nr. 2, Leitplanke L8', '2026-10-15'),
 ('varroa_pro_tag',        1, 'Milben der Windelzählung ÷ Liegedauer in Tagen', 'beep-stockkarte-setup, Mapping 911', '2026-10-15');

-- =====================================================================
-- Sichten
-- =====================================================================

-- Messwert mit Volk bzw. Stand zum Messzeitpunkt
CREATE VIEW messwert_bezug AS
SELECT m.kanal_id, m.zeit, m.wert * k.faktor + k.versatz AS wert, m.qualitaet, m.zeitqualitaet,
       k.messgroesse_code, k.messstelle_id, k.geraet_id, z.volk_id, z.stand_id
FROM messwert m
JOIN kanal k ON k.id = m.kanal_id
LEFT JOIN geraet_zuordnung z ON z.geraet_id = k.geraet_id AND z.gueltig @> m.zeit;

-- Stand eines Volks zu einem Zeitpunkt: Volk → Beute → Stand
CREATE FUNCTION stand_von_volk(p_volk int, p_zeit timestamptz) RETURNS int
LANGUAGE sql STABLE AS $$
  SELECT a.stand_id
  FROM belegung b JOIN aufstellung a ON a.beute_id = b.beute_id AND a.gueltig @> p_zeit
  WHERE b.volk_id = p_volk AND b.gueltig @> p_zeit
$$;

-- Tagesreferenz Gewicht: Median 00:00–04:00 Ortszeit (Grundgerüst 3.4)
CREATE VIEW gewicht_tagesreferenz AS
SELECT volk_id,
       (zeit AT TIME ZONE 'Europe/Berlin')::date AS tag,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY wert) AS referenz_kg,
       count(*) AS werte,
       'gewicht_tagesreferenz@1'::text AS berechnung
FROM messwert_bezug
WHERE messgroesse_code = 'gewicht' AND volk_id IS NOT NULL AND qualitaet = 'ok'
  AND extract(hour FROM zeit AT TIME ZONE 'Europe/Berlin') < 4
GROUP BY volk_id, tag;

-- Tagesbilanz = Referenz(t) − Referenz(t−1); Maßnahmen an diesem Tag werden markiert (Leitplanke L8)
CREATE VIEW gewicht_tagesbilanz AS
SELECT r.volk_id, r.tag, r.referenz_kg,
       r.referenz_kg - v.referenz_kg AS bilanz_kg,
       EXISTS (SELECT 1 FROM massnahme mn
               WHERE mn.volk_id = r.volk_id
                 AND mn.zeitraum && tstzrange((v.tag::timestamp) AT TIME ZONE 'Europe/Berlin',
                                              (r.tag::timestamp + time '04:00') AT TIME ZONE 'Europe/Berlin')) AS mit_eingriff,
       'gewicht_tagesbilanz@1'::text AS berechnung
FROM gewicht_tagesreferenz r
JOIN gewicht_tagesreferenz v ON v.volk_id = r.volk_id AND v.tag = r.tag - 1;

-- Milbenfall pro Tag (nur Windel)
CREATE VIEW varroa_pro_tag AS
SELECT id, volk_id, lower(zeitraum) AS von, upper(zeitraum) AS bis, milben,
       round(milben / (extract(epoch FROM upper(zeitraum) - lower(zeitraum)) / 86400.0)::numeric, 1) AS milben_pro_tag,
       anmerkung, quelle, zeitgenauigkeit,
       'varroa_pro_tag@1'::text AS berechnung
FROM varroa_messung
WHERE methode = 'windel' AND upper(zeitraum) IS NOT NULL;

-- Prüfung: Stockmesssystem einem Volk zugeordnet, das im Zeitraum aufgelöst ist oder keine Beute belegt
-- (fängt vergessene Zuordnungsenden ab, Akzeptanzfall HB-09)
CREATE VIEW pruefung_geraet_zuordnung AS
SELECT z.id AS zuordnung_id, g.name AS geraet, v.name AS volk, z.gueltig,
       CASE WHEN v.aufgeloest_am IS NOT NULL AND z.gueltig @> v.aufgeloest_am THEN 'volk_aufgeloest'
            WHEN v.aufgeloest_am IS NOT NULL AND lower(z.gueltig) >= v.aufgeloest_am THEN 'volk_aufgeloest'
            ELSE 'ohne_belegung' END AS befund
FROM geraet_zuordnung z
JOIN geraet g ON g.id = z.geraet_id
JOIN volk v ON v.id = z.volk_id
WHERE (v.aufgeloest_am IS NOT NULL AND (z.gueltig @> v.aufgeloest_am OR lower(z.gueltig) >= v.aufgeloest_am))
   OR NOT EXISTS (SELECT 1 FROM belegung b WHERE b.volk_id = z.volk_id AND b.gueltig && z.gueltig);
