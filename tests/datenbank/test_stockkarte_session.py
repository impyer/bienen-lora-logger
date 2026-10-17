# SPDX-License-Identifier: GPL-3.0-or-later
"""HttpOnly-Sitzung und Volkrechte gegen wegwerfbare PostgreSQL-16-DB.

Keine echten BEEP-/Imkerdaten. Destruktives Grundschema nur nach
DB-Namensprüfung des bestehenden test_stockkarte_persistenz.setup().
"""
from pathlib import Path
import os
import sys

import psycopg
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"server"/"datenbank"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from stockkarte_session_api import create_session_app
from test_stockkarte_persistenz import setup

DSN=os.environ["BIENEN_TEST_DSN"]
PASSWORD="Testing-only-strong-password-2026"
checks=0


def verify(response, code):
    global checks
    assert response.status_code==code, (response.status_code,response.text)
    checks+=1
    return response


def main():
    global checks
    with TestClient(create_session_app(enabled=False,dsn=DSN,secret="p"*40),
                    base_url="https://testserver") as disabled:
        verify(disabled.get("/api/v1/stockkarte/voelker"),503)
        verify(disabled.post("/api/v1/stockkarte/session/login",
                            json={"username":"imker1","password":PASSWORD}),503)
    with TestClient(create_session_app(enabled=True,dsn=DSN,secret="too short"),
                    base_url="https://testserver") as disabled:
        verify(disabled.get("/api/v1/stockkarte/voelker"),503)

    with psycopg.connect(DSN,autocommit=True) as conn:
        setup(conn)
        conn.execute(
            (ROOT/"server/datenbank/migrations/002_stockkarte_benutzer.sql").read_text(encoding="utf-8")
        )
        a=conn.execute("INSERT INTO bienen.volk(name) VALUES ('Anonymes Volk A') RETURNING id").fetchone()[0]
        b=conn.execute("INSERT INTO bienen.volk(name) VALUES ('Anonymes Volk B') RETURNING id").fetchone()[0]
        h=PasswordHasher().hash(PASSWORD)
        user=conn.execute(
            "INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES ('imker1',%s) RETURNING id",
            (h,)
        ).fetchone()[0]
        reader=conn.execute(
            "INSERT INTO bienen.sk_benutzer(benutzername,passwort_hash) VALUES ('leser1',%s) RETURNING id",
            (h,)
        ).fetchone()[0]
        conn.execute(
            """INSERT INTO bienen.sk_benutzer_volk(benutzer_id,volk_id,darf_lesen,darf_schreiben)
               VALUES (%s,%s,true,true),(%s,%s,true,false)""",
            (user,a,reader,a),
        )
        conn.execute(
            """INSERT INTO bienen.sk_kategorie(id,bezeichnung,eingabetyp,pflicht,meta)
               VALUES ('bl:seen','Königin gesehen','boolean',true,'{}'),
                      ('bl:frames','Brutwaben','number_0_decimals',true,'{"min":0,"max":20}')"""
        )
    app=create_session_app(enabled=True,dsn=DSN,secret="private-test-key-"+("x"*48))
    base="/api/v1/stockkarte"
    with TestClient(app,base_url="https://testserver") as c:
        verify(c.get(base+"/session"),401)
        verify(c.get(base+"/voelker"),401)
        verify(c.post(base+"/session/login",json={"username":"unknown","password":PASSWORD}),401)
        verify(c.post(base+"/session/login",json={"username":"imker1","password":"wrong"}),401)
        login=verify(c.post(base+"/session/login",json={"username":"imker1","password":PASSWORD}),200)
        cookie=login.headers.get("set-cookie","")
        assert "httponly" in cookie.lower() and "secure" in cookie.lower()
        assert "samesite=strict" in cookie.lower()
        checks+=1
        csrf=login.json()["csrf_token"]
        verify(c.get(base+"/session"),200)
        rows=verify(c.get(base+"/voelker"),200).json()
        assert len(rows)==1 and rows[0]["id"]==a and rows[0]["can_write"]
        checks+=1
        verify(c.get(base+f"/voelker/{b}/durchsichten"),404)
        verify(c.get(base+f"/voelker/{a}/durchsichten"),200)
        path=base+f"/voelker/{a}/durchsichten"
        body={"event_date":"2026-10-16","values":{"bl:seen":False,"bl:frames":0},
              "accuracy":"nur_datum","note":"Nur Datum","reason":"Anlage"}
        verify(c.post(path,json=body),403)
        verify(c.post(path,json=body,headers={"X-CSRF-Token":"invalid"}),403)
        verify(c.post(path,json=body,headers={"X-CSRF-Token":csrf,
               "Origin":"https://evil.test"}),403)
        verify(c.post(base+f"/voelker/{b}/durchsichten",json=body,
               headers={"X-CSRF-Token":csrf}),404)
        verify(c.post(path,json={**body,"source":"beep_import"},
               headers={"X-CSRF-Token":csrf}),422)
        result=verify(c.post(path,json=body,headers={"X-CSRF-Token":csrf}),201)
        entry=result.json()["id"]
        assert result.json()["revision"]==1
        checks+=1
        original=verify(c.get(path),200).json()[0]
        assert original["values"]["bl:seen"] is False
        assert original["values"]["bl:frames"]==0
        assert original["event_time"] is None
        checks+=1
        revisions=base+f"/durchsichten/{entry}/revisionen"
        latest={**body,"expected_revision":1,"values":{"bl:seen":True,"bl:frames":3},
                "reason":"Zählung korrigiert"}
        verify(c.post(revisions,json=latest,headers={"X-CSRF-Token":csrf}),201)
        verify(c.post(revisions,json=latest,headers={"X-CSRF-Token":csrf}),409)
        history=verify(c.get(revisions),200).json()
        assert len(history)==2 and history[0]["values"]["bl:seen"] is False
        assert history[1]["values"]["bl:seen"] is True
        checks+=1
        verify(c.post(base+"/session/logout"),403)
        verify(c.post(base+"/session/logout",headers={"X-CSRF-Token":csrf}),200)
        verify(c.get(base+"/session"),401)
        verify(c.get(path),401)

    with TestClient(app,base_url="https://testserver") as guest:
        login=verify(guest.post(base+"/session/login",json={
            "username":"leser1","password":PASSWORD}),200)
        csrf=login.json()["csrf_token"]
        rows=verify(guest.get(base+"/voelker"),200).json()
        assert len(rows)==1 and rows[0]["id"]==a and not rows[0]["can_write"]
        checks+=1
        verify(guest.get(path),200)
        verify(guest.get(revisions),200)
        verify(guest.post(path,json=body,headers={"X-CSRF-Token":csrf}),404)
        verify(guest.post(revisions,json=latest,headers={"X-CSRF-Token":csrf}),404)
        verify(guest.get(base+f"/voelker/{b}/durchsichten"),404)
    with psycopg.connect(DSN) as conn:
        stored=conn.execute(
            "SELECT autor FROM bienen.sk_durchsicht_revision WHERE durchsicht_id=%s ORDER BY revision",
            (entry,)
        ).fetchall()
        assert stored==[("imker1",),("imker1",)]
        checks+=1
    print("Sitzungs-API: ",checks,
          "Prüfungen (Authentifizierung, ACL je Volk, CSRF, Historie, Logout) PASS")


if __name__=="__main__":
    main()
