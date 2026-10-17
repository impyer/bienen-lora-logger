# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded per-process immutable query pages, with authenticated expiring cursors."""
import base64
from collections import OrderedDict
from dataclasses import dataclass
import hmac
import json
import secrets
import threading
import time


MAX_POINTS = 40000
MAX_BYTES = 64 * 1024 * 1024
MAX_SNAPSHOTS = 4
TTL_SECONDS = 120


class CursorError(ValueError):
    pass


class SnapshotGone(ValueError):
    pass


class SnapshotDenied(ValueError):
    pass


class SnapshotBudgetError(ValueError):
    pass


@dataclass(frozen=True)
class Snapshot:
    identity: str
    actor: int
    query: tuple
    metadata: dict
    data: bytes
    expires: float


class SnapshotStore:
    def __init__(self, *, clock=time.monotonic, ttl=TTL_SECONDS,
                 max_bytes=MAX_BYTES, max_snapshots=MAX_SNAPSHOTS):
        self.clock, self.ttl = clock, ttl
        self.max_bytes, self.max_snapshots = max_bytes, max_snapshots
        self.entries = OrderedDict()
        self.lock = threading.Lock()
        self.secret = secrets.token_bytes(32)

    def _prune(self):
        for key in list(self.entries):
            if self.entries[key].expires <= self.clock():
                del self.entries[key]

    def create(self, actor, query, metadata, points):
        if len(points) > MAX_POINTS:
            raise SnapshotBudgetError('Mehr als 40000 Diagrammpunkte; Zeitraum/Kanalauswahl oder Auflösung anpassen')
        encoded = json.dumps(points, ensure_ascii=False, separators=(',', ':')).encode()
        if len(encoded) > self.max_bytes:
            raise SnapshotBudgetError('Speicherbudget für Diagramm-Snapshot überschritten')
        entry = Snapshot(secrets.token_urlsafe(18), actor, query, metadata,
                         encoded, self.clock()+self.ttl)
        with self.lock:
            self._prune()
            while self.entries and (len(self.entries) >= self.max_snapshots
                    or sum(len(x.data) for x in self.entries.values())+len(encoded) > self.max_bytes):
                self.entries.popitem(last=False)
            self.entries[entry.identity] = entry
        return entry

    def cursor(self, entry, offset):
        data = json.dumps([2, entry.identity, offset], separators=(',', ':')).encode()
        signature = hmac.digest(self.secret, data, 'sha256')[:16]
        return base64.urlsafe_b64encode(data+signature).decode()

    def resume(self, cursor, actor, query):
        try:
            raw = base64.b64decode(cursor, altchars=b'-_', validate=True)
            data, signature = raw[:-16], raw[-16:]
            version, identity, offset = json.loads(data)
            if version != 2 or not isinstance(identity, str) or type(offset) is not int or offset <= 0:
                raise ValueError
        except (ValueError, TypeError, UnicodeError) as exc:
            raise CursorError('Ungültiger v2-Cursor') from exc
        with self.lock:
            self._prune()
            entry = self.entries.get(identity)
            if entry is None:
                raise SnapshotGone('Snapshot abgelaufen oder App neu gestartet; Abfrage erneut beginnen')
            if not hmac.compare_digest(signature, hmac.digest(self.secret, data, 'sha256')[:16]):
                raise CursorError('Cursor-Signatur ungültig')
            if actor != entry.actor:
                raise SnapshotDenied('Snapshot nicht freigegeben')
            if query != entry.query:
                raise CursorError('Cursor gehört zu einer anderen Abfrage')
        return entry, offset
