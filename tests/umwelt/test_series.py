# SPDX-License-Identifier: GPL-3.0-or-later
import base64
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest

from support import ROOT
from umwelt.series_reader import select_observations, choose_interval, SeriesBudgetError
from umwelt.snapshots import SnapshotStore, SnapshotGone, SnapshotDenied, CursorError


START = datetime(2026,10,25,tzinfo=timezone.utc)


def observation(kid, minute, value, *, quality=None):
    return (kid,START+timedelta(minutes=minute),value,quality or [],'empfang',1,
            'synthetic',True,value,'a'*64,minute+2,'fixture@1',START,1)


class ReductionTests(unittest.TestCase):
    def test_extrema_missing_and_quality_keep_original_timestamps(self):
        c = SimpleNamespace(id=1,quantity='temperatur',interval_seconds=60)
        rows = [observation(1,i,v,quality=['sensor_warnung'] if i==3 else [])
                for i,v in enumerate([2,99,3,None,4,-17,5])]
        points, summary = select_observations(rows,[c],3600)
        rendered = [p for _,p in points]
        self.assertTrue({99,-17,None}.issubset({p['value'] for p in rendered}))
        self.assertTrue({p['time'] for p in rendered}.issubset({row[1].isoformat().replace('+00:00','Z') for row in rows}))
        bucket = rendered[0]['bucket']
        self.assertEqual((bucket['minimum'],bucket['maximum'],bucket['count'],bucket['missing']),(-17,99,7,1))
        self.assertEqual(bucket['quality'],['sensor_warnung'])
        self.assertEqual(summary[1]['source_points'],7)

    def test_counters_direction_status_and_unknown_quantity_remain_raw(self):
        for name in ['regen_summe','windrichtung','alarm_status','unbekannt','sendeintervall']:
            c=SimpleNamespace(id=1,quantity=name,interval_seconds=60)
            rows=[observation(1,i,v) for i,v in enumerate([359,1,0,7,None])]
            points,summary=select_observations(rows,[c],86400)
            self.assertEqual([p['value'] for _,p in points],[359,1,0,7,None])
            self.assertTrue(all(p['bucket'] is None for _,p in points))
            self.assertEqual(summary[1]['method'],'raw')

    def test_real_gap_preserved_but_omitted_observations_are_not_a_gap(self):
        c=SimpleNamespace(id=1,quantity='temperatur',interval_seconds=60)
        rows=[observation(1,i,i) for i in range(30)]+[observation(1,80,30)]
        points,_=select_observations(rows,[c],3600)
        gaps=[p['time'] for _,p in points if p['gap_before']]
        self.assertEqual(gaps,[(START+timedelta(minutes=80)).isoformat().replace('+00:00','Z')])
        self.assertIn((START+timedelta(minutes=29)).isoformat().replace('+00:00','Z'),[p['time'] for _,p in points])

    def test_auto_and_raw_resolution_budgets_are_explicit(self):
        self.assertEqual(choose_interval('raw',86400,99999,3),0)
        self.assertEqual(choose_interval('auto',86400,5000,3),0)
        self.assertGreater(choose_interval('auto',86400,5001,3),0)


class SnapshotTests(unittest.TestCase):
    def test_expiry_and_eviction_never_reuse_another_snapshot(self):
        now=[0.0]
        store=SnapshotStore(clock=lambda:now[0],ttl=10,max_snapshots=1)
        first=store.create(1,('q',),{},[(1,{'value':1})])
        token=store.cursor(first,1)
        now[0]=11
        with self.assertRaises(SnapshotGone):store.resume(token,1,('q',))
        second=store.create(1,('q',),{},[(1,{'value':2})])
        store.create(1,('q',),{},[(1,{'value':3})])
        with self.assertRaises(SnapshotGone):store.resume(store.cursor(second,1),1,('q',))

    def test_query_actor_and_cursor_signature_are_bound(self):
        store=SnapshotStore()
        first=store.create(1,('q',),{},[(1,{'value':1})])
        token=store.cursor(first,1)
        with self.assertRaises(SnapshotDenied):store.resume(token,2,('q',))
        with self.assertRaises(CursorError):store.resume(token,1,('other',))
        raw=bytearray(base64.urlsafe_b64decode(token));raw[-1]^=1
        with self.assertRaises(CursorError):store.resume(base64.urlsafe_b64encode(raw).decode(),1,('q',))
        for invalid in ['xxx','',base64.urlsafe_b64encode(b'not-json').decode()]:
            with self.assertRaises(CursorError):store.resume(invalid,1,('q',))

    def test_memory_limit_refuses_oversize_snapshot(self):
        store=SnapshotStore(max_bytes=10)
        with self.assertRaises(ValueError):store.create(1,(),{},[(1,{'value':'long-value'})])
