#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Tests (ohne Datenbank) für server/datenbank/beep_base.py und altbestand_beep.py.
Aufruf: python3 tests/datenbank/test_beep_base.py

Sollwerte: echter Uplink der BEEPBASE-5A76 vom 23.10.2026 und Beispiele aus den Kommentaren des BEEP-Quelltexts,
jeweils gegengeprüft mit BEEPs eigenem Decoder (lokal, 23.10.2026). Kalibrierung aus BEEP (Sensordefinition 5A76).
"""
import base64
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server" / "datenbank"))
import altbestand_beep as ab  # noqa: E402
import beep_base as bb  # noqa: E402

anz = fehler = 0


def pruefe(name, ok, info=""):
    global anz, fehler
    anz += 1
    if not ok:
        fehler += 1
        print(f"FEHL - {name}\n       {info}")


ECHT = base64.b64decode("GwzIDMFkCgEVPEQEAQeRDAoJRgAMAAgACwAEAAQAAgACAAIAAgAABwAAAAAAACsAAAAC")
d = bb.dekodieren(ECHT, 3)
pruefe("echter Uplink 5A76", d == {"vcc": 3.272, "bv": 3.265, "bat_perc": 100, "w_v": 1391684, "t_i": 19.37,
       "s_bin_71_122": 12, "s_bin_122_173": 8, "s_bin_173_224": 11, "s_bin_224_276": 4, "s_bin_276_327": 4,
       "s_bin_327_378": 2, "s_bin_378_429": 2, "s_bin_429_480": 2, "s_bin_480_532": 2, "s_bin_532_583": 0}, d)
kg = (d["w_v"] - 83811) * 0.000024211515512725
pruefe("Kalibrierung aus BEEP: 31,67 kg (BEEP-Export Vorabend 31,72 kg)", abs(kg - 31.666) < 0.01, kg)
faktor, versatz = 0.000024211515512725, -83811 * 0.000024211515512725
pruefe("Kanal-Faktor/Versatz ergeben dasselbe", abs(d["w_v"] * faktor + versatz - kg) < 1e-9)

d = bb.dekodieren(bytes.fromhex("1b0c1b0c0e640a01fff69804020ad70add0c0a00ff00580012001000" "0c000d000a000a00090008000707000000000000"), 3)
pruefe("negativer Rohwert, zwei Temperaturen, ohne BME280", d and d["w_v"] == -2408 and d["t_0"] == 27.75
       and d["t_1"] == 27.81 and "t" not in d and "s_bin_0_510" not in d, d)
d = bb.dekodieren(bytes.fromhex("1b0d670d59640a01fffbeb040108340c0a0946000c0007000600040002000300030002000300000700000000000025" "60ad41030a"), 3)
pruefe("nachgesendet mit MCU-Zeit: Zeit ja, aber nicht als abgeglichen", d and d["Messzeit_unix"] == 1621967107
       and d["Status"] == {"zeit_ok": False}, d)
d = bb.dekodieren(bytes.fromhex("1b0d670d59640a01fffbeb040108340c0a0946000c000700060004000200030003000200030000"
                                "070a28138803f22d6960d743"), 3)
pruefe("BME280 und Echtzeituhr", d and (d["t"], d["h"], d["p"]) == (26.0, 50.0, 1010)
       and d["Messzeit_unix"] == 0x6960D743 and d["Status"] == {"zeit_ok": True}, d)
pruefe("anderer Port", bb.dekodieren(ECHT, 2) is None)
pruefe("kein Messbeginn 1B", bb.dekodieren(b"\x01\x02\x03\x04\x05\x06\x07", 3) is None)
pruefe("abgeschnitten", bb.dekodieren(ECHT[:9], 3) is None)
pruefe("leer / kein bytes", bb.dekodieren(b"", 3) is None and bb.dekodieren("1b", 3) is None)

# --- BEEP-Export
KOPF = ("time;Voltage (V);Temperature (°C);Weight (kg);Signal strength (dBm);Decibel (dB);- (-);- (-) - lon;"
        "- (-) - s_bin_71_122")
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    f = tmp / "beep-export-user-1-device-BEEPBASE-5A76-2026-10-01-2026-10-23-x.csv"
    f.write_text(KOPF + "\n2026-10-15T09:37:29Z;;;;-74;12.5;51.111;13.912;\n"
                 "2026-10-15T09:59:28Z;3.337;24.31;0.092028;-58;13.5;51.111;13.912;6\n"
                 "2026-10-23T04:16:41Z;3.265;19.37;31.66;-61;14;51.111;13.912;12\n"
                 "kaputt\n", encoding="utf-8")
    log = tmp / "bienen_log"
    log.mkdir()
    (log / "2026-10.jsonl").write_text('{"geraet":"my-beep-base-2","art":"uplink","nachricht":{"received_at":'
                                       '"2026-10-23T04:16:41.322990303Z"}}\n')
    dateien, ber = ab.umsetzen([f], {"BEEPBASE-5A76": "my-beep-base-2"}, log)
    pruefe("Bericht", ber == {"zeilen": 4, "uebernommen": 1, "ab_bienen_eingang": 1, "ohne_werte": 1, "ungueltig": 1}, ber)
    import json
    z = json.loads(dateien["2026-10.jsonl"].decode().splitlines()[0])
    up = z["nachricht"]["uplink_message"]
    pruefe("Zuordnung der Spalten (belegt am Payload)", up["decoded_payload"] == {"bv": 3.337, "t_i": 24.31,
           "weight_kg": 0.092028, "s_bin_71_122": 6.0} and up["rx_metadata"] == [{"rssi": -58.0, "snr": 13.5}], up)
    pruefe("Gerät = TTN-Name, Herkunft BEEP", z["geraet"] == "my-beep-base-2" and z["herkunft"]["beep_geraet"] == "BEEPBASE-5A76"
           and z["herkunft"]["zeile"] == 3, z)
    try:
        ab.umsetzen([f], {}, None)
        pruefe("ohne Gerätezuordnung → Abbruch", False)
    except SystemExit as e:
        pruefe("ohne Gerätezuordnung → Abbruch", "zuordnen" in str(e), e)
    g = tmp / "beep-export-user-1-device-BEEPBASE-5A76-y.csv"
    g.write_text("time;Weight (kg);Humidity (%)\n2026-10-15T09:59:28Z;1;2\n", encoding="utf-8")
    try:
        ab.umsetzen([g], {"BEEPBASE-5A76": "x"}, None)
        pruefe("unbekannte Spalte → Abbruch statt raten", False)
    except SystemExit as e:
        pruefe("unbekannte Spalte → Abbruch statt raten", "Humidity" in str(e), e)

print(f"{'OK' if not fehler else 'FEHLER'}: BEEP Base {anz - fehler} von {anz} Prüfungen bestanden")
sys.exit(1 if fehler else 0)
