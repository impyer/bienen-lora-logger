# SPDX-License-Identifier: GPL-3.0-or-later
"""Explizite Administration der isolierten Heimnetz-TESTdatenbank.

Kein Standardkonto und keine automatische Berechtigungsvergabe.
Ruft vor allen Schreibbefehlen die aktuelle Datenbankbezeichnung ab.
"""
from __future__ import annotations
import argparse
import getpass
import os
import re
from argon2 import PasswordHasher
import psycopg
from psycopg.types.json import Jsonb


def test_connection():
    dsn = os.environ.get('BIENEN_AUTH_DSN', '')
    if not dsn:
        raise SystemExit('ABBRUCH: BIENEN_AUTH_DSN fehlt')
    conn = psycopg.connect(dsn)
    with conn.cursor() as cur:
        cur.execute('SELECT current_database()')
        database = cur.fetchone()[0]
    if database != 'bienenlogger_test':
        conn.close()
        raise SystemExit(f'ABBRUCH: Nicht die isolierte Testdatenbank ({database})')
    return conn


def seed_demo(cur):
    for name in ('Testvolk A', 'Testvolk B'):
        cur.execute('SELECT id FROM bienen.volk WHERE name=%s ORDER BY id LIMIT 1', (name,))
        if cur.fetchone() is None:
            cur.execute('INSERT INTO bienen.volk(name) VALUES (%s)', (name,))
    definitions = [
        ('bl:queen_seen', 'Königin gesehen', 'boolean', False, {}),
        ('bl:frames', 'Brutwaben', 'number_0_decimals', True, {'min':0,'max':20}),
        ('bl:varroa', 'Varroa-Methode', 'select', False, {}),
        ('bl:fall', 'Natürlicher Varroafall je Tag', 'number_2_decimals', False, {'min':0}),
        ('bl:food', 'Futtervorrat (kg)', 'number_2_decimals', False, {'min':0}),
        ('bl:note', 'Beobachtung', 'text', False, {}),
    ]
    for ident,name,kind,required,meta in definitions:
        cur.execute('''INSERT INTO bienen.sk_kategorie(id,bezeichnung,eingabetyp,pflicht,meta)
                       VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING''',
                    (ident,name,kind,required,Jsonb(meta)))
    for position,(ident,name) in enumerate([('bl:powder','Puderzucker'),('bl:wash','Auswaschen'),('bl:oxal','Oxalsäure')],1):
        cur.execute('''INSERT INTO bienen.sk_option(id,kategorie_id,bezeichnung,reihenfolge)
                       VALUES (%s,'bl:varroa',%s,%s) ON CONFLICT (id) DO NOTHING''',
                    (ident,name,position))
    cur.execute('''INSERT INTO bienen.sk_checkliste(schluessel,name)
                   VALUES ('beispiel-durchsicht','Beispiel-Durchsicht (synthetischer Katalog)')
                   ON CONFLICT (schluessel) DO NOTHING''')
    cur.execute("SELECT id FROM bienen.sk_checkliste WHERE schluessel='beispiel-durchsicht'")
    cid=cur.fetchone()[0]
    cur.execute('''INSERT INTO bienen.sk_checkliste_version(checkliste_id,version,begruendung)
                   VALUES (%s,1,'Explizite Testdaten') ON CONFLICT DO NOTHING''',(cid,))
    for pos,(ident,required) in enumerate([('bl:queen_seen',False),('bl:frames',True),('bl:varroa',False),
                                          ('bl:fall',False),('bl:food',False),('bl:note',False)],1):
        cur.execute('''INSERT INTO bienen.sk_checkliste_feld(checkliste_id,version,kategorie_id,position,pflicht)
                       VALUES (%s,1,%s,%s,%s) ON CONFLICT DO NOTHING''',(cid,ident,pos,required))
    print('Synthetische Testvölker und Testkatalog vorbereitet. Kein BEEP-Import.')


def main():
    parser=argparse.ArgumentParser(description='Eigene Heimnetz-Testdatenbank verwalten')
    sub=parser.add_subparsers(dest='operation',required=True)
    sub.add_parser('seed-demo')
    sub.add_parser('list-colonies')
    sub.add_parser('list-users')
    user=sub.add_parser('create-user');user.add_argument('username')
    grant=sub.add_parser('grant');grant.add_argument('username');grant.add_argument('colony_id',type=int)
    grant.add_argument('right',choices=['read','write'])
    revoke=sub.add_parser('revoke');revoke.add_argument('username');revoke.add_argument('colony_id',type=int)
    args=parser.parse_args()
    with test_connection() as conn:
        with conn.cursor() as cur:
            if args.operation=='seed-demo':
                seed_demo(cur)
            elif args.operation=='list-colonies':
                cur.execute('SELECT id,name FROM bienen.volk ORDER BY id')
                for ident,name in cur.fetchall():print(ident,name)
            elif args.operation=='list-users':
                cur.execute('SELECT id,benutzername,aktiv FROM bienen.sk_benutzer ORDER BY id')
                for ident,name,active in cur.fetchall():print(ident,name,'aktiv' if active else 'gesperrt')
            elif args.operation=='create-user':
                if not re.fullmatch(r'[a-z0-9_.-]{3,80}',args.username):
                    raise SystemExit('Benutzername ungültig')
                password=getpass.getpass('Passwort (mind. 14 Zeichen): ')
                confirm=getpass.getpass('Wiederholen: ')
                if password!=confirm or len(password)<14:
                    raise SystemExit('Passwortabweichung oder Passwort zu kurz')
                cur.execute('INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id',
                            (args.username,PasswordHasher().hash(password)))
                print('Neuer Benutzer:',cur.fetchone()[0],'- zunächst OHNE Völkerrecht')
            else:
                cur.execute('SELECT id FROM bienen.sk_benutzer WHERE benutzername=%s AND aktiv',(args.username,))
                row=cur.fetchone()
                if not row:raise SystemExit('Aktiver Benutzer nicht gefunden')
                cur.execute('SELECT id FROM bienen.volk WHERE id=%s',(args.colony_id,))
                if not cur.fetchone():raise SystemExit('Volk-ID nicht gefunden')
                if args.operation=='grant':
                    write=args.right=='write'
                    cur.execute('''INSERT INTO bienen.sk_benutzer_volk(benutzer_id,volk_id,darf_lesen,darf_schreiben)
                        VALUES (%s,%s,true,%s) ON CONFLICT(benutzer_id,volk_id)
                        DO UPDATE SET darf_lesen=true,darf_schreiben=EXCLUDED.darf_schreiben''',
                        (row[0],args.colony_id,write))
                    print(args.username,'Volk',args.colony_id,args.right)
                else:
                    cur.execute('DELETE FROM bienen.sk_benutzer_volk WHERE benutzer_id=%s AND volk_id=%s',
                                (row[0],args.colony_id))
                    cur.execute('''UPDATE bienen.sk_sitzung SET widerrufen_am=now()
                                   WHERE benutzer_id=%s AND widerrufen_am IS NULL''',(row[0],))
                    print('Recht entzogen und Sitzungen widerrufen:',args.username,args.colony_id)


if __name__=='__main__':main()
