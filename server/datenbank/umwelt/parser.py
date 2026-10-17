# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure CSV adapters. No file writes, network, database, or inferred identities."""
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json

from .profiles import PROFILES, REQUIRED, TIME_FIELD, DEVICE_FIELD, TELEMETRY


class SourceFormatError(ValueError):
    pass


@dataclass(frozen=True)
class Issue:
    line: int
    code: str


@dataclass(frozen=True)
class Record:
    time: datetime
    event_key: str
    sha256: str
    line: int
    values: dict
    raw: dict
    raw_text: str
    quality: tuple


@dataclass(frozen=True)
class ParsedFile:
    records: list
    errors: list
    unmapped_fields: list


def utc_time(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError('UTC offset required')
        return result.astimezone(timezone.utc)
    except (ValueError, AttributeError, OverflowError) as exc:
        raise ValueError('ungueltiger_zeitstempel') from exc


def parse_csv(text, profile, *, expected_stand, expected_device):
    if profile not in PROFILES:
        raise SourceFormatError('Unbekanntes Quellenprofil')
    if len(text.encode('utf-8')) > 32 * 1024 * 1024:
        raise SourceFormatError('Quelldatei über 32 MiB; explizit kleinere Monatsquelle auswählen')
    text = text.removeprefix('\ufeff')
    lines = text.splitlines(keepends=True)
    reader = csv.reader(io.StringIO(text, newline=''), delimiter=';', strict=True)
    try:
        headers = next(reader)
    except (StopIteration, csv.Error) as exc:
        raise SourceFormatError('CSV-Kopf fehlt oder ist beschädigt') from exc
    if len(headers) != len(set(headers)) or not REQUIRED[profile].issubset(headers):
        raise SourceFormatError('CSV-Kopf enthält doppelte oder fehlende Pflichtspalten')
    known = set(PROFILES[profile]) | REQUIRED[profile] | TELEMETRY
    unknown = sorted(set(headers) - known)
    records, errors = [], []
    last_line = reader.line_num
    try:
        for cells in reader:
            first = last_line + 1
            raw_text = ''.join(lines[last_line:reader.line_num])
            last_line = reader.line_num
            if not cells:
                continue
            if len(cells) != len(headers):
                errors.append(Issue(first, 'falsche_spaltenzahl'))
                continue
            if last_line == len(lines) and not text.endswith(('\n', '\r')):
                errors.append(Issue(first, 'unvollstaendige_letzte_zeile'))
                continue
            raw = dict(zip(headers, cells))
            if raw['stand'] != expected_stand or raw[DEVICE_FIELD[profile]] != expected_device:
                errors.append(Issue(first, 'quellenzuordnung_widerspricht_konfiguration'))
                continue
            try:
                measured = utc_time(raw[TIME_FIELD[profile]])
            except ValueError:
                errors.append(Issue(first, 'ungueltiger_zeitstempel'))
                continue
            values, quality = {}, []
            for field in PROFILES[profile]:
                if field not in raw:
                    continue
                value = raw[field].strip()
                if not value:
                    values[field] = None
                    continue
                try:
                    number = Decimal(value)
                    converted = float(number)
                    if not number.is_finite() or not (-1e100 < converted < 1e100):
                        raise InvalidOperation
                    values[field] = converted
                except (InvalidOperation, ValueError, OverflowError):
                    values[field] = None
                    quality.append('ungueltige_zahl:' + field)
            identity = raw.get('message_id') if profile == 'boden' else None
            key = ['message_id', identity] if identity else [
                'timestamp-counters-v1', measured.isoformat(),
                raw.get('f_cnt', ''), raw.get('f_port', ''),
            ]
            event_key = hashlib.sha256(json.dumps(key, ensure_ascii=False).encode()).hexdigest()
            records.append(Record(
                measured, event_key, hashlib.sha256(raw_text.encode()).hexdigest(),
                first, values, raw, raw_text, tuple(quality),
            ))
    except csv.Error as exc:
        raise SourceFormatError('CSV-Struktur beschädigt; kein Checkpoint wird fortgeschrieben') from exc
    return ParsedFile(records, errors, unknown)
