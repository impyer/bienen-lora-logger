# SPDX-License-Identifier: GPL-3.0-or-later
"""Integrationstest ausschließlich auf disposable PostgreSQL-16-DB bienen_test.

ACHTUNG: schema.sql löscht das Schema bienen! Schutz durch DB-Namensprüfung.
"""
import os
from pathlib import Path
import sys

import psycopg
from psycopg import errors
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server" / "datenbank"))
from stockkarte_store import write_inspection, write_queen_revision, current_inspections  # noqa: E402

DSN = os.environ.get("BIENEN_TEST_DSN")
if not DSN:
    raise SystemExit("BIENEN_TEST_DSN für isolierte Testdatenbank erforderlich")
count = 0


def check(ok, label):
    global count
    assert ok, label
    count += 1
    print("PASS", label)


def must_fail(fn, label, error=ValueError):
    try:
        fn()
    except error:
        check(True, label)
    else:
        check(False, label)


def scalar(conn, sql, args=()):
    return conn.execute(sql, args).fetchone()[0]


def setup(conn):
    # Vor JEDER potentiell destruktiven Ausführung sicherstellen, dass dies
    # wirklich unsere wegwerfbare CI-Datenbank ist.
    database = scalar(conn, "SELECT current_database()")
    if database != "bienen_test":
        raise RuntimeError("Refuse destructive base schema outside bienen_test: " + database)
    conn.execute((ROOT / "server/datenbank/schema.sql").read_text(encoding="utf-8"))
    conn.execute((ROOT / "server/datenbank/migrations/001_stockkarte.sql").read_text(encoding="utf-8"))


def main():
    with psycopg.connect(DSN, autocommit=True) as con:
        setup(con)
        v = scalar(con, "INSERT INTO bienen.volk(name) VALUES ('Demo-Volk') RETURNING id")
        queen = scalar(con, "INSERT INTO bienen.koenigin(jahrgang,farbe) VALUES (2026,'weiß') RETURNING id")
        check(v > 0 and queen > 0, "Bestehende biologische IDs werden referenziert")
        con.execute(
            """INSERT INTO bienen.sk_kategorie(id,bezeichnung,eingabetyp,pflicht,meta)
               VALUES ('bl:koenigin','Königin gesehen','boolean',true,'{}'),
                      ('bl:brut','Brutwaben','number_0_decimals',true,%s),
                      ('bl:methode','Behandlung','select',false,'{}'),
                      ('bl:kommentar','Befund','text',false,'{}'),
                      ('bl:datum','Befunddatum','date',false,'{}')""",
            (Jsonb({"min":0,"max":20}),),
        )
        con.execute(
            """INSERT INTO bienen.sk_option(id,kategorie_id,bezeichnung,reihenfolge)
               VALUES ('bl:oxal','bl:methode','Oxalsäure',1),
                      ('bl:varro','bl:methode','VarroMed',2)"""
        )
        cl = scalar(
            con, "INSERT INTO bienen.sk_checkliste(schluessel,name) VALUES ('winter','Winterkontrolle') RETURNING id"
        )
        con.execute(
            """INSERT INTO bienen.sk_checkliste_version(checkliste_id,version,begruendung)
               VALUES (%s,1,'Angelegt'),(%s,2,'Umgeordnet')""", (cl, cl)
        )
        con.execute(
            """INSERT INTO bienen.sk_checkliste_feld(checkliste_id,version,kategorie_id,position,pflicht)
               VALUES (%s,1,'bl:koenigin',1,true),(%s,1,'bl:brut',2,true),
                      (%s,1,'bl:methode',3,false),(%s,2,'bl:brut',1,true),
                      (%s,2,'bl:koenigin',2,true)""",
            (cl, cl, cl, cl, cl),
        )
        check(scalar(con, "SELECT count(*) FROM bienen.sk_checkliste_feld") == 5, "Checklisten-Versionen behalten eigene Reihenfolge")
        values = {"bl:koenigin":False, "bl:brut":0, "bl:methode":"bl:oxal"}
        entry, rev, new = write_inspection(
            con, volk_id=v, event_date="2026-10-16", accuracy="nur_datum",
            checklist=(cl,1), values=values, note="Nur Datum belegt",
            author="demo", reason="Neue Durchsicht"
        )
        check((rev, new) == (1, True), "Durchsicht wird erstmals angelegt")
        row = con.execute(
            "SELECT ereignis_datum,ereignis_zeit,zeitgenauigkeit,werte FROM bienen.sk_durchsicht_revision WHERE durchsicht_id=%s",
            (entry,)
        ).fetchone()
        check(str(row[0]) == "2026-10-16" and row[1] is None and row[2] == "nur_datum",
              "BEEP-Datum ohne erfundene Uhrzeit")
        check(row[3]["bl:koenigin"] is False and row[3]["bl:brut"] == 0,
              "NULL, false und 0 bleiben unterscheidbar")
        correction = {"bl:koenigin":True,"bl:brut":2,"bl:methode":"bl:varro"}
        revised = write_inspection(
            con, entry_id=entry, expected_revision=1, event_date="2026-10-16",
            accuracy="exakt", event_time="2026-10-16T14:10:00+02:00",
            checklist=(cl,1), values=correction, note="Korrigiert",
            author="demo", reason="Wert berichtigt"
        )
        check(revised == (entry,2,True), "Korrektur legt ausschließlich neue Revision an")
        versions = con.execute(
            "SELECT revision,werte FROM bienen.sk_durchsicht_revision WHERE durchsicht_id=%s ORDER BY revision",
            (entry,)
        ).fetchall()
        check(len(versions) == 2 and versions[0][1] == values and versions[1][1] == correction,
              "Beide historischen Fassungen bleiben lesbar")
        check(len(current_inspections(con,v)) == 1 and current_inspections(con,v)[0][1] == 2,
              "Aktuelle Ansicht zeigt letzte Revision")
        must_fail(
            lambda: write_inspection(con, entry_id=entry, expected_revision=1,
                                     event_date="2026-10-16", values=correction,
                                     author="demo", reason="veraltete Änderung"),
            "Konkurrierende Änderung mit alter Versionsnummer abgewiesen"
        )
        must_fail(
            lambda: write_inspection(con, entry_id=entry, expected_revision=2,
                                     event_date="2026-10-16",
                                     values={"bl:koenigin":True,"bl:brut":3,"bl:methode":"falsch"},
                                     author="demo", reason="ungültige Option"),
            "Unbekannte Option wird serverseitig abgewiesen"
        )
        must_fail(
            lambda: write_inspection(con, entry_id=entry, expected_revision=2,
                                     event_date="2026-10-16",
                                     values={"bl:koenigin":True,"bl:brut":21},
                                     author="demo", reason="Zahl außerhalb des Bereichs"),
            "Zahlenbereich auch ohne Browser validiert"
        )
        must_fail(
            lambda: write_inspection(con, entry_id=entry, expected_revision=2,
                                     event_date="2026-10-16", values={"bl:brut":1},
                                     checklist=(cl,1), author="demo", reason="Pflichtfeld fehlt"),
            "Pflichtfelder der gewählten Checkliste erzwungen"
        )
        must_fail(
            lambda: write_inspection(con,volk_id=v,event_date="2026-10-16",
                                     event_time="2026-10-16T12:00:00+02:00",
                                     accuracy="nur_datum",values={},
                                     author="demo",reason="synthetische Uhrzeit"),
            "Nur-Datum schließt Uhrzeit aus"
        )
        must_fail(
            lambda: write_inspection(con,volk_id=v,event_date="2026-10-16",
                                     event_time="2026-10-17T12:00:00+02:00",
                                     accuracy="exakt",values={},
                                     author="demo",reason="Zeitversatz"),
            "Widerspruch zwischen lokalem Tag und Zeitpunkt erkannt"
        )
        must_fail(
            lambda: write_inspection(con,volk_id=v,event_date="2026-10-16",
                                     event_time="2026-10-16T12:00:00",
                                     accuracy="exakt",values={},
                                     author="demo",reason="Zeit ohne Offset"),
            "Zeitstempel ohne Zeitzone wird abgewiesen"
        )
        imported = dict(volk_id=v,source="beep_import",external_id="fixture-101",
                        event_date="2026-10-15",values={"bl:koenigin":False,"bl:brut":1},
                        author="importer",reason="BEEP-Testimport")
        first = write_inspection(con,**imported)
        second = write_inspection(con,**imported)
        check(first[0:2] == second[0:2] and first[2] and not second[2],
              "Wiederholter BEEP-Import ist idempotent")
        check(scalar(con,"SELECT count(*) FROM bienen.sk_durchsicht_revision WHERE durchsicht_id=%s",(first[0],)) == 1,
              "Doppelimport schreibt keine zweite Revision")
        v2 = scalar(con,"INSERT INTO bienen.volk(name) VALUES ('Demo-Volk 2') RETURNING id")
        must_fail(
            lambda: write_inspection(con,**{**imported,"volk_id":v2}),
            "Gleiche BEEP-ID darf nicht einem zweiten Volk gehören"
        )
        def forbidden_sql(statement):
            with con.transaction():
                con.execute(statement, (entry,))
        must_fail(
            lambda: forbidden_sql("UPDATE bienen.sk_durchsicht_revision SET notiz='verändert' WHERE durchsicht_id=%s"),
            "SQL-UPDATE einer historischen Revision wird verhindert",
            errors.CheckViolation
        )
        must_fail(
            lambda: forbidden_sql("DELETE FROM bienen.sk_durchsicht_revision WHERE durchsicht_id=%s"),
            "SQL-DELETE historischer Revisionen wird verhindert",
            errors.CheckViolation
        )
        q1 = write_queen_revision(con,queen_id=queen,details={"name":"Demo","farbe":"weiß"},
                                   author="demo",reason="Eintrag")
        q2 = write_queen_revision(con,queen_id=queen,details={"name":"Demo","farbe":"rot"},
                                   author="demo",reason="Korrektur",expected_revision=q1)
        check((q1,q2)==(1,2), "Königinnenattribute werden historisiert")
        check(scalar(con,"SELECT count(*) FROM bienen.sk_koenigin_revision WHERE koenigin_id=%s",(queen,)) == 2,
              "Königinnenkorrektur überschreibt nicht den alten Stand")
        must_fail(
            lambda: write_queen_revision(con,queen_id=queen,details={"farbe":"blau"},
                                         author="demo",reason="Überholt",expected_revision=1),
            "Konkurrierende Königinnenkorrektur verhindert"
        )
        check(scalar(con,"SELECT count(*) FROM bienen.messwert") == 0,
              "LoRa-/Messdaten unberührt")
    print(f"\nStockkarten-Persistenz: {count} Integrationstests erfolgreich")


if __name__ == "__main__":
    main()
