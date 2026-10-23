#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Messdaten-Export aus BEEP (CSV je Gerät) für den Importer umsetzen (Quelle beep_alt).

BEEP exportiert je BEEP Base eine CSV (Trennzeichen ';') mit Spalten wie 'Weight (kg)' ohne BEEP-Kürzel.
Die Zuordnung Spalte → Kürzel ist an einer echten Nachricht belegt (22./23.10.2026: BEEPs eigener Decoder auf
ein Payload der Base, verglichen mit dem Export): Temperatur = t_i, Gewicht = weight_kg (in BEEP mit der
Kalibrierung des Geräts aus w_v berechnet), Spannung = bv, 'Decibel' = snr (Funk), 'Signal strength' = rssi.
Unbekannte Spalten brechen ab – geraten wird nicht.

- Gerät: der TTN-Gerätename (--geraet BEEPBASE-5A76=my-beep-base-2), damit Export und Bienen-Eingang dieselben
  Kanäle nutzen. Ohne Zuordnung bricht das Skript ab.
- Messzeit: Spalte time (BEEP speichert die Empfangszeit, die Base sendet keine Uhrzeit).
- Mit --bienen werden Zeilen ab dem ersten Uplink des Geräts im Bienen-Eingang (−60 s) ausgelassen (keine Doppelten).
- Ausgabe <ziel>/JJJJ-MM.jsonl; Herkunft je Zeile (Datei, Zeile, SHA-256); gleiche Eingabe → gleiche Ausgabe;
  vorhandene Zieldatei mit anderem Inhalt wird nicht überschrieben.

Aufruf:
    python3 server/datenbank/altbestand_beep.py --ziel /var/lib/bienen/beep_alt --bienen /var/lib/bienen/bienen_log \
        --geraet BEEPBASE-5A76=my-beep-base-2 --geraet BEEPBASE-D054=my-beep-base-1 beep-export-…-BEEPBASE-5A76-….csv …
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from altbestand_boden import ZEIT, umwelt_bekannt, zeit_unix  # noqa: E402,F401

SPALTEN = {"Voltage (V)": "bv", "Temperature (°C)": "t_i", "Weight (kg)": "weight_kg"}
FUNK = {"Signal strength (dBm)": "rssi", "Decibel (dB)": "snr"}
OHNE = {"- (-)", "- (-) - lon"}                      # Ort des Gateways, keine Messung
S_BIN = re.compile(r"^- \(-\) - (s_bin_\d+_\d+)$")
TOLERANZ_S = 60                      # Messungen kommen alle 5 min; 60 s trennen sicher
BEEP_NAME = re.compile(r"device-(BEEPBASE-[0-9A-Fa-f]+)-")


def zahl(s):
    s = (s or "").strip()
    if not s:
        return None
    v = float(s)
    return v if v == v and abs(v) != float("inf") else None


def erster_uplink(verz):
    """{Gerät: früheste Empfangszeit (Unix)} aus dem Bienen-Protokoll."""
    erst = {}
    for p in sorted(Path(verz).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].jsonl")) if verz else ():
        for z in p.read_bytes().split(b"\n"):
            try:
                e = json.loads(z)
                if e.get("art") != "uplink":
                    continue
                t = zeit_unix(e["nachricht"]["received_at"])
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            erst[e["geraet"]] = min(t, erst.get(e["geraet"], t))
    return erst


def umsetzen(dateien, zuordnung, bienen=None):
    erst = erster_uplink(bienen)
    aus = defaultdict(list)
    ber = {"zeilen": 0, "uebernommen": 0, "ab_bienen_eingang": 0, "ohne_werte": 0, "ungueltig": 0}
    for datei in dateien:
        datei = Path(datei)
        m = BEEP_NAME.search(datei.name)
        if not m or m.group(1) not in zuordnung:
            raise SystemExit(f"ABBRUCH: {datei.name}: BEEP-Gerät unbekannt – mit --geraet BEEPBASE-…=<TTN-Name> zuordnen")
        geraet = zuordnung[m.group(1)]
        roh = datei.read_bytes()
        zeilen = roh.split(b"\n")
        kopf = next(csv.reader(io.StringIO(zeilen[0].decode("utf-8-sig")), delimiter=";"))
        felder = []
        for k in kopf:
            if k == "time" or k in OHNE:
                felder.append(None)
            elif k in SPALTEN:
                felder.append(("d", SPALTEN[k]))
            elif k in FUNK:
                felder.append(("f", FUNK[k]))
            elif S_BIN.match(k):
                felder.append(("d", S_BIN.match(k).group(1)))
            else:
                raise SystemExit(f"ABBRUCH: {datei.name}: unbekannte Spalte {k!r} – Zuordnung erst klären")
        if "time" not in kopf:
            raise SystemExit(f"ABBRUCH: {datei.name}: Spalte time fehlt")
        it = kopf.index("time")
        for nr, z in enumerate(zeilen[1:], start=2):
            if not z.strip():
                continue
            ber["zeilen"] += 1
            try:
                w = next(csv.reader(io.StringIO(z.decode("utf-8")), delimiter=";"))
                t = w[it]
                t_unix = zeit_unix(t)
                if len(w) != len(kopf):
                    raise ValueError
                daten, funk = {}, {}
                for f, v in zip(felder, w):
                    if f and zahl(v) is not None:
                        (daten if f[0] == "d" else funk)[f[1]] = zahl(v)
            except (ValueError, StopIteration):
                ber["ungueltig"] += 1
                continue
            if geraet in erst and t_unix >= erst[geraet] - TOLERANZ_S:   # BEEP-Zeit auf die Sekunde, eigene Uhr
                ber["ab_bienen_eingang"] += 1
                continue
            if not daten:
                ber["ohne_werte"] += 1
                continue
            up = {"received_at": t, "decoded_payload": daten}
            if funk:
                up["rx_metadata"] = [funk]
            zeile = {"geraet": geraet, "art": "uplink",
                     "id": hashlib.sha1(f"beep_export|{geraet}|{t}".encode(), usedforsecurity=False).hexdigest(),
                     "herkunft": {"quelle": "BEEP-Export", "beep_geraet": m.group(1), "datei": datei.name, "zeile": nr,
                                  "sha256": hashlib.sha256(z).hexdigest()},
                     "nachricht": {"end_device_ids": {"device_id": geraet}, "received_at": t, "uplink_message": up}}
            aus[t[:7] + ".jsonl"].append(json.dumps(zeile, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
            ber["uebernommen"] += 1
    # zeitlich sortiert, damit mehrere Exporte in fester Reihenfolge landen
    return {n: ("\n".join(sorted(z, key=lambda x: json.loads(x)["nachricht"]["received_at"])) + "\n").encode()
            for n, z in aus.items()}, ber


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dateien", nargs="+", type=Path, help="CSV-Exporte aus BEEP (je Gerät)")
    ap.add_argument("--ziel", type=Path, required=True, help="Zielverzeichnis (Quelle beep_alt des Importers)")
    ap.add_argument("--geraet", action="append", default=[], help="BEEP-Name=TTN-Gerätename, je Base einmal")
    ap.add_argument("--bienen", type=Path, help="bienen_log: Zeilen ab dem ersten Uplink des Geräts auslassen")
    a = ap.parse_args(argv)
    zuordnung = dict(x.split("=", 1) for x in a.geraet if "=" in x)
    dateien, ber = umsetzen(a.dateien, zuordnung, a.bienen)
    a.ziel.mkdir(parents=True, exist_ok=True)
    for name, inhalt in sorted(dateien.items()):
        p = a.ziel / name
        if p.exists() and p.read_bytes() != inhalt:
            print(f"ABBRUCH: {p} gibt es schon mit anderem Inhalt – nichts geschrieben", file=sys.stderr)
            return 1
    for name, inhalt in sorted(dateien.items()):
        p = a.ziel / name
        if not p.exists():
            p.write_bytes(inhalt)
        print(f"{p}: {inhalt.count(10)} Zeilen")
    print(", ".join(f"{v} {k.replace('_', ' ')}" for k, v in ber.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
