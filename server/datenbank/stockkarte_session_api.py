# SPDX-License-Identifier: GPL-3.0-or-later
"""Geschlossene Test-Web-API: HttpOnly-Sitzungen und Berechtigungen je Volk.

Separat von der älteren Bearer-Token-Entwicklungs-API. Kein Login ist
voreingestellt, keine Standardnutzer, keine automatische Dateneinrichtung.
Nur auf einem isolierten localhost-Testsystem verwenden.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import ipaddress
import os
import re
import secrets
import time

import psycopg
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, FastAPI, Header, HTTPException, Path, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from stockkarte_api import Inspection, Correction, _checklist, _storage_error
from stockkarte_store import write_inspection

COOKIE = "bl_dev_session"
MINUTES = 20


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9_.-]+$")
    password: str = Field(min_length=1, max_length=1000)


def create_session_app(*, dsn=None, secret=None, enabled=None, secure_cookie=True):
    dsn = dsn if dsn is not None else os.environ.get("BIENEN_AUTH_DSN", "")
    secret = secret if secret is not None else os.environ.get("BIENEN_AUTH_SECRET", "")
    enabled = enabled if enabled is not None else os.environ.get("BIENEN_AUTH_DEV_MODE") == "1"
    active = bool(enabled and dsn and isinstance(secret, str) and len(secret) >= 32)
    ph = PasswordHasher()
    dummy_hash = ph.hash("never-the-real-password-000")
    failed = {}
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def privacy(request: Request, call_next):
        # Kein versehentlich im LAN veröffentlichter Dev-Sitzungsdienst.
        # TestClient benutzt "testclient"; echte Zugriffe nur Loopback.
        peer = request.client.host if request.client else ""
        allowed = peer in {"127.0.0.1", "::1", "testclient"}
        # Der Heimnetz-Test läuft hinter einem TLS-Reverse-Proxy in einem
        # ausschließlich internen Docker-Netz. Direkte Portfreigabe des
        # FastAPI-Dienstes bleibt verboten.
        if not allowed and os.environ.get("BIENEN_AUTH_TRUST_DOCKER_PROXY") == "1":
            try:
                allowed = ipaddress.ip_address(peer) in ipaddress.ip_network("172.16.0.0/12")
            except ValueError:
                allowed = False
        if not allowed:
            return JSONResponse(
                status_code=403, content={"detail":"Nur lokaler Entwicklungsbetrieb"},
                headers={"Cache-Control":"no-store"},
            )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response

    def check_active():
        if not active:
            raise HTTPException(503, "Lokaler Sitzungsdienst nicht aktiviert")

    def db():
        return psycopg.connect(dsn, connect_timeout=5)

    def hash_cookie(raw):
        return hashlib.sha256(raw.encode("ascii")).hexdigest()

    def csrf(raw):
        return hmac.new(secret.encode("utf-8"), ("csrf-v1:" + raw).encode("ascii"), hashlib.sha256).hexdigest()

    def principal(request: Request):
        check_active()
        token = request.cookies.get(COOKIE, "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,160}", token):
            raise HTTPException(401, "Sitzung fehlt")
        with db() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT u.id,u.benutzername
                   FROM bienen.sk_sitzung s
                   JOIN bienen.sk_benutzer u ON u.id=s.benutzer_id
                   WHERE s.token_sha256=%s AND s.ablauf_am>now()
                     AND s.widerrufen_am IS NULL AND u.aktiv""",
                (hash_cookie(token),),
            )
            item = cur.fetchone()
        if item is None:
            raise HTTPException(401, "Sitzung ungültig oder abgelaufen")
        return (item[0], item[1], token)

    def can_access(cur, user_id, volk_id, write=False):
        cur.execute(
            """SELECT 1 FROM bienen.sk_benutzer_volk
               WHERE benutzer_id=%s AND volk_id=%s
                 AND darf_lesen AND (%s=false OR darf_schreiben)""",
            (user_id, volk_id, write),
        )
        if cur.fetchone() is None:
            # Versteckt auch die Existenz fremder Völker.
            raise HTTPException(404, "Volk oder Durchsicht nicht gefunden")

    def check_csrf(request: Request, actor, presented):
        expected = csrf(actor[2])
        if not isinstance(presented, str) or not hmac.compare_digest(presented, expected):
            raise HTTPException(403, "CSRF-Schutz: gültiger X-CSRF-Token erforderlich")
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
            raise HTTPException(403, "Cross-Origin-Schreibzugriff verweigert")

    @app.post("/api/v1/stockkarte/session/login")
    def login(body: Login, response: Response):
        check_active()
        # Nur isolierter Dev-Dienst; einfache prozesslokale Verzögerung gegen
        # automatisierte Fehlversuche, kein Produktions-Rate-Limiter.
        now = time.monotonic()
        previous = [t for t in failed.get(body.username, []) if now - t < 60]
        if len(previous) >= 5:
            raise HTTPException(429, "Zu viele Anmeldeversuche")
        with db() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT id,passwort_hash FROM bienen.sk_benutzer
                   WHERE benutzername=%s AND aktiv""", (body.username,),
            )
            record = cur.fetchone()
            try:
                valid = ph.verify(record[1] if record else dummy_hash, body.password)
            except (VerifyMismatchError, VerificationError):
                valid = False
            if not valid or record is None:
                failed[body.username] = previous + [now]
                raise HTTPException(401, "Anmeldung nicht erfolgreich")
            failed.pop(body.username, None)
            token = secrets.token_urlsafe(48)
            cur.execute(
                """INSERT INTO bienen.sk_sitzung
                   (token_sha256,benutzer_id,ablauf_am)
                   VALUES (%s,%s,%s)""",
                (hash_cookie(token), record[0],
                 datetime.now(timezone.utc) + timedelta(minutes=MINUTES)),
            )
        response.set_cookie(
            key=COOKIE, value=token, max_age=MINUTES*60, httponly=True,
            secure=secure_cookie, samesite="strict", path="/api/v1/stockkarte",
        )
        return {"username":body.username,"csrf_token":csrf(token),"expires_in_seconds":MINUTES*60}

    @app.get("/api/v1/stockkarte/session")
    def session(actor=Depends(principal)):
        return {"username":actor[1],"csrf_token":csrf(actor[2]),"expires_in_seconds":MINUTES*60}

    @app.post("/api/v1/stockkarte/session/logout")
    def logout(request: Request, response: Response,
               x_csrf_token: str | None = Header(default=None),
               actor=Depends(principal)):
        check_csrf(request, actor, x_csrf_token)
        with db() as conn, conn.cursor() as cur:
            cur.execute(
                """UPDATE bienen.sk_sitzung SET widerrufen_am=now()
                   WHERE token_sha256=%s AND widerrufen_am IS NULL""",
                (hash_cookie(actor[2]),),
            )
        response.delete_cookie(COOKIE, path="/api/v1/stockkarte", secure=secure_cookie,
                               httponly=True, samesite="strict")
        return {"signed_out":True}

    @app.get("/api/v1/stockkarte/voelker")
    def colonies(actor=Depends(principal)):
        with db() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT v.id,v.name,p.darf_schreiben
                   FROM bienen.volk v
                   JOIN bienen.sk_benutzer_volk p ON p.volk_id=v.id
                   WHERE p.benutzer_id=%s AND p.darf_lesen ORDER BY v.id""",
                (actor[0],),
            )
            return [{"id":a,"name":b,"can_write":c} for a,b,c in cur.fetchall()]

    @app.get("/api/v1/stockkarte/katalog")
    def catalog(actor=Depends(principal)):
        # Gemeinsamer Katalog ohne einzelne Standorte/Volknamen. Nur
        # eingeloggten und einem Volk berechtigten Personen anzeigen.
        with db() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM bienen.sk_benutzer_volk WHERE benutzer_id=%s AND darf_lesen LIMIT 1",
                (actor[0],),
            )
            if cur.fetchone() is None:
                return {"categories":[],"options":[],"checklists":[]}
            cur.execute(
                """SELECT id,parent_id,bezeichnung,eingabetyp,pflicht,meta
                   FROM bienen.sk_kategorie ORDER BY id"""
            )
            categories=[dict(zip(
                ("id","parent_id","name","input","required","meta"),row
            )) for row in cur.fetchall()]
            cur.execute(
                """SELECT id,kategorie_id,bezeichnung,reihenfolge,inaktiv
                   FROM bienen.sk_option ORDER BY kategorie_id,reihenfolge"""
            )
            options=[dict(zip(
                ("id","category_id","name","position","inactive"),row
            )) for row in cur.fetchall()]
            cur.execute(
                """SELECT c.id,c.name,v.version FROM bienen.sk_checkliste c
                   JOIN bienen.sk_checkliste_version v ON v.checkliste_id=c.id
                   ORDER BY c.id,v.version"""
            )
            checklists=[]
            for cid,name,version in cur.fetchall():
                cur.execute(
                    """SELECT kategorie_id,position,pflicht
                       FROM bienen.sk_checkliste_feld
                       WHERE checkliste_id=%s AND version=%s ORDER BY position""",
                    (cid,version),
                )
                checklists.append({
                    "id":cid,"name":name,"version":version,
                    "fields":[{"category_id":fid,"position":p,"required":req}
                              for fid,p,req in cur.fetchall()],
                })
        return {"categories":categories,"options":options,"checklists":checklists}

    @app.get("/api/v1/stockkarte/voelker/{volk_id}/durchsichten")
    def inspections(volk_id: int = Path(gt=0),
                    limit: int = Query(default=50,ge=1,le=100),
                    offset: int = Query(default=0,ge=0),
                    actor=Depends(principal)):
        with db() as conn, conn.cursor() as cur:
            can_access(cur,actor[0],volk_id)
            cur.execute(
                """SELECT id,revision,ereignis_datum,ereignis_zeit,zeitgenauigkeit,
                          werte,notiz,quelle,quelle_id,checkliste_id,checkliste_version
                   FROM bienen.sk_durchsicht_aktuell WHERE volk_id=%s
                   ORDER BY ereignis_datum DESC,id DESC LIMIT %s OFFSET %s""",
                (volk_id,limit,offset),
            )
            keys=("id","revision","event_date","event_time","accuracy","values",
                  "note","source","external_id","checklist_id","checklist_version")
            return [dict(zip(keys,r)) for r in cur.fetchall()]

    @app.post("/api/v1/stockkarte/voelker/{volk_id}/durchsichten", status_code=201)
    def new_inspection(request: Request, body: Inspection, volk_id: int = Path(gt=0),
                       x_csrf_token: str | None = Header(default=None),
                       actor=Depends(principal)):
        check_csrf(request,actor,x_csrf_token)
        cl=_checklist(body)
        try:
            with db() as conn:
                with conn.cursor() as cur:
                    can_access(cur,actor[0],volk_id,write=True)
                item,rev,done=write_inspection(
                    conn,volk_id=volk_id,source="eigen",event_date=body.event_date,
                    event_time=body.event_time,accuracy=body.accuracy,checklist=cl,
                    values=body.values,note=body.note,author=actor[1],reason=body.reason,
                )
            return {"id":item,"revision":rev,"created":done}
        except (ValueError,psycopg.errors.ForeignKeyViolation,
                psycopg.errors.UniqueViolation) as exc:
            _storage_error(exc)

    def owner_of(cur,entry_id):
        cur.execute("SELECT volk_id FROM bienen.sk_durchsicht WHERE id=%s",(entry_id,))
        r=cur.fetchone()
        if r is None:
            raise HTTPException(404,"Durchsicht nicht gefunden")
        return r[0]

    @app.get("/api/v1/stockkarte/durchsichten/{entry_id}/revisionen")
    def history(entry_id: int = Path(gt=0),actor=Depends(principal)):
        with db() as conn, conn.cursor() as cur:
            volk_id=owner_of(cur,entry_id)
            can_access(cur,actor[0],volk_id)
            cur.execute(
                """SELECT revision,ereignis_datum,ereignis_zeit,zeitgenauigkeit,
                          werte,notiz,aenderungsgrund,autor,erstellt_am,
                          geloescht,checkliste_id,checkliste_version
                   FROM bienen.sk_durchsicht_revision
                   WHERE durchsicht_id=%s ORDER BY revision""",(entry_id,),
            )
            keys=("revision","event_date","event_time","accuracy","values","note",
                  "reason","author","recorded_at","deleted","checklist_id","checklist_version")
            return [dict(zip(keys,r)) for r in cur.fetchall()]

    @app.post("/api/v1/stockkarte/durchsichten/{entry_id}/revisionen", status_code=201)
    def revise(request: Request, body: Correction, entry_id: int = Path(gt=0),
               x_csrf_token: str | None = Header(default=None),
               actor=Depends(principal)):
        check_csrf(request,actor,x_csrf_token)
        cl=_checklist(body)
        try:
            with db() as conn:
                with conn.cursor() as cur:
                    volk_id=owner_of(cur,entry_id)
                    can_access(cur,actor[0],volk_id,write=True)
                item,rev,done=write_inspection(
                    conn,entry_id=entry_id,expected_revision=body.expected_revision,
                    event_date=body.event_date,event_time=body.event_time,
                    accuracy=body.accuracy,checklist=cl,values=body.values,
                    note=body.note,author=actor[1],reason=body.reason,
                )
            return {"id":item,"revision":rev,"created":done}
        except (ValueError,psycopg.errors.ForeignKeyViolation,
                psycopg.errors.UniqueViolation) as exc:
            _storage_error(exc)
    return app


app=create_session_app()
