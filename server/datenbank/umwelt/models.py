# SPDX-License-Identifier: GPL-3.0-or-later
"""Public measurement contracts shared by legacy raw and snapshot readers."""
from datetime import datetime
from pydantic import BaseModel


class Bucket(BaseModel):
    start: datetime
    end: datetime
    seconds: int
    method: str = 'observed-first-last-min-max'
    count: int
    missing: int
    minimum: float | None
    maximum: float | None
    quality: list[str]
    sources: list[str]
    time_qualities: list[str]
    synthetic_count: int


class Point(BaseModel):
    time: datetime
    value: float | None
    quality: list[str]
    time_quality: str
    revision: int
    source: str
    synthetic: bool
    raw_value: float | None
    record_sha256: str
    record_line: int
    interpretation: str
    imported_at: datetime
    event_revision: int
    bucket: Bucket | None = None
    gap_before: bool = False


class Channel(BaseModel):
    id: int
    name: str
    field: str
    quantity: str
    unit: str
    semantics: str
    display: str
    depth_cm: float | None
    profile: str
    interval_seconds: int | None
    device_id: int
    device_name: str
    position_id: int | None
    status: str
    calibration: str | None


class Series(BaseModel):
    channel: Channel
    points: list[Point]


class Measurements(BaseModel):
    timezone: str = 'Europe/Berlin'
    resolution: str = 'raw'
    series: list[Series]
    truncated: bool
    next_cursor: str | None


class SeriesSummary(BaseModel):
    source_points: int
    missing: int
    rendered_points: int
    method: str
    bucket_seconds: int
    first_time: datetime | None
    last_time: datetime | None


class DiagramSeries(Series):
    summary: SeriesSummary


class DiagramPage(BaseModel):
    version: int = 2
    snapshot: str
    as_of: datetime
    expires_at: datetime
    timezone: str = 'Europe/Berlin'
    series: list[DiagramSeries]
    source_points: int
    total_points: int
    offset: int
    returned_points: int
    complete: bool
    next_cursor: str | None
