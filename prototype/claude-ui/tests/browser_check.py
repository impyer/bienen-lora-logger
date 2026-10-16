#!/usr/bin/env python3
"""Kompatibilitätseinstieg: aktueller Claude-Design-Browser-Test statt veralteter Sidebar-Assertions."""
from pathlib import Path
from runpy import run_path
run_path(str(Path(__file__).with_name('verify_claude_design.py')),run_name='__main__')
