# SPDX-License-Identifier: GPL-3.0-or-later
"""Stockkarten-API E2E nur in einer wegwerfbaren PostgreSQL-Testinstanz."""
import os
from pathlib import Path
import sys
import psycopg
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"server"/"datenbank"))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from stockkarte_api import create_app
from test_stockkarte_persistenz import setup

DSN=os.environ["BIENEN_TEST_DSN"]
READER="test-reader-catalog-only-aaaaaaaaaaaaaaa"
WRITER="test-writer-edit-revisions-bbbbbbbbbbbbbbb"


def expect(response,code):
    assert response.status_code==code,(response.status_code,response.text)


def main():
    with TestClient(create_app(read_token="short",write_token="short",dsn=DSN,enabled=True)) as closed:
        expect(closed.get("/api/v1/stockkarte/voelker"),503)
    with psycopg.connect(DSN,autocommit=True) as conn:
        setup(conn)
        volk=conn.execute("INSERT INTO bienen.volk(name) VALUES ('Fiktives Volk') RETURNING id").fetchone()[0]
        queen=conn.execute("INSERT INTO bienen.koenigin(jahrgang) VALUES (2026) RETURNING id").fetchone()[0]
        conn.execute(
            """INSERT INTO bienen.sk_kategorie(id,bezeichnung,eingabetyp,pflicht,meta)
               VALUES ('bl:seen','Königin gesehen','boolean',true,'{}'),
                      ('bl:comb','Brutwaben','number_0_decimals',true,'{"min":0,"max":20}'),
                      ('bl:method','Behandlung','select',false,'{}')"""
        )
        conn.execute("INSERT INTO bienen.sk_option(id,kategorie_id,bezeichnung,reihenfolge) VALUES ('bl:oxal','bl:method','Oxalsäure',1)")
        checklist=conn.execute(
            "INSERT INTO bienen.sk_checkliste(schluessel,name) VALUES ('winter','Winter') RETURNING id"
        ).fetchone()[0]
        conn.execute("INSERT INTO bienen.sk_checkliste_version(checkliste_id,version) VALUES (%s,1)",(checklist,))
        conn.execute(
            """INSERT INTO bienen.sk_checkliste_feld(checkliste_id,version,kategorie_id,position,pflicht)
               VALUES (%s,1,'bl:seen',1,true),(%s,1,'bl:comb',2,true),(%s,1,'bl:method',3,false)""",
            (checklist,checklist,checklist),
        )
    read={"Authorization":"Bearer "+READER}
    write={"Authorization":"Bearer "+WRITER}
    path=f"/api/v1/stockkarte/voelker/{volk}/durchsichten"
    with TestClient(create_app(read_token=READER,write_token=WRITER,dsn=DSN,enabled=True)) as client:
        expect(client.get(path),401)
        expect(client.get(path,headers={"Authorization":"Bearer invalid"}),401)
        expect(client.get(path,headers=read),200)
        expect(client.get(path.replace(str(volk),str(volk+9999)),headers=read),404)
        expect(client.get("/openapi.json"),404)
        assert "access-control-allow-origin" not in client.get(path,headers=read).headers
        assert client.get(path,headers=read).headers["cache-control"]=="no-store"
        response=client.get("/api/v1/stockkarte/voelker",headers=read)
        expect(response,200)
        assert response.json()[0]["id"]==volk
        catalog=client.get("/api/v1/stockkarte/katalog",headers=read)
        expect(catalog,200)
        assert len(catalog.json()["categories"])==3
        assert catalog.json()["options"][0]["id"]=="bl:oxal"
        assert catalog.json()["checklists"][0]["fields"][0]["category_id"]=="bl:seen"
        body={
            "event_date":"2026-10-16","accuracy":"nur_datum",
            "checklist_id":checklist,"checklist_version":1,
            "values":{"bl:seen":False,"bl:comb":0,"bl:method":"bl:oxal"},
            "note":"Fiktiver Eintrag","reason":"Erstaufnahme"
        }
        expect(client.post(path,json=body,headers=read),403)
        expect(client.post(path,json={**body,"source":"beep_import"},headers=write),422)
        expect(client.post(path,json={**body,"event_time":"2026-10-16T09:00:00+02:00"},headers=write),422)
        expect(client.post(path,json={**body,"values":{**body["values"],"bl:method":"bad"}},headers=write),422)
        expect(client.post(path,json={**body,"values":{"bl:comb":2}},headers=write),422)
        created=client.post(path,json=body,headers=write)
        expect(created,201)
        entry=created.json()["id"]
        assert created.json()["revision"]==1
        rows=client.get(path,headers=read)
        expect(rows,200)
        assert rows.json()[0]["values"]["bl:seen"] is False
        assert rows.json()[0]["values"]["bl:comb"]==0
        assert rows.json()[0]["event_time"] is None
        revision_url=f"/api/v1/stockkarte/durchsichten/{entry}/revisionen"
        fix={
            **body,"expected_revision":1,"accuracy":"exakt",
            "event_time":"2026-10-16T12:30:00+02:00",
            "values":{"bl:seen":True,"bl:comb":2,"bl:method":"bl:oxal"},
            "reason":"Korrektur"
        }
        expect(client.post(revision_url,json=fix,headers=read),403)
        updated=client.post(revision_url,json=fix,headers=write)
        expect(updated,201)
        assert updated.json()["revision"]==2
        expect(client.post(revision_url,json=fix,headers=write),409)
        history=client.get(revision_url,headers=read)
        expect(history,200)
        assert [x["revision"] for x in history.json()]==[1,2]
        assert history.json()[0]["values"]["bl:seen"] is False
        assert history.json()[1]["values"]["bl:seen"] is True
        expect(client.get("/api/v1/stockkarte/durchsichten/999999/revisionen",headers=read),404)
        qpath=f"/api/v1/stockkarte/koeniginnen/{queen}/revisionen"
        expect(client.post(qpath,json={"details":{"farbe":"weiß"},"reason":"Neu"},headers=read),403)
        first=client.post(qpath,json={"details":{"farbe":"weiß"},"reason":"Neu"},headers=write)
        expect(first,201)
        assert first.json()["revision"]==1
        expect(client.post(qpath,json={
            "details":{"farbe":"rot"},"reason":"Korrektur","expected_revision":1
        },headers=write),201)
        expect(client.post(qpath,json={
            "details":{"farbe":"blau"},"reason":"Veraltet","expected_revision":1
        },headers=write),409)
        qhist=client.get(qpath,headers=read)
        expect(qhist,200)
        assert len(qhist.json())==2
        assert qhist.json()[0]["details"]["farbe"]=="weiß"
        expect(client.get("/api/v1/stockkarte/koeniginnen/999999/revisionen",headers=read),404)
    print("Stockkarte-FastAPI: Berechtigungen, Katalog, Revisionen, Konflikte und Königinnen PASS")


if __name__=="__main__":
    main()
