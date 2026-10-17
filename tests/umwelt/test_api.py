# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import tempfile
import unittest

from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from support import reset_database, source, soil_row, SOIL_HEADER
from stockkarte_session_api import create_session_app
from umwelt.ingest import import_source


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.conn = reset_database()
        self.temp = tempfile.TemporaryDirectory()
        file = Path(self.temp.name) / 'soil.csv'
        file.write_text(SOIL_HEADER + soil_row() + soil_row('2026-10-25T01:30:00Z', '14;15;16', 'msg-2'))
        self.sid = source(self.conn, file)
        import_source(self.conn, self.sid)
        self.stand = self.conn.execute('SELECT id FROM bienen.stand').fetchone()[0]
        self.uid = self.conn.execute('INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id', ('synthetic', PasswordHasher().hash('Synthetic-only-test-password'))).fetchone()[0]
        self.conn.execute('INSERT INTO bienen.sk_benutzer_stand VALUES (%s,%s,true)', (self.uid, self.stand))
        self.client = TestClient(create_session_app(dsn=self.conn.info.dsn, enabled=True, secret='synthetic-session-secret-'*3), base_url='https://testserver')
        self.base = '/api/v1/umwelt'
        self.query = {'stand_id':self.stand,'von':'2026-10-25T00:00:00Z','bis':'2026-10-26T00:00:00Z'}

    def tearDown(self):
        self.client.close()
        self.conn.close()
        self.temp.cleanup()

    def login(self):
        response = self.client.post('/api/v1/stockkarte/session/login', json={'username':'synthetic','password':'Synthetic-only-test-password'})
        self.assertEqual(response.status_code, 200)
        return response

    def test_login_cookie_scope_and_authorized_api(self):
        self.assertEqual(self.client.get(self.base+'/staende').status_code, 401)
        response = self.login()
        self.assertTrue(any(c.path == '/api/v1' for c in self.client.cookies.jar))
        self.assertFalse(any(c.path == '/api/v1/stockkarte' for c in self.client.cookies.jar))
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertEqual(self.client.get(self.base+'/staende').json()[0]['id'], self.stand)

    def test_actual_values_units_depths_null_and_utc(self):
        self.login()
        response = self.client.get(self.base+'/messreihen', params=self.query)
        self.assertEqual(response.status_code, 200, response.text)
        series = response.json()['series']
        soil = {s['channel']['depth_cm']:s for s in series if s['channel']['depth_cm']}
        self.assertEqual(set(soil), {5,20,50})
        self.assertEqual(soil[5]['channel']['unit'], '°C')
        self.assertEqual(soil[5]['points'][0]['value'], 12)
        self.assertIsNone(soil[20]['points'][0]['value'])
        self.assertEqual(soil[5]['points'][0]['time'], '2026-10-25T00:30:00Z')
        self.assertTrue(soil[5]['points'][0]['synthetic'])
        self.assertEqual(soil[5]['points'][0]['raw_value'], 12)
        self.assertEqual(len(soil[5]['points'][0]['record_sha256']), 64)
        self.assertEqual(soil[5]['points'][0]['record_line'], 2)
        self.assertEqual(soil[5]['points'][0]['interpretation'], 'umwelt-csv@1')

    def test_bounded_cursor_and_invalid_windows(self):
        self.login()
        first = self.client.get(self.base+'/messreihen', params=dict(self.query, limit=2)).json()
        self.assertTrue(first['truncated'])
        self.assertEqual(sum(len(s['points']) for s in first['series']), 2)
        next_page = self.client.get(self.base+'/messreihen', params=dict(self.query, limit=2, cursor=first['next_cursor']))
        self.assertEqual(next_page.status_code, 200)
        for change in [{'limit':5001}, {'von':'2026-10-25T00:00:00'}, {'cursor':'not-base64'}, {'bis':'2029-01-01T00:00:00Z'}]:
            r = self.client.get(self.base+'/messreihen', params=dict(self.query, **change))
            self.assertEqual(r.status_code, 422, r.text)

    def test_live_revocation_no_cross_apiary_access(self):
        self.login()
        self.assertEqual(self.client.get(self.base+'/kanaele', params={'stand_id':99999}).status_code, 404)
        self.conn.execute('UPDATE bienen.sk_benutzer_stand SET darf_lesen=false WHERE benutzer_id=%s', (self.uid,))
        self.assertEqual(self.client.get(self.base+'/staende').json(), [])
        self.assertEqual(self.client.get(self.base+'/messreihen', params=self.query).status_code, 404)

    def test_logout_and_openapi_are_real_and_authenticated(self):
        self.assertEqual(self.client.get(self.base+'/openapi.json').status_code, 401)
        login = self.login()
        schema = self.client.get(self.base+'/openapi.json').json()
        self.assertIn(self.base+'/messreihen', schema['paths'])
        self.assertEqual(self.client.post('/api/v1/stockkarte/session/logout').status_code, 403)
        response = self.client.post('/api/v1/stockkarte/session/logout', headers={'X-CSRF-Token':login.json()['csrf_token']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(self.base+'/staende').status_code, 401)


if __name__ == '__main__':
    unittest.main()
