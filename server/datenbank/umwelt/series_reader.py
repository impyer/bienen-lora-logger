# SPDX-License-Identifier: GPL-3.0-or-later
"""Streaming selection of original observations, preserving extrema and gaps."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import time

from .models import Bucket, Point, SeriesSummary
from .snapshots import MAX_POINTS

MAX_INPUT_POINTS = 2_000_000
MAX_QUERY_SECONDS = 20
ENVELOPE_QUANTITIES = frozenset({
    'temperatur', 'feuchte', 'luftdruck', 'beleuchtungsstaerke', 'uv_index',
    'windgeschwindigkeit', 'windboee', 'batterie_prozent', 'batteriespannung',
})


class SeriesBudgetError(ValueError):
    pass


def choose_interval(resolution, seconds, count, channel_count, requested=None):
    if resolution == 'raw' or (resolution == 'auto' and count <= 5000):
        return 0
    if requested is not None:
        return requested
    buckets = max(1, min(1000, int(MAX_POINTS * .6 / (6 * max(1, channel_count)))))
    return max(1, math.ceil(seconds/buckets))


@dataclass(frozen=True)
class Observation:
    row: tuple
    gap: bool

    @property
    def stamp(self):
        return self.row[1]

    @property
    def value(self):
        return self.row[2]


def point(observation, bucket=None):
    row = observation.row
    return Point(time=row[1], value=row[2], quality=row[3], time_quality=row[4],
        revision=row[5], source=row[6], synthetic=row[7], raw_value=row[8],
        record_sha256=row[9], record_line=row[10], interpretation=row[11],
        imported_at=row[12], event_revision=row[13], gap_before=observation.gap,
        bucket=bucket)


class Envelope:
    def __init__(self, stamp, seconds):
        self.start = datetime.fromtimestamp(math.floor(stamp.timestamp()/seconds)*seconds, timezone.utc)
        self.seconds = seconds
        self.count = self.missing = self.synthetic = 0
        self.first = self.last = self.low = self.high = None
        self.quality, self.sources, self.time_qualities = set(), set(), set()
        self.boundaries = {}

    def add(self, value, previous):
        if self.first is None:
            self.first = value
        self.last = value
        self.count += 1
        self.synthetic += int(value.row[7])
        self.quality.update(value.row[3])
        self.sources.add(value.row[6]); self.time_qualities.add(value.row[4])
        if max(len(self.quality),len(self.sources),len(self.time_qualities)) > 128:
            raise SeriesBudgetError('Zu viele Qualitäts-/Quellvarianten im Intervall')
        if value.value is None:
            self.missing += 1
        else:
            if self.low is None or value.value < self.low.value:
                self.low = value
            if self.high is None or value.value > self.high.value:
                self.high = value
        if previous and (value.gap or (previous.value is None) != (value.value is None)):
            self.boundaries[value.stamp] = value
            if previous.stamp >= self.start:
                self.boundaries[previous.stamp] = previous
        if len(self.boundaries) > MAX_POINTS:
            raise SeriesBudgetError('Zu viele echte Datenlücken; Zeitraum oder Kanalauswahl verkleinern')

    def finish(self):
        candidates = dict(self.boundaries)
        for item in (self.first, self.last, self.low, self.high):
            if item:
                candidates[item.stamp] = item
        stats = Bucket(start=self.start, end=self.start+timedelta(seconds=self.seconds),
            seconds=self.seconds, count=self.count, missing=self.missing,
            minimum=self.low.value if self.low else None,
            maximum=self.high.value if self.high else None,
            quality=sorted(self.quality), sources=sorted(self.sources),
            time_qualities=sorted(self.time_qualities), synthetic_count=self.synthetic)
        return [point(item, stats) for item in candidates.values()]


def select_observations(rows, definitions, seconds, *, clock=time.monotonic):
    """Rows must be ordered channel/time; memory is bounded by output, not input."""
    channels = {c.id:c for c in definitions}
    totals = {c.id:dict(count=0, missing=0, first=None, last=None, rendered=0) for c in definitions}
    chosen = []
    current_id, envelope, previous = None, None, None
    started, seen = clock(), 0

    def emit(kid, values):
        if len(chosen)+len(values) > MAX_POINTS:
            raise SeriesBudgetError('Mehr als 40000 Original-/Lückenpunkte; Zeitraum, Kanäle oder Auflösung anpassen. Keine vollständige Darstellung möglich.')
        chosen.extend((kid,p) for p in values)
        totals[kid]['rendered'] += len(values)

    for row in rows:
        seen += 1
        if seen > MAX_INPUT_POINTS or (seen % 1000 == 0 and clock()-started > MAX_QUERY_SECONDS):
            raise SeriesBudgetError('Abfrage überschreitet das Eingabe-/Zeitbudget')
        kid, stamp, value = row[:3]
        channel = channels[kid]
        aggregated = bool(seconds and channel.quantity in ENVELOPE_QUANTITIES)
        if kid != current_id:
            if envelope:
                emit(current_id, envelope.finish())
            envelope, previous, current_id = None, None, kid
        gap = bool(previous and channel.interval_seconds
            and (stamp-previous.stamp).total_seconds() > channel.interval_seconds*2.5)
        observation = Observation(row, gap)
        stats = totals[kid]
        stats['count'] += 1; stats['missing'] += int(value is None)
        stats['first'] = stats['first'] or stamp; stats['last'] = stamp
        if aggregated:
            if envelope is None or stamp >= envelope.start+timedelta(seconds=seconds):
                if envelope:
                    emit(kid, envelope.finish())
                envelope = Envelope(stamp, seconds)
            envelope.add(observation, previous)
        else:
            emit(kid, [point(observation)])
        previous = observation
    if envelope:
        emit(current_id, envelope.finish())
    chosen.sort(key=lambda pair:(pair[1].time,pair[0]))
    summaries = {}
    for c in definitions:
        stats = totals[c.id]
        aggregated = bool(seconds and c.quantity in ENVELOPE_QUANTITIES)
        summaries[c.id] = SeriesSummary(source_points=stats['count'], missing=stats['missing'],
            rendered_points=stats['rendered'], first_time=stats['first'], last_time=stats['last'],
            method='observed-first-last-min-max' if aggregated else 'raw',
            bucket_seconds=seconds if aggregated else 0).model_dump(mode='json')
    return [(kid,p.model_dump(mode='json')) for kid,p in chosen], summaries
