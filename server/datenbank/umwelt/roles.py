# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit admin provisioning, separate from migrations and import execution."""
import re
from psycopg import sql

READ = ('um_quelle','um_quelle_kanal','kanal','geraet_zuordnung','um_rohdatensatz',
        'um_ereignis_revision','um_messwert_revision','um_archiv_datei','um_roh_fundstelle','um_checkpoint','um_import_lauf')
APPEND = ('um_rohdatensatz','um_ereignis_revision','um_messwert_revision','um_roh_fundstelle','um_import_lauf')
CHECKPOINT = ('um_archiv_datei','um_checkpoint')


def provision_importer(conn,role,password):
    if conn.info.dbname not in {'bienen_test','bienenlogger_test'}:
        raise ValueError('Import-Login nur in isolierter Testdatenbank')
    if not re.fullmatch(r'bl_um_[a-z0-9_]{1,40}',role) or not 24<=len(password)<=200 or '\n' in password:
        raise ValueError('Eigenes bl_um_ Login und privates Passwort (24–200 Zeichen) erforderlich')
    with conn.transaction():
        conn.execute('SELECT pg_advisory_xact_lock(714005)')
        existing=conn.execute('''SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls
            FROM pg_roles WHERE rolname=%s''',(role,)).fetchone()
        if existing and any(existing):raise ValueError('Bestehende privilegierte Rolle nicht umstellen')
        if existing and conn.execute('SELECT 1 FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=%s)',(role,)).fetchone():
            raise ValueError('Bestehende Rollenmitgliedschaften untersuchen')
        identifier=sql.Identifier(role)
        if not existing:conn.execute(sql.SQL('CREATE ROLE {} LOGIN').format(identifier))
        verifier=conn.pgconn.encrypt_password(password.encode(),role.encode(),b'scram-sha-256').decode()
        conn.execute(sql.SQL('ALTER ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}').format(identifier,sql.Literal(verifier)))
        conn.execute(sql.SQL('GRANT CONNECT,TEMPORARY ON DATABASE {} TO {}').format(sql.Identifier(conn.info.dbname),identifier))
        conn.execute(sql.SQL('GRANT USAGE ON SCHEMA bienen TO {}').format(identifier))
        for operation,tables in [('SELECT',READ),('INSERT',APPEND),('INSERT,UPDATE',CHECKPOINT)]:
            for table in tables:
                conn.execute(sql.SQL('GRANT '+operation+' ON bienen.{} TO {}').format(sql.Identifier(table),identifier))
        for sequence in ['um_rohdatensatz_id_seq','um_import_lauf_id_seq','um_archiv_datei_id_seq']:
            conn.execute(sql.SQL('GRANT USAGE ON SEQUENCE bienen.{} TO {}').format(sql.Identifier(sequence),identifier))
