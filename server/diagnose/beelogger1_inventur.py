#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only metadata inventory for a single beelogger directory.

Does NOT print records, original values, paths to secret files, config content,
authentication material, radio identifiers, or raw payloads. Never executes PHP.
It cannot prove which physical sensors are attached.
"""
import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Positional CSV layout from beelogger_log.php, Single M.40.
# Three columns can mean bee-counter fields instead of power/service values.
SINGLE_COLUMNS = [
    "zeit", "temp_in", "temp_out", "feuchte_in_oder_temp2", "feuchte_out",
    "licht", "gewicht_korrigiert", "vbatt_oder_bienen_in",
    "vsolar_oder_bienen_out", "service_oder_bienendifferenz",
    "gewicht_quelle", "aux1", "aux2", "aux3",
    "reserviert_1", "reserviert_2", "unix",
]
LORA_FIELDS = [
    "zeit_utc", "unix", "zeitquelle", "geraet", "f_cnt", "f_port",
    "rssi", "snr", "gateways", "sf", "format", "firmware_id",
    "temp_cpu", "temp_in2", "fft_hz", "fft_db", "fft_gesamt_db",
    "fft_baender_db", "status", "neustart", "warnungen", "antwort_beelogger",
]
FILES = ("week.csv", "month.csv", "beelogger.csv", "lora_zusatz.csv")


def stat_info(path):
    if path.is_symlink() or not path.is_file():
        return {"vorhanden": False, "hinweis": "fehlt oder Symlink (nicht gelesen)"}
    stat = path.stat()
    return {
        "vorhanden": True,
        "groesse_bytes": stat.st_size,
        "geaendert_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def analyze_csv(path, limit):
    result = stat_info(path)
    if not result["vorhanden"]:
        return result
    is_extra = path.name == "lora_zusatz.csv"
    sep = ";" if is_extra else ","
    counts = Counter()
    nonempty = Counter()
    n = 0
    header = []
    fmt_counts = Counter()
    format_index = None
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.reader(handle, delimiter=sep)
            for row in reader:
                if not row or all(not x.strip() for x in row):
                    continue
                if is_extra and not header:
                    header = [x.strip() for x in row]
                    format_index = header.index("format") if "format" in header else None
                    continue
                counts[len(row)] += 1
                n += 1
                allowed = LORA_FIELDS if is_extra else SINGLE_COLUMNS
                for i, key in enumerate(allowed):
                    if i < len(row) and row[i].strip():
                        nonempty[key] += 1
                if is_extra and format_index is not None and format_index < len(row):
                    if row[format_index] in ("1", "2"):
                        fmt_counts[row[format_index]] += 1
                if n >= limit:
                    break
    except (OSError, csv.Error) as exc:
        result["lesefehler_typ"] = type(exc).__name__
        return result
    result["untersuchte_datenzeilen"] = n
    result["stichprobe_begrenzt"] = n >= limit
    result["feldanzahlen"] = {str(k): counts[k] for k in sorted(counts)}
    result["nichtleere_bekannte_felder"] = dict(nonempty)
    if is_extra:
        result["bekannte_headerfelder"] = [x for x in LORA_FIELDS if x in header]
        result["formatverteilung"] = dict(fmt_counts)
        result["hinweis"] = "Header und Dateninhalte wurden nicht ausgegeben."
    else:
        result["hinweis"] = (
            "17 Spalten werden nur nach M.40-Single-Layout bezeichnet. "
            "Spaltenbelegung ist kein Nachweis des Sensors oder der physikalischen Bedeutung."
        )
    return result


def run(root, limit):
    result = {
        "art": "beelogger1_sichere_strukturinventur",
        "stand": "Entwurfsdiagnose, kein physischer Sensornachweis",
        "dateien": {},
    }
    if root.is_symlink() or not root.is_dir():
        result["fehler"] = "Logger-Verzeichnis fehlt oder ist ein Symlink."
        return result
    for name in FILES:
        result["dateien"][name] = analyze_csv(root / name, limit)
    result["quelltext_dateien_nur_vorhandensein"] = {
        name: (root / name).is_file() and not (root / name).is_symlink()
        for name in ("beelogger_log.php", "beelogger_config.php", "beelogger_show.php")
    }
    result["warnungen"] = [
        "Es wurden keine Geheimnisse/Konfigurationsinhalte und keine Messwerte ausgegeben.",
        "Die Dateistruktur beweist weder angeschlossene Sensoren noch aktuelle Echtmessungen.",
        "FeuchteIn und Aux-Felder sind ohne geprüfte Firmware-/Pfadkonfiguration nicht eindeutig.",
        "Bitte keine vollständigen PHP-Konfigurationen, Webhook-Logs oder Rohdaten öffentlich teilen.",
    ]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path("/var/www/bienen-logger/beelogger1"),
        help="Pfad zum beelogger1-Verzeichnis (nur lesen)",
    )
    parser.add_argument(
        "--max-zeilen", type=int, default=50000,
        help="Obergrenze der zu pruefenden Datenzeilen je CSV (1..1000000)",
    )
    args = parser.parse_args()
    if not 1 <= args.max_zeilen <= 1000000:
        parser.error("--max-zeilen muss zwischen 1 und 1000000 liegen")
    print(json.dumps(run(args.root, args.max_zeilen), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
