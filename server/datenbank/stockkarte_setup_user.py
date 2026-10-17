# SPDX-License-Identifier: GPL-3.0-or-later
"""Nur bewusst manuell nutzbare lokale Einrichtung, KEIN Start-up-Seeder.

Beispiel: BIENEN_TEST_DSN=... python3 server/datenbank/stockkarte_setup_user.py
Schreibt ausschließlich mit expliziter DB-Konfiguration, nie in CI oder beim Start.
Passwort kommt via getpass (nicht als CLI-Argument oder Shell-History).
"""
from __future__ import annotations
import getpass
import os
import re
from psycopg import connect
from argon2 import PasswordHasher

def main():
    dsn=os.environ.get("BIENEN_AUTH_DSN")
    if not dsn:
        raise SystemExit("BIENEN_AUTH_DSN fehlt; kein Benutzer angelegt")
    name=input("Neuen Benutzernamen (a-z/0-9/._-): ").strip()
    if not re.fullmatch(r"[a-z0-9_.-]{3,80}",name):
        raise SystemExit("Benutzername ungültig")
    password=getpass.getpass("Passwort: ")
    confirm=getpass.getpass("Passwort wiederholen: ")
    if password!=confirm or len(password)<14:
        raise SystemExit("Passwortabweichung oder Passwort kürzer als 14 Zeichen")
    h=PasswordHasher().hash(password)
    with connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES (%s,%s) RETURNING id",(name,h))
            ident=cur.fetchone()[0]
    print("Benutzer angelegt:",ident,"– zunächst ohne Zugriff auf Völker")
    print("Völkerrechte separat nach Betreiberprüfung setzen; keine pauschale Freigabe.")
if __name__=="__main__":
    main()
