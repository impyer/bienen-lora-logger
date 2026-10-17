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
        if existing:
            allowed={table:{'SELECT'} for table in READ}
            for table in APPEND:allowed[table].add('INSERT')
            for table in CHECKPOINT:allowed[table].update({'INSERT','UPDATE'})
            privileges=conn.execute('''SELECT table_schema,table_name,privilege_type
                FROM information_schema.table_privileges WHERE grantee=%s
                UNION SELECT table_schema,table_name,privilege_type
                FROM information_schema.column_privileges WHERE grantee=%s''',(role,role)).fetchall()
            if any(schema!='bienen' or privilege not in allowed.get(table,set()) for schema,table,privilege in privileges):
                raise ValueError('Bestehende zusätzliche Tabellenrechte untersuchen')
            if conn.execute('SELECT 1 FROM pg_namespace WHERE has_schema_privilege(%s,oid,\'CREATE\') AND nspname NOT LIKE \'pg_temp_%%\' AND nspname NOT LIKE \'pg_toast_temp_%%\' LIMIT 1',(role,)).fetchone():
                raise ValueError('Bestehende permanente Schema-Erstellrechte untersuchen')
            if conn.execute("SELECT has_database_privilege(%s,current_database(),'CREATE')",(role,)).fetchone()[0]:
                raise ValueError('Bestehende Datenbank-Erstellrechte untersuchen')
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
