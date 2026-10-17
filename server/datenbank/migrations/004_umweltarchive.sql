-- SPDX-License-Identifier: GPL-3.0-or-later
-- Explicit additive upgrade after 003; no startup migration or source switch.
ALTER TABLE bienen.um_quelle ADD COLUMN archiv_muster text;
CREATE TABLE bienen.um_archiv_datei (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  quelle_id bigint NOT NULL REFERENCES bienen.um_quelle,
  name text NOT NULL CHECK (name <> '' AND name NOT LIKE '%/%' AND name NOT LIKE '%..%'),
  version integer NOT NULL CHECK (version > 0),
  dev bigint NOT NULL, inode bigint NOT NULL, groesse bigint NOT NULL,
  mtime_ns bigint NOT NULL, ctime_ns bigint NOT NULL,
  offset_bytes bigint NOT NULL CHECK (offset_bytes >= 0 AND offset_bytes <= groesse),
  zeilen bigint NOT NULL CHECK (zeilen >= 0),
  prefix_sha256 char(64) NOT NULL,
  kopf jsonb NOT NULL, bericht jsonb NOT NULL,
  aktualisiert_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (quelle_id,name)
);
CREATE TABLE bienen.um_roh_fundstelle (
  roh_id bigint NOT NULL REFERENCES bienen.um_rohdatensatz,
  datei_id bigint NOT NULL REFERENCES bienen.um_archiv_datei,
  version integer NOT NULL CHECK (version > 0),
  datei_sha256 char(64) NOT NULL,
  zeile bigint NOT NULL, byte_bis bigint NOT NULL,
  PRIMARY KEY (datei_id,version,zeile,roh_id)
);
CREATE TRIGGER um_fundstelle_immutable BEFORE UPDATE OR DELETE ON bienen.um_roh_fundstelle
FOR EACH ROW EXECUTE FUNCTION bienen.sk_append_only();
