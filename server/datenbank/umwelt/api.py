# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded environment API using the existing session principal and live ACLs."""
import base64
from datetime import datetime, timedelta, timezone
import json

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.openapi.utils import get_openapi

from .parser import utc_time


from .models import Point, Channel, Series, Measurements
from .series_api import register_series_routes


def register_routes(app, connection, principal):
    router = APIRouter(prefix='/api/v1/umwelt', tags=['Umwelt'])

    def connect(snapshot=False):
        try:
            conn = connection()
            if snapshot:
                conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            if not conn.execute("SELECT to_regclass('bienen.um_quelle') IS NOT NULL").fetchone()[0]:
                conn.close()
                raise HTTPException(503, 'Umweltmigration noch nicht eingerichtet')
            return conn
        except psycopg.OperationalError as exc:
            raise HTTPException(503, 'Messdatenbank derzeit nicht erreichbar') from exc

    def permitted(cur, actor, stand_id):
        if not cur.execute('SELECT 1 FROM bienen.sk_benutzer_stand WHERE benutzer_id=%s AND stand_id=%s AND darf_lesen', (actor[0], stand_id)).fetchone():
            raise HTTPException(404, 'Stand oder Messkanal nicht freigegeben')

    def channels(cur, stand_id):
        rows = cur.execute('''SELECT DISTINCT ON (k.id) k.id,qk.bezeichnung,k.quellfeld,k.messgroesse_code,
            g.einheit,g.semantik,g.darstellung,p.tiefe_cm,q.profil,q.intervall_s,
            k.geraet_id,d.name,k.messstelle_id,k.status,k.kalibrierung
            FROM bienen.um_quelle q JOIN bienen.um_quelle_kanal qk ON qk.quelle_id=q.id
            JOIN bienen.kanal k ON k.id=qk.kanal_id
            JOIN bienen.geraet d ON d.id=k.geraet_id
            JOIN bienen.messgroesse g ON g.code=k.messgroesse_code
            LEFT JOIN bienen.messstelle p ON p.id=k.messstelle_id
            WHERE q.stand_id=%s ORDER BY k.id,q.id DESC''', (stand_id,)).fetchall()
        keys = ('id','name','field','quantity','unit','semantics','display','depth_cm','profile','interval_seconds','device_id','device_name','position_id','status','calibration')
        return [Channel(**dict(zip(keys, row))) for row in rows]

    @router.get('/staende')
    def apiaries(actor=Depends(principal)):
        with connect() as conn:
            return [dict(zip(('id','name'), row)) for row in conn.execute('''
                SELECT s.id,s.name FROM bienen.stand s JOIN bienen.sk_benutzer_stand p ON p.stand_id=s.id
                WHERE p.benutzer_id=%s AND p.darf_lesen ORDER BY s.id''', (actor[0],)).fetchall()]

    @router.get('/kanaele', response_model=list[Channel])
    def registry(stand_id: int = Query(gt=0), actor=Depends(principal)):
        with connect() as conn:
            permitted(conn, actor, stand_id)
            return channels(conn, stand_id)

    @router.get('/quellen')
    def sources(stand_id: int = Query(gt=0), actor=Depends(principal)):
        with connect() as conn:
            permitted(conn, actor, stand_id)
            return [dict(zip(('id','key','profile','synthetic','last_checked','success','report','last_value','interval_seconds'), row)) for row in conn.execute('''
                SELECT q.id,q.schluessel,q.profil,q.synthetisch,l.geprueft_am,l.erfolgreich,l.bericht,
                  (SELECT max(m.zeit) FROM bienen.um_messwert_aktuell m WHERE m.quelle_id=q.id AND m.wert IS NOT NULL),q.intervall_s
                FROM bienen.um_quelle q LEFT JOIN LATERAL
                  (SELECT geprueft_am,erfolgreich,bericht FROM bienen.um_import_lauf WHERE quelle_id=q.id ORDER BY id DESC LIMIT 1) l ON true
                WHERE q.stand_id=%s ORDER BY q.id''', (stand_id,)).fetchall()]

    @router.get('/messreihen', response_model=Measurements)
    def measurements(stand_id: int = Query(gt=0), von: datetime = Query(), bis: datetime = Query(),
                     kanal_id: list[int] | None = Query(default=None, max_length=30),
                     limit: int = Query(default=2000, ge=1, le=5000),
                     cursor: str | None = Query(default=None, max_length=200), actor=Depends(principal)):
        if von.tzinfo is None or bis.tzinfo is None or not timedelta(0) < bis-von <= timedelta(days=366):
            raise HTTPException(422, 'Begrenztes Zeitfenster mit explizitem UTC-Offset erforderlich (höchstens 366 Tage)')
        after_time, after_id = von, 0
        if cursor:
            try:
                decoded = json.loads(base64.b64decode(cursor.encode(), altchars=b'-_', validate=True))
                if not isinstance(decoded, list) or len(decoded) != 2:
                    raise ValueError
                after_time, after_id = utc_time(decoded[0]), decoded[1]
                if type(after_id) is not int or after_id <= 0 or not von <= after_time < bis:
                    raise ValueError
            except (ValueError, TypeError, IndexError, UnicodeError) as exc:
                raise HTTPException(422, 'Ungültiger Zeitreihen-Cursor') from exc
        with connect() as conn:
            permitted(conn, actor, stand_id)
            definitions = channels(conn, stand_id)
            available = {c.id for c in definitions}
            if kanal_id is not None and (not kanal_id or not set(kanal_id).issubset(available)):
                raise HTTPException(404, 'Stand oder Messkanal nicht freigegeben')
            selected = [c for c in definitions if kanal_id is None or c.id in kanal_id]
            ids = [c.id for c in selected]
            rows = conn.execute('''SELECT m.kanal_id,m.zeit,m.wert*k.faktor+k.versatz,m.qualitaet,
                m.zeitqualitaet,m.revision,q.schluessel,q.synthetisch,
                m.wert,r.sha256,r.zeile,m.interpretation,m.importiert_am,e.revision
                FROM bienen.um_messwert_aktuell m JOIN bienen.kanal k ON k.id=m.kanal_id
                JOIN bienen.um_quelle q ON q.id=m.quelle_id
                JOIN bienen.um_rohdatensatz r ON r.id=m.roh_id
                JOIN bienen.um_ereignis_aktuell e ON e.roh_id=r.id
                WHERE q.stand_id=%s AND m.kanal_id=ANY(%s) AND m.zeit>=%s AND m.zeit<%s
                  AND k.gueltig @> m.zeit AND (m.zeit,m.kanal_id)>(%s,%s)
                ORDER BY m.zeit,m.kanal_id LIMIT %s''',
                (stand_id, ids, von, bis, after_time, after_id, limit+1)).fetchall() if ids else []
        truncated = len(rows) > limit
        rows = rows[:limit]
        series = {c.id: Series(channel=c, points=[]) for c in selected}
        for kid, time, value, quality, time_quality, revision, source, synthetic, raw_value, record_sha256, record_line, interpretation, imported_at, event_revision in rows:
            series[kid].points.append(Point(time=time, value=value, quality=quality,
                time_quality=time_quality, revision=revision, source=source, synthetic=synthetic,
                raw_value=raw_value,record_sha256=record_sha256,record_line=record_line,
                interpretation=interpretation,imported_at=imported_at,event_revision=event_revision))
        next_cursor = None
        if truncated and rows:
            next_cursor = base64.urlsafe_b64encode(json.dumps([rows[-1][1].isoformat(), rows[-1][0]]).encode()).decode()
        return Measurements(series=list(series.values()), truncated=truncated, next_cursor=next_cursor)

    register_series_routes(router, connect, permitted, channels, principal)

    @router.get('/openapi.json', include_in_schema=False)
    def schema(actor=Depends(principal)):
        document = get_openapi(title='Bienenlogger Umwelt API', version='1.0.0', routes=router.routes)
        document.setdefault('components', {}).setdefault('securitySchemes', {})['session'] = {
            'type':'apiKey','in':'cookie','name':'bl_dev_session'}
        document['security'] = [{'session':[]}]
        return document

    app.include_router(router)
