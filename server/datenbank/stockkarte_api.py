# SPDX-License-Identifier: GPL-3.0-or-later
"""Eigenständige Bienenlogger-Stockkarte: ausschließlich interne Entwicklungs-API.

Ohne explizites Opt-in, zwei unterschiedliche starke Tokens und DSN fail closed.
Keine Browser-/BEEP-Laufzeitabhängigkeit; kein produktives Mehrbenutzer-Login.
"""
from __future__ import annotations

from datetime import date, datetime
import hmac
import os
from typing import Any, Literal

import psycopg
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from stockkarte_store import write_inspection, write_queen_revision


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Inspection(StrictBody):
    event_date: date
    event_time: datetime | None = None
    accuracy: Literal["nur_datum", "exakt", "geschaetzt"] = "nur_datum"
    checklist_id: int | None = Field(default=None, gt=0)
    checklist_version: int | None = Field(default=None, gt=0)
    values: dict[str, Any] = Field(default_factory=dict)
    note: str = Field(default="", max_length=10000)
    reason: str = Field(min_length=1, max_length=1000)


class Correction(Inspection):
    expected_revision: int = Field(ge=1)


class QueenCorrection(StrictBody):
    details: dict[str, Any]
    reason: str = Field(min_length=1, max_length=1000)
    expected_revision: int | None = Field(default=None, ge=0)


def _checklist(body):
    if (body.checklist_id is None) != (body.checklist_version is None):
        raise HTTPException(422, "Checklisten-ID und Version müssen zusammen angegeben werden")
    if body.checklist_id is None:
        return None
    return (body.checklist_id, body.checklist_version)


def _storage_error(error):
    if isinstance(error, ValueError):
        status = 409 if "Versionskonflikt" in str(error) else 404 if "nicht gefunden" in str(error) else 422
        raise HTTPException(status, str(error)) from error
    if isinstance(error, psycopg.errors.ForeignKeyViolation):
        raise HTTPException(422, "Ungültige Referenz auf Stammdaten") from error
    if isinstance(error, psycopg.errors.UniqueViolation):
        raise HTTPException(409, "Kennung bereits vergeben") from error
    raise error


def create_app(*, read_token=None, write_token=None, dsn=None, enabled=None):
    read_token = read_token if read_token is not None else os.getenv("BIENEN_API_READ_TOKEN", "")
    write_token = write_token if write_token is not None else os.getenv("BIENEN_API_WRITE_TOKEN", "")
    dsn = dsn if dsn is not None else os.getenv("BIENEN_API_DSN", "")
    enabled = enabled if enabled is not None else os.getenv("BIENEN_API_DEV_MODE") == "1"
    active = bool(enabled and dsn and isinstance(read_token, str) and
                  isinstance(write_token, str) and len(read_token) >= 32 and
                  len(write_token) >= 32 and
                  not hmac.compare_digest(read_token, write_token))

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def private_response(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def auth(request: Request):
        if not active:
            raise HTTPException(503, "Stockkarten-API ist nicht aktiviert")
        header = request.headers.get("authorization", "")
        if not header.startswith("Bearer "):
            raise HTTPException(401, "Bearer-Token erforderlich",
                                headers={"WWW-Authenticate": "Bearer"})
        token = header[7:]
        writer = hmac.compare_digest(token, write_token)
        reader = hmac.compare_digest(token, read_token)
        if not (writer or reader):
            raise HTTPException(401, "Ungültiges Token",
                                headers={"WWW-Authenticate": "Bearer"})
        if request.method != "GET" and not writer:
            raise HTTPException(403, "Schreibberechtigung erforderlich")

    router = APIRouter(prefix="/api/v1/stockkarte", dependencies=[Depends(auth)])

    def connection():
        return psycopg.connect(dsn, connect_timeout=5)

    @router.get("/voelker")
    def get_colonies():
        with connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT id,name FROM bienen.volk ORDER BY id LIMIT 1000")
            return [{"id": a, "name": b} for a, b in cur.fetchall()]

    @router.get("/katalog")
    def get_catalog():
        with connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id,parent_id,bezeichnung,eingabetyp,pflicht,meta,quelle FROM bienen.sk_kategorie ORDER BY id"
            )
            fields = [dict(zip(("id","parent_id","name","input","required","meta","source"), row))
                      for row in cur.fetchall()]
            cur.execute(
                "SELECT id,kategorie_id,bezeichnung,reihenfolge,inaktiv FROM bienen.sk_option ORDER BY kategorie_id,reihenfolge"
            )
            options = [dict(zip(("id","category_id","name","position","inactive"), row))
                       for row in cur.fetchall()]
            cur.execute(
                """SELECT c.id,c.name,v.version FROM bienen.sk_checkliste c
                   JOIN bienen.sk_checkliste_version v ON v.checkliste_id=c.id
                   ORDER BY c.id,v.version"""
            )
            checklists = []
            for cid, name, version in cur.fetchall():
                cur.execute(
                    """SELECT kategorie_id,position,pflicht FROM bienen.sk_checkliste_feld
                       WHERE checkliste_id=%s AND version=%s ORDER BY position""",
                    (cid, version),
                )
                checklists.append({
                    "id": cid, "name": name, "version": version,
                    "fields": [
                        {"category_id": a, "position": b, "required": c}
                        for a, b, c in cur.fetchall()
                    ],
                })
            return {"categories":fields,"options":options,"checklists":checklists}

    @router.get("/voelker/{volk_id}/durchsichten")
    def get_inspections(volk_id: int = Path(gt=0),
                        limit: int = Query(default=50, ge=1, le=100),
                        offset: int = Query(default=0, ge=0)):
        with connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM bienen.volk WHERE id=%s", (volk_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, "Volk nicht gefunden")
            cur.execute(
                """SELECT id,revision,ereignis_datum,ereignis_zeit,zeitgenauigkeit,
                          werte,notiz,quelle,quelle_id,checkliste_id,checkliste_version
                   FROM bienen.sk_durchsicht_aktuell WHERE volk_id=%s
                   ORDER BY ereignis_datum DESC,id DESC LIMIT %s OFFSET %s""",
                (volk_id, limit, offset),
            )
            names=("id","revision","event_date","event_time","accuracy","values","note",
                   "source","external_id","checklist_id","checklist_version")
            return [dict(zip(names, row)) for row in cur.fetchall()]

    @router.post("/voelker/{volk_id}/durchsichten", status_code=201)
    def add_inspection(body: Inspection, volk_id: int = Path(gt=0)):
        try:
            cl = _checklist(body)
            with connection() as conn:
                record, version, created = write_inspection(
                    conn, volk_id=volk_id, source="eigen", event_date=body.event_date,
                    event_time=body.event_time, accuracy=body.accuracy,
                    checklist=cl, values=body.values, note=body.note,
                    author="stockkarte-dev-editor", reason=body.reason,
                )
            return {"id":record,"revision":version,"created":created}
        except (ValueError, psycopg.errors.ForeignKeyViolation,
                psycopg.errors.UniqueViolation) as error:
            _storage_error(error)

    @router.get("/durchsichten/{entry_id}/revisionen")
    def get_inspection_history(entry_id: int = Path(gt=0)):
        with connection() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT d.volk_id,r.revision,r.ereignis_datum,r.ereignis_zeit,
                          r.zeitgenauigkeit,r.werte,r.notiz,r.aenderungsgrund,
                          r.autor,r.erstellt_am,r.geloescht,r.checkliste_id,r.checkliste_version
                   FROM bienen.sk_durchsicht d
                   JOIN bienen.sk_durchsicht_revision r ON r.durchsicht_id=d.id
                   WHERE d.id=%s ORDER BY r.revision""", (entry_id,),
            )
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(404, "Durchsicht nicht gefunden")
            names=("volk_id","revision","event_date","event_time","accuracy","values",
                   "note","reason","author","recorded_at","deleted",
                   "checklist_id","checklist_version")
            return [dict(zip(names, row)) for row in rows]

    @router.post("/durchsichten/{entry_id}/revisionen", status_code=201)
    def correct_inspection(body: Correction, entry_id: int = Path(gt=0)):
        try:
            cl = _checklist(body)
            with connection() as conn:
                record, version, created = write_inspection(
                    conn, entry_id=entry_id, expected_revision=body.expected_revision,
                    event_date=body.event_date, event_time=body.event_time,
                    accuracy=body.accuracy, checklist=cl, values=body.values,
                    note=body.note, author="stockkarte-dev-editor", reason=body.reason,
                )
            return {"id":record,"revision":version,"created":created}
        except (ValueError, psycopg.errors.ForeignKeyViolation,
                psycopg.errors.UniqueViolation) as error:
            _storage_error(error)

    @router.get("/koeniginnen/{queen_id}/revisionen")
    def get_queen_history(queen_id: int = Path(gt=0)):
        with connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM bienen.koenigin WHERE id=%s", (queen_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, "Königin nicht gefunden")
            cur.execute(
                """SELECT revision,daten,aenderungsgrund,autor,erstellt_am
                   FROM bienen.sk_koenigin_revision
                   WHERE koenigin_id=%s ORDER BY revision""", (queen_id,),
            )
            return [dict(zip(("revision","details","reason","author","recorded_at"), row))
                    for row in cur.fetchall()]

    @router.post("/koeniginnen/{queen_id}/revisionen", status_code=201)
    def correct_queen(body: QueenCorrection, queen_id: int = Path(gt=0)):
        try:
            with connection() as conn:
                version = write_queen_revision(
                    conn, queen_id=queen_id, details=body.details,
                    expected_revision=body.expected_revision,
                    author="stockkarte-dev-editor", reason=body.reason,
                )
            return {"queen_id":queen_id,"revision":version}
        except (ValueError, psycopg.errors.ForeignKeyViolation,
                psycopg.errors.UniqueViolation) as error:
            _storage_error(error)

    app.include_router(router)
    return app


app = create_app()
