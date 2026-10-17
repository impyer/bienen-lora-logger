# SPDX-License-Identifier: GPL-3.0-or-later
"""Real isolated TLS/API/PostgreSQL/browser test with synthetic CSV files.

Requires BIENEN_TEST_DSN for a disposable database literally named bienen_test,
Caddy, Node/Playwright/Chromium and pg_dump/pg_restore. Never contacts ThinkStation.
"""
from datetime import datetime, timedelta, timezone
import argparse
import base64
import hashlib
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import psycopg
from argon2 import PasswordHasher

from support import ROOT, reset_database, source, SOIL_HEADER, WEATHER_HEADER
from stockkarte_admin import seed_demo
from stockkarte_store import write_inspection
from umwelt.ingest import import_source
from umwelt.migrate import migrate


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--caddy', default=shutil.which('caddy'))
    parser.add_argument('--pg-bin', type=Path)
    parser.add_argument('--output', type=Path, default=Path(tempfile.mkdtemp(prefix='bienen-r1-e2e-')))
    parser.add_argument('--long-history', action='store_true', help='35 days, >5000 values through the real stack')
    args = parser.parse_args()
    if not args.caddy:
        parser.error('Caddy executable required')
    work = args.output.resolve();work.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    def pg(name):
        return str(args.pg_bin/name) if args.pg_bin else shutil.which(name)
    if not pg('pg_dump') or not pg('pg_restore'):
        parser.error('pg_dump/pg_restore required')
    conn = reset_database(migrate_environment=False)
    try:
        with conn.cursor() as cur:
            seed_demo(cur)
        colonies = [row[0] for row in conn.execute('SELECT id FROM bienen.volk ORDER BY id').fetchall()]
        write_inspection(conn, volk_id=colonies[0], event_date=datetime.now().date(),
            values={'bl:queen_seen':False,'bl:frames':0}, note='Synthetic pre-migration record',
            author='r1-e2e', reason='Migration preservation probe')
        before = conn.execute('SELECT to_jsonb(r) FROM bienen.sk_durchsicht_revision r').fetchall()
        # Backup before migration and restore to a newly named separate DB.
        dump = work/'before-migration.dump'
        with dump.open('wb') as output:
            subprocess.run([pg('pg_dump'),'--dbname',os.environ['BIENEN_TEST_DSN'],'-Fc','--no-owner','--no-privileges'],env=env,stdout=output,check=True)
        restore_name = 'bienen_r1_restore_' + secrets.token_hex(5)
        conn.execute('CREATE DATABASE ' + restore_name)
        restore_dsn = psycopg.conninfo.make_conninfo(os.environ['BIENEN_TEST_DSN'], dbname=restore_name)
        subprocess.run([pg('pg_restore'),'--dbname',restore_dsn,'--no-owner','--no-privileges',str(dump)],env=env,check=True)
        with psycopg.connect(restore_dsn) as restored:
            assert restored.execute('SELECT to_jsonb(r) FROM bienen.sk_durchsicht_revision r').fetchall() == before
        assert migrate(conn) and not migrate(conn)
        assert conn.execute('SELECT to_jsonb(r) FROM bienen.sk_durchsicht_revision r').fetchall() == before
        stand = conn.execute("INSERT INTO bienen.stand(name) VALUES ('Synthetischer Umwelt-Teststand') RETURNING id").fetchone()[0]
        empty = conn.execute("INSERT INTO bienen.stand(name) VALUES ('Synthetischer Leerstand') RETURNING id").fetchone()[0]
        secret = conn.execute("INSERT INTO bienen.stand(name) VALUES ('Nicht freigegebener synthetischer Stand') RETURNING id").fetchone()[0]
        now = datetime.now(timezone.utc).replace(microsecond=0)
        first, second = now-timedelta(minutes=45), now-timedelta(minutes=15)
        soil = work/'synthetic-soil.csv'
        soil.write_text(SOIL_HEADER + f'{first.isoformat()};synthetic;synthetic-soil;12;;13;3.2;0;1;2;msg-1\n' + f'{second.isoformat()};synthetic;synthetic-soil;14;15;16;3.2;0;2;2;msg-2\n')
        if args.long_history:
            with soil.open('w') as output:
                output.write(SOIL_HEADER)
                for i in range(5040):
                    stamp = second-timedelta(minutes=10*(5039-i))
                    value = 77.125 if i == 5039 else (i % 50)-5
                    middle = '' if i % 31 == 0 else str(value+1)
                    output.write(f'{stamp.isoformat()};synthetic;synthetic-soil;{value};{middle};{value+2};3.2;0;{i};2;long-{i}\n')
        weather = work/'synthetic-weather.csv'
        weather_row = f'{first.isoformat()};synthetic;synthetic-weather;-2.5;;1013;0;0;0;359;0;0;7;1;3;AA;retained\n'
        weather.write_text(WEATHER_HEADER.rstrip('\n') + ';unknown_sensor\n' + weather_row * 2
            + f'{second.isoformat()};synthetic;synthetic-weather;invalid;0;NaN;0;0;0;1;0;0;7;2;3;BB;retained\n'
            + 'invalid-time;synthetic;synthetic-weather;999;0;1013;0;0;0;1;0;0;7;3;3;CC;retained\n')
        sid = source(conn, soil, stand_id=stand)
        wid = source(conn, weather, 's2120', 'weather', stand_id=stand)
        import_source(conn, sid)
        weather_report = import_source(conn, wid)
        assert any(x['code'] == 'ungueltiger_zeitstempel' for x in weather_report['fehler'])
        assert weather_report['unbekannte_spalten'] == ['unknown_sensor']
        assert conn.execute('SELECT count(*) FROM bienen.um_rohdatensatz WHERE quelle_id=%s', (wid,)).fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM bienen.um_rohdatensatz WHERE quelle_id=%s AND felder->>'unknown_sensor'='retained'", (wid,)).fetchone()[0] == 2
        password = secrets.token_urlsafe(30)
        uid = conn.execute('INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id', ('r1_e2e', PasswordHasher().hash(password))).fetchone()[0]
        for colony in colonies:
            conn.execute('INSERT INTO bienen.sk_benutzer_volk VALUES (%s,%s,true,true)', (uid,colony))
        for apiary in (stand,empty):
            conn.execute('INSERT INTO bienen.sk_benutzer_stand VALUES (%s,%s,true)', (uid,apiary))
    finally:
        conn.close()
    port, tls_port = free_port(), free_port()
    origin = f'https://127.0.0.1:{tls_port}'
    env.update(BIENEN_AUTH_DEV_MODE='1',BIENEN_AUTH_DSN=os.environ['BIENEN_TEST_DSN'],
        BIENEN_AUTH_SECRET=secrets.token_urlsafe(48),BIENEN_AUTH_TRUST_DOCKER_PROXY='1',
        XDG_DATA_HOME=str(work/'data'),XDG_CONFIG_HOME=str(work/'config'))
    config=work/'Caddyfile'
    config.write_text(f'{{\n admin off\n skip_install_trust\n auto_https disable_redirects\n default_sni 127.0.0.1\n}}\nhttps://127.0.0.1:{tls_port} {{\n tls internal\n reverse_proxy 127.0.0.1:{port}\n}}\n')
    processes=[]
    try:
        env['PYTHONPATH']=str(ROOT/'server/datenbank')
        commands=[([sys.executable,'-m','uvicorn','stockkarte_dev_web:app','--app-dir',str(ROOT/'server/datenbank'),'--host','127.0.0.1','--port',str(port),'--no-access-log','--no-proxy-headers'],'app.log'),([args.caddy,'run','--config',str(config),'--adapter','caddyfile'],'caddy.log'),([sys.executable,'-m','umwelt.cli','watch','--interval','5'],'importer.log')]
        for command,name in commands:
            with (work/name).open('w') as output:
                processes.append(subprocess.Popen(command,env=env,stdout=output,stderr=subprocess.STDOUT,cwd=ROOT))
        ca=work/'data/caddy/pki/authorities/local/root.crt'
        for _ in range(100):
            try:
                context=ssl.create_default_context(cafile=str(ca))
                with urllib.request.urlopen(origin,context=context,timeout=1) as response:
                    if response.status==200:break
            except (OSError,urllib.error.HTTPError):pass
            time.sleep(.1)
        else:raise RuntimeError('HTTPS stack not ready; inspect app.log/caddy.log')
        pins=[]
        for cert in (ca,ca.with_name('intermediate.crt')):
            public=subprocess.check_output(['openssl','x509','-in',str(cert),'-pubkey','-noout'])
            der=subprocess.check_output(['openssl','pkey','-pubin','-outform','DER'],input=public)
            pins.append(base64.b64encode(hashlib.sha256(der).digest()).decode())
        browser_input={'origin':origin,'username':'r1_e2e','password':password,'user_id':uid,
            'stand_id':stand,'empty_stand':empty,'secret_stand':secret,'soil_source':sid,
            'soil_file':str(soil),'python_path':str(ROOT/'server/datenbank'),
            'new_row':f'{now.isoformat()};synthetic;synthetic-soil;29.5;18;19;3.2;0;3;2;msg-live\n',
            'from':(now-timedelta(days=1)).isoformat(),'to':(now+timedelta(minutes=5)).isoformat(),
            'ca_pins':','.join(pins),'screenshot':str(work/'environment-mobile.png')}
        browser_input['last_known'] = second.isoformat()
        bundle=work/'node-trusted-ca.pem'
        existing_ca=Path(os.environ['NODE_EXTRA_CA_CERTS']).read_bytes() if os.environ.get('NODE_EXTRA_CA_CERTS') else b''
        bundle.write_bytes(existing_ca+b'\n'+ca.read_bytes())
        browser_env=dict(env,R1_PYTHON=sys.executable,R1_BROWSER_INPUT=json.dumps(browser_input),NODE_EXTRA_CA_CERTS=str(bundle))
        browser_script = 'long_browser_e2e.js' if args.long_history else 'browser_e2e.js'
        result=subprocess.run(['node',str(ROOT/'tests/umwelt'/browser_script)],env=browser_env,cwd=ROOT,capture_output=True,text=True,timeout=150)
        safe_output=re.sub(r'(?im)^.*(?:cookie|authorization):.*$', '[sensitive header redacted]', result.stdout+result.stderr)
        (work/'browser.log').write_text(safe_output)
        if result.returncode:
            raise RuntimeError('Browser E2E failed; inspect '+str(work/'browser.log'))
        outcome=json.loads(result.stdout.strip().splitlines()[-1])
        outcome.update(backup_restore='PASS',migration_preserves_existing_revisions=True,
                       restore_database=restore_name,https_ca_verified=True)
        (work/'result.json').write_text(json.dumps(outcome,indent=2)+'\n')
        print(json.dumps(outcome,ensure_ascii=False))
    finally:
        for process in reversed(processes):
            process.terminate();process.wait(timeout=15)


if __name__=='__main__':
    main()
