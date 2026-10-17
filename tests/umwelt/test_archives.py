# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import tempfile
import unittest

from support import reset_database, source, soil_row, SOIL_HEADER
from umwelt.ingest import import_source, register_source


class ArchiveTests(unittest.TestCase):
    def test_explicit_monthly_source_discovers_following_month(self):
        conn = reset_database()
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                first = root/'soil-2026-10.csv'
                first.write_text(SOIL_HEADER+soil_row())
                existing = source(conn, first)
                stand, device = conn.execute('SELECT stand_id,geraet_id FROM bienen.um_quelle WHERE id=%s', (existing,)).fetchone()
                archive = register_source(conn, key='monthly', profile='boden', path=root,
                    pattern='soil-{YYYY}-{MM}.csv', stand_id=stand, device_id=device,
                    source_stand='synthetic', source_device='synthetic-soil', synthetic=True,
                    valid_from='2026-01-01T00:00:00Z', time_quality='unbekannt')
                import_source(conn, archive)
                (root/'soil-2026-11.csv').write_text(SOIL_HEADER+soil_row('2026-11-01T00:30:00Z','25;26;27','msg-nov'))
                import_source(conn, archive)
                count = conn.execute('SELECT count(DISTINCT zeit) FROM bienen.um_messwert_aktuell WHERE quelle_id=%s', (archive,)).fetchone()[0]
                self.assertEqual(count,2)
        finally:
            conn.close()
