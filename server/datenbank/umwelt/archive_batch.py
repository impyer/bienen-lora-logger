# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded SQL batches. Only previously unseen raw variants can advance history."""
from psycopg.types.json import Jsonb

BATCH_SIZE=500


def prepare(conn):
    conn.execute('''CREATE TEMP TABLE IF NOT EXISTS um_batch (
        seq integer, event char(64), sha char(64), line bigint, byte_end bigint,
        original text, fields jsonb, measured timestamptz, vals jsonb, quality jsonb
    ) ON COMMIT DELETE ROWS''')
    conn.execute('CREATE TEMP TABLE IF NOT EXISTS um_new_raw(id bigint PRIMARY KEY) ON COMMIT DELETE ROWS')


def flush(conn,batch,source_id,file_id,version,digest,time_quality):
    if not batch:return 0
    conn.execute('TRUNCATE pg_temp.um_batch,pg_temp.um_new_raw')
    with conn.cursor().copy('COPY pg_temp.um_batch FROM STDIN') as copy:
        for seq,(record,byte_end) in enumerate(batch):
            copy.write_row((seq,record.event_key,record.sha256,record.line,byte_end,
                record.raw_text,Jsonb(record.raw),record.time,Jsonb(record.values),Jsonb(list(record.quality))))
    conn.execute('ANALYZE pg_temp.um_batch')
    conn.execute('''WITH added AS (
        INSERT INTO bienen.um_rohdatensatz(quelle_id,ereignis_schluessel,sha256,datei_sha256,zeile,original,felder)
        SELECT %s,event,sha,%s,line,original,fields FROM pg_temp.um_batch ORDER BY seq
        ON CONFLICT DO NOTHING RETURNING id)
        INSERT INTO pg_temp.um_new_raw SELECT id FROM added''',(source_id,digest))
    conn.execute('ANALYZE pg_temp.um_new_raw')
    conn.execute('''INSERT INTO bienen.um_roh_fundstelle(roh_id,datei_id,version,datei_sha256,zeile,byte_bis)
        SELECT r.id,%s,%s,%s,b.line,b.byte_end FROM pg_temp.um_batch b
        JOIN bienen.um_rohdatensatz r ON r.quelle_id=%s AND r.ereignis_schluessel=b.event AND r.sha256=b.sha
        ON CONFLICT DO NOTHING''',(file_id,version,digest,source_id))
    # A known historical variant from another month must never undo a correction.
    conn.execute('''INSERT INTO bienen.um_ereignis_revision(quelle_id,ereignis_schluessel,revision,roh_id,zeit)
        SELECT %s,b.event,coalesce(old.revision,0)+1,b.id,b.measured FROM (
          SELECT DISTINCT ON (s.event) s.*,r.id FROM pg_temp.um_batch s
          JOIN bienen.um_rohdatensatz r ON r.quelle_id=%s AND r.ereignis_schluessel=s.event AND r.sha256=s.sha
          JOIN pg_temp.um_new_raw n ON n.id=r.id ORDER BY s.event,s.seq DESC) b
        LEFT JOIN LATERAL (SELECT revision FROM bienen.um_ereignis_revision e
          WHERE e.quelle_id=%s AND e.ereignis_schluessel=b.event ORDER BY revision DESC LIMIT 1) old ON true''',
        (source_id,source_id,source_id))
    result=conn.execute('''WITH conflicts AS (
        SELECT measured,count(DISTINCT sha)>1 AS clash FROM pg_temp.um_batch GROUP BY measured)
        INSERT INTO bienen.um_messwert_revision
        (kanal_id,zeit,revision,quelle_id,roh_id,wert,qualitaet,zeitqualitaet)
        SELECT k.kanal_id,b.measured,coalesce(old.revision,0)+1,%s,b.id,v.value::double precision,
          b.quality || CASE WHEN old.revision IS NOT NULL THEN '["quellinhalt_geaendert"]'::jsonb ELSE '[]'::jsonb END
          || CASE WHEN v.value IS NULL THEN '["fehlender_wert"]'::jsonb ELSE '[]'::jsonb END
          || CASE WHEN conflicts.clash
             THEN '["quellkonflikt_selber_zeitpunkt"]'::jsonb ELSE '[]'::jsonb END,%s
        FROM (SELECT DISTINCT ON (s.measured) s.*,r.id FROM pg_temp.um_batch s
          JOIN bienen.um_rohdatensatz r ON r.quelle_id=%s AND r.ereignis_schluessel=s.event AND r.sha256=s.sha
          JOIN pg_temp.um_new_raw n ON n.id=r.id ORDER BY s.measured,s.seq DESC) b
        JOIN conflicts ON conflicts.measured=b.measured
        CROSS JOIN LATERAL jsonb_each_text(b.vals) v
        JOIN bienen.um_quelle_kanal k ON k.quelle_id=%s AND k.quellfeld=v.key
        LEFT JOIN LATERAL (SELECT revision FROM bienen.um_messwert_revision m
          WHERE m.kanal_id=k.kanal_id AND m.zeit=b.measured ORDER BY revision DESC LIMIT 1) old ON true''',
        (source_id,time_quality,source_id,source_id))
    return result.rowcount
