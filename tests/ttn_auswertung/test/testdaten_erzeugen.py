#!/usr/bin/env python3
"""Erzeugt aus einer Simulations-CSV (sim_zeitsync --csv) Testdateien im Format der
TTN-Konsole (Live data -> Export as JSON) und der Storage Integration (NDJSON).
NUR für den Test von ttn_zeitanalyse.py - das sind keine echten TTN-Daten."""
import csv
import datetime as dt
import json
import sys

def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "123Z"  # ns-Stellen wie TTN

quelle, ziel_json, ziel_ndjson = sys.argv[1:4]
fcnt = {}
events, nd = [], []
for z in csv.DictReader(open(quelle)):
    dev = z["device_id"]
    fcnt[dev] = fcnt.get(dev, -1) + 1
    if z["verloren"] == "1":
        continue                      # verlorene Pakete kommen bei TTN nicht an
    ende = float(z["tx_ende_utc_s"])
    start = float(z["tx_start_utc_s"])
    up = {"end_device_ids": {"device_id": dev, "application_ids": {"application_id": "test-bienen"}},
          "received_at": iso(ende + 0.35),
          "uplink_message": {"f_port": 1, "f_cnt": fcnt[dev], "frm_payload": "AA==",
                             "rx_metadata": [{"gateway_ids": {"gateway_id": "rak7268v2"}, "time": iso(ende + 0.004),
                                              "timestamp": 12345, "rssi": -80, "received_at": iso(ende + 0.12)}],
                             "settings": {"data_rate": {"lora": {"bandwidth": 125000, "spreading_factor": 7}}},
                             "received_at": iso(ende + 0.30), "consumed_airtime": "%.6fs" % (ende - start)}}
    events.append({"name": "as.up.data.forward", "time": iso(ende + 0.36),
                   "identifiers": [{"device_ids": {"device_id": dev}}],
                   "data": dict(up, **{"@type": "type.googleapis.com/ttn.lorawan.v3.ApplicationUp"})})
    nd.append(json.dumps({"result": up}))
    if z["abfrage"] == "1":
        events.append({"name": "ns.mac.device_time.answer.enqueue", "time": iso(ende + 0.40),
                       "identifiers": [{"device_ids": {"device_id": dev}}], "data": {}})
json.dump(events, open(ziel_json, "w"), indent=1)
open(ziel_ndjson, "w").write("\n".join(nd) + "\n")
print(len(events), "Ereignisse,", len(nd), "Uplinks")
