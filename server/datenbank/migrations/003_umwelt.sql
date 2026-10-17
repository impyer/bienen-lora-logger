-- SPDX-License-Identifier: GPL-3.0-or-later
-- R1: additive environment import, revisions, and explicit apiary permissions.
-- Apply through umwelt.migrate in an isolated test DB after backup/restore.
-- No DROP/TRUNCATE, no production source changes, no automatic app startup SQL.

DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM bienen.messwert m JOIN bienen.kanal k ON k.id=m.kanal_id
    WHERE NOT k.gueltig @> m.zeit
  ) THEN
    RAISE EXCEPTION 'Kanalgueltigkeit im Altbestand verletzt; Migration abgebrochen';
  END IF;
END $$;

CREATE TABLE bienen.sk_benutzer_stand (
  benutzer_id bigint NOT NULL REFERENCES bienen.sk_benutzer,
  stand_id integer NOT NULL REFERENCES bienen.stand,
  darf_lesen boolean NOT NULL DEFAULT false,
  PRIMARY KEY (benutzer_id,stand_id)
);

CREATE TABLE bienen.um_quelle (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  schluessel text NOT NULL UNIQUE CHECK (schluessel ~ '^[a-z0-9_-]{1,80}$'),
  profil text NOT NULL CHECK (profil IN ('s2120','boden')),
  stand_id integer NOT NULL REFERENCES bienen.stand,
  geraet_id integer NOT NULL REFERENCES bienen.geraet,
  datei text NOT NULL,
  quell_stand text NOT NULL,
  quell_geraet text NOT NULL,
  synthetisch boolean NOT NULL,
  zeitqualitaet text NOT NULL CHECK (zeitqualitaet IN ('geraet','empfang','unbekannt')),
  intervall_s integer CHECK (intervall_s BETWEEN 1 AND 86400),
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (geraet_id,datei)
);

CREATE TABLE bienen.um_quelle_kanal (
  quelle_id bigint NOT NULL REFERENCES bienen.um_quelle,
  quellfeld text NOT NULL,
  kanal_id integer NOT NULL REFERENCES bienen.kanal,
  bezeichnung text NOT NULL,
  PRIMARY KEY (quelle_id,quellfeld),
  UNIQUE (quelle_id,kanal_id)
);

CREATE TABLE bienen.um_rohdatensatz (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  quelle_id bigint NOT NULL REFERENCES bienen.um_quelle,
  ereignis_schluessel char(64) NOT NULL,
  sha256 char(64) NOT NULL,
  datei_sha256 char(64) NOT NULL,
  zeile integer NOT NULL CHECK (zeile > 1),
  original text NOT NULL,
  felder jsonb NOT NULL,
  importiert_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (quelle_id,ereignis_schluessel,sha256)
);

CREATE TABLE bienen.um_ereignis_revision (
  quelle_id bigint NOT NULL REFERENCES bienen.um_quelle,
  ereignis_schluessel char(64) NOT NULL,
  revision integer NOT NULL CHECK (revision > 0),
  roh_id bigint NOT NULL REFERENCES bienen.um_rohdatensatz,
  zeit timestamptz NOT NULL,
  importiert_am timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (quelle_id,ereignis_schluessel,revision)
);
CREATE VIEW bienen.um_ereignis_aktuell AS
SELECT DISTINCT ON (quelle_id,ereignis_schluessel) * FROM bienen.um_ereignis_revision
ORDER BY quelle_id,ereignis_schluessel,revision DESC;

CREATE TABLE bienen.um_messwert_revision (
  kanal_id integer NOT NULL REFERENCES bienen.kanal,
  zeit timestamptz NOT NULL,
  revision integer NOT NULL CHECK (revision > 0),
  quelle_id bigint NOT NULL REFERENCES bienen.um_quelle,
  roh_id bigint NOT NULL REFERENCES bienen.um_rohdatensatz,
  wert double precision,
  qualitaet jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(qualitaet)='array'),
  zeitqualitaet text NOT NULL CHECK (zeitqualitaet IN ('geraet','empfang','unbekannt')),
  interpretation text NOT NULL DEFAULT 'umwelt-csv@1',
  importiert_am timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (kanal_id,zeit,revision),
  CHECK (wert IS NULL OR (wert > '-Infinity'::float8 AND wert < 'Infinity'::float8))
);
CREATE INDEX um_messwert_zeit ON bienen.um_messwert_revision(zeit,kanal_id,revision DESC);

CREATE VIEW bienen.um_messwert_aktuell AS
SELECT DISTINCT ON (m.kanal_id,m.zeit) m.* FROM bienen.um_messwert_revision m
JOIN bienen.um_rohdatensatz r ON r.id=m.roh_id
JOIN bienen.um_ereignis_aktuell e ON e.quelle_id=r.quelle_id
  AND e.ereignis_schluessel=r.ereignis_schluessel AND e.roh_id=m.roh_id
ORDER BY m.kanal_id,m.zeit,m.revision DESC;

CREATE TABLE bienen.um_checkpoint (
  quelle_id bigint PRIMARY KEY REFERENCES bienen.um_quelle,
  datei_sha256 char(64) NOT NULL,
  groesse bigint NOT NULL,
  aktualisiert_am timestamptz NOT NULL DEFAULT now(),
  bericht jsonb NOT NULL
);

CREATE TABLE bienen.um_import_lauf (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  quelle_id bigint NOT NULL REFERENCES bienen.um_quelle,
  geprueft_am timestamptz NOT NULL DEFAULT now(),
  erfolgreich boolean NOT NULL,
  bericht jsonb NOT NULL
);
CREATE INDEX um_import_quelle ON bienen.um_import_lauf(quelle_id,id DESC);

CREATE TRIGGER um_roh_immutable BEFORE UPDATE OR DELETE ON bienen.um_rohdatensatz
FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();
CREATE TRIGGER um_revision_immutable BEFORE UPDATE OR DELETE ON bienen.um_messwert_revision
FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();
CREATE TRIGGER um_ereignis_immutable BEFORE UPDATE OR DELETE ON bienen.um_ereignis_revision
FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();

CREATE FUNCTION bienen.um_pruefe_kanalzeit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM bienen.kanal WHERE id=NEW.kanal_id AND gueltig @> NEW.zeit) THEN
    RAISE EXCEPTION 'Messzeit ausserhalb der Kanalgueltigkeit' USING ERRCODE='check_violation';
  END IF;
  IF TG_TABLE_NAME='um_messwert_revision' THEN
    IF NOT EXISTS (
      SELECT 1 FROM bienen.um_quelle q
      JOIN bienen.um_quelle_kanal qk ON qk.quelle_id=q.id AND qk.kanal_id=NEW.kanal_id
      JOIN bienen.geraet_zuordnung z ON z.geraet_id=q.geraet_id AND z.stand_id=q.stand_id AND z.gueltig @> NEW.zeit
      WHERE q.id=NEW.quelle_id
    ) THEN
      RAISE EXCEPTION 'Messzeit ohne gueltige konfigurierte Standzuordnung' USING ERRCODE='check_violation';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER um_kanalzeit BEFORE INSERT OR UPDATE ON bienen.um_messwert_revision
FOR EACH ROW EXECUTE FUNCTION bienen.um_pruefe_kanalzeit();
CREATE TRIGGER messwert_kanalzeit BEFORE INSERT OR UPDATE ON bienen.messwert
FOR EACH ROW EXECUTE FUNCTION bienen.um_pruefe_kanalzeit();

CREATE FUNCTION bienen.um_schuetze_kanalhistorie() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM bienen.messwert WHERE kanal_id=OLD.id)
     OR EXISTS (SELECT 1 FROM bienen.um_messwert_revision WHERE kanal_id=OLD.id) THEN
    IF (to_jsonb(NEW)-'gueltig'-'status') IS DISTINCT FROM (to_jsonb(OLD)-'gueltig'-'status')
       OR EXISTS (SELECT 1 FROM bienen.messwert WHERE kanal_id=OLD.id AND NOT NEW.gueltig @> zeit)
       OR EXISTS (SELECT 1 FROM bienen.um_messwert_revision WHERE kanal_id=OLD.id AND NOT NEW.gueltig @> zeit) THEN
      RAISE EXCEPTION 'Historischen Kanal nicht umdeuten; neuen Abschnitt anlegen' USING ERRCODE='check_violation';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER um_kanalhistorie BEFORE UPDATE ON bienen.kanal
FOR EACH ROW EXECUTE FUNCTION bienen.um_schuetze_kanalhistorie();

CREATE OR REPLACE VIEW bienen.messwert_bezug AS
SELECT m.kanal_id,m.zeit,m.wert*k.faktor+k.versatz AS wert,m.qualitaet,m.zeitqualitaet,
       k.messgroesse_code,k.messstelle_id,k.geraet_id,z.volk_id,z.stand_id
FROM bienen.messwert m
JOIN bienen.kanal k ON k.id=m.kanal_id AND k.gueltig @> m.zeit
LEFT JOIN bienen.geraet_zuordnung z ON z.geraet_id=k.geraet_id AND z.gueltig @> m.zeit;
