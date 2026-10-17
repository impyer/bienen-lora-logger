# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import os
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

import psycopg
from support import reset_database, source, soil_row, SOIL_HEADER, WEATHER_HEADER
from umwelt.ingest import import_source, register_source, SourceReadError
from umwelt.parser import SourceFormatError
from umwelt.roles import provision_importer
from umwelt import archive_import


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.conn=reset_database();self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.file=self.root/'soil-2026-10.csv';self.file.write_text(SOIL_HEADER+soil_row())
        legacy=source(self.conn,self.file)
        stand,device=self.conn.execute('SELECT stand_id,geraet_id FROM bienen.um_quelle WHERE id=%s',(legacy,)).fetchone()
        self.config=dict(key='monthly',profile='boden',path=self.root,pattern='soil-{YYYY}-{MM}.csv',
            stand_id=stand,device_id=device,source_stand='synthetic',source_device='synthetic-soil',synthetic=True,
            valid_from='2026-01-01T00:00:00Z',time_quality='unbekannt')
        self.sid=register_source(self.conn,**self.config)
    def tearDown(self):self.conn.close();self.temp.cleanup()
    def scalar(self,sql,params=()):return self.conn.execute(sql,params).fetchone()[0]
    def run_import(self):return import_source(self.conn,self.sid)
    def latest(self):return self.conn.execute("SELECT zeit,wert FROM bienen.um_messwert_aktuell m JOIN bienen.kanal k ON k.id=m.kanal_id WHERE m.quelle_id=%s AND k.quellfeld='temp_5cm' ORDER BY zeit",(self.sid,)).fetchall()

    def test_explicit_monthly_source_discovers_following_month(self):
        self.run_import()
        (self.root/'soil-2026-11.csv').write_text(SOIL_HEADER+soil_row('2026-11-01T00:30:00Z','25;26;27','msg-nov'))
        self.run_import();self.assertEqual(len(self.latest()),2)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_archiv_datei'),2)

    def test_append_partial_tail_then_complete_and_restart(self):
        self.run_import();old=self.scalar('SELECT offset_bytes FROM bienen.um_archiv_datei')
        row=soil_row('2026-10-26T00:30:00Z','25;26;27','append')
        with self.file.open('a') as f:f.write(row[:-8])
        result=self.run_import();self.assertTrue(result['partielles_ende'])
        self.assertEqual(self.scalar('SELECT offset_bytes FROM bienen.um_archiv_datei'),old)
        with self.file.open('a') as f:f.write(row[-8:])
        self.assertEqual(self.run_import()['neue_revisionen'],5)
        self.assertTrue(self.run_import()['unveraendert']);self.assertEqual(len(self.latest()),2)

    def test_rename_replace_truncate_and_historical_replay_do_not_undo_correction(self):
        self.run_import()
        replacement=self.root/'replacement';replacement.write_text(SOIL_HEADER+soil_row(values='22;;13'))
        replacement.replace(self.file);self.run_import()
        self.assertEqual(self.latest()[0][1],22)
        self.assertEqual(self.scalar('SELECT version FROM bienen.um_archiv_datei'),2)
        (self.root/'soil-2026-11.csv').write_text(SOIL_HEADER+soil_row())
        self.run_import();self.assertEqual(self.latest()[0][1],22)
        self.file.write_text(SOIL_HEADER);self.run_import();self.assertEqual(self.latest()[0][1],22)
        self.file.write_text(SOIL_HEADER+soil_row());self.run_import();self.assertEqual(self.latest()[0][1],22)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_rohdatensatz'),2)
        self.assertGreaterEqual(self.scalar('SELECT count(*) FROM bienen.um_roh_fundstelle'),4)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_messwert_revision'),10)

    def test_backfill_and_duplicate_across_months_keeps_single_revision(self):
        self.run_import()
        (self.root/'soil-2026-09.csv').write_text(SOIL_HEADER+soil_row('2026-09-01T00:00Z','7;8;9','older')+soil_row())
        self.run_import();count=self.scalar('SELECT count(*) FROM bienen.um_messwert_revision')
        self.assertEqual(count,10);self.assertEqual(self.run_import()['neue_revisionen'],0)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_roh_fundstelle'),3)

    def test_source_unchanged_and_registration_is_idempotent_but_never_remaps(self):
        self.file.chmod(0o400);before=self.file.stat();digest=hashlib.sha256(self.file.read_bytes()).digest()
        self.run_import();after=self.file.stat()
        self.assertEqual((before.st_ino,before.st_mode,before.st_size,before.st_mtime_ns),(after.st_ino,after.st_mode,after.st_size,after.st_mtime_ns))
        self.assertEqual(digest,hashlib.sha256(self.file.read_bytes()).digest())
        self.assertEqual(register_source(self.conn,**self.config),self.sid)
        with self.assertRaisesRegex(ValueError,'überschreiben'):register_source(self.conn,**dict(self.config,source_device='wrong'))

    def test_symlinks_special_files_and_traversal_rejected(self):
        self.file.unlink();self.file.symlink_to(self.root/'outside')
        with self.assertRaises(SourceReadError):self.run_import()
        self.file.unlink();os.mkfifo(self.file)
        with self.assertRaises(SourceReadError):self.run_import()
        for pattern in ('../{YYYY}-{MM}.csv','{YYYY}-{MM}/*.csv','{YYYY}-{MM}-{MM}.csv'):
            with self.assertRaises(ValueError):register_source(self.conn,**dict(self.config,pattern=pattern))
        self.file.unlink();self.file.write_text(SOIL_HEADER+soil_row())
        alias=self.root/'alias';alias.symlink_to(self.root,target_is_directory=True)
        self.conn.execute('UPDATE bienen.um_quelle SET datei=%s WHERE id=%s',(str(alias),self.sid))
        with self.assertRaises(SourceReadError):self.run_import()

    def test_bad_header_utf8_permissions_and_recovery(self):
        for content,error in [(b'bad;header\n',SourceFormatError),(SOIL_HEADER.encode()+b'\xff\n',SourceReadError)]:
            self.file.write_bytes(content)
            with self.assertRaises(error):self.run_import()
            self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_archiv_datei'),0)
        self.file.write_text(SOIL_HEADER+soil_row());self.file.chmod(0)
        try:
            with self.assertRaises(SourceReadError):self.run_import()
        finally:self.file.chmod(0o600)
        self.run_import();self.assertEqual(len(self.latest()),1)

    def test_changed_during_read_rolls_back_file_and_checkpoint_then_recovers(self):
        original=archive_import.flush
        def mutate(*args):
            result=original(*args)
            with self.file.open('a') as f:f.write(soil_row('2026-10-26T00:30Z','8;9;10','mutation'))
            return result
        with patch.object(archive_import,'flush',side_effect=mutate):
            with self.assertRaisesRegex(SourceReadError,'geaendert'):self.run_import()
        for table in ('um_archiv_datei','um_checkpoint','um_rohdatensatz','um_messwert_revision'):
            self.assertEqual(self.scalar('SELECT count(*) FROM bienen.'+table),0)
        self.run_import();self.assertEqual(len(self.latest()),2)

    def test_diagnostics_are_bounded_and_invalid_records_are_visible(self):
        self.file.write_text(SOIL_HEADER+('broken\n'*120)+soil_row(device='wrong')+soil_row())
        result=self.run_import();self.assertEqual(result['fehler_anzahl'],121)
        self.assertEqual(len(result['fehler']),50);self.assertEqual(len(self.latest()),1)

    def test_restricted_real_login_imports_but_cannot_access_stockkarte_or_admin(self):
        password=secrets.token_urlsafe(32);role='bl_um_archive_test'
        provision_importer(self.conn,role,password)
        dsn=psycopg.conninfo.make_conninfo(os.environ['BIENEN_TEST_DSN'],user=role,password=password)
        with psycopg.connect(dsn,autocommit=True) as restricted:
            self.assertEqual(import_source(restricted,self.sid)['neue_revisionen'],5)
            self.assertTrue(import_source(restricted,self.sid)['unveraendert'])
            for statement in [
                'SELECT * FROM bienen.sk_benutzer','SELECT * FROM bienen.sk_sitzung',
                'INSERT INTO bienen.stand(name) VALUES (\'forbidden\')',
                'UPDATE bienen.kanal SET faktor=2','UPDATE bienen.um_quelle SET synthetisch=false',
                'DELETE FROM bienen.um_checkpoint','UPDATE bienen.um_rohdatensatz SET original=\'bad\'',
                'CREATE TABLE bienen.forbidden(id int)','CREATE ROLE forbidden_import_role',
                'SELECT * FROM bienen.schema_migration']:
                with self.subTest(statement=statement),self.assertRaises(psycopg.errors.InsufficientPrivilege):restricted.execute(statement)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_messwert_revision'),5)

    def test_weather_monthly_stream_uses_same_discovery_and_provenance(self):
        weather=self.root/'weather-2026-10.csv'
        row='2026-10-25T00:30:00Z;synthetic;synthetic-weather;-2.5;80;1013;0;0;0;359;0;0;7;1;3;AA\n'
        weather.write_text(WEATHER_HEADER+row)
        legacy=source(self.conn,weather,'s2120','weather',stand_id=self.config['stand_id'])
        did=self.scalar('SELECT geraet_id FROM bienen.um_quelle WHERE id=%s',(legacy,))
        sid=register_source(self.conn,**dict(self.config,key='weather-monthly',profile='s2120',device_id=did,
            pattern='weather-{YYYY}-{MM}.csv',source_device='synthetic-weather',time_quality='empfang'))
        import_source(self.conn,sid)
        (self.root/'weather-2026-11.csv').write_text(WEATHER_HEADER+row.replace('2026-10-25','2026-11-01'))
        import_source(self.conn,sid)
        self.assertEqual(self.scalar('SELECT count(*) FROM bienen.um_roh_fundstelle f JOIN bienen.um_archiv_datei a ON a.id=f.datei_id WHERE a.quelle_id=%s',(sid,)),2)
