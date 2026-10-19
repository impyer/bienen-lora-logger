#!/usr/bin/env python3
"""
ttn_zeitanalyse.py - prüft im Feldtest, WANN die beelogger senden.

Eingabe (eine oder mehrere Dateien, Format wird erkannt):
  * TTN-Konsole: Live data -> "Export as JSON" (Anwendung oder einzelnes Gerät)
  * TTN Storage Integration (eine JSON-Zeile je Nachricht, {"result": {...}})
  * Webhook-Mitschnitte (ApplicationUp-JSON, auch mehrere je Datei)
  * CSV aus der Simulation (sim_zeitsync --csv ...)

Zeitquelle je Uplink (beste zuerst):
  1. rx_metadata[].time    = Empfangszeit laut Gateway-Uhr (beim RAK7268V2 per NTP gestellt)
  2. rx_metadata[].received_at / uplink_message.received_at = Empfang beim TTN-Server
Daraus wird der Sendebeginn geschätzt: Empfangszeit - Airtime (consumed_airtime).

Ausgabe je Logger: Lage im Raster (Sekunde im 10-min-Takt), Streuung, Gang zwischen
Abgleichen, verlorene Pakete (FCnt-Lücken), kleinster Abstand zu anderen Loggern.

Nur Python-Standardbibliothek. Aufruf:
  python ttn_zeitanalyse.py export.json
  python ttn_zeitanalyse.py export.json --intervall 600 --nacht 23-6 --csv-aus uplinks.csv
"""
import argparse
import csv
import datetime as dt
import json
import math
import statistics
import sys
from collections import defaultdict


def zeit_parsen(s):
    """ISO-8601 von TTN (bis Nanosekunden, 'Z') -> Unix-Sekunden float."""
    if s is None:
        return None
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    # Nachkommastellen auf 6 kürzen (Python kann nur Mikrosekunden)
    if "." in s:
        kopf, rest = s.split(".", 1)
        ziffern = ""
        i = 0
        while i < len(rest) and rest[i].isdigit():
            ziffern += rest[i]
            i += 1
        s = kopf + "." + (ziffern[:6].ljust(6, "0")) + rest[i:]
    try:
        return dt.datetime.fromisoformat(s).timestamp()
    except ValueError:
        return None


def dauer_parsen(s):
    """'0.071936s' -> 0.071936"""
    if isinstance(s, (int, float)):
        return float(s)
    if isinstance(s, str) and s.endswith("s"):
        try:
            return float(s[:-1])
        except ValueError:
            return None
    return None


def objekte_finden(o):
    """Alle dicts mit end_device_ids + uplink_message bzw. DeviceTime-Ereignisse rekursiv finden."""
    if isinstance(o, dict):
        if "uplink_message" in o and "end_device_ids" in o:
            yield ("up", o)
        name = o.get("name", "")
        if isinstance(name, str) and "device_time" in name:
            yield ("dt", o)
        for v in o.values():
            yield from objekte_finden(v)
    elif isinstance(o, list):
        for v in o:
            yield from objekte_finden(v)


def json_lesen(text):
    text = text.strip()
    if not text:
        return []
    try:
        return [json.loads(text)]
    except json.JSONDecodeError:
        pass
    objs = []
    dec = json.JSONDecoder()
    i = 0
    while i < len(text):
        while i < len(text) and text[i] in " \r\n\t,":
            i += 1
        if i >= len(text):
            break
        o, j = dec.raw_decode(text, i)
        objs.append(o)
        i = j
    return objs


def datei_lesen(pfad, uplinks, zeitantworten):
    with open(pfad, encoding="utf-8") as f:
        text = f.read()
    if text.lstrip().startswith("device_id,"):
        for z in csv.DictReader(text.splitlines()):
            ende = float(z["tx_ende_utc_s"])
            start = float(z["tx_start_utc_s"])
            uplinks.append({"dev": z["device_id"], "t_rx": ende, "quelle": "sim", "air": ende - start,
                            "fcnt": None, "verloren": z.get("verloren") == "1"})
        return
    for o in json_lesen(text):
        for art, d in objekte_finden(o):
            if art == "up":
                um = d["uplink_message"]
                dev = d["end_device_ids"].get("device_id", "?")
                t_gw = None
                t_srv = None
                for md in um.get("rx_metadata", []) or []:
                    t = zeit_parsen(md.get("time"))
                    if t is not None and (t_gw is None or t < t_gw):
                        t_gw = t
                    t = zeit_parsen(md.get("received_at"))
                    if t is not None and (t_srv is None or t < t_srv):
                        t_srv = t
                if t_srv is None:
                    t_srv = zeit_parsen(um.get("received_at")) or zeit_parsen(d.get("received_at"))
                t_rx, quelle = (t_gw, "gateway") if t_gw is not None else (t_srv, "server")
                if t_rx is None:
                    continue
                uplinks.append({"dev": dev, "t_rx": t_rx, "quelle": quelle,
                                "air": dauer_parsen(um.get("consumed_airtime")) or 0.072,
                                "fcnt": um.get("f_cnt"), "verloren": False})
            else:
                t = zeit_parsen(d.get("time"))
                dev = "?"
                for idn in d.get("identifiers", []) or []:
                    dev = (idn.get("device_ids") or {}).get("device_id", dev)
                zeitantworten.append({"dev": dev, "t": t, "name": d.get("name")})


def theil_sen(xs, ys):
    st = []
    n = len(xs)
    schritt = max(1, n // 60)          # bei vielen Punkten ausdünnen
    idx = list(range(0, n, schritt))
    for i in range(len(idx)):
        for j in range(i + 1, len(idx)):
            dx = xs[idx[j]] - xs[idx[i]]
            if dx > 0:
                st.append((ys[idx[j]] - ys[idx[i]]) / dx)
    return statistics.median(st) if st else None


def gang_und_spruenge(L, abw):
    """Sprünge (Abgleich) erkennen, dazwischen Gang in s/Tag schätzen."""
    if len(L) < 20:
        return "-", []
    d = [abw[i + 1] - abw[i] for i in range(len(abw) - 1)]
    mad = statistics.median(abs(x) for x in d) or 0.01
    grenze = max(0.25, 6 * mad)
    spruenge = []
    segmente = [[0]]
    for i, x in enumerate(d):
        if abs(x) > grenze:
            spruenge.append((L[i + 1]["t_tx"], x))
            segmente.append([i + 1])
        else:
            segmente[-1].append(i + 1)
    steig = []
    for seg in segmente:
        if len(seg) < 12:
            continue
        xs = [L[k]["t_tx"] / 86400.0 for k in seg]
        if xs[-1] - xs[0] < 0.25:      # mindestens 6 h
            continue
        ys = [abw[k] for k in seg]
        m = theil_sen(xs, ys)
        if m is not None:
            steig.append(m)
    gang = ("%+.2f" % statistics.median(steig)) if steig else "-"
    return gang, spruenge


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dateien", nargs="+")
    ap.add_argument("--intervall", type=int, default=600, help="Tagesintervall in s (Standard 600)")
    ap.add_argument("--nacht", default="23-6", help="Nachtfenster Ortszeit, nur zur Info (Standard 23-6)")
    ap.add_argument("--warnabstand", type=float, default=2.0, help="Warnung, wenn zwei Logger näher senden (s)")
    ap.add_argument("--csv-aus", help="alle Uplinks mit berechneter Rasterlage als CSV schreiben")
    a = ap.parse_args()

    uplinks, zeitantworten = [], []
    for p in a.dateien:
        datei_lesen(p, uplinks, zeitantworten)
    # doppelte (mehrere Exporte) entfernen
    gesehen = set()
    rein = []
    for u in sorted(uplinks, key=lambda u: u["t_rx"]):
        k = (u["dev"], u["fcnt"], round(u["t_rx"], 1)) if u["fcnt"] is not None else (u["dev"], round(u["t_rx"], 3))
        if k in gesehen:
            continue
        gesehen.add(k)
        u["t_tx"] = u["t_rx"] - (u["air"] or 0.072)
        rein.append(u)
    uplinks = [u for u in rein if not u["verloren"]]
    if not uplinks:
        print("Keine Uplinks gefunden.")
        return 1

    intervall = a.intervall
    quellen = defaultdict(int)
    for u in uplinks:
        quellen[u["quelle"]] += 1
    t0, t1 = uplinks[0]["t_rx"], uplinks[-1]["t_rx"]
    print("=== Sendezeiten der beelogger ===")
    print("Zeitraum: %s bis %s UTC, %d Uplinks" % (dt.datetime.fromtimestamp(t0, dt.timezone.utc).strftime("%d.%m.%Y %H:%M"),
                                                    dt.datetime.fromtimestamp(t1, dt.timezone.utc).strftime("%d.%m.%Y %H:%M"),
                                                    len(uplinks)))
    print("Zeitquelle: " + ", ".join("%s %d" % (k, v) for k, v in quellen.items())
          + ("   (Gateway-Uhr = genauer; Server-Zeit enthält Internet-Laufzeit)" if "server" in quellen else ""))
    print()

    je = defaultdict(list)
    for u in uplinks:
        je[u["dev"]].append(u)

    print("Logger              Uplinks  verl.*  Lage im %d-s-Raster [s]   Streuung p5-p95 [s]  Gang zw. Abgleichen [s/Tag]" % intervall)
    zeilen = []
    spruenge_alle = {}
    for dev in sorted(je):
        L = je[dev]
        # Lage im Raster: Sendebeginn - 1 s (Weckzeit = Raster + Slot*Abstand + 1 s) modulo Intervall
        lagen = [((u["t_tx"] - 1.0) % intervall) for u in L]
        # zirkulärer Mittelwert, dann Abweichungen in (-intervall/2, intervall/2]
        w = [2 * math.pi * x / intervall for x in lagen]
        m = math.atan2(sum(math.sin(v) for v in w), sum(math.cos(v) for v in w)) * intervall / (2 * math.pi) % intervall
        abw = [((x - m + intervall / 2) % intervall) - intervall / 2 for x in lagen]
        abw_s = sorted(abw)
        p5 = abw_s[int(0.05 * (len(abw_s) - 1))]
        p95 = abw_s[int(0.95 * (len(abw_s) - 1))]
        # Gang und Korrekturen: Sprünge der Rasterlage erkennen (= Abgleich), dazwischen Steigung
        gang_s, spr = gang_und_spruenge(L, abw)
        spruenge_alle[dev] = spr
        # FCnt-Lücken
        fc = [u["fcnt"] for u in L if u["fcnt"] is not None]
        verl = "-"
        if len(fc) > 1:
            luecken = sum(max(0, b - a - 1) for a, b in zip(fc, fc[1:]) if 0 < b - a < 1000)
            verl = str(luecken)
        print("%-18s %8d %7s  %10.2f                %6.2f ... %+6.2f     %s" % (dev[:18], len(L), verl, m, p5, p95, gang_s))
        zeilen.append((dev, m))
    print("* verloren = Lücken im Frame-Counter (nur bei TTN-Export)")
    print()
    print("Erkannte Sprünge der Sendezeit (Uhrkorrekturen durch den Abgleich, > 0,25 s):")
    for dev in sorted(spruenge_alle):
        spr = spruenge_alle[dev]
        if spr:
            erster = spr[0][1]
            rest = sorted(abs(x[1]) for x in spr[1:])
            text = "  %-18s %3d Sprünge; erster %+.1f s" % (dev[:18], len(spr), erster)
            if abs(erster) > 30:
                text += " (vermutlich erster Abgleich: Ortszeit/Compile-Zeit -> UTC)"
            if rest:
                text += "; danach Betrag Median %.2f s, max %.2f s" % (statistics.median(rest), rest[-1])
            print(text)
        else:
            print("  %-18s keine" % dev[:18])
    print()

    # kleinster Abstand zwischen verschiedenen Loggern
    alle = sorted(uplinks, key=lambda u: u["t_tx"])
    nah = []
    for x, y in zip(alle, alle[1:]):
        if x["dev"] != y["dev"]:
            d = y["t_tx"] - x["t_tx"]
            nah.append((d, x, y))
    if nah:
        nah.sort(key=lambda z: z[0])
        d, x, y = nah[0]
        print("Kleinster Abstand zweier Logger: %.3f s (%s / %s am %s UTC)" % (
            d, x["dev"], y["dev"], dt.datetime.fromtimestamp(x["t_tx"], dt.timezone.utc).strftime("%d.%m. %H:%M:%S")))
        n_warn = sum(1 for z in nah if z[0] < a.warnabstand)
        print("Abstände unter %.1f s: %d von %d" % (a.warnabstand, n_warn, len(nah)))
    # Reihenfolge im Raster
    print()
    print("Reihenfolge im Raster (sollte LOGGER_SLOT entsprechen, Abstand ~ SLOT_ABSTAND_S):")
    zeilen.sort(key=lambda z: z[1])
    vorher = None
    doppelt = []
    for dev, m in zeilen:
        print("  %8.2f s  %s%s" % (m, dev, "" if vorher is None else "   (+%.2f s)" % (m - vorher)))
        if vorher is not None and m - vorher < a.warnabstand:
            doppelt.append(dev)
        vorher = m
    if doppelt:
        print("  WARNUNG: Logger mit fast gleicher Rasterlage (gleicher LOGGER_SLOT?): " + ", ".join(doppelt))
    if zeitantworten:
        print()
        print("DeviceTime-Ereignisse im Export: %d" % len(zeitantworten))
        for z in zeitantworten[:20]:
            print("  %s  %s  %s" % (dt.datetime.fromtimestamp(z["t"], dt.timezone.utc).strftime("%d.%m. %H:%M:%S") if z["t"] else "?",
                                    z["dev"], z["name"]))

    if a.csv_aus:
        with open(a.csv_aus, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["device_id", "utc", "sendebeginn_unix", "lage_im_raster_s", "fcnt", "zeitquelle"])
            for u in alle:
                w.writerow([u["dev"], dt.datetime.fromtimestamp(u["t_tx"], dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                            "%.3f" % u["t_tx"], "%.3f" % ((u["t_tx"] - 1.0) % intervall), u["fcnt"], u["quelle"]])
        print("\nCSV geschrieben: " + a.csv_aus)
    return 0


if __name__ == "__main__":
    sys.exit(main())
