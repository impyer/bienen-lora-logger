# SPDX-License-Identifier: GPL-3.0-or-later
"""Temporary admission outage ONLY for the owned browser fixture bienen_test.

A separate postgres admin connection restores access on stdin/timeout/exception.
No schema/data changes, no receiver or production services. Test helper only.
"""
import os
import select
import sys
import psycopg


def main():
    dsn=os.environ['BIENEN_TEST_DSN']
    with psycopg.connect(dsn) as fixture:
        if fixture.info.dbname!='bienen_test' or not fixture.execute("SELECT 1 FROM bienen.sk_benutzer WHERE benutzername='r1_e2e'").fetchone():
            raise RuntimeError('Owned E2E fixture required')
    with psycopg.connect(psycopg.conninfo.make_conninfo(dsn,dbname='postgres'),autocommit=True) as admin:
        try:
            admin.execute('ALTER DATABASE bienen_test WITH ALLOW_CONNECTIONS false')
            admin.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='bienen_test'")
            print('ready',flush=True)
            if select.select([sys.stdin],[],[],20)[0]:sys.stdin.readline()
        finally:
            admin.execute('ALTER DATABASE bienen_test WITH ALLOW_CONNECTIONS true')


if __name__=='__main__':main()
