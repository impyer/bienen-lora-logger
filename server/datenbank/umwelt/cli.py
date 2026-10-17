# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit CLI for the isolated R1 test stack; no receiver configuration edits."""
import argparse
import json
import os
import sys
import time

import psycopg

from .ingest import import_source, register_source
from .migrate import migrate
from .roles import provision_importer


def main():
    parser = argparse.ArgumentParser(description='Bienenlogger Umwelt-Teststack verwalten')
    sub = parser.add_subparsers(dest='operation', required=True)
    sub.add_parser('migrate', help='Additive Migration explizit anwenden, nach Backup/Restore')
    sub.add_parser('inventory', help='Nur lesende DB-Inventur, keine Dateipfade oder Geheimnisse')
    inspect=sub.add_parser('inspect-config',help='Explizite synthetische CSV-Konfiguration nur lesend inventarisieren')
    inspect.add_argument('--config',required=True)
    login = sub.add_parser('import-login', help='Expliziter Admin-Schritt für isolierten Import-Login')
    login.add_argument('--role',required=True)
    login.add_argument('--password-stdin',action='store_true',required=True)
    add = sub.add_parser('source', help='Eine ausdrücklich freigegebene Datei registrieren')
    add.add_argument('--config', required=True, help='Lokale JSON-Datei mit expliziten IDs und Pfad')
    run = sub.add_parser('import')
    run.add_argument('--source-id', required=True, type=int)
    watch = sub.add_parser('watch')
    watch.add_argument('--interval', type=int, default=60)
    grant = sub.add_parser('grant-stand')
    grant.add_argument('--username', required=True)
    grant.add_argument('--stand-id', required=True, type=int)
    args = parser.parse_args()
    if args.operation=='inspect-config':
        from .inventory import inspect_config
        with open(args.config,encoding='utf-8') as file:config=json.load(file)
        print(json.dumps(inspect_config(config),ensure_ascii=False))
        return
    dsn = os.environ.get('BIENEN_IMPORT_DSN') if args.operation in {'import','watch'} else os.environ.get('BIENEN_AUTH_DSN') or os.environ.get('BIENEN_TEST_DSN')
    if not dsn:
        parser.error('Import/watch benötigt BIENEN_IMPORT_DSN; Admin benötigt BIENEN_AUTH_DSN oder BIENEN_TEST_DSN')
    with psycopg.connect(dsn, autocommit=True) as conn:
        if conn.info.dbname not in {'bienen_test', 'bienenlogger_test'}:
            parser.error('R1-CLI nur auf expliziter isolierter Testdatenbank erlaubt')
        if args.operation == 'migrate':
            print(json.dumps({'migration_applied': migrate(conn)}))
        elif args.operation == 'inventory':
            print(json.dumps({
                'stands':conn.execute('SELECT id,name FROM bienen.stand ORDER BY id').fetchall(),
                'devices':conn.execute('SELECT id,name,art FROM bienen.geraet ORDER BY id').fetchall(),
                'sources':conn.execute('SELECT id,schluessel,profil,stand_id,geraet_id,synthetisch,archiv_muster FROM bienen.um_quelle ORDER BY id').fetchall(),
                'channels':conn.execute('SELECT id,geraet_id,quellfeld,messgroesse_code,status FROM bienen.kanal ORDER BY id').fetchall()
            },ensure_ascii=False))
        elif args.operation == 'import-login':
            password=sys.stdin.readline(202).removesuffix('\n')
            provision_importer(conn,args.role,password)
            print('Eingeschränktes Import-Login eingerichtet')
        elif args.operation == 'source':
            with open(args.config, encoding='utf-8') as file:
                config = json.load(file)
            print(json.dumps({'source_id': register_source(conn, **config)}))
        elif args.operation == 'import':
            print(json.dumps(import_source(conn, args.source_id), ensure_ascii=False))
        elif args.operation == 'grant-stand':
            user = conn.execute('SELECT id FROM bienen.sk_benutzer WHERE benutzername=%s AND aktiv', (args.username,)).fetchone()
            if not user:
                parser.error('Aktiver Benutzer existiert nicht')
            conn.execute('''INSERT INTO bienen.sk_benutzer_stand(benutzer_id,stand_id,darf_lesen)
                VALUES (%s,%s,true) ON CONFLICT (benutzer_id,stand_id) DO UPDATE SET darf_lesen=true''', (user[0], args.stand_id))
            print('Explizites Stand-Leserecht eingerichtet')
        else:
            if not 5 <= args.interval <= 3600:
                parser.error('Importintervall muss zwischen 5 und 3600 Sekunden liegen')
            while True:
                for (source_id,) in conn.execute('SELECT id FROM bienen.um_quelle ORDER BY id').fetchall():
                    try:
                        report = import_source(conn, source_id)
                        print(json.dumps({'source_id':source_id, 'result':report}), flush=True)
                    except Exception:
                        print(json.dumps({'source_id':source_id, 'error':'Import fehlgeschlagen; Status in der Umweltansicht prüfen'}), flush=True)
                time.sleep(args.interval)


if __name__ == '__main__':
    main()
