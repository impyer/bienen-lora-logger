# SPDX-License-Identifier: GPL-3.0-or-later
"""Real filesystem publication/fault recovery. No production input or API mocks."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
import time
import fcntl
from unittest.mock import patch

from support import SOIL_HEADER,soil_row,ROOT
from umwelt.staging_sync import sync_synthetic
from umwelt import staging_sync
from umwelt.ingest import SourceReadError


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'receiver';self.target=self.root/'staging';self.source.mkdir();self.target.mkdir()
        self.file=self.source/'soil-2026-10.csv';self.file.write_text(SOIL_HEADER+soil_row())
        self.config=dict(source=str(self.source),staging=str(self.target),pattern='soil-{YYYY}-{MM}.csv',
            profile='boden',source_stand='synthetic',source_device='synthetic-soil',synthetic=True)
    def tearDown(self):self.temp.cleanup()
    def run_sync(self):return sync_synthetic(self.config)
    def fingerprint(self):
        s=self.file.stat();return hashlib.sha256(self.file.read_bytes()).hexdigest(),s.st_size,s.st_mode,s.st_ino,s.st_mtime_ns,s.st_ctime_ns

    def test_month_append_correction_idempotence_and_unchanged_original(self):
        self.file.chmod(0o400);before=self.fingerprint()
        self.assertEqual(self.run_sync()['files'][0]['status'],'published');self.assertEqual(before,self.fingerprint())
        destination=self.target/self.file.name;inode=destination.stat().st_ino
        self.assertEqual(self.run_sync()['files'][0]['status'],'unchanged');self.assertEqual(inode,destination.stat().st_ino)
        self.file.chmod(0o600)
        self.file.write_text(self.file.read_text()+soil_row('2026-10-26T00:00Z','1;2;3','next'))
        self.run_sync();self.assertEqual(destination.read_bytes(),self.file.read_bytes())
        self.file.write_text(SOIL_HEADER+soil_row(values='22;;13'));self.run_sync()
        (self.source/'soil-2026-11.csv').write_text(SOIL_HEADER+soil_row('2026-11-01T00:00Z','1;2;3','nov'))
        self.assertEqual(len(self.run_sync()['files']),2)
        self.assertEqual(destination.read_bytes(),self.file.read_bytes())
        entries=[json.loads(line) for line in (self.target/'.bienen-sync.jsonl').read_text().splitlines()]
        self.assertTrue({'prepared','published','unchanged'}.issubset({e['status'] for e in entries}))
        self.assertNotIn(str(self.source),str(entries))

    def test_bad_and_partial_csv_keep_last_complete_version(self):
        self.run_sync();before=(self.target/self.file.name).read_bytes()
        for content in (b'bad;header\n',SOIL_HEADER.encode()+b'\xff\n',(SOIL_HEADER+soil_row()[:-1]).encode(),(SOIL_HEADER+soil_row(device='wrong')).encode()):
            self.file.write_bytes(content);self.assertFalse(self.run_sync()['success'])
            self.assertEqual((self.target/self.file.name).read_bytes(),before)
        self.file.write_text(SOIL_HEADER+soil_row(values='25;;13'));self.assertTrue(self.run_sync()['success'])

    def test_unexpected_valid_truncation_cannot_erase_last_staged_copy(self):
        self.run_sync();before=(self.target/self.file.name).read_bytes()
        self.file.write_text(SOIL_HEADER)
        self.assertFalse(self.run_sync()['success'])
        self.assertEqual((self.target/self.file.name).read_bytes(),before)

    def test_publication_failure_and_source_change_leave_no_partial_destination(self):
        with patch.object(staging_sync.os,'replace',side_effect=OSError('synthetic interruption')):
            self.assertFalse(self.run_sync()['success'])
        self.assertFalse((self.target/self.file.name).exists());self.assertFalse(list(self.target.glob('*.part')))
        original=staging_sync.hash_prefix;once=[False]
        def changing(stream,size,deadline):
            digest=original(stream,size,deadline)
            if not once[0]:
                once[0]=True
                with self.file.open('a') as f:f.write(soil_row('2026-10-26T00:00Z','1;2;3','changed'))
            return digest
        with patch.object(staging_sync,'hash_prefix',side_effect=changing):self.assertFalse(self.run_sync()['success'])
        self.assertFalse((self.target/self.file.name).exists());self.assertTrue(self.run_sync()['success'])

    def test_source_target_symlinks_special_files_and_real_declaration_rejected(self):
        with self.assertRaises(ValueError):sync_synthetic(dict(self.config,synthetic=False))
        with self.assertRaises(ValueError):sync_synthetic(dict(self.config,staging=str(self.source)))
        with self.assertRaises(ValueError):sync_synthetic(dict(self.config,pattern='../{YYYY}-{MM}.csv'))
        link=self.root/'alias';link.symlink_to(self.source,target_is_directory=True)
        with self.assertRaises(SourceReadError):sync_synthetic(dict(self.config,source=str(link)))
        self.file.unlink();os.mkfifo(self.file)
        with self.assertRaises(SourceReadError):self.run_sync()
        self.file.unlink();self.file.write_text(SOIL_HEADER+soil_row())
        (self.target/self.file.name).symlink_to(self.file)
        self.assertFalse(self.run_sync()['success']);self.assertTrue((self.target/self.file.name).is_symlink())

    def test_interrupted_temporary_copy_is_never_discovered_as_archive(self):
        (self.target/'.bienen-sync-abandoned.part').write_text('synthetic partial')
        self.assertTrue(self.run_sync()['success'])
        self.assertEqual([p.name for p in self.target.glob('soil-*.csv')],[self.file.name])

    def test_exclusive_publisher_hardlinks_and_staging_permissions(self):
        with (self.target/'.bienen-sync.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(SourceReadError,'bereits_aktiv'):self.run_sync()
        os.link(self.file,self.target/self.file.name)
        self.assertFalse(self.run_sync()['success'])
        (self.target/self.file.name).unlink()
        self.target.chmod(0o777)
        try:
            with self.assertRaisesRegex(ValueError,'Schreibzugriffe'):self.run_sync()
        finally:self.target.chmod(0o700)
        self.assertTrue(self.run_sync()['success'])

    def test_real_periodic_cli_discovers_new_month_without_database_credentials(self):
        config=self.root/'config.json';config.write_text(json.dumps(self.config))
        env=dict(os.environ,PYTHONPATH=str(ROOT/'server/datenbank'))
        for key in ('BIENEN_TEST_DSN','BIENEN_AUTH_DSN','BIENEN_AUTH_SECRET','BIENEN_IMPORT_DSN'):env.pop(key,None)
        with (self.root/'cli.log').open('w') as log:
            process=subprocess.Popen([sys.executable,'-m','umwelt.cli','sync-synthetic','--config',str(config),'--interval','5'],env=env,stdout=log,stderr=log)
            try:
                def wait_for(path):
                    deadline=time.monotonic()+12
                    while not path.exists() and time.monotonic()<deadline and process.poll() is None:time.sleep(.05)
                    self.assertTrue(path.exists(),(self.root/'cli.log').read_text())
                wait_for(self.target/self.file.name)
                next_month=self.source/'soil-2026-11.csv';next_month.write_text(SOIL_HEADER+soil_row('2026-11-01T00:00Z','1;2;3','periodic'))
                wait_for(self.target/next_month.name)
            finally:process.terminate();process.wait(timeout=5)
