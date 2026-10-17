# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
from pathlib import Path
import tempfile
import unittest

import psycopg
from support import reset_database, source, soil_row, SOIL_HEADER, WEATHER_HEADER
from umwelt.ingest import import_source, SourceReadError
from umwelt.migrate import migrate


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.conn = reset_database()
        self.temp = tempfile.TemporaryDirectory()
        self.file = Path(self.temp.name) / 'synthetic.csv'
        self.file.write_text(SOIL_HEADER + soil_row())
        self.source_id = source(self.conn, self.file)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def scalar(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()[0]

    def test_read_only_idempotence_and_three_depths(self):
        self.file.chmod(0o400)
        digest = hashlib.sha256(self.file.read_bytes()).hexdigest()
        first = import_source(self.conn, self.source_id)
        count = self.scalar('SELECT count(*) FROM bienen.um_messwert_revision')
        second = import_source(self.conn, self.source_id)
        self.assertGreater(first['neue_revisionen'], 0)
        self.assertTrue(second['unveraendert'])
        self.assertEqual(count, self.scalar('SELECT count(*) FROM bienen.um_messwert_revision'))
        self.assertEqual(digest, hashlib.sha256(self.file.read_bytes()).hexdigest())
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o400)
        self.assertEqual(self.scalar('SELECT count(DISTINCT tiefe_cm) FROM bienen.messstelle WHERE zone=\'boden\''), 3)
        self.assertIsNone(self.scalar('SELECT wert FROM bienen.um_messwert_aktuell m JOIN bienen.kanal k ON k.id=m.kanal_id WHERE quellfeld=\'temp_20cm\''))

    def test_append_duplicate_and_value_correction_preserve_raw_history(self):
        import_source(self.conn, self.source_id)
        self.file.write_text(SOIL_HEADER + soil_row() + soil_row() + soil_row('2026-10-25T01:30:00Z', '14;15;16', 'msg-2'))
        import_source(self.conn, self.source_id)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_rohdatensatz'), 2)
        self.file.write_text(SOIL_HEADER + soil_row(values='22;;13') + soil_row('2026-10-25T01:30:00Z', '14;15;16', 'msg-2'))
        import_source(self.conn, self.source_id)
        rows = self.conn.execute("SELECT revision,wert FROM bienen.um_messwert_revision m JOIN bienen.kanal k ON k.id=m.kanal_id WHERE quellfeld='temp_5cm' AND zeit='2026-10-25T00:30Z' ORDER BY revision").fetchall()
        self.assertEqual(rows, [(1, 12.0), (2, 22.0)])
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_rohdatensatz'), 3)
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conn.execute('UPDATE bienen.um_rohdatensatz SET original=\'changed\'')

    def test_database_failure_rolls_back_data_and_checkpoint(self):
        self.conn.execute("""CREATE FUNCTION bienen.test_failure() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'synthetic failure'; END $$""")
        self.conn.execute('CREATE TRIGGER synthetic_failure BEFORE INSERT ON bienen.um_messwert_revision FOR EACH ROW EXECUTE FUNCTION bienen.test_failure()')
        with self.assertRaises(psycopg.errors.RaiseException):
            import_source(self.conn, self.source_id)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_rohdatensatz'), 0)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_checkpoint'), 0)
        self.conn.execute('DROP TRIGGER synthetic_failure ON bienen.um_messwert_revision')
        import_source(self.conn, self.source_id)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_checkpoint'), 1)

    def test_timestamp_correction_supersedes_old_point_without_erasing_history(self):
        import_source(self.conn, self.source_id)
        self.file.write_text(SOIL_HEADER + soil_row('2026-10-25T01:30:00Z', '14;15;16', 'msg-1'))
        import_source(self.conn, self.source_id)
        self.assertEqual(self.scalar('SELECT count(DISTINCT zeit) FROM bienen.um_messwert_aktuell'), 1)
        self.assertEqual(self.scalar('SELECT count(DISTINCT zeit) FROM bienen.um_messwert_revision'), 2)

    def test_conflicting_same_timestamp_does_not_toggle_on_backfill(self):
        self.file.write_text(SOIL_HEADER + soil_row() + soil_row(values='20;21;22', ident='other-event'))
        import_source(self.conn, self.source_id)
        count = self.scalar('SELECT count(*) FROM bienen.um_messwert_revision')
        self.file.write_text(self.file.read_text() + soil_row('2026-10-25T01:30:00Z', '14;15;16', 'later-event'))
        import_source(self.conn, self.source_id)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_messwert_revision'), count+5)

    def test_permissions_failure_and_recovery_observable(self):
        self.file.chmod(0)
        try:
            with self.assertRaises(SourceReadError):
                import_source(self.conn, self.source_id)
        finally:
            self.file.chmod(0o600)
        self.assertFalse(self.scalar('SELECT erfolgreich FROM bienen.um_import_lauf ORDER BY id DESC LIMIT 1'))
        import_source(self.conn, self.source_id)
        self.assertTrue(self.scalar('SELECT erfolgreich FROM bienen.um_import_lauf ORDER BY id DESC LIMIT 1'))

    def test_migration_repeat_is_idempotent(self):
        self.assertFalse(migrate(self.conn))
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.schema_migration'), 2)

    def test_missing_base_schema_refused_without_rebuild(self):
        self.assertEqual(self.conn.info.dbname, 'bienen_test')
        self.conn.execute('DROP SCHEMA bienen CASCADE')
        with self.assertRaisesRegex(ValueError, 'Grundschema'):
            migrate(self.conn)
        self.assertFalse(self.scalar("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname='bienen')"))

    def test_channel_validity_and_historical_calibration_are_enforced(self):
        import_source(self.conn, self.source_id)
        kid = self.scalar("SELECT id FROM bienen.kanal WHERE quellfeld='temp_5cm'")
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conn.execute('UPDATE bienen.kanal SET faktor=2 WHERE id=%s', (kid,))
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conn.execute("INSERT INTO bienen.messwert(kanal_id,zeit,wert,zeitqualitaet) VALUES (%s,'2025-01-01T00:00Z',1,'empfang')", (kid,))

    def test_weather_values_units_and_unknown_counter_semantics(self):
        other = Path(self.temp.name) / 'weather.csv'
        other.write_text(WEATHER_HEADER + '2026-10-25T00:30:00Z;synthetic;synthetic-weather;-2.5;;1013;0;0;0;359;0;0;7;1;3;AA\n')
        stand = self.scalar('SELECT id FROM bienen.stand LIMIT 1')
        sid = source(self.conn, other, 's2120', 'weather', stand_id=stand)
        import_source(self.conn, sid)
        self.assertEqual(self.scalar("SELECT wert FROM bienen.um_messwert_aktuell m JOIN bienen.kanal k ON k.id=m.kanal_id WHERE quellfeld='t'"), -2.5)
        self.assertEqual(self.scalar("SELECT semantik FROM bienen.messgroesse WHERE code='regen_summe'"), 'unbekannte_summe')


if __name__ == '__main__':
    unittest.main()
