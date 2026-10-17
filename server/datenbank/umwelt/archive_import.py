# SPDX-License-Identifier: GPL-3.0-or-later
"""Streaming file transactions, prefix checkpoints and stable archive provenance."""
from pathlib import Path
import time

from psycopg.types.json import Jsonb

from .archive_files import directory,names,read_file,identity,hash_prefix,Lines,FILE_SECONDS
from .archive_batch import prepare,flush,BATCH_SIZE
from .parser import parse_stream,CsvHeader,Issue
from .ingest import SourceReadError

MAX_DIAGNOSTICS=50


def import_stream_source(conn,source_id):
    row=conn.execute('''SELECT profil,datei,quell_stand,quell_geraet,zeitqualitaet,geraet_id,archiv_muster
        FROM bienen.um_quelle WHERE id=%s''',(source_id,)).fetchone()
    if not row:raise ValueError('Unbekannte konfigurierte Quelle')
    profile,path,stand,device,time_quality,device_id,pattern=row
    root=path if pattern else str(Path(path).parent)
    reports=[];failure=None
    with directory(root) as descriptor:
        selected=names(descriptor,pattern) if pattern else [Path(path).name]
        if not selected:raise SourceReadError('keine_passende_archivdatei')
        for name in selected:
            try:
                reports.append(_file(conn,descriptor,name,source_id,device_id,profile,stand,device,time_quality))
            except Exception as exc:
                # Earlier successfully committed months stay intact. The failed
                # file transaction rolls back including checkpoint/provenance.
                if failure is None:failure=exc
    if failure is not None:
        raise failure
    report={'dateien':len(reports),'datensaetze':sum(r['datensaetze'] for r in reports),
        'ereignisse':sum(r['datensaetze'] for r in reports),
        'neue_revisionen':sum(r['neue_revisionen'] for r in reports),
        'fehler': [e for r in reports for e in r['fehler']][:MAX_DIAGNOSTICS],
        'fehler_anzahl':sum(r.get('fehler_anzahl',0) for r in reports),
        'unbekannte_spalten':sorted({s for r in reports for s in r['unbekannte_spalten']}),
        'unveraendert':all(r['unveraendert'] for r in reports),
        'partielles_ende':any(r.get('partielles_ende',False) for r in reports)}
    with conn.transaction():
        conn.execute('INSERT INTO bienen.um_import_lauf(quelle_id,erfolgreich,bericht) VALUES (%s,true,%s)',(source_id,Jsonb(report)))
    return report


def _file(conn,descriptor,name,source_id,device_id,profile,stand,device,time_quality):
    # The read_file context exits (and checks inode/stat) BEFORE transaction commit.
    with conn.transaction():
        conn.execute("SET LOCAL lock_timeout='5000'")
        conn.execute("SET LOCAL statement_timeout='60000'")
        conn.execute('SELECT pg_advisory_xact_lock(714004,%s)',(device_id,))
        with read_file(descriptor,name) as (stream,before):
            deadline=time.monotonic()+FILE_SECONDS
            previous=conn.execute('''SELECT id,version,dev,inode,groesse,mtime_ns,ctime_ns,
                offset_bytes,zeilen,prefix_sha256,kopf,bericht FROM bienen.um_archiv_datei
                WHERE quelle_id=%s AND name=%s''',(source_id,name)).fetchone()
            if previous and tuple(previous[2:7])==identity(before):
                return dict(previous[11],unveraendert=True,neue_revisionen=0,datensaetze=0)
            digest=hash_prefix(stream,before.st_size,deadline)
            append=bool(previous and tuple(previous[2:4])==identity(before)[:2] and before.st_size>=previous[7]
                and hash_prefix(stream,previous[7],deadline)==previous[9])
            version=previous[1] if append else previous[1]+1 if previous else 1
            offset,line,header=(previous[7],previous[8],previous[10]) if append else (0,0,None)
            if previous:file_id=previous[0]
            else:
                file_id=conn.execute('''INSERT INTO bienen.um_archiv_datei
                    (quelle_id,name,version,dev,inode,groesse,mtime_ns,ctime_ns,offset_bytes,zeilen,prefix_sha256,kopf,bericht)
                    VALUES (%s,%s,1,%s,%s,%s,%s,%s,0,0,%s,'[]','{}') RETURNING id''',
                    (source_id,name,*identity(before),'0'*64)).fetchone()[0]
            prepare(conn)
            lines=Lines(stream,offset,line,deadline)
            batch=[];errors=[];error_count=0;records=0;revisions=0;unknown=[]
            for item in parse_stream(lines,profile,expected_stand=stand,expected_device=device,header=header,first_line=line+1):
                if isinstance(item,CsvHeader):
                    header=list(item.fields);unknown=list(item.unknown)
                elif isinstance(item,Issue):
                    error_count+=1
                    if len(errors)<MAX_DIAGNOSTICS:errors.append(vars(item))
                else:
                    batch.append((item,lines.offset));records+=1
                    if len(batch)>=BATCH_SIZE:
                        revisions+=flush(conn,batch,source_id,file_id,version,digest,time_quality);batch.clear()
            revisions+=flush(conn,batch,source_id,file_id,version,digest,time_quality)
            if lines.partial:
                error_count+=1
                if len(errors)<MAX_DIAGNOSTICS:errors.append({'line':lines.line+1,'code':'unvollstaendige_letzte_zeile'})
            prefix=hash_prefix(stream,lines.offset,deadline)
            report={'datensaetze':records,'neue_revisionen':revisions,'fehler':errors,'fehler_anzahl':error_count,
                'unbekannte_spalten':unknown,'unveraendert':False,'partielles_ende':lines.partial,
                'modus':'append' if append else 'replay','offset_bytes':lines.offset,'zeilen':lines.line,'version':version}
            conn.execute('''UPDATE bienen.um_archiv_datei SET version=%s,dev=%s,inode=%s,groesse=%s,mtime_ns=%s,ctime_ns=%s,
                offset_bytes=%s,zeilen=%s,prefix_sha256=%s,kopf=%s,bericht=%s,aktualisiert_am=now() WHERE id=%s''',
                (version,*identity(before),lines.offset,lines.line,prefix,Jsonb(header),Jsonb(report),file_id))
            # R1 compatibility checkpoint remains available, now for last completed file.
            conn.execute('''INSERT INTO bienen.um_checkpoint(quelle_id,datei_sha256,groesse,bericht)
                VALUES (%s,%s,%s,%s) ON CONFLICT (quelle_id) DO UPDATE SET datei_sha256=EXCLUDED.datei_sha256,
                groesse=EXCLUDED.groesse,bericht=EXCLUDED.bericht,aktualisiert_am=now()''',
                (source_id,digest,before.st_size,Jsonb(report)))
    return report
