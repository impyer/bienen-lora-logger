# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual PostgreSQL snapshots, pages, live ACL and late corrections."""
import os
from pathlib import Path
import tempfile
import unittest
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import psycopg

from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from support import reset_database, source, soil_row, SOIL_HEADER
from stockkarte_session_api import create_session_app
from umwelt.ingest import import_source


def seed_series(conn, source_id, count=1200):
    """Bulk synthetic SQL fixture; full CSV path is independently tested in E2E."""
    conn.execute('''INSERT INTO bienen.um_rohdatensatz
        (quelle_id,ereignis_schluessel,sha256,datei_sha256,zeile,original,felder)
        SELECT %s,md5('series-event-'||i)||md5('series-event-'||i),md5('series-raw-'||i)||md5('series-raw-'||i),
          repeat('b',64),i+2,'synthetic-series-fixture',
          jsonb_build_object('stamp',timestamptz '2026-10-01T00:00Z'+i*interval '5 minutes','i',i)
        FROM generate_series(0,%s) i''',(source_id,count-1))
    conn.execute('''INSERT INTO bienen.um_ereignis_revision
        (quelle_id,ereignis_schluessel,revision,roh_id,zeit)
        SELECT quelle_id,ereignis_schluessel,1,id,(felder->>'stamp')::timestamptz
        FROM bienen.um_rohdatensatz WHERE quelle_id=%s AND original='synthetic-series-fixture' ''',(source_id,))
    conn.execute('''INSERT INTO bienen.um_messwert_revision
        (kanal_id,zeit,revision,quelle_id,roh_id,wert,qualitaet,zeitqualitaet)
        SELECT k.kanal_id,(r.felder->>'stamp')::timestamptz,1,r.quelle_id,r.id,
          CASE WHEN k.quellfeld='temp_20cm' AND (r.felder->>'i')::int %% 31=0 THEN NULL
               WHEN (r.felder->>'i')::int=751 THEN -99
               WHEN (r.felder->>'i')::int=752 THEN 123
               ELSE (r.felder->>'i')::int %% 50 END,
          '[]'::jsonb,'unbekannt'
        FROM bienen.um_rohdatensatz r JOIN bienen.um_quelle_kanal k ON k.quelle_id=r.quelle_id
        WHERE r.quelle_id=%s AND r.original='synthetic-series-fixture' ''',(source_id,))


class SeriesApiTests(unittest.TestCase):
    def test_parallel_queries_have_bounded_admission_and_recover(self):
        with psycopg.connect(os.environ['BIENEN_TEST_DSN']) as blocker, ThreadPoolExecutor(2) as pool:
            blocker.execute('LOCK TABLE bienen.um_messwert_revision IN ACCESS EXCLUSIVE MODE')
            pending=[pool.submit(self.client.get,self.path,params=self.params) for _ in range(2)]
            timer=None
            try:
                deadline=time.monotonic()+4
                while time.monotonic()<deadline:
                    count=self.conn.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock'").fetchone()[0]
                    if count>=2:break
                    time.sleep(.02)
                self.assertGreaterEqual(count,2,'two real SQL queries must be in flight')
                timer=threading.Timer(2,blocker.rollback);timer.start()
                response=self.client.get(self.path,params=self.params)
                self.assertEqual(response.status_code,503)
                self.assertIn('gleichzeitige',response.json()['detail'])
            finally:
                if timer:timer.cancel();timer.join()
                blocker.rollback()
                for future in pending:self.assertEqual(future.result(timeout=10).status_code,200)
        self.assertEqual(self.client.get(self.path,params=self.params).status_code,200)

    def test_offsets_half_open_boundaries_and_frozen_correction(self):
        params=dict(self.params,von='2026-10-25T02:30:00+02:00',bis='2026-10-25T02:31:00+02:00',limit=1)
        first=self.client.get(self.path,params=params).json()
        self.assertEqual(first['source_points'],5)
        self.file.write_text(SOIL_HEADER+soil_row(values='22;;13'))
        import_source(self.conn,self.sid)
        pages=[first]
        while pages[-1]['next_cursor']:
            pages.append(self.client.get(self.path,params=dict(params,cursor=pages[-1]['next_cursor'])).json())
        self.assertEqual(sum(p['returned_points'] for p in pages),5)
        self.assertTrue(all(point['revision']==1 for p in pages for s in p['series'] for point in s['points']))
        self.assertTrue(all(point['time']=='2026-10-25T00:30:00Z' for p in pages for s in p['series'] for point in s['points']))
        fresh=self.client.get(self.path,params=dict(params,limit=5000)).json()
        self.assertTrue(any(point['revision']==2 for s in fresh['series'] for point in s['points']))
        empty=self.client.get(self.path,params=dict(params,von='2026-10-25T02:31:00+02:00')).status_code
        self.assertEqual(empty,422)

    def setUp(self):
        self.conn=reset_database();self.temp=tempfile.TemporaryDirectory()
        self.file=Path(self.temp.name)/'soil.csv';self.file.write_text(SOIL_HEADER+soil_row())
        self.sid=source(self.conn,self.file);import_source(self.conn,self.sid)
        seed_series(self.conn,self.sid)
        self.stand=self.conn.execute('SELECT stand_id FROM bienen.um_quelle WHERE id=%s',(self.sid,)).fetchone()[0]
        self.uid=self.conn.execute('INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id',('synthetic-series',PasswordHasher().hash('synthetic-test-password'))).fetchone()[0]
        self.conn.execute('INSERT INTO bienen.sk_benutzer_stand VALUES (%s,%s,true)',(self.uid,self.stand))
        self.app=lambda:create_session_app(dsn=os.environ['BIENEN_TEST_DSN'],enabled=True,secret='synthetic-series-session-secret-'*3)
        self.client=TestClient(self.app(),base_url='https://testserver')
        self.assertEqual(self.client.post('/api/v1/stockkarte/session/login',json={'username':'synthetic-series','password':'synthetic-test-password'}).status_code,200)
        self.params=dict(stand_id=self.stand,von='2026-10-01T00:00:00Z',bis='2026-11-01T00:00:00Z',resolution='raw',limit=257)
        self.path='/api/v1/umwelt/zeitreihen'

    def tearDown(self):
        self.client.close();self.conn.close();self.temp.cleanup()

    def read(self,**changes):
        response=self.client.get(self.path,params=dict(self.params,**changes))
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def all_pages(self,first,**changes):
        pages=[first]
        while pages[-1]['next_cursor']:
            self.assertLess(len(pages),100)
            pages.append(self.read(cursor=pages[-1]['next_cursor'],**changes))
        pairs=[(s['channel']['id'],p) for page in pages for s in page['series'] for p in s['points']]
        self.assertEqual(len(pairs),first['total_points'])
        self.assertEqual(len({(kid,p['time']) for kid,p in pairs}),len(pairs))
        self.assertTrue(pages[-1]['complete'])
        return pairs

    def test_more_than_5000_pages_are_complete_and_unique(self):
        first=self.read()
        self.assertEqual(first['source_points'],6005)
        self.assertEqual(first['total_points'],6005)
        self.assertEqual(len(self.all_pages(first)),6005)

    def test_late_backfill_is_visible_only_in_next_snapshot(self):
        first=self.read()
        self.file.write_text(SOIL_HEADER+soil_row()+soil_row('2026-10-01T00:02:00Z','155.125;2;3','late'))
        import_source(self.conn,self.sid)
        self.assertFalse(any(p['value']==155.125 for _,p in self.all_pages(first)))
        fresh=self.read()
        self.assertEqual(fresh['source_points'],6010)
        self.assertTrue(any(p['value']==155.125 for _,p in self.all_pages(fresh)))

    def test_envelope_preserves_extrema_missing_and_exact_units(self):
        first=self.read(resolution='envelope',bucket_seconds=86400)
        points=self.all_pages(first,resolution='envelope',bucket_seconds=86400)
        temperatures=[p for kid,p in points if p['bucket']]
        self.assertTrue({-99,123}.issubset({p['value'] for p in temperatures}))
        self.assertTrue(any(p['bucket']['missing'] for p in temperatures))
        self.assertTrue(any(s['summary']['method']=='raw' for s in first['series']))
        self.assertTrue(all(s['channel']['unit']=='°C' for s in first['series'] if s['channel']['depth_cm']))
        self.assertLess(first['total_points'],first['source_points'])

    def test_cursor_window_actor_live_rights_and_restart(self):
        first=self.read();cursor=first['next_cursor']
        self.assertEqual(self.client.get(self.path,params=dict(self.params,cursor=cursor,von='2026-10-02T00:00Z')).status_code,422)
        self.assertEqual(self.client.get(self.path,params=dict(self.params,cursor='bad')).status_code,422)
        with TestClient(self.app(),base_url='https://testserver') as restarted:
            restarted.cookies.update(self.client.cookies)
            self.assertEqual(restarted.get(self.path,params=dict(self.params,cursor=cursor)).status_code,410)
        self.conn.execute('UPDATE bienen.sk_benutzer_stand SET darf_lesen=false WHERE benutzer_id=%s',(self.uid,))
        self.assertEqual(self.client.get(self.path,params=dict(self.params,cursor=cursor)).status_code,404)

    def test_limits_and_foreign_apiary_are_enforced(self):
        for changes,code in [({'limit':5001},422),({'von':'2026-10-01'},422),({'bis':'2029-01-01T00:00Z'},422),({'stand_id':999999},404)]:
            self.assertEqual(self.client.get(self.path,params=dict(self.params,**changes)).status_code,code)

    def test_another_session_cannot_read_shared_snapshot_cursor(self):
        first=self.read()
        with TestClient(self.client.app,base_url='https://testserver') as other:
            self.assertEqual(other.get(self.path,params=self.params).status_code,401)
            uid=self.conn.execute('INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id',('synthetic-other',PasswordHasher().hash('synthetic-other-password'))).fetchone()[0]
            self.conn.execute('INSERT INTO bienen.sk_benutzer_stand VALUES (%s,%s,true)',(uid,self.stand))
            self.assertEqual(other.post('/api/v1/stockkarte/session/login',json={'username':'synthetic-other','password':'synthetic-other-password'}).status_code,200)
            self.assertEqual(other.get(self.path,params=dict(self.params,cursor=first['next_cursor'])).status_code,404)
