#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Altbestand des früheren Boden-Eingangs (boden_eingang.php, bis 22.10.2026) für den Importer umsetzen.

Der alte Eingang schrieb je Uplink eine eigene Zeile (time_utc, device_id, temp_5cm …, payload_base64, message_id)
statt der TTN-Nachricht – und mit den Namen des Dragino-Decoders, der bei der LSN50v2-D23 weiß und rot vertauscht
(temp_5cm war in Wahrheit der rote Fühler in 20 cm). Dieses Skript übernimmt deshalb NICHT die gespeicherten
Temperaturen, sondern dekodiert jedes Payload neu wie formatter/lsn50v2_d23_formatter.js (temp_weiss = C1,
temp_rot = C2, temp_schwarz = C3) und schreibt Zeilen im Format der Eingänge nach <ziel>/JJJJ-MM.jsonl.
Der Importer liest sie mit --boden-alt (Quelle boden_alt).

- Kennung wie ein_nachricht_id(): sha1(gerät|f_port|f_cnt|frm_payload|received_at).
- Uplinks, die schon im Umwelt-Protokoll stehen (gleiches Gerät, f_cnt und Payload, Empfang ≤ 60 s auseinander;
  beide Webhooks liefen am 22.10. eine Zeit lang parallel), werden ausgelassen, damit nichts doppelt kommt.
- Jede Zeile verweist auf Datei, Zeilennummer und SHA-256 der Originalzeile (Herkunft nachvollziehbar).
- Ausgabe ist bei gleicher Eingabe Byte für Byte gleich. Eine vorhandene Zieldatei mit anderem Inhalt wird nicht
  überschrieben (der Importer merkt sich Leseposition und Prüfsumme je Datei).

Aufruf:
    python3 server/datenbank/altbestand_boden.py --ziel /var/lib/bienen/boden_alt \
        --umwelt /var/lib/bienen/umwelt_log /var/lib/bienen-logger/boden/hauptstand/erdboden-temperatur_2026-10.jsonl
"""
import argparse
import base64
import binascii
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ZEITFENSTER_S = 60


def dekodieren(b):
    """Wie formatter/lsn50v2_d23_formatter.js: dict der Messwerte oder None (anderer Modus, falsche Länge)."""
    if len(b) != 11 or (b[6] & 0x7C) >> 2 != 3:
        return None

    def temp(hi, lo):
        if b[hi] == 0xFF and b[lo] == 0xFF:
            return None
        v = (b[hi] << 8) | b[lo]
        return (v - 0x10000 if v & 0x8000 else v) / 10

    return {"Work_mode": "DS18B20", "BatV": ((b[0] << 8) | b[1]) / 1000,
            "ALARM_status": "TRUE" if b[6] & 0x01 else "FALSE",
            "temp_weiss": temp(2, 3), "temp_rot": temp(7, 8), "temp_schwarz": temp(9, 10)}


ZEIT = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?Z$")


def zeit_unix(s):
    """TTN-Zeit (bis Nanosekunden) in Unix-Sekunden; ValueError bei anderem Format."""
    m = ZEIT.match(s) if isinstance(s, str) else None
    if not m:
        raise ValueError(f"Zeit {s!r}")
    t = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    return t + (int((m.group(2) or "0")[:6].ljust(6, "0")) / 1e6)


def umwelt_bekannt(verz):
    """{(gerät, f_cnt, payload): [empfang_unix, …]} aus allen JJJJ-MM.jsonl des Umwelt-Protokolls."""
    bekannt = defaultdict(list)
    if verz is None:
        return bekannt
    for p in sorted(Path(verz).glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].jsonl")):
        for z in p.read_bytes().split(b"\n"):
            try:
                e = json.loads(z)
                up = e["nachricht"]["uplink_message"]
                t = up.get("received_at") or e["nachricht"]["received_at"]
                bekannt[(e["geraet"], up.get("f_cnt"), up.get("frm_payload"))].append(zeit_unix(t))
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
    return bekannt


def umsetzen(quellen, umwelt=None):
    """Liefert ({'JJJJ-MM.jsonl': bytes}, Bericht)."""
    bekannt = umwelt_bekannt(umwelt)
    aus = defaultdict(list)
    ber = {"zeilen": 0, "uebernommen": 0, "schon_im_umwelt_protokoll": 0, "ohne_messwerte": 0, "ungueltig": 0}
    for q in quellen:
        q = Path(q)
        for nr, roh in enumerate(q.read_bytes().split(b"\n"), start=1):
            if not roh.strip():
                continue
            ber["zeilen"] += 1
            try:
                d = json.loads(roh)
                geraet, t, b64 = d["device_id"], d["time_utc"], d["payload_base64"]
                f_port, f_cnt = int(d["f_port"]), int(d["f_cnt"])
                payload = base64.b64decode(b64, validate=True)
                t_unix = zeit_unix(t)
                if not (isinstance(geraet, str) and geraet and isinstance(t, str)):
                    raise ValueError
            except (ValueError, KeyError, TypeError, binascii.Error):
                ber["ungueltig"] += 1
                continue
            if any(abs(t_unix - u) <= ZEITFENSTER_S for u in bekannt.get((geraet, f_cnt, b64), ())):
                ber["schon_im_umwelt_protokoll"] += 1
                continue
            daten = dekodieren(payload) if f_port == 2 else None
            if daten is None:
                ber["ohne_messwerte"] += 1
            up = {"f_port": f_port, "f_cnt": f_cnt, "frm_payload": b64, "received_at": t}
            if daten is not None:
                up["decoded_payload"] = daten
            meta = {k: d[k] for k in ("rssi", "snr") if isinstance(d.get(k), (int, float))}
            if meta:
                up["rx_metadata"] = [meta]
            kennung = hashlib.sha1("|".join((geraet, str(f_port), str(f_cnt), b64, t)).encode(),
                                   usedforsecurity=False).hexdigest()   # Kennung wie PHP sha1(), kein Schutz
            zeile = {"geraet": geraet, "art": "uplink", "id": kennung,
                     "herkunft": {"eingang": "boden_eingang.php", "datei": str(q), "zeile": nr,
                                  "sha256": hashlib.sha256(roh).hexdigest()},
                     "nachricht": {"end_device_ids": {"device_id": geraet}, "received_at": t, "uplink_message": up}}
            monat = t[:7]
            aus[monat + ".jsonl"].append(json.dumps(zeile, ensure_ascii=False, separators=(",", ":")))
            ber["uebernommen"] += 1
    return {n: ("\n".join(z) + "\n").encode() for n, z in aus.items()}, ber


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("quellen", nargs="+", type=Path, help="Monatsdateien des alten Boden-Eingangs")
    ap.add_argument("--ziel", type=Path, required=True, help="Zielverzeichnis (Quelle boden_alt des Importers)")
    ap.add_argument("--umwelt", type=Path, help="umwelt_log: dort schon vorhandene Uplinks auslassen")
    a = ap.parse_args(argv)
    dateien, ber = umsetzen(a.quellen, a.umwelt)
    a.ziel.mkdir(parents=True, exist_ok=True)
    for name, inhalt in sorted(dateien.items()):      # erst alles prüfen, dann schreiben
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
