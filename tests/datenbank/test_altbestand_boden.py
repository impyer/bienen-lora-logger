#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Tests für server/datenbank/altbestand_boden.py (ohne Datenbank). Aufruf: python3 tests/datenbank/test_altbestand_boden.py

Erste Zeile: echte Zeile des alten Boden-Eingangs vom 14.10.2026 (Hauptstand). Darin sind temp_5cm/temp_20cm
vertauscht (Dragino-Decoder); der Umsetzer muss aus dem Payload weiß 12,3 / rot 12,4 / schwarz 13,1 machen.
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server" / "datenbank"))
import altbestand_boden as ab  # noqa: E402

ECHT = ('{"time_utc":"2026-10-14T17:27:13.795443Z","stand":"hauptstand","device_id":"erdboden-temperatur",'
        '"temp_5cm":12.4,"temp_20cm":12.3,"temp_50cm":13.1,"battery_v":3.624,"alarm_status":0,"f_cnt":21,'
        '"f_port":2,"rssi":-87,"snr":13.25,"payload_base64":"DigAewAADAB8AIM=",'
        '"message_id":"4b7273aac4a1dcb06fd37e70c152526b991e8d04bd525e3741e6af067770acc9"}')
anz = fehler = 0


def pruefe(name, ok, info=""):
    global anz, fehler
    anz += 1
    if not ok:
        fehler += 1
        print(f"FEHL - {name}\n       {info}")


def zeile(t, fcnt, b64, **extra):
    d = json.loads(ECHT)
    d.update(time_utc=t, f_cnt=fcnt, payload_base64=b64, **extra)
    return json.dumps(d)


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    alt = tmp / "erdboden-temperatur_2026-10.jsonl"
    import base64
    frost = base64.b64encode(bytes.fromhex("0E28FF3F00000CFFFF00C8")).decode()       # weiß -19,3, rot fehlt, schwarz 20,0
    alarm = base64.b64encode(bytes.fromhex("0E280000F61E7CF61E1E0A")).decode()       # Modus 31: keine Messwerte
    alt.write_text("\n".join([ECHT, "kaputt", zeile("2026-10-15T01:00:00.1Z", 22, frost),
                              zeile("2026-10-15T02:00:00Z", 23, alarm),
                              zeile("2026-11-01T00:10:00Z", 24, "DigAewAADAB8AIM="),
                              zeile("2026-10-22T09:00:00.5Z", 99, "DigAewAADAB8AIM="), ""]) + "\n")
    umwelt = tmp / "umwelt_log"
    umwelt.mkdir()
    # derselbe Uplink (f_cnt 99) kam am 22.10. auch über den Umwelt-Webhook, Zeit mit Nanosekunden
    (umwelt / "2026-10.jsonl").write_text(json.dumps({"geraet": "erdboden-temperatur", "art": "uplink", "id": "x",
        "nachricht": {"received_at": "2026-10-22T09:00:00.512345678Z", "uplink_message": {
            "f_cnt": 99, "frm_payload": "DigAewAADAB8AIM=", "received_at": "2026-10-22T09:00:00.512345678Z"}}}) + "\n")

    dateien, ber = ab.umsetzen([alt], umwelt)
    pruefe("Bericht", ber == {"zeilen": 6, "uebernommen": 4, "schon_im_umwelt_protokoll": 1, "ohne_messwerte": 1,
                              "ungueltig": 1}, ber)
    pruefe("je Monat eine Datei", sorted(dateien) == ["2026-10.jsonl", "2026-11.jsonl"], sorted(dateien))
    z = [json.loads(x) for x in dateien["2026-10.jsonl"].decode().splitlines()]
    d0 = z[0]["nachricht"]["uplink_message"]["decoded_payload"]
    pruefe("echte Zeile: Farben aus dem Payload, nicht die vertauschten gespeicherten Werte",
           (d0["temp_weiss"], d0["temp_rot"], d0["temp_schwarz"], d0["BatV"]) == (12.3, 12.4, 13.1, 3.624), d0)
    pruefe("keine alten Namen", not {"Temp_Red", "Temp_White", "temp_5cm"} & set(d0), d0)
    pruefe("Kennung wie ein_nachricht_id", z[0]["id"] == hashlib.sha1(
        "erdboden-temperatur|2|21|DigAewAADAB8AIM=|2026-10-14T17:27:13.795443Z".encode()).hexdigest(), z[0]["id"])
    pruefe("Herkunft: Datei, Zeile, SHA-256 der Originalzeile",
           z[0]["herkunft"]["zeile"] == 1 and z[0]["herkunft"]["sha256"] == hashlib.sha256(ECHT.encode()).hexdigest(),
           z[0]["herkunft"])
    pruefe("Format für den Importer", z[0]["art"] == "uplink" and z[0]["geraet"] == "erdboden-temperatur"
           and z[0]["nachricht"]["received_at"] == "2026-10-14T17:27:13.795443Z"
           and z[0]["nachricht"]["uplink_message"]["rx_metadata"] == [{"rssi": -87, "snr": 13.25}], z[0])
    d1 = z[1]["nachricht"]["uplink_message"]["decoded_payload"]
    pruefe("Frost und fehlender Fühler", (d1["temp_weiss"], d1["temp_rot"], d1["temp_schwarz"]) == (-19.3, None, 20.0), d1)
    pruefe("Alarmabfrage ohne decoded_payload, aber als Rohnachricht", "decoded_payload" not in z[2]["nachricht"]["uplink_message"], z[2])
    pruefe("am 22.10. doppelt gelieferter Uplink ausgelassen", all(x["nachricht"]["uplink_message"]["f_cnt"] != 99 for x in z))

    # Wiederholbar: gleiche Ausgabe; vorhandene Datei mit anderem Inhalt wird nicht überschrieben
    ziel = tmp / "boden_alt"
    pruefe("erster Lauf", ab.main([str(alt), "--ziel", str(ziel), "--umwelt", str(umwelt)]) == 0)
    vorher = (ziel / "2026-10.jsonl").read_bytes()
    pruefe("zweiter Lauf gleich", ab.main([str(alt), "--ziel", str(ziel), "--umwelt", str(umwelt)]) == 0
           and (ziel / "2026-10.jsonl").read_bytes() == vorher)
    (ziel / "2026-10.jsonl").write_bytes(vorher + b"{}\n")
    pruefe("andere Zieldatei → Abbruch, nichts überschrieben",
           ab.main([str(alt), "--ziel", str(ziel)]) == 1 and (ziel / "2026-10.jsonl").read_bytes() == vorher + b"{}\n")

pruefe("Zeit mit Nanosekunden", abs(ab.zeit_unix("2026-10-22T09:00:00.512345678Z") - 1792659600.512345) < 1e-6,
       ab.zeit_unix("2026-10-22T09:00:00.512345678Z"))
print(f"{'OK' if not fehler else 'FEHLER'}: Altbestand Boden {anz - fehler} von {anz} Prüfungen bestanden")
sys.exit(1 if fehler else 0)
