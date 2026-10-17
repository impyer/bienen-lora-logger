# SPDX-License-Identifier: GPL-3.0-or-later
"""CSV domain checks, exclusively synthetic records; no network or devices."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'server/datenbank'))
from umwelt.parser import parse_csv, SourceFormatError

WEATHER = 'zeit_utc;stand;station;t;h;p_hpa;l;uv;wind_ms;wind_dir_deg;gust_ms;rain_mmh;rain_mm;f_cnt;f_port;payload_hex\n'
SOIL = 'time_utc;stand;device_id;temp_5cm;temp_20cm;temp_50cm;battery_v;alarm_status;message_id\n'


class ParserTests(unittest.TestCase):
    def parse(self, text, profile='s2120'):
        return parse_csv(text, profile, expected_stand='synthetic', expected_device='test-device')

    def test_zero_missing_negative_and_unknown_columns(self):
        text = WEATHER.rstrip() + ';future_column\n2026-10-25T00:30:00Z;synthetic;test-device;-2.5;;1013;0;0;0;359;0;0;7;1;3;AA;future\n'
        result = self.parse(text)
        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual(record.values['t'], -2.5)
        self.assertIsNone(record.values['h'])
        self.assertEqual(record.values['rain_mmh'], 0)
        self.assertEqual(record.raw['future_column'], 'future')
        self.assertIn('future_column', result.unmapped_fields)

    def test_three_depths_and_no_invented_missing_value(self):
        result = self.parse(SOIL + '2026-10-25T01:30:00Z;synthetic;test-device;12;;13;3.2;0;soil-1\n', 'boden')
        self.assertEqual(result.records[0].values['temp_5cm'], 12)
        self.assertIsNone(result.records[0].values['temp_20cm'])
        self.assertEqual(result.records[0].values['temp_50cm'], 13)

    def test_invalid_timestamp_rejected_and_invalid_number_visible(self):
        text = SOIL + 'no-time;synthetic;test-device;1;2;3;3.2;0;a\n' + '2026-10-25T00:30:00Z;synthetic;test-device;NaN;bad;3;3.2;0;b\n'
        result = self.parse(text, 'boden')
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.records), 1)
        self.assertIsNone(result.records[0].values['temp_5cm'])
        self.assertTrue(result.records[0].quality)

    def test_naive_time_and_foreign_device_not_accepted(self):
        result = self.parse(SOIL + '2026-10-25T01:30:00;synthetic;test-device;1;2;3;3;0;a\n' + '2026-10-25T01:30:00Z;other;wrong;1;2;3;3;0;b\n', 'boden')
        self.assertEqual(len(result.records), 0)
        self.assertEqual(len(result.errors), 2)

    def test_dst_hour_is_two_distinct_utc_observations(self):
        result = self.parse(SOIL + '2026-10-25T02:30:00+02:00;synthetic;test-device;1;2;3;3;0;a\n' + '2026-10-25T02:30:00+01:00;synthetic;test-device;4;5;6;3;0;b\n', 'boden')
        self.assertEqual((result.records[1].time - result.records[0].time).total_seconds(), 3600)

    def test_duplicate_header_and_malformed_csv_fail(self):
        with self.assertRaises(SourceFormatError):
            self.parse(SOIL.replace('temp_20cm', 'temp_5cm'), 'boden')
        with self.assertRaises(SourceFormatError):
            self.parse(SOIL + '"unterminated', 'boden')

    def test_partial_last_line_is_deferred(self):
        text = SOIL + '2026-10-25T00:30:00Z;synthetic;test-device;1;2;3;3;0;a'
        result = self.parse(text, 'boden')
        self.assertFalse(result.records)
        self.assertEqual(result.errors[0].code, 'unvollstaendige_letzte_zeile')


if __name__ == '__main__':
    unittest.main()
