# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit synthetic yearly load, actual streaming import and authenticated API.

Destructively resets ONLY the guarded disposable bienen_test fixture database.
No receiver, private files or production host. Run separately from other DB tests.
"""
from datetime import datetime,timedelta,timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import secrets
import time

from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from support import reset_database,source,SOIL_HEADER,WEATHER_HEADER
from stockkarte_session_api import create_session_app
from umwelt.ingest import import_source,register_source
from umwelt.roles import provision_importer
import psycopg


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    work=args.output.resolve();work.mkdir(parents=True,exist_ok=False)
    soil=work/'soil';weather=work/'weather';soil.mkdir();weather.mkdir()
    start=datetime(2026,1,1,tzinfo=timezone.utc);files={};counts={'soil':0,'weather':0}
    try:
        for index in range(365*24*4):
            stamp=start+timedelta(minutes=15*index);month=stamp.strftime('%Y-%m')
            key=('soil',month)
            if key not in files:
                f=(soil/('soil-'+month+'.csv')).open('w');f.write(SOIL_HEADER.rstrip('\n')+';unknown_sensor\n');files[key]=f
            # A retained unknown payload exercises bounded batches (~147 MiB/year).
            middle='' if index%31==0 else str(index%40)
            files[key].write(f'{stamp.isoformat()};synthetic;synthetic-soil;{index%50};{middle};{index%35};3.2;0;{index};2;year-{index};'+('x'*4096)+'\n');counts['soil']+=1
            if index%4==0:
                key=('weather',month)
                if key not in files:
                    f=(weather/('weather-'+month+'.csv')).open('w');f.write(WEATHER_HEADER);files[key]=f
                files[key].write(f'{stamp.isoformat()};synthetic;synthetic-weather;-2.5;80;1013;0;0;0;359;0;0;7;{index};3;AA\n');counts['weather']+=1
    finally:
        for f in files.values():f.close()
    paths=sorted(soil.glob('*.csv'))+sorted(weather.glob('*.csv'))
    def fingerprints():
        result={}
        for p in paths:
            s=p.stat();h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
            result[p.name]=(h,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ino)
        return result
    before=fingerprints();conn=reset_database();phases={}
    try:
        old=source(conn,next(soil.glob('*.csv')));stand,device=conn.execute('SELECT stand_id,geraet_id FROM bienen.um_quelle WHERE id=%s',(old,)).fetchone()
        base=dict(path=soil,pattern='soil-{YYYY}-{MM}.csv',stand_id=stand,device_id=device,source_stand='synthetic',source_device='synthetic-soil',synthetic=True,valid_from=start.isoformat(),time_quality='unbekannt')
        sid=register_source(conn,key='annual-soil',profile='boden',interval_seconds=900,**base)
        wid_old=source(conn,next(weather.glob('*.csv')),'s2120','weather',stand_id=stand)
        did=conn.execute('SELECT geraet_id FROM bienen.um_quelle WHERE id=%s',(wid_old,)).fetchone()[0]
        wid=register_source(conn,key='annual-weather',profile='s2120',interval_seconds=3600,**dict(base,path=weather,pattern='weather-{YYYY}-{MM}.csv',device_id=did,source_device='synthetic-weather',time_quality='empfang'))
        secret=secrets.token_urlsafe(32);provision_importer(conn,'bl_um_annual',secret)
        dsn=psycopg.conninfo.make_conninfo(os.environ['BIENEN_TEST_DSN'],user='bl_um_annual',password=secret)
        with psycopg.connect(dsn,autocommit=True) as importer:
            for name,ident in [('soil',sid),('weather',wid)]:
                tick=time.monotonic();report=import_source(importer,ident);phases[name]={'seconds':round(time.monotonic()-tick,3),'report':report};print(name,phases[name]['seconds'],flush=True)
            tick=time.monotonic();assert import_source(importer,sid)['unveraendert'];assert import_source(importer,wid)['unveraendert'];phases['unchanged_seconds']=round(time.monotonic()-tick,3)
            # Actual >32-MiB single file and append suffix: replay an existing
            # archive month enlarged with additional unknown payload bytes.
            large=next(soil.glob('*.csv'))
            with large.open('a') as f:
                for i in range(8500):
                    stamp=start+timedelta(seconds=i,microseconds=500)
                    f.write(f'{stamp.isoformat()};synthetic;synthetic-soil;1;2;3;3.2;0;{i};2;large-{i};'+('z'*4096)+'\n')
            assert large.stat().st_size>32*1024*1024
            tick=time.monotonic();report=import_source(importer,sid);assert report['datensaetze']==8500
            phases['large_append']={'bytes':large.stat().st_size,'seconds':round(time.monotonic()-tick,3),'records':report['datensaetze']}
        assert fingerprints()!=before # test driver intentionally appended only its synthetic file
        after=fingerprints()
        for name,fp in before.items():
            if name!=large.name:assert after[name]==fp
        # Validate unchanged input after a fresh import as well.
        retained=after;import_source(conn,sid);assert fingerprints()==retained
        uid=conn.execute('INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id',('annual-synthetic',PasswordHasher().hash(secret))).fetchone()[0]
        conn.execute('INSERT INTO bienen.sk_benutzer_stand VALUES (%s,%s,true)',(uid,stand))
        conn.execute('ANALYZE bienen.um_messwert_revision');conn.execute('ANALYZE bienen.um_rohdatensatz');conn.execute('ANALYZE bienen.um_ereignis_revision')
        app=create_session_app(dsn=os.environ['BIENEN_TEST_DSN'],enabled=True,secret=secrets.token_urlsafe(48))
        with TestClient(app,base_url='https://testserver') as client:
            assert client.post('/api/v1/stockkarte/session/login',json={'username':'annual-synthetic','password':secret}).status_code==200
            ids=[r[0] for r in conn.execute("SELECT kanal_id FROM bienen.um_quelle_kanal WHERE quelle_id=%s AND quellfeld LIKE 'temp_%%'",(sid,))]
            params=dict(stand_id=stand,von=start.isoformat(),bis=(start+timedelta(days=365)).isoformat(),kanal_id=ids,resolution='auto',limit=5000)
            tick=time.monotonic();points=0;pages=0;bytes_out=0
            while True:
                response=client.get('/api/v1/umwelt/zeitreihen',params=params)
                assert response.status_code==200,response.text
                data=response.json();points+=data['returned_points'];pages+=1;bytes_out+=len(response.content)
                assert data['returned_points']<=5000 and data['total_points']<=40000
                if not data['next_cursor']:break
                params['cursor']=data['next_cursor']
            assert points==data['total_points'];assert data['source_points']==(35040+8500)*3
            phases['year_api']={'seconds':round(time.monotonic()-tick,3),'source_points':data['source_points'],'rendered_points':points,'pages':pages,'response_bytes':bytes_out}
        result={'result':'PASS','synthetic':True,'files':len(paths),'records':counts,'bytes_before':sum(fp[2] for fp in before.values()),'phases':phases,
            'python_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'postgres':conn.execute('SHOW server_version').fetchone()[0],
            'limits':'One year, two streams, temperature API subset. No multiuser/production throughput claim; PostgreSQL/Caddy RSS excluded.'}
        (work/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    finally:conn.close()


if __name__=='__main__':main()
