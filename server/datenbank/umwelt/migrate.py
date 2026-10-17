# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit, transactional, checksum-checked migration. Never a schema rebuild."""
from pathlib import Path
import hashlib


def migrate(conn):
    if conn.info.dbname not in {'bienen_test', 'bienenlogger_test'}:
        raise ValueError('R1-Migration nur auf expliziter isolierter Testdatenbank erlaubt')
    if not conn.execute("SELECT to_regclass('bienen.sk_sitzung') IS NOT NULL").fetchone()[0]:
        raise ValueError('Grundschema und SK-001/SK-002 fehlen; Initialisierung untersuchen, keinen Bestand neu aufbauen')
    path = Path(__file__).resolve().parents[1] / 'migrations/003_umwelt.sql'
    content = path.read_text(encoding='utf-8')
    digest = hashlib.sha256(content.encode()).hexdigest()
    with conn.transaction():
        conn.execute('SELECT pg_advisory_xact_lock(714003)')
        conn.execute('CREATE TABLE IF NOT EXISTS bienen.schema_migration (kennung text PRIMARY KEY, sha256 text NOT NULL, angewandt_am timestamptz NOT NULL DEFAULT now())')
        row = conn.execute('SELECT sha256 FROM bienen.schema_migration WHERE kennung=%s', (path.name,)).fetchone()
        if row:
            if row[0] != digest:
                raise ValueError('Migration wurde nach Anwendung verändert; nicht automatisch fortsetzen')
            return False
        conn.execute(content)
        conn.execute('INSERT INTO bienen.schema_migration(kennung,sha256) VALUES (%s,%s)', (path.name, digest))
    return True
