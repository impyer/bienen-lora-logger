-- SPDX-License-Identifier: GPL-3.0-or-later
-- PostgreSQL-16-Migration SK-001: eigenständige Stockkarten-Persistenz.
-- Additiv. Voraussetzung: server/datenbank/schema.sql ist bereits in einer
-- TESTDATENBANK eingerichtet. Niemals schema.sql auf bestehende Daten anwenden:
-- diese Datei enthält DROP SCHEMA ... CASCADE.
-- Migration genau einmal anwenden; nicht als automatische Startup-SQL verwenden.
BEGIN;

CREATE TABLE bienen.sk_kategorie (
  id              text PRIMARY KEY CHECK (char_length(id) BETWEEN 1 AND 128),
  parent_id       text REFERENCES bienen.sk_kategorie(id) DEFERRABLE INITIALLY DEFERRED,
  bezeichnung     text NOT NULL CHECK (char_length(trim(bezeichnung)) BETWEEN 1 AND 250),
  eingabetyp      text NOT NULL CHECK (char_length(eingabetyp) BETWEEN 1 AND 64),
  pflicht         boolean NOT NULL DEFAULT false,
  meta            jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(meta) = 'object'),
  quelle          text NOT NULL DEFAULT 'eigen' CHECK (quelle IN ('eigen','beep_import')),
  quelle_id       text,
  erstellt_am     timestamptz NOT NULL DEFAULT now(),
  CHECK (parent_id IS DISTINCT FROM id)
);
CREATE UNIQUE INDEX sk_kategorie_extern ON bienen.sk_kategorie(quelle,quelle_id)
  WHERE quelle_id IS NOT NULL;

CREATE TABLE bienen.sk_option (
  id              text PRIMARY KEY CHECK (char_length(id) BETWEEN 1 AND 128),
  kategorie_id    text NOT NULL REFERENCES bienen.sk_kategorie(id),
  bezeichnung     text NOT NULL CHECK (char_length(trim(bezeichnung)) BETWEEN 1 AND 250),
  reihenfolge     integer NOT NULL CHECK (reihenfolge >= 0),
  inaktiv         boolean NOT NULL DEFAULT false,
  quelle          text NOT NULL DEFAULT 'eigen' CHECK (quelle IN ('eigen','beep_import')),
  UNIQUE (kategorie_id,reihenfolge),
  UNIQUE (kategorie_id,id)
);

CREATE TABLE bienen.sk_checkliste (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  schluessel   text NOT NULL UNIQUE,
  name         text NOT NULL CHECK (char_length(trim(name)) BETWEEN 1 AND 120),
  erstellt_am  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bienen.sk_checkliste_version (
  checkliste_id bigint NOT NULL REFERENCES bienen.sk_checkliste(id),
  version       integer NOT NULL CHECK (version > 0),
  erstellt_am   timestamptz NOT NULL DEFAULT now(),
  begruendung   text NOT NULL DEFAULT '',
  PRIMARY KEY (checkliste_id,version)
);
CREATE TABLE bienen.sk_checkliste_feld (
  checkliste_id bigint NOT NULL,
  version       integer NOT NULL,
  kategorie_id  text NOT NULL REFERENCES bienen.sk_kategorie(id),
  position      integer NOT NULL CHECK (position >= 0),
  pflicht       boolean NOT NULL DEFAULT false,
  PRIMARY KEY (checkliste_id,version,kategorie_id),
  UNIQUE (checkliste_id,version,position),
  FOREIGN KEY (checkliste_id,version)
    REFERENCES bienen.sk_checkliste_version(checkliste_id,version)
);

-- Dauerhafte Identität und BEEP-Quellreferenz nur hier; Korrekturen in Revisionen.
CREATE TABLE bienen.sk_durchsicht (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  volk_id     integer NOT NULL REFERENCES bienen.volk(id),
  quelle      text NOT NULL DEFAULT 'eigen' CHECK (quelle IN ('eigen','beep_import')),
  quelle_id   text,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  CHECK (quelle <> 'beep_import' OR NULLIF(trim(quelle_id),'') IS NOT NULL)
);
CREATE UNIQUE INDEX sk_durchsicht_import_id ON bienen.sk_durchsicht(quelle,quelle_id)
  WHERE quelle_id IS NOT NULL;
CREATE INDEX sk_durchsicht_volk ON bienen.sk_durchsicht(volk_id);

-- Lokaler Datumstag getrennt von optionalem exakt bekanntem Zeitpunkt.
CREATE TABLE bienen.sk_durchsicht_revision (
  durchsicht_id     bigint NOT NULL REFERENCES bienen.sk_durchsicht(id),
  revision          integer NOT NULL CHECK (revision >= 1),
  ereignis_datum    date NOT NULL,
  ereignis_zeit     timestamptz,
  zeitgenauigkeit   text NOT NULL CHECK (zeitgenauigkeit IN ('nur_datum','exakt','geschaetzt')),
  checkliste_id     bigint,
  checkliste_version integer,
  werte             jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(werte) = 'object'),
  notiz             text NOT NULL DEFAULT '',
  aenderungsgrund   text NOT NULL,
  autor             text NOT NULL CHECK (char_length(trim(autor)) > 0),
  erstellt_am       timestamptz NOT NULL DEFAULT now(),
  geloescht         boolean NOT NULL DEFAULT false,
  PRIMARY KEY (durchsicht_id,revision),
  CHECK ((zeitgenauigkeit = 'nur_datum' AND ereignis_zeit IS NULL)
      OR (zeitgenauigkeit IN ('exakt','geschaetzt') AND ereignis_zeit IS NOT NULL)),
  CHECK (ereignis_zeit IS NULL OR ereignis_datum = (ereignis_zeit AT TIME ZONE 'Europe/Berlin')::date),
  CHECK ((checkliste_id IS NULL) = (checkliste_version IS NULL)),
  FOREIGN KEY (checkliste_id,checkliste_version)
    REFERENCES bienen.sk_checkliste_version(checkliste_id,version)
);
CREATE INDEX sk_durchsicht_revision_datum
  ON bienen.sk_durchsicht_revision(ereignis_datum);

-- Stammdaten der Königin bleiben in bienen.koenigin;
-- zusätzliche Details und Korrekturen werden append-only erfasst.
CREATE TABLE bienen.sk_koenigin_revision (
  koenigin_id    integer NOT NULL REFERENCES bienen.koenigin(id),
  revision       integer NOT NULL CHECK (revision >= 1),
  daten          jsonb NOT NULL CHECK (jsonb_typeof(daten) = 'object'),
  aenderungsgrund text NOT NULL,
  autor          text NOT NULL CHECK (char_length(trim(autor)) > 0),
  erstellt_am    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (koenigin_id,revision)
);

-- Historische Versionen dürfen nicht unbemerkt überschrieben werden.
CREATE FUNCTION bienen.sk_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Stockkartenhistorie ist append-only: %.%', TG_TABLE_SCHEMA, TG_TABLE_NAME
    USING ERRCODE='check_violation';
END;
$$;
CREATE TRIGGER sk_durchsicht_stamm_immutable
  BEFORE UPDATE OR DELETE ON bienen.sk_durchsicht
  FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();
CREATE TRIGGER sk_durchsicht_revision_immutable
  BEFORE UPDATE OR DELETE ON bienen.sk_durchsicht_revision
  FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();
CREATE TRIGGER sk_checkliste_version_immutable
  BEFORE UPDATE OR DELETE ON bienen.sk_checkliste_version
  FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();
CREATE TRIGGER sk_checkliste_feld_immutable
  BEFORE UPDATE OR DELETE ON bienen.sk_checkliste_feld
  FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();
CREATE TRIGGER sk_koenigin_revision_immutable
  BEFORE UPDATE OR DELETE ON bienen.sk_koenigin_revision
  FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();

CREATE VIEW bienen.sk_durchsicht_aktuell AS
SELECT d.id, d.volk_id, d.quelle, d.quelle_id, d.erstellt_am,
       r.revision, r.ereignis_datum, r.ereignis_zeit, r.zeitgenauigkeit,
       r.checkliste_id, r.checkliste_version, r.werte, r.notiz,
       r.autor, r.geloescht
FROM bienen.sk_durchsicht d
JOIN LATERAL (
  SELECT * FROM bienen.sk_durchsicht_revision r
  WHERE r.durchsicht_id = d.id
  ORDER BY r.revision DESC LIMIT 1
) r ON true
WHERE NOT r.geloescht;

COMMIT;
