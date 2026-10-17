-- SPDX-License-Identifier: GPL-3.0-or-later
-- SK-002: Benutzerkonten und sitzungsbasierte Rechte für die native Stockkarte.
-- Nur additiv, abhängig von SK-001 und dem bienen.volk-Stammdatenschema.
-- Einmalige Testmigration; keine Produktivfreigabe ohne Review.
BEGIN;

CREATE TABLE bienen.sk_benutzer (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  benutzername text NOT NULL UNIQUE
    CHECK (char_length(benutzername) BETWEEN 3 AND 80
       AND benutzername ~ '^[a-z0-9_.-]+$'),
  passwort_hash text NOT NULL CHECK (char_length(passwort_hash) BETWEEN 40 AND 512),
  aktiv boolean NOT NULL DEFAULT true,
  angelegt_am timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bienen.sk_benutzer_volk (
  benutzer_id bigint NOT NULL REFERENCES bienen.sk_benutzer(id),
  volk_id integer NOT NULL REFERENCES bienen.volk(id),
  darf_lesen boolean NOT NULL DEFAULT false,
  darf_schreiben boolean NOT NULL DEFAULT false,
  PRIMARY KEY (benutzer_id,volk_id),
  CHECK (NOT darf_schreiben OR darf_lesen)
);
CREATE INDEX sk_benutzer_volk_volk ON bienen.sk_benutzer_volk(volk_id);

CREATE TABLE bienen.sk_sitzung (
  token_sha256 char(64) PRIMARY KEY CHECK (token_sha256 ~ '^[0-9a-f]{64}$'),
  benutzer_id bigint NOT NULL REFERENCES bienen.sk_benutzer(id),
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  ablauf_am timestamptz NOT NULL,
  widerrufen_am timestamptz,
  CHECK (ablauf_am > erstellt_am)
);
CREATE INDEX sk_sitzung_aktiv ON bienen.sk_sitzung(benutzer_id,ablauf_am)
  WHERE widerrufen_am IS NULL;

COMMIT;
