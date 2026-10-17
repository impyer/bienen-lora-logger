# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic fixtures and guarded disposable database setup."""
from pathlib import Path
import os
import sys

import psycopg

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'server/datenbank'))
from umwelt.migrate import migrate
from umwelt.ingest import register_source

SOIL_HEADER = 'time_utc;stand;device_id;temp_5cm;temp_20cm;temp_50cm;battery_v;alarm_status;f_cnt;f_port;message_id\n'
WEATHER_HEADER = 'zeit_utc;stand;station;t;h;p_hpa;l;uv;wind_ms;wind_dir_deg;gust_ms;rain_mmh;rain_mm;f_cnt;f_port;payload_hex\n'


def reset_database(*, migrate_environment=True):
    conn = psycopg.connect(os.environ['BIENEN_TEST_DSN'], autocommit=True)
    if conn.info.dbname != 'bienen_test':
        conn.close()
        raise RuntimeError('Refuse destructive fixtures outside bienen_test')
    for file in ['schema.sql', 'migrations/001_stockkarte.sql', 'migrations/002_stockkarte_benutzer.sql']:
        conn.execute((ROOT / 'server/datenbank' / file).read_text())
    if migrate_environment:
        migrate(conn)
    return conn


def source(conn, path, profile='boden', key='soil', stand_id=None, device_id=None):
    stand_id = stand_id or conn.execute("INSERT INTO bienen.stand(name) VALUES ('Synthetischer Teststand') RETURNING id").fetchone()[0]
    device_id = device_id or conn.execute('INSERT INTO bienen.geraet(name,art) VALUES (%s,%s) RETURNING id', ('synthetic-' + key, 'boden' if profile == 'boden' else 'wetter')).fetchone()[0]
    return register_source(conn, key=key, profile=profile, path=path,
        stand_id=stand_id, device_id=device_id, source_stand='synthetic',
        source_device='synthetic-' + key, synthetic=True,
        valid_from='2026-01-01T00:00:00Z', time_quality='empfang' if profile == 's2120' else 'unbekannt')


def soil_row(time='2026-10-25T00:30:00Z', values='12;;13', ident='msg-1', device='synthetic-soil'):
    return f'{time};synthetic;{device};{values};3.2;0;1;2;{ident}\n'
