# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Lese-API und Auslieferung der Oberfläche (Konzept 0.2, §4 Nr. 4 und §10 Schritt 5, Phase B: nur lesend).

Start (im Ordner server/plattform, nur auf localhost; Apache leitet aus dem Heimnetz weiter):
    BIENEN_PLATTFORM_CONFIG=/etc/bienen/plattform_config.toml uvicorn --factory api.app:erstellen --host 127.0.0.1 --port 8081
Alle Endpunkte außer /api/gesundheit und /api/anmelden verlangen eine Sitzung (ADR-0003 Nr. 10).
Zeiten gehen als ISO 8601 mit Zeitzone ein und kommen in UTC zurück.
"""
import os
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import abfragen, stammdaten, verwaltung
from .anmeldung import COOKIE, Bremse, csrf_gueltig, csrf_token, passwort_pruefen, sitzung_erzeugen, sitzung_gueltig
from .verdichtung import MAX_ZEITRAUM, raster

WEB = Path(__file__).resolve().parent.parent / "web"
VORGABEN = {"dsn": "", "dsn_schreiben": "", "passwort_hash": "", "sitzungsschluessel": "", "cookie_sicher": True,
            "sitzung_tage": 90, "protokolle": {}}
CSP = ("default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")


def konfig_laden(pfad=None):
    pfad = Path(pfad or os.environ.get("BIENEN_PLATTFORM_CONFIG", Path(__file__).resolve().parent.parent / "plattform_config.toml"))
    with open(pfad, "rb") as f:
        k = {**VORGABEN, **tomllib.load(f)}
    if len(k["sitzungsschluessel"]) < 32 or not k["passwort_hash"].startswith("scrypt$") or not k["dsn"]:
        raise SystemExit(f"{pfad}: dsn, passwort_hash und sitzungsschluessel (≥ 32 Zeichen) eintragen")
    return k


def psycopg_verbinden(dsn, nur_lesen=True):
    """Verbindung für eine Anfrage: UTC, Schema bienen; zum Lesen als Nur-Lese-Transaktion."""
    def verbinden():
        import psycopg                     # erst bei Bedarf: Hosttests laufen ohne Treiber
        from psycopg.rows import dict_row
        con = psycopg.connect(dsn, row_factory=dict_row, autocommit=False)
        con.read_only = nur_lesen
        con.execute("SET search_path = bienen, public")
        con.execute("SET TIME ZONE 'UTC'")
        return con
    return verbinden


# ---------------------------------------------------------------- Parameter

def zeitpunkt(text, name):
    if text is None:
        return None
    try:
        t = datetime.fromisoformat(text)
    except ValueError:
        raise HTTPException(400, f"{name}: keine ISO-8601-Zeit") from None
    if t.tzinfo is None:
        raise HTTPException(400, f"{name}: Zeitzone fehlt (z. B. 2026-10-01T00:00:00Z)")
    return t.astimezone(timezone.utc)


def zeitraum(von, bis):
    bis_t = zeitpunkt(bis, "bis") or datetime.now(timezone.utc)
    von_t = zeitpunkt(von, "von") or bis_t - timedelta(days=14)
    if von_t >= bis_t:
        raise HTTPException(400, "von muss vor bis liegen")
    if bis_t - von_t > MAX_ZEITRAUM:
        raise HTTPException(400, f"Zeitraum länger als {MAX_ZEITRAUM.days} Tage")
    return von_t, bis_t


def messgroessen_waehlen(cur, text):
    if not text:
        return {}
    katalog = abfragen.messgroessen_codes(cur)
    codes = [c.strip() for c in text.split(",") if c.strip()]
    unbekannt = [c for c in codes if c not in katalog]
    if unbekannt:
        raise HTTPException(400, "unbekannte Messgröße: " + ", ".join(unbekannt))
    return {c: katalog[c] for c in codes}


class Anmeldung(BaseModel):
    passwort: str


# ---------------------------------------------------------------- App

def importer_nachtragen(dsn, protokolle):
    """Nachtragen über server/datenbank/importer.py, falls die Protokollverzeichnisse konfiguriert sind."""
    if not protokolle:
        return None

    def nachtragen(geraet):
        import sys
        import psycopg
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "datenbank"))
        import importer
        with psycopg.connect(dsn) as con:
            b = importer.Importer(con).nachtragen({q: Path(v) for q, v in protokolle.items()}, geraet)
        return {"messwerte": b.messwerte, "belegt": b.messwert_belegt, "fehler": b.fehler[:20]}
    return nachtragen


def erstellen(konfig=None, verbinden=None, verbinden_schreiben=None):
    k = {**VORGABEN, **(konfig or konfig_laden())}
    verbinden = verbinden or psycopg_verbinden(k["dsn"])
    verbinden_schreiben = verbinden_schreiben or psycopg_verbinden(k["dsn_schreiben"] or k["dsn"], nur_lesen=False)
    bremse = Bremse()
    app = FastAPI(title="Bienen-Plattform", docs_url=None, redoc_url=None, openapi_url=None)

    @app.exception_handler(stammdaten.Konflikt)
    async def konflikt(request, e):
        return JSONResponse({"detail": str(e)}, status_code=409)

    @app.exception_handler(stammdaten.NichtGefunden)
    async def nicht_gefunden(request, e):
        return JSONResponse({"detail": str(e)}, status_code=404)

    try:
        from psycopg import errors as pg

        @app.exception_handler(pg.IntegrityError)
        async def integritaet(request, e):
            # Regeln der Datenbank (Überlappung, Eindeutigkeit, Prüfungen) als verständlicher Konflikt
            text = {pg.ExclusionViolation: "Zeitraum überschneidet sich mit einer bestehenden Angabe "
                                           "(z. B. Beute schon belegt, Gerät schon zugeordnet)",
                    pg.UniqueViolation: "Name oder Kennung ist schon vergeben",
                    pg.ForeignKeyViolation: "Verweis auf ein unbekanntes Objekt",
                    pg.CheckViolation: "Angabe verletzt eine Regel der Datenbank"}.get(type(e), "Widerspruch zu den gespeicherten Daten")
            return JSONResponse({"detail": text}, status_code=409)
    except ImportError:          # Hosttests ohne Treiber
        pass

    @app.middleware("http")
    async def kopfzeilen(request, call_next):
        antwort = await call_next(request)
        antwort.headers["Content-Security-Policy"] = CSP
        antwort.headers["X-Content-Type-Options"] = "nosniff"
        antwort.headers["Referrer-Policy"] = "same-origin"
        # API nie zwischenspeichern; Oberfläche bei jedem Laden revalidieren (ETag), damit Updates sofort wirken
        antwort.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "no-cache"
        return antwort

    def cursor():
        con = verbinden()
        try:
            with con.cursor() as cur:
                yield cur
        finally:
            con.rollback()
            con.close()

    def angemeldet(request: Request):
        if not sitzung_gueltig(k["sitzungsschluessel"], request.cookies.get(COOKIE)):
            raise HTTPException(401, "nicht angemeldet")

    def herkunft_passt(request):
        for kopf in ("origin", "referer"):
            w = request.headers.get(kopf)
            if w:
                return urlparse(w).netloc == request.headers.get("host")
        return True

    def schreiben(request: Request):
        """Cursor für schreibende Anfragen: Sitzung, Herkunft, CSRF-Token; Commit nur ohne Fehler (PLT26-04)."""
        sitzung = request.cookies.get(COOKIE)
        if not sitzung_gueltig(k["sitzungsschluessel"], sitzung):
            raise HTTPException(401, "nicht angemeldet")
        if not herkunft_passt(request):
            raise HTTPException(403, "fremde Herkunft")
        if not csrf_gueltig(k["sitzungsschluessel"], sitzung, request.headers.get("x-csrf-token")):
            raise HTTPException(403, "CSRF-Token fehlt oder ist falsch")
        con = verbinden_schreiben()
        try:
            with con.cursor() as cur:
                yield cur
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    nur_angemeldet = [Depends(angemeldet)]

    # ---------- ohne Sitzung
    @app.get("/api/gesundheit")
    def gesundheit(cur=Depends(cursor)):
        return {"datenbank": "ok", **abfragen.gesundheit(cur)}

    @app.post("/api/anmelden")
    def anmelden(daten: Anmeldung, request: Request, response: Response):
        herkunft = request.headers.get("origin")
        if herkunft and urlparse(herkunft).netloc != request.headers.get("host"):
            raise HTTPException(403, "fremde Herkunft")
        adresse = request.client.host if request.client else "?"
        if not bremse.versuch(adresse):          # prüft und zählt in einem Schritt, vor dem teuren scrypt
            raise HTTPException(429, "zu viele Fehlversuche, bitte eine Minute warten")
        if not passwort_pruefen(daten.passwort, k["passwort_hash"]):
            raise HTTPException(401, "Passwort falsch")
        bremse.erfolg(adresse)
        dauer = int(k["sitzung_tage"]) * 86400
        response.set_cookie(COOKIE, sitzung_erzeugen(k["sitzungsschluessel"], dauer), max_age=dauer, httponly=True,
                            samesite="strict", secure=bool(k["cookie_sicher"]), path="/")
        return {"angemeldet": True}

    @app.post("/api/abmelden")
    def abmelden(response: Response):
        response.delete_cookie(COOKIE, path="/")
        return {"angemeldet": False}

    # ---------- mit Sitzung
    @app.get("/api/sitzung", dependencies=nur_angemeldet)
    def sitzung(request: Request):
        return {"angemeldet": True, "csrf": csrf_token(k["sitzungsschluessel"], request.cookies.get(COOKIE))}

    @app.get("/api/messgroessen", dependencies=nur_angemeldet)
    def messgroessen(cur=Depends(cursor)):
        return abfragen.messgroessen(cur)

    @app.get("/api/staende", dependencies=nur_angemeldet)
    def staende(zeit: Optional[str] = None, cur=Depends(cursor)):
        return abfragen.staende(cur, zeitpunkt(zeit, "zeit") or datetime.now(timezone.utc))

    @app.get("/api/voelker/{volk_id}", dependencies=nur_angemeldet)
    def volk(volk_id: int, zeit: Optional[str] = None, cur=Depends(cursor)):
        v = abfragen.volk(cur, volk_id, zeitpunkt(zeit, "zeit") or datetime.now(timezone.utc))
        if v is None:
            raise HTTPException(404, "Volk unbekannt")
        return v

    def reihen(cur, bezug, bezug_id, von, bis, groessen):
        if not abfragen.gibt_es(cur, bezug, bezug_id):
            raise HTTPException(404, {"volk": "Volk", "stand": "Stand"}[bezug] + " unbekannt")
        von_t, bis_t = zeitraum(von, bis)
        r = raster(von_t, bis_t)
        return {"von": von_t, "bis": bis_t, "raster_s": int(r.total_seconds()),
                "reihen": abfragen.messreihen(cur, bezug, bezug_id, von_t, bis_t, messgroessen_waehlen(cur, groessen), r)}

    @app.get("/api/voelker/{volk_id}/messreihen", dependencies=nur_angemeldet)
    def volk_messreihen(volk_id: int, von: Optional[str] = None, bis: Optional[str] = None,
                        groessen: Optional[str] = None, cur=Depends(cursor)):
        return reihen(cur, "volk", volk_id, von, bis, groessen)

    @app.get("/api/staende/{stand_id}/umwelt", dependencies=nur_angemeldet)
    def umwelt(stand_id: int, von: Optional[str] = None, bis: Optional[str] = None,
               groessen: Optional[str] = None, cur=Depends(cursor)):
        return reihen(cur, "stand", stand_id, von, bis, groessen)

    @app.get("/api/voelker/{volk_id}/tagesbilanz", dependencies=nur_angemeldet)
    def tagesbilanz(volk_id: int, von: Optional[str] = None, bis: Optional[str] = None, cur=Depends(cursor)):
        if not abfragen.gibt_es(cur, "volk", volk_id):
            raise HTTPException(404, "Volk unbekannt")
        von_t, bis_t = zeitraum(von, bis)
        return abfragen.tagesbilanz(cur, volk_id, von_t, bis_t)

    @app.get("/api/voelker/{volk_id}/ereignisse", dependencies=nur_angemeldet)
    def ereignisse(volk_id: int, von: Optional[str] = None, bis: Optional[str] = None, cur=Depends(cursor)):
        if not abfragen.gibt_es(cur, "volk", volk_id):
            raise HTTPException(404, "Volk unbekannt")
        von_t, bis_t = zeitraum(von, bis)
        return abfragen.ereignisse(cur, volk_id, von_t, bis_t)

    @app.get("/api/pruefungen", dependencies=nur_angemeldet)
    def pruefungen(cur=Depends(cursor)):
        return abfragen.pruefungen(cur)

    def lesen_angemeldet(request: Request):
        angemeldet(request)
        yield from cursor()

    app.include_router(verwaltung.router(lesen_angemeldet, schreiben,
                                         importer_nachtragen(k["dsn_schreiben"] or k["dsn"], k["protokolle"])))

    @app.get("/api/{rest:path}")
    def unbekannt(rest: str):
        raise HTTPException(404, "unbekannter Endpunkt")

    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
    return app
