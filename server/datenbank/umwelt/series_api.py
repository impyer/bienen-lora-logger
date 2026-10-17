# SPDX-License-Identifier: GPL-3.0-or-later
"""Snapshot API: short consistent SQL read, bounded streaming reduction, stable pages."""
from datetime import datetime, timedelta, timezone
import json
from typing import Literal

from fastapi import Depends, HTTPException, Query
import psycopg

from .models import DiagramPage
from .series_reader import MAX_INPUT_POINTS, choose_interval, select_observations, SeriesBudgetError
from .snapshots import SnapshotStore, CursorError, SnapshotGone, SnapshotDenied, SnapshotBudgetError, TTL_SECONDS


ROW_QUERY = '''SELECT m.kanal_id,m.zeit,m.wert*k.faktor+k.versatz,m.qualitaet,
    m.zeitqualitaet,m.revision,q.schluessel,q.synthetisch,m.wert,r.sha256,r.zeile,
    m.interpretation,m.importiert_am,e.revision
    FROM bienen.um_messwert_aktuell m
    JOIN bienen.kanal k ON k.id=m.kanal_id
    JOIN bienen.um_quelle q ON q.id=m.quelle_id
    JOIN bienen.um_rohdatensatz r ON r.id=m.roh_id
    JOIN bienen.um_ereignis_aktuell e ON e.roh_id=r.id
    WHERE q.stand_id=%s AND m.kanal_id=ANY(%s) AND m.zeit>=%s AND m.zeit<%s
      AND k.gueltig @> m.zeit'''


def register_series_routes(router, connect, permitted, channels, principal):
    store = SnapshotStore()

    @router.get('/zeitreihen', response_model=DiagramPage)
    def diagram(stand_id: int = Query(gt=0), von: datetime = Query(), bis: datetime = Query(),
                kanal_id: list[int] | None = Query(default=None, max_length=30),
                resolution: Literal['raw','auto','envelope'] = 'auto',
                bucket_seconds: int | None = Query(default=None, ge=1, le=604800),
                limit: int = Query(default=5000, ge=1, le=5000),
                cursor: str | None = Query(default=None, max_length=200), actor=Depends(principal)):
        if von.tzinfo is None or bis.tzinfo is None or not timedelta(0)<bis-von<=timedelta(days=366):
            raise HTTPException(422, 'Zeitfenster mit expliziten Offsets erforderlich, höchstens 366 Tage')
        query = (stand_id, von.astimezone(timezone.utc).isoformat(), bis.astimezone(timezone.utc).isoformat(),
                 tuple(sorted(set(kanal_id))) if kanal_id is not None else None, resolution, bucket_seconds)
        try:
            if cursor:
                # Live permissions are deliberately checked outside the cached snapshot.
                with connect() as conn:
                    permitted(conn, actor, stand_id)
                entry, offset = store.resume(cursor, actor[0], query)
            else:
                with connect(snapshot=True) as conn:
                    permitted(conn, actor, stand_id)
                    as_of = conn.execute('SELECT transaction_timestamp()').fetchone()[0]
                    definitions = channels(conn, stand_id)
                    available = {c.id for c in definitions}
                    if kanal_id is not None and (not kanal_id or not set(kanal_id).issubset(available)):
                        raise HTTPException(404, 'Stand oder Messkanal nicht freigegeben')
                    selected = [c for c in definitions if kanal_id is None or c.id in kanal_id]
                    if len(selected)>30:
                        raise HTTPException(422, 'Höchstens 30 Kanäle pro Abfrage ausdrücklich auswählen')
                    ids = [c.id for c in selected]
                    conn.execute("SELECT set_config('statement_timeout','8000',true)")
                    params = (stand_id, ids, von, bis)
                    count = conn.execute('SELECT count(*) FROM ('+ROW_QUERY+' LIMIT %s) bounded', params+(MAX_INPUT_POINTS+1,)).fetchone()[0] if ids else 0
                    if count>MAX_INPUT_POINTS:
                        raise SeriesBudgetError('Mehr als zwei Millionen Quellwerte; Zeitraum/Kanäle verkleinern')
                    seconds = choose_interval(resolution,(bis-von).total_seconds(),count,len(ids),bucket_seconds)
                    with conn.cursor(name='um_diagram_stream') as stream:
                        stream.itersize = 2000
                        stream.execute(ROW_QUERY+' ORDER BY m.kanal_id,m.zeit LIMIT %s', params+(MAX_INPUT_POINTS+1,))
                        points, summaries = select_observations(stream,selected,seconds)
                    now = datetime.now(timezone.utc)
                    metadata = dict(as_of=as_of,expires_at=now+timedelta(seconds=TTL_SECONDS),
                        source_points=count,total_points=len(points),
                        definitions=[dict(channel=c.model_dump(mode='json'),summary=summaries[c.id]) for c in selected])
                entry = store.create(actor[0],query,metadata,points)
                offset = 0
            points = json.loads(entry.data)
            if offset>=len(points) and offset!=0:
                raise CursorError('Cursor-Offset außerhalb der Reihe')
            page = points[offset:offset+limit]
            grouped = {d['channel']['id']:dict(**d,points=[]) for d in entry.metadata['definitions']}
            for kid,value in page:
                grouped[kid]['points'].append(value)
            following = offset+len(page)
            complete = following==len(points)
            return DiagramPage(snapshot=entry.identity,as_of=entry.metadata['as_of'],
                expires_at=entry.metadata['expires_at'],series=list(grouped.values()),
                source_points=entry.metadata['source_points'],total_points=len(points),offset=offset,
                returned_points=len(page),complete=complete,
                next_cursor=None if complete else store.cursor(entry,following))
        except SnapshotDenied as exc:
            raise HTTPException(404,str(exc)) from exc
        except SnapshotGone as exc:
            raise HTTPException(410,str(exc)) from exc
        except (CursorError,SeriesBudgetError,SnapshotBudgetError) as exc:
            raise HTTPException(422,str(exc)) from exc
        except psycopg.errors.QueryCanceled as exc:
            raise HTTPException(503,'Zeitbudget der Messreihenabfrage erreicht; Zeitraum/Kanäle verkleinern') from exc
