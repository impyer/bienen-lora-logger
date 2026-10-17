# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit source registration and atomic read-only CSV import."""
from pathlib import Path
import re

from psycopg.types.json import Jsonb

from .parser import utc_time, SourceFormatError
from .profiles import PROFILES


class SourceReadError(ValueError):
    pass


def register_source(conn, *, key, profile, path, stand_id, device_id,
                    source_stand, source_device, synthetic, valid_from,
                    interval_seconds=900, time_quality='unbekannt', pattern=None):
    if not re.fullmatch(r'[a-z0-9_-]{1,80}', key) or profile not in PROFILES:
        raise ValueError('Ungültige Quellenkonfiguration')
    file = Path(path).absolute()
    if pattern is not None:
        from .archive_files import compile_pattern
        compile_pattern(pattern)
    if file.resolve() != file or not (file.is_dir() if pattern else file.is_file()):
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
            configured = conn.execute('''SELECT profil,datei,stand_id,geraet_id,quell_stand,quell_geraet,
                synthetisch,zeitqualitaet,intervall_s,archiv_muster FROM bienen.um_quelle WHERE id=%s''',existing).fetchone()
            if configured != (profile,str(file),stand_id,device_id,source_stand,source_device,synthetic,time_quality,interval_seconds,pattern):
                raise ValueError('Quellschlüssel existiert; Konfiguration nicht still überschreiben')
            return existing[0]
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
        if pattern:
            conn.execute('UPDATE bienen.um_quelle SET archiv_muster=%s WHERE id=%s',(pattern,source_id))
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


def import_source(conn, source_id):
    try:
        from .archive_import import import_stream_source
        return import_stream_source(conn, source_id)
    except Exception as exc:
        # The data/checkpoint transaction has already rolled back. Persist a
        # bounded diagnostic, never raw records, DSNs, paths, or database errors.
        code = str(exc) if isinstance(exc, (SourceReadError, SourceFormatError)) else 'import_transaktion_abgebrochen'
        with conn.transaction():
            conn.execute('INSERT INTO bienen.um_import_lauf(quelle_id,erfolgreich,bericht) VALUES (%s,false,%s)', (source_id, Jsonb({'fehler': code[:180]})))
        raise
