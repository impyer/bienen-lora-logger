# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit source registration and atomic read-only CSV import."""
import hashlib
import os
from pathlib import Path
import re

from psycopg.types.json import Jsonb

from .parser import parse_csv, utc_time, SourceFormatError
from .profiles import PROFILES


class SourceReadError(ValueError):
    pass


def register_source(conn, *, key, profile, path, stand_id, device_id,
                    source_stand, source_device, synthetic, valid_from,
                    interval_seconds=900, time_quality='unbekannt'):
    if not re.fullmatch(r'[a-z0-9_-]{1,80}', key) or profile not in PROFILES:
        raise ValueError('Ungültige Quellenkonfiguration')
    file = Path(path).absolute()
    if file.resolve() != file or not file.is_file():
        raise ValueError('Quelle muss eine explizite reguläre Datei ohne Symlink sein')
    start = utc_time(valid_from)
    if time_quality not in {'geraet', 'empfang', 'unbekannt'} or (profile == 's2120' and time_quality != 'empfang'):
        raise ValueError('S2120 verwendet belegte TTN-Empfangszeit; Zeitqualität ausdrücklich konfigurieren')
    with conn.transaction():
        conn.execute('SELECT pg_advisory_xact_lock(714004,%s)', (device_id,))
        if not conn.execute('SELECT 1 FROM bienen.stand WHERE id=%s', (stand_id,)).fetchone():
            raise ValueError('Stand-ID existiert nicht')
        device = conn.execute('SELECT art FROM bienen.geraet WHERE id=%s', (device_id,)).fetchone()
        if not device or device[0] != ('wetter' if profile == 's2120' else 'boden'):
            raise ValueError('Geräte-ID/Art passt nicht zum freigegebenen Profil')
        existing = conn.execute('SELECT id FROM bienen.um_quelle WHERE schluessel=%s', (key,)).fetchone()
        if existing:
            raise ValueError('Quellschlüssel existiert; Konfiguration nicht still überschreiben')
        assignments = conn.execute('SELECT stand_id,volk_id FROM bienen.geraet_zuordnung WHERE geraet_id=%s AND gueltig && tstzrange(%s,NULL,\'[)\')', (device_id, start)).fetchall()
        if any(row != (stand_id, None) for row in assignments):
            raise ValueError('Gerätezuordnung widerspricht explizitem Stand')
        if not assignments:
            conn.execute("INSERT INTO bienen.geraet_zuordnung(geraet_id,stand_id,gueltig) VALUES (%s,%s,tstzrange(%s,NULL,'[)'))", (device_id, stand_id, start))
        source_id = conn.execute('''INSERT INTO bienen.um_quelle
            (schluessel,profil,stand_id,geraet_id,datei,quell_stand,quell_geraet,synthetisch,zeitqualitaet,intervall_s)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
            (key, profile, stand_id, device_id, str(file), source_stand, source_device,
             synthetic, time_quality, interval_seconds)).fetchone()[0]
        for field, definition in PROFILES[profile].items():
            conn.execute('''INSERT INTO bienen.messgroesse
                (code,name,einheit,semantik,verdichtung,achse,darstellung)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (code) DO NOTHING''',
                (definition.quantity, 'Temperatur' if definition.quantity == 'temperatur' else definition.name, definition.unit, definition.semantics,
                 definition.aggregation, definition.unit, definition.display))
            semantics = conn.execute('SELECT einheit,semantik FROM bienen.messgroesse WHERE code=%s', (definition.quantity,)).fetchone()
            if semantics != (definition.unit, definition.semantics):
                raise ValueError('Bestehende Messgröße hat abweichende Einheit/Semantik')
            channels = conn.execute("SELECT id,messgroesse_code,faktor,versatz FROM bienen.kanal WHERE geraet_id=%s AND quellfeld=%s AND gueltig && tstzrange(%s,NULL,'[)')", (device_id, field, start)).fetchall()
            if channels:
                if len(channels) != 1 or channels[0][1:] != (definition.quantity, 1.0, 0.0):
                    raise ValueError('Kanalbelegung nicht eindeutig; explizite Migration nötig')
                channel_id = channels[0][0]
            else:
                position_name = f'geraet:{device_id}:{field}'
                zone = 'boden' if definition.depth else ('luft_stand' if profile == 's2120' else 'elektronik')
                position = conn.execute('SELECT id FROM bienen.messstelle WHERE stand_id=%s AND bezeichnung=%s', (stand_id, position_name)).fetchone()
                position_id = position[0] if position else conn.execute('INSERT INTO bienen.messstelle(stand_id,zone,tiefe_cm,bezeichnung) VALUES (%s,%s,%s,%s) RETURNING id', (stand_id, zone, definition.depth, position_name)).fetchone()[0]
                channel_id = conn.execute("INSERT INTO bienen.kanal(geraet_id,quellfeld,messgroesse_code,messstelle_id,gueltig,status) VALUES (%s,%s,%s,%s,tstzrange(%s,NULL,'[)'),'geprueft') RETURNING id", (device_id, field, definition.quantity, position_id, start)).fetchone()[0]
            conn.execute('INSERT INTO bienen.um_quelle_kanal VALUES (%s,%s,%s,%s)', (source_id, field, channel_id, definition.name))
    return source_id


def _read_source(path):
    file = Path(path)
    if file.resolve() != file.absolute():
        raise SourceReadError('quellpfad_enthaelt_symlink')
    try:
        # No receiver writes, file renaming, shared write locks, or chmod.
        descriptor = os.open(file, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if before.st_size > 32 * 1024 * 1024:
                raise SourceReadError('quelle_ueber_32_mib')
            data = stream.read(32 * 1024 * 1024 + 1)
            after = os.fstat(stream.fileno())
            current = file.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino) or current.st_ino != before.st_ino:
                raise SourceReadError('quelle_waehrend_lesen_geaendert')
        return data
    except OSError as exc:
        raise SourceReadError('quelle_nicht_lesbar') from exc


def import_source(conn, source_id):
    try:
        return _import_source(conn, source_id)
    except Exception as exc:
        # The data/checkpoint transaction has already rolled back. Persist a
        # bounded diagnostic, never raw records, DSNs, paths, or database errors.
        code = str(exc) if isinstance(exc, (SourceReadError, SourceFormatError)) else 'import_transaktion_abgebrochen'
        with conn.transaction():
            conn.execute('INSERT INTO bienen.um_import_lauf(quelle_id,erfolgreich,bericht) VALUES (%s,false,%s)', (source_id, Jsonb({'fehler': code[:180]})))
        raise


def _import_source(conn, source_id):
    with conn.transaction():
        row = conn.execute('''SELECT profil,datei,quell_stand,quell_geraet,zeitqualitaet,geraet_id
            FROM bienen.um_quelle WHERE id=%s FOR UPDATE''', (source_id,)).fetchone()
        if not row:
            raise ValueError('Unbekannte konfigurierte Quelle')
        profile, path, stand, device, time_quality, device_id = row
        conn.execute('SELECT pg_advisory_xact_lock(714004,%s)', (device_id,))
        data = _read_source(path)
        digest = hashlib.sha256(data).hexdigest()
        checkpoint = conn.execute('SELECT datei_sha256,bericht FROM bienen.um_checkpoint WHERE quelle_id=%s', (source_id,)).fetchone()
        if checkpoint and checkpoint[0] == digest:
            report = dict(checkpoint[1], unveraendert=True, neue_revisionen=0)
            conn.execute('INSERT INTO bienen.um_import_lauf(quelle_id,erfolgreich,bericht) VALUES (%s,true,%s)', (source_id, Jsonb(report)))
            return report
        try:
            parsed = parse_csv(data.decode('utf-8-sig'), profile, expected_stand=stand, expected_device=device)
        except UnicodeError as exc:
            raise SourceFormatError('CSV ist nicht UTF-8') from exc
        channels = dict(conn.execute('SELECT quellfeld,kanal_id FROM bienen.um_quelle_kanal WHERE quelle_id=%s', (source_id,)).fetchall())
        final = {}
        events = {}
        collisions = set()
        for record in parsed.records:
            conn.execute('''INSERT INTO bienen.um_rohdatensatz
                (quelle_id,ereignis_schluessel,sha256,datei_sha256,zeile,original,felder)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
                (source_id, record.event_key, record.sha256, digest, record.line, record.raw_text, Jsonb(record.raw)))
            # Preserve every original, but choose one deterministic current
            # record per channel timestamp. Rescans must not toggle revisions
            # between two conflicting records at the same instant.
            if record.time in final and final[record.time].sha256 != record.sha256:
                collisions.add(record.time)
            final[record.time] = record
            events[record.event_key] = record
        # An event with a corrected source timestamp must supersede its former
        # position in the current series, while keeping both originals/revisions.
        for record in events.values():
            raw_id = conn.execute('SELECT id FROM bienen.um_rohdatensatz WHERE quelle_id=%s AND ereignis_schluessel=%s AND sha256=%s', (source_id, record.event_key, record.sha256)).fetchone()[0]
            previous = conn.execute('SELECT revision,roh_id FROM bienen.um_ereignis_revision WHERE quelle_id=%s AND ereignis_schluessel=%s ORDER BY revision DESC LIMIT 1', (source_id,record.event_key)).fetchone()
            if not previous or previous[1] != raw_id:
                conn.execute('INSERT INTO bienen.um_ereignis_revision(quelle_id,ereignis_schluessel,revision,roh_id,zeit) VALUES (%s,%s,%s,%s,%s)', (source_id,record.event_key,previous[0]+1 if previous else 1,raw_id,record.time))
        revisions = 0
        for record in final.values():
            raw_id = conn.execute('SELECT id FROM bienen.um_rohdatensatz WHERE quelle_id=%s AND ereignis_schluessel=%s AND sha256=%s', (source_id, record.event_key, record.sha256)).fetchone()[0]
            for field, value in record.values.items():
                channel = channels[field]
                current = conn.execute('SELECT revision,roh_id FROM bienen.um_messwert_revision WHERE kanal_id=%s AND zeit=%s ORDER BY revision DESC LIMIT 1', (channel, record.time)).fetchone()
                if current and current[1] == raw_id:
                    continue
                quality = list(record.quality)
                if record.time in collisions:
                    quality.append('quellkonflikt_selber_zeitpunkt')
                if current:
                    quality.append('quellinhalt_geaendert')
                if value is None:
                    quality.append('fehlender_wert')
                conn.execute('''INSERT INTO bienen.um_messwert_revision
                    (kanal_id,zeit,revision,quelle_id,roh_id,wert,qualitaet,zeitqualitaet)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (channel, record.time, current[0]+1 if current else 1, source_id, raw_id, value, Jsonb(quality), time_quality))
                revisions += 1
        report = {'datensaetze': len(parsed.records), 'ereignisse': len(final),
                  'neue_revisionen': revisions, 'fehler': [vars(x) for x in parsed.errors],
                  'unbekannte_spalten': parsed.unmapped_fields, 'unveraendert': False}
        conn.execute('''INSERT INTO bienen.um_checkpoint(quelle_id,datei_sha256,groesse,bericht)
            VALUES (%s,%s,%s,%s) ON CONFLICT (quelle_id) DO UPDATE SET
            datei_sha256=EXCLUDED.datei_sha256,groesse=EXCLUDED.groesse,
            aktualisiert_am=now(),bericht=EXCLUDED.bericht''', (source_id, digest, len(data), Jsonb(report)))
        conn.execute('INSERT INTO bienen.um_import_lauf(quelle_id,erfolgreich,bericht) VALUES (%s,true,%s)', (source_id, Jsonb(report)))
    return report
