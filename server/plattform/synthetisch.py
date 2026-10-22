#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Synthetische Testdaten für die Plattform: ein Oktober 2026 mit Fehlern und Grenzfällen.

Erzeugt
  * Rohprotokolle im Format der Eingänge (server/eingang/ ein_rohprotokoll): lora_log/2026-10.jsonl
    (Herkunftsfeld "geraet") und wetter_log/2026-10.jsonl ("station"). Diese liest server/datenbank/importer.py
    ein – so läuft die ganze Kette Eingang → Importer → Datenbank → Lese-API.
  * Stammdaten und Stockkarte direkt per SQL (dafür gibt es noch keinen Eingang).

Eingebaute Fehler und Grenzfälle (FAELLE gibt die Zeitpunkte für die Tests):
  Logger 2 zwei Tage aus (Lücke) · Winterzeit-Nacht 25.10. · Uhr nicht abgeglichen · doppelte Zustellung ·
  FCnt-Rücksprung bei 16384 · DS18B20 −127 °C und 85 °C · Gewichtsspitze · Füttern, Tarieren und Umsetzen mit
  Gewichtssprung samt Maßnahme · Vereinigung (Zuordnung der Waage endet, Logger sendet weiter) · Kanalwechsel nach
  Sensortausch · unbekanntes Quellfeld und unbekanntes Gerät · Regenzähler-Rücksetzung · Windrichtung um 0/360° ·
  leerer Uplink nach Join · defekte JSON-Zeile · halbe letzte Zeile · Behandlung als Zeitraum (K-04) ·
  Durchsicht nur mit Datum (K-03) · Windelzählung.

Nur für Testdatenbanken: Das Schema "bienen" wird gelöscht und neu angelegt.
    BIENEN_TEST_DSN="dbname=bienen_test ..." python3 server/plattform/synthetisch.py --verzeichnis /tmp/syn
"""
import argparse
import base64
import hashlib
import json
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from api import katalog

HIER = Path(__file__).resolve().parent
SCHEMA = HIER.parent / "datenbank" / "schema.sql"

UTC = timezone.utc
START = datetime(2026, 10, 1, tzinfo=UTC)
ENDE = datetime(2026, 11, 1, tzinfo=UTC)
TAKT = timedelta(minutes=30)


def z(s):
    """'2026-10-15 12:00' (UTC) → datetime"""
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


# Zeitpunkte der Grenzfälle (UTC); die Tests prüfen genau diese
FAELLE = {
    "luecke": (z("2026-10-10 06:00"), z("2026-10-12 06:00")),       # Logger 2 sendet nicht
    "uhr_falsch": (z("2026-10-05 00:00"), z("2026-10-06 00:00")),   # Logger 2: zeit_ok false
    "ds18b20_minus127": z("2026-10-08 03:00"),                      # Logger 2 TempIn
    "ds18b20_85": z("2026-10-08 03:30"),
    "gewichtsspitze": z("2026-10-09 13:00"),                        # Logger 2 +50 kg für einen Wert
    "fuettern": z("2026-10-03 15:00"),                              # Volk 1 +10 kg
    "tarieren": z("2026-10-22 09:00"),                              # Volk 1 −30 kg (Waage auf 0 + Volkgewicht neu)
    "vereinigung": z("2026-10-15 12:00"),                           # Volk 3 → Volk 1
    "umsetzen": z("2026-10-20 10:00"),                              # Volk 4 in neue Beute, −4 kg Leergewicht
    "kanalwechsel": z("2026-10-18 08:00"),                          # Logger 1 TempIn: Sensortausch, Versatz −0,5
    "winterzeit": (z("2026-10-24 23:30"), z("2026-10-25 02:30")),   # 7 Messungen, Ortszeit 01:30 … 03:30 mit doppelter Stunde
    "regen_reset": z("2026-10-16 06:00"),
    "join_leer": z("2026-10-16 05:50"),                            # Station startet neu (vor regen_reset)
    "behandlung": (z("2026-10-01 08:00"), z("2026-10-11 08:00")),   # K-04, Volk 2
    "durchsicht_nur_datum": z("2026-10-07 10:00"),                  # K-03 (12:00 Ortszeit, aus BEEP übernommen)
    "durchsicht_exakt": z("2026-10-02 12:30"),
    "windel": (z("2026-10-12 10:00"), z("2026-10-15 10:00")),
    # Randfälle, damit Tests Vorzeichen, Grenzen und Verwechslungen erkennen (PLT26-16)
    "sprung_negativ": z("2026-10-27 12:00"),                       # Volk 4 −3 kg ohne erfasste Maßnahme (Schwarm?)
    "kurzausfall": (z("2026-10-27 06:00"), z("2026-10-27 07:30")),  # Logger 4: 3 Nachrichten fehlen, Abstand 120 min
    "ungueltig": z("2026-10-20 03:00"),                             # Logger 1 TempIn 99,9 °C, nach Import als ungültig markiert
}
VERSATZ_STATION = 1.5   # Luft an der Wetterstation wärmer als der Außenfühler am Kasten: Verwechslungen fallen auf
FCNT_START = 16000      # Logger 1 läuft am 08.10. über 16383 und beginnt wieder bei 0 (ABP-Reset, bewusst akzeptiert)
DOPPELT_JEDE = 97       # jede 97. Nachricht stellt TTN ein zweites Mal zu

# Standardkatalog und Vorlagen der Verwaltung (api/katalog.py); im Testbestand fehlt bei der Wetterstation
# absichtlich der Kanal für "l" (Helligkeit), und FeuchteIn der Logger hat keinen (K-06 „unbenannt“)
MESSGROESSEN = katalog.MESSGROESSEN
LOGGER_KANAELE = katalog.VORLAGEN["beelogger"]["kanaele"]
WETTER_KANAELE = [(feld, groesse) for feld, groesse, _ in katalog.VORLAGEN["s2120"]["kanaele"] if feld != "l"]


# ---------------------------------------------------------------- Modell der Messwerte (ohne Datenbank)

def ortsstunde(t):
    """Stunde in Mitteleuropa (für Tagesgang; Sommerzeit bis 25.10. 01:00 UTC)."""
    versatz = 2 if t < z("2026-10-25 01:00") else 1
    return (t.hour + versatz + t.minute / 60) % 24


def tagesgang(t):
    """0 nachts, 1 um 14 Uhr Ortszeit"""
    return max(0.0, math.sin(math.pi * (ortsstunde(t) - 7) / 14)) if 7 <= ortsstunde(t) <= 21 else 0.0


class Modell:
    """Völker, Waagen und Wetter als deterministische Funktionen der Zeit (fester Seed für das Rauschen)."""

    def __init__(self, seed=1):
        self.r = random.Random(seed)

    def gewicht(self, logger, t):
        tage = (t - START).total_seconds() / 86400
        g = {1: 32.0, 2: 28.0, 3: 18.0, 4: 24.0}[logger] - 0.04 * tage    # Winterzehrung
        g -= 0.6 * tagesgang(t)                                         # Flugbienen tagsüber unterwegs
        if logger == 1:
            if t >= FAELLE["fuettern"]:
                g += 10.0
            if t >= FAELLE["vereinigung"]:
                g += 6.0                                                # Volk 3 aufgesetzt
            if t >= FAELLE["tarieren"]:
                g -= 30.0
        if logger == 3 and t >= FAELLE["vereinigung"]:
            g = 0.4                                                     # leere Waage, Logger sendet weiter
        if logger == 4 and t >= FAELLE["umsetzen"]:
            g -= 4.0                                                    # leichtere Beute
        if logger == 4 and t >= FAELLE["sprung_negativ"]:
            g -= 3.0                                                    # ohne Maßnahme: muss als Sprung gemeldet werden
        if logger == 2 and t == FAELLE["gewichtsspitze"]:
            g += 50.0
        return round(g + self.r.gauss(0, 0.02), 3)

    def temp_in(self, logger, t):
        if logger == 2 and t == FAELLE["ds18b20_minus127"]:
            return -127.0
        if logger == 2 and t == FAELLE["ds18b20_85"]:
            return 85.0
        if logger == 1 and t == FAELLE["ungueltig"]:
            return 99.9
        if logger == 3 and t >= FAELLE["vereinigung"]:
            return round(self.temp_aussen(t) + 1, 2)
        roh = 33.5 - 0.5 * logger + self.r.gauss(0, 0.1)
        if logger == 1 and t >= FAELLE["kanalwechsel"]:
            roh += 0.5                                                  # neuer Sensor zeigt 0,5 K zu viel
        return round(roh, 2)

    def temp_aussen(self, t):
        tage = (t - START).total_seconds() / 86400
        return round(12 - 0.2 * tage + 7 * tagesgang(t) - 3, 2)

    def feuchte_aussen(self, t):
        return round(85 - 25 * tagesgang(t), 1)

    def wetter(self, t):
        tage = (t - START).total_seconds() / 86400
        richtung = (360 + 12 * math.sin(tage * 3.1)) % 360               # pendelt um 0/360°
        regen_mmh = 2.4 if 4 <= ortsstunde(t) < 7 and int(tage) % 3 == 0 else 0.0
        return {
            "t": round(self.temp_aussen(t) + VERSATZ_STATION, 2), "h": self.feuchte_aussen(t), "p_hpa": round(1003 + 6 * math.sin(tage / 2), 1),
            "l": round(40000 * tagesgang(t)), "uv": round(4 * tagesgang(t), 1),
            "wind_ms": round(2 + 1.5 * tagesgang(t), 1), "gust_ms": round(4 + 3 * tagesgang(t), 1),
            "wind_dir_deg": round(richtung), "rain_mmh": regen_mmh,
        }


# ---------------------------------------------------------------- Rohprotokolle

def ttn_text(t, us=0):
    return t.strftime("%Y-%m-%dT%H:%M:%S") + f".{us:06d}000Z"


def nachricht_id(msg):
    """Wie ein_nachricht_id() in server/eingang/eingang_funktionen.php"""
    up = msg.get("uplink_message") if isinstance(msg.get("uplink_message"), dict) else {}
    empf = up.get("received_at", msg.get("received_at", ""))
    teile = [msg.get("end_device_ids", {}).get("device_id", ""), str(up.get("f_port", "")), str(up.get("f_cnt", "")),
             str(up.get("frm_payload", "")), str(empf)]
    return hashlib.sha1("|".join(teile).encode(), usedforsecurity=False).hexdigest()   # Kennung, kein Schutz


def uplink(geraet, fport, fcnt, empfang, daten, rssi=-90):
    payload = base64.b64encode(hashlib.sha256(json.dumps(daten, sort_keys=True).encode()).digest()[:12]).decode()
    up = {"f_port": fport, "f_cnt": fcnt, "frm_payload": payload, "decoded_payload": daten,
          "rx_metadata": [{"gateway_ids": {"gateway_id": "gw-syn"}, "rssi": rssi, "snr": 7.5}],
          "settings": {"data_rate": {"lora": {"bandwidth": 125000, "spreading_factor": 7}}},
          "received_at": empfang}
    return {"end_device_ids": {"device_id": geraet}, "received_at": empfang, "uplink_message": up}


def protokollzeile(herkunft_feld, geraet, msg, log_zeit):
    """Eine Zeile wie ein_rohprotokoll(): Herkunft, art, id, roh_sha256, nachricht, log_zeit"""
    roh = json.dumps(msg, ensure_ascii=False, separators=(",", ":"))
    e = {herkunft_feld: geraet, "art": "uplink", "id": nachricht_id(msg),
         "roh_sha256": hashlib.sha256(roh.encode()).hexdigest(), "nachricht": msg, "log_zeit": log_zeit}
    return json.dumps(e, ensure_ascii=False, separators=(",", ":"))


def zeitpunkte():
    t = START
    while t < ENDE:
        yield t
        t += TAKT


def logger_zeilen(m):
    """Zeilen für lora_log/2026-10.jsonl in Empfangsreihenfolge"""
    zeilen, fcnt, nr = [], {1: FCNT_START, 2: 0, 3: 0, 4: 0}, 0
    for t in zeitpunkte():
        for lg in (1, 2, 3, 4):
            if lg == 2 and FAELLE["luecke"][0] <= t < FAELLE["luecke"][1]:
                continue
            if lg == 4 and FAELLE["kurzausfall"][0] <= t < FAELLE["kurzausfall"][1]:
                continue
            uhr_ok = not (lg == 2 and FAELLE["uhr_falsch"][0] <= t < FAELLE["uhr_falsch"][1])
            daten = {"Format": 2, "TempIn": m.temp_in(lg, t), "TempOut": m.temp_aussen(t),
                     "FeuchteIn": 60 + lg, "FeuchteOut": m.feuchte_aussen(t), "Gewicht": m.gewicht(lg, t),
                     "VBatt": round(3.95 - 0.002 * (t - START).days, 3),
                     "Status": {"zeit_ok": uhr_ok, "fehler_aussen": False, "fehler_ds1": False, "akku_niedrig": False},
                     "Messzeit_unix": int(t.timestamp()) if uhr_ok else 1600000000 + nr}
            empfang = t + timedelta(seconds=5 + lg)          # ohne abgeglichene Uhr gilt diese Zeit
            msg = uplink(f"beelogger-0{lg}", 2, fcnt[lg], ttn_text(empfang, 123456), daten)
            fcnt[lg] = (fcnt[lg] + 1) % 16384
            zeile = protokollzeile("geraet", f"beelogger-0{lg}", msg, ttn_text(empfang + timedelta(seconds=1))[:19] + "Z")
            zeilen.append(zeile)
            nr += 1
            if nr % DOPPELT_JEDE == 0:
                zeilen.append(zeile)                         # TTN stellt dieselbe Nachricht noch einmal zu
            zeilen.append(json.dumps({"geraet": f"beelogger-0{lg}", "art": "ergebnis", "klasse": "gespeichert",
                                      "id": nachricht_id(msg)}, separators=(",", ":")))
        if t == z("2026-10-14 12:00"):
            zeilen.append('{"geraet":"beelogger-02","art":"uplink","id":"kaputt",')   # defekte JSON-Zeile
        if t.hour == 12 and t.minute == 0 and t.day in (3, 17):             # unbekanntes Gerät
            msg = uplink("beelogger-99", 2, t.day, ttn_text(t + timedelta(seconds=9)), {"Gewicht": 11.1, "TempIn": 20.0})
            zeilen.append(protokollzeile("geraet", "beelogger-99", msg, ttn_text(t)[:19] + "Z"))
    return zeilen


def wetter_zeilen(m):
    zeilen, fcnt, offset = [], 0, 0.0
    summe = 0.0
    for t in zeitpunkte():
        if t == FAELLE["regen_reset"]:                         # nach Neustart: Join, erster Uplink ohne Nutzdaten
            leer = uplink("wetterstation-01", 3, 0, ttn_text(FAELLE["join_leer"]), {})
            del leer["uplink_message"]["decoded_payload"], leer["uplink_message"]["frm_payload"]
            zeilen.append(protokollzeile("station", "wetterstation-01", leer, ttn_text(FAELLE["join_leer"])[:19] + "Z"))
        d = m.wetter(t)
        summe += d["rain_mmh"] * 0.5
        if t == FAELLE["regen_reset"]:
            offset = summe                                     # Station neu gestartet: Zähler beginnt bei 0
        d["rain_mm"] = round(summe - offset, 3)
        msg = uplink("wetterstation-01", 3, fcnt, ttn_text(t + timedelta(seconds=2), 476207), d, rssi=-66)
        fcnt += 1
        zeilen.append(protokollzeile("station", "wetterstation-01", msg, ttn_text(t)[:19] + "Z"))
    return zeilen


def protokolle_schreiben(verz, seed=1):
    """Schreibt <verz>/lora_log/2026-10.jsonl und <verz>/wetter_log/2026-10.jsonl.
    Rückgabe: {'lora_log': Pfad, 'wetter_log': Pfad} für importer.importieren()."""
    m = Modell(seed)
    verz = Path(verz)
    aus = {}
    for quelle, zeilen in (("lora_log", logger_zeilen(m)), ("wetter_log", wetter_zeilen(m))):
        d = verz / quelle
        d.mkdir(parents=True, exist_ok=True)
        text = "\n".join(zeilen) + "\n"
        if quelle == "lora_log":
            text += '{"geraet":"beelogger-01","art":"uplink","id":"halb'      # Eingang schreibt gerade: halbe Zeile
        (d / "2026-10.jsonl").write_text(text, encoding="utf-8", newline="\n")
        aus[quelle] = d
    return aus


# ---------------------------------------------------------------- Stammdaten und Stockkarte (SQL)

def bereich(von, bis=None):
    return f"[{von.isoformat()},{bis.isoformat() if bis else ''})"


def stammdaten_schreiben(cur):
    """Testbestand. Rückgabe: Kennungen {'volk1': id, …, 'stand1': id, …} für die Tests."""
    def eins(sql, p=()):
        cur.execute(sql, p)
        return cur.fetchone()[0]

    k = {}
    cur.executemany("""INSERT INTO messgroesse(code,name,einheit,semantik,verdichtung,achse,darstellung,farbe,oeffentlich)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", MESSGROESSEN)
    k["stand1"] = eins("INSERT INTO stand(name, ort_oeffentlich) VALUES ('Hauptstand (synthetisch)','Radeberg') RETURNING id")
    k["stand2"] = eins("INSERT INTO stand(name, ort_oeffentlich) VALUES ('Wiese (synthetisch)','Radeberg') RETURNING id")
    beginn = START - timedelta(days=60)
    for i, (stand, platz) in enumerate([("stand1", 1), ("stand1", 2), ("stand1", 3), ("stand2", 1)], start=1):
        k[f"volk{i}"] = eins("INSERT INTO volk(name, entstanden_am) VALUES (%s, %s) RETURNING id", (f"Volk {i} (syn)", beginn))
        k[f"beute{i}"] = eins("INSERT INTO beute(bezeichnung, beutentyp) VALUES (%s,'Segeberger 1,5') RETURNING id",
                              (f"Beute {i}",))
        cur.execute("INSERT INTO beute_konfiguration(beute_id,gueltig,brutzargen,honigzargen) VALUES (%s,%s,%s,0)",
                    (k[f"beute{i}"], bereich(beginn), 1 if i != 2 else 2))
        cur.execute("INSERT INTO aufstellung(beute_id,stand_id,gueltig,platz) VALUES (%s,%s,%s,%s)",
                    (k[f"beute{i}"], k[stand], bereich(beginn), platz))
    # Volk 3 wird am 15.10. mit Volk 1 vereinigt: Belegung, Volk und Waagenzuordnung enden
    v = FAELLE["vereinigung"]
    for i in (1, 2, 4):
        bis = FAELLE["umsetzen"] if i == 4 else None
        cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,%s)",
                    (k[f"volk{i}"], k[f"beute{i}"], bereich(beginn, bis)))
    cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,%s)", (k["volk3"], k["beute3"], bereich(beginn, v)))
    cur.execute("UPDATE volk SET aufgeloest_am = %s WHERE id = %s", (v, k["volk3"]))
    e = eins("INSERT INTO volk_ereignis(art, zeit, notiz) VALUES ('vereinigung', %s, 'synthetisch') RETURNING id", (v,))
    cur.executemany("INSERT INTO volk_ereignis_teil(ereignis_id,volk_id,rolle) VALUES (%s,%s,%s)",
                    [(e, k["volk3"], "quelle"), (e, k["volk1"], "bleibt")])
    # Volk 4 zieht am 20.10. in eine neue Beute auf derselben Waage am selben Platz
    k["beute5"] = eins("INSERT INTO beute(bezeichnung, beutentyp) VALUES ('Beute 5','Segeberger 1,5') RETURNING id")
    u = FAELLE["umsetzen"]
    cur.execute("UPDATE aufstellung SET gueltig = %s WHERE beute_id = %s", (bereich(beginn, u), k["beute4"]))
    cur.execute("INSERT INTO aufstellung(beute_id,stand_id,gueltig,platz) VALUES (%s,%s,%s,1)", (k["beute5"], k["stand2"], bereich(u)))
    cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,%s)", (k["volk4"], k["beute5"], bereich(u)))
    kgn = eins("INSERT INTO koenigin(jahrgang,farbe,rasse,gezeichnet) VALUES (2026,'grün','Carnica',true) RETURNING id")
    cur.execute("INSERT INTO koenigin_volk(koenigin_id,volk_id,gueltig) VALUES (%s,%s,%s)", (kgn, k["volk1"], bereich(beginn)))

    # Geräte, Zuordnungen, Messstellen, Kanäle
    for i in (1, 2, 3, 4):
        g = eins("INSERT INTO geraet(name, art, modell) VALUES (%s,'stockwaage','BlackPill RFM95') RETURNING id",
                 (f"beelogger-0{i}",))
        k[f"geraet{i}"] = g
        cur.execute("INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,%s)",
                    (g, k[f"volk{i}"], bereich(beginn, v if i == 3 else None)))
        for feld, groesse, zone in LOGGER_KANAELE:
            ms = eins("INSERT INTO messstelle(volk_id, zone) VALUES (%s,%s) RETURNING id", (k[f"volk{i}"], zone))
            if i == 1 and feld == "TempIn":      # Sensortausch: neuer Kanal mit Versatz und Kalibrierangabe
                w = FAELLE["kanalwechsel"]
                cur.execute("""INSERT INTO kanal(geraet_id,quellfeld,messgroesse_code,messstelle_id,gueltig,status,sensor)
                               VALUES (%s,%s,%s,%s,%s,'geprueft','DS18B20 alt')""", (g, feld, groesse, ms, bereich(beginn, w)))
                cur.execute("""INSERT INTO kanal(geraet_id,quellfeld,messgroesse_code,messstelle_id,versatz,gueltig,status,
                                                 kalibriert_am,kalibrierung,sensor)
                               VALUES (%s,%s,%s,%s,-0.5,%s,'geprueft',%s,'Vergleich mit Referenzthermometer','DS18B20 neu')""",
                            (g, feld, groesse, ms, bereich(w), w))
            else:
                cur.execute("""INSERT INTO kanal(geraet_id,quellfeld,messgroesse_code,messstelle_id,gueltig)
                               VALUES (%s,%s,%s,%s,%s)""", (g, feld, groesse, ms, bereich(beginn)))
    w = eins("INSERT INTO geraet(name, art, modell) VALUES ('wetterstation-01','wetter','SenseCAP S2120') RETURNING id")
    k["wetter"] = w
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,stand_id,gueltig) VALUES (%s,%s,%s)", (w, k["stand1"], bereich(beginn)))
    ms = eins("INSERT INTO messstelle(stand_id, zone) VALUES (%s,'luft_stand') RETURNING id", (k["stand1"],))
    for feld, groesse in WETTER_KANAELE:
        cur.execute("INSERT INTO kanal(geraet_id,quellfeld,messgroesse_code,messstelle_id,gueltig) VALUES (%s,%s,%s,%s,%s)",
                    (w, feld, groesse, ms, bereich(beginn)))

    # Stockkarte
    cur.execute("INSERT INTO durchsicht(volk_id,zeit,notiz) VALUES (%s,%s,'Brut auf 6 Waben, ruhig')",
                (k["volk1"], FAELLE["durchsicht_exakt"]))
    cur.execute("""INSERT INTO durchsicht(volk_id,zeit,zeitgenauigkeit,notiz,quelle)
                   VALUES (%s,%s,'nur_datum','aus BEEP übernommen, Uhrzeit 12:00 gesetzt','beep_import')""",
                (k["volk2"], FAELLE["durchsicht_nur_datum"]))
    b0, b1 = FAELLE["behandlung"]
    cur.execute("""INSERT INTO massnahme(volk_id,art,zeitraum,menge,einheit,mittel,notiz)
                   VALUES (%s,'behandlung',%s,60,'ml','Ameisensäure 60 %%','AS-Verdunster')""", (k["volk2"], bereich(b0, b1)))
    eine_minute = timedelta(minutes=1)
    for volk, art, t, menge, einheit in [("volk1", "fuetterung", FAELLE["fuettern"], 10, "kg"),
                                         ("volk1", "tarieren", FAELLE["tarieren"], None, None),
                                         ("volk4", "umsetzen", FAELLE["umsetzen"], None, None)]:
        cur.execute("INSERT INTO massnahme(volk_id,art,zeitraum,menge,einheit) VALUES (%s,%s,%s,%s,%s)",
                    (k[volk], art, bereich(t - eine_minute, t + eine_minute), menge, einheit))
    w0, w1 = FAELLE["windel"]
    cur.execute("INSERT INTO varroa_messung(volk_id,zeitraum,methode,milben) VALUES (%s,%s,'windel',45)",
                (k["volk2"], bereich(w0, w1)))
    return k


# ---------------------------------------------------------------- alles zusammen

def ist_testdatenbank(con):
    return "test" in con.info.dbname


def aufbauen(con, verz, seed=1):
    """Schema neu laden, Stammdaten schreiben, Protokolle erzeugen und importieren. Rückgabe: (Kennungen, Bericht)."""
    sys.path.insert(0, str(HIER.parent / "datenbank"))
    import importer                                   # server/datenbank/importer.py

    con.autocommit = True
    con.execute(SCHEMA.read_text(encoding="utf-8"))
    con.autocommit = False
    with con.cursor() as cur:
        cur.execute("SET search_path = bienen, public")
        k = stammdaten_schreiben(cur)
    con.commit()
    bericht = importer.importieren(con, protokolle_schreiben(verz, seed))
    # Von Hand als ungültig markierter Messwert (wie eine spätere Plausibilitätsprüfung, PLT26-11): darf in keine
    # Kurve und keinen Mittelwert eingehen
    with con.cursor() as cur:
        cur.execute("""UPDATE bienen.messwert m SET qualitaet = 'ungueltig' FROM bienen.kanal k JOIN bienen.geraet g ON g.id = k.geraet_id
                       WHERE m.kanal_id = k.id AND g.name = 'beelogger-01' AND k.quellfeld = 'TempIn' AND m.zeit = %s""",
                    (FAELLE["ungueltig"],))
        assert cur.rowcount == 1, cur.rowcount
    con.commit()
    return k, bericht


def main(argv=None):
    ap = argparse.ArgumentParser(description="Synthetische Testdaten in eine Testdatenbank laden (löscht das Schema bienen)")
    ap.add_argument("--dsn", default=os.environ.get("BIENEN_TEST_DSN"))
    ap.add_argument("--verzeichnis", type=Path, required=True, help="Ziel für lora_log/ und wetter_log/")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ziel-ist-test", action="store_true", help="auch wenn der Datenbankname nicht 'test' enthält")
    a = ap.parse_args(argv)
    if not a.dsn:
        ap.error("--dsn oder BIENEN_TEST_DSN angeben")
    import psycopg
    with psycopg.connect(a.dsn) as con:
        if not (ist_testdatenbank(con) or a.ziel_ist_test):
            print(f"Abbruch: Datenbank '{con.info.dbname}' ist keine Testdatenbank (Name ohne 'test')", file=sys.stderr)
            return 2
        k, bericht = aufbauen(con, a.verzeichnis, a.seed)
    print(bericht.text())
    print("Kennungen:", json.dumps(k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
