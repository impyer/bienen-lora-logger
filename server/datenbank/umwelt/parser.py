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


def _normalize(headers, cells, raw_text, first, profile, expected_stand, expected_device):
    raw = dict(zip(headers, cells))
    if raw['stand'] != expected_stand or raw[DEVICE_FIELD[profile]] != expected_device:
        return Issue(first, 'quellenzuordnung_widerspricht_konfiguration')
    try:
        measured = utc_time(raw[TIME_FIELD[profile]])
    except ValueError:
        return Issue(first, 'ungueltiger_zeitstempel')
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
    return Record(
        measured, event_key, hashlib.sha256(raw_text.encode()).hexdigest(),
        first, values, raw, raw_text, tuple(quality),
    )

MAX_RECORD_BYTES = 64 * 1024


@dataclass(frozen=True)
class CsvHeader:
    fields: tuple
    unknown: tuple


class _CapturedLines:
    def __init__(self, lines):
        self.lines = iter(lines)
        self.parts = []
        self.size = 0

    def __iter__(self):
        return self

    def __next__(self):
        line = next(self.lines)
        self.size += len(line.encode('utf-8'))
        if self.size > MAX_RECORD_BYTES:
            raise SourceFormatError('csv_record_ueber_64_kib')
        self.parts.append(line)
        return line

    def take(self):
        raw = ''.join(self.parts)
        self.parts.clear(); self.size = 0
        return raw


def parse_stream(lines, profile, *, expected_stand, expected_device, header=None, first_line=1):
    """Yield header, Record or Issue; caller controls bounded binary I/O and commits.

    With an explicit header, first_line denotes the first physical suffix line.
    Each yielded item has consumed only its own record, never the complete file.
    """
    if profile not in PROFILES:
        raise SourceFormatError('Unbekanntes Quellenprofil')
    tracked = _CapturedLines(lines)
    reader = csv.reader(tracked, delimiter=';', strict=True)
    if header is None:
        try:
            fields = next(reader)
            fields[0] = fields[0].removeprefix('\ufeff')
        except (StopIteration, csv.Error, IndexError) as exc:
            raise SourceFormatError('CSV-Kopf fehlt oder ist beschädigt') from exc
        tracked.take()
    else:
        fields = list(header)
    if len(fields) != len(set(fields)) or not REQUIRED[profile].issubset(fields):
        raise SourceFormatError('CSV-Kopf enthält doppelte oder fehlende Pflichtspalten')
    known = set(PROFILES[profile]) | REQUIRED[profile] | TELEMETRY
    yield CsvHeader(tuple(fields), tuple(sorted(set(fields)-known)))
    last_line = reader.line_num
    try:
        for cells in reader:
            first = first_line + last_line
            last_line = reader.line_num
            raw_text = tracked.take()
            if not cells:
                continue
            if len(cells) != len(fields):
                yield Issue(first, 'falsche_spaltenzahl')
            elif not raw_text.endswith(('\n', '\r')):
                yield Issue(first, 'unvollstaendige_letzte_zeile')
            else:
                yield _normalize(fields,cells,raw_text,first,profile,expected_stand,expected_device)
    except csv.Error as exc:
        raise SourceFormatError('CSV-Struktur beschädigt; kein Checkpoint wird fortgeschrieben') from exc


def parse_csv(text, profile, *, expected_stand, expected_device):
    """Compatibility collector for existing small text inputs; file imports stream."""
    if len(text.encode('utf-8')) > 32 * 1024 * 1024:
        raise SourceFormatError('Quelldatei über 32 MiB; streaming verwenden')
    records, errors, unknown = [], [], []
    for item in parse_stream(io.StringIO(text,newline=''), profile,
                             expected_stand=expected_stand,expected_device=expected_device):
        if isinstance(item, CsvHeader):
            unknown = list(item.unknown)
        elif isinstance(item, Issue):
            errors.append(item)
        else:
            records.append(item)
    return ParsedFile(records,errors,unknown)
