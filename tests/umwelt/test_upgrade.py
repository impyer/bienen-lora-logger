# SPDX-License-Identifier: GPL-3.0-or-later
"""Dump/restore a populated 003 database before additive 004."""
from datetime import date
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import unittest

import psycopg
from argon2 import PasswordHasher
from support import reset_database,source,SOIL_HEADER,soil_row
from stockkarte_admin import seed_demo
from stockkarte_store import write_inspection
from umwelt.migrate import migrate


class UpgradeTests(unittest.TestCase):
    def test_populated_r1_backup_restore_and_additive_upgrade(self):
        conn=reset_database(migrate_environment=False)
        try:
            migrate(conn,through=3)
            with conn.cursor() as cur:seed_demo(cur)
            colony=conn.execute('SELECT id FROM bienen.volk ORDER BY id LIMIT 1').fetchone()[0]
            write_inspection(conn,volk_id=colony,event_date=date(2026,10,17),values={'bl:queen_seen':False},note='Synthetic upgrade',author='r11',reason='Retention')
            conn.execute("INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES ('synthetic-upgrade',%s)",(PasswordHasher().hash(secrets.token_urlsafe(32)),))
            with tempfile.TemporaryDirectory() as directory:
                file=Path(directory)/'old.csv';file.write_text(SOIL_HEADER+soil_row())
                sid=source(conn,file)
                kid=conn.execute("SELECT kanal_id FROM bienen.um_quelle_kanal WHERE quelle_id=%s AND quellfeld='temp_5cm'",(sid,)).fetchone()[0]
                for revision,value in [(1,12),(2,22)]:
                    raw=conn.execute('''INSERT INTO bienen.um_rohdatensatz(quelle_id,ereignis_schluessel,sha256,datei_sha256,zeile,original,felder)
                        VALUES (%s,repeat('a',64),%s,repeat('d',64),2,%s,'{}') RETURNING id''',(sid,str(revision)*64,'synthetic-revision-'+str(revision))).fetchone()[0]
                    conn.execute("INSERT INTO bienen.um_ereignis_revision(quelle_id,ereignis_schluessel,revision,roh_id,zeit) VALUES (%s,repeat('a',64),%s,%s,'2026-10-17T00:00Z')",(sid,revision,raw))
                    conn.execute("INSERT INTO bienen.um_messwert_revision(kanal_id,zeit,revision,quelle_id,roh_id,wert,zeitqualitaet) VALUES (%s,'2026-10-17T00:00Z',%s,%s,%s,%s,'unbekannt')",(kid,revision,sid,raw,value))
                conn.execute("INSERT INTO bienen.um_checkpoint(quelle_id,datei_sha256,groesse,bericht) VALUES (%s,repeat('d',64),123,'{\"synthetic\":true}')",(sid,))
                tables=('stand','volk','geraet','kanal','sk_benutzer','sk_durchsicht_revision','um_quelle','um_rohdatensatz','um_ereignis_revision','um_messwert_revision','um_checkpoint')
                def state(c):return {t:c.execute("SELECT to_jsonb(r)-'archiv_muster' FROM bienen."+t+' r ORDER BY to_jsonb(r)::text').fetchall() for t in tables}
                before=state(conn);dump=Path(directory)/'before004.dump'
                self.assertIsNotNone(shutil.which('pg_dump'));self.assertIsNotNone(shutil.which('pg_restore'))
                with dump.open('wb') as output:subprocess.run(['pg_dump','--dbname',os.environ['BIENEN_TEST_DSN'],'-Fc','--no-owner','--no-privileges'],stdout=output,check=True)
                restored_name='bienen_r11_restore_'+secrets.token_hex(5)
                conn.execute('CREATE DATABASE '+restored_name)
                dsn=psycopg.conninfo.make_conninfo(os.environ['BIENEN_TEST_DSN'],dbname=restored_name)
                subprocess.run(['pg_restore','--dbname',dsn,'--no-owner','--no-privileges',str(dump)],check=True)
                with psycopg.connect(dsn) as restored:self.assertEqual(state(restored),before)
                self.assertTrue(migrate(conn));self.assertFalse(migrate(conn));self.assertEqual(state(conn),before)
                self.assertEqual(conn.execute('SELECT wert FROM bienen.um_messwert_aktuell').fetchone()[0],22)
                self.assertEqual(conn.execute('SELECT count(*) FROM bienen.schema_migration').fetchone()[0],2)
                print('R11 pre-004 restore verified in separately retained database:',restored_name)
        finally:conn.close()
