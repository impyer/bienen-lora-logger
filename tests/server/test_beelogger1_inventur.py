#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline unit tests for the read-only beelogger channel inventory."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "server" / "diagnose" / "beelogger1_inventur.py"
spec = importlib.util.spec_from_file_location("beelogger1_inventur", MODULE_PATH)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def test_no_raw_data_or_secrets_in_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = "SECRET_SHOULD_NEVER_APPEAR"
            row = [
                "2026-10-12 12:00", "34.5", "12.5", "78", "", "100",
                "42.1", "3.8", "", "", "41.9", "", "", "", "", "", "1791806400",
            ]
            (root / "week.csv").write_text(",".join(row) + "\n", encoding="utf-8")
            (root / "beelogger_config.php").write_text(
                '<?php $password="' + secret + '";', encoding="utf-8"
            )
            (root / "lora_zusatz.csv").write_text(
                "zeit_utc;format;geraet;warnungen\n"
                "2026-10-12T12:00:00Z;2;" + secret + ";not for output\n",
                encoding="utf-8"
            )
            result = inventory.run(root, 100)
            encoded = json.dumps(result, ensure_ascii=False)
            self.assertNotIn(secret, encoded)
            self.assertNotIn("2026-10-12T12:00:00Z", encoded)
            self.assertNotIn("not for output", encoded)
            self.assertNotIn("34.5", encoded)
            self.assertEqual(result["dateien"]["week.csv"]["untersuchte_datenzeilen"], 1)
            self.assertEqual(result["dateien"]["week.csv"]["feldanzahlen"], {"17": 1})
            self.assertEqual(
                result["dateien"]["lora_zusatz.csv"]["formatverteilung"], {"2": 1}
            )

    def test_missing_files_and_no_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = inventory.run(root, 100)
            self.assertFalse(result["dateien"]["week.csv"]["vorhanden"])
            self.assertNotIn("fehler", result)
            self.assertIn("fehler", inventory.run(root / "nichtvorhanden", 100))

    def test_limits_and_symlink_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "month.csv").write_text(
                ("x," * 16 + "x\n") * 3, encoding="utf-8"
            )
            (root / "week.csv").symlink_to(root / "month.csv")
            result = inventory.run(root, 2)
            self.assertTrue(result["dateien"]["month.csv"]["stichprobe_begrenzt"])
            self.assertEqual(result["dateien"]["month.csv"]["untersuchte_datenzeilen"], 2)
            self.assertFalse(result["dateien"]["week.csv"]["vorhanden"])


if __name__ == "__main__":
    unittest.main()
