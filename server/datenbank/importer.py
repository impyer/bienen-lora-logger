#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Importer: Rohprotokolle der PHP-Eingänge → PostgreSQL (Schema server/datenbank/schema.sql).

Konzept 0.2, §4/§4a und §10 Schritt 4 (Befund PLT26-02, R-4/R-5; Akzeptanzfälle K-06, K-09).

Liest die Monatsdateien JJJJ-MM.jsonl der Eingänge
    lora_log/   (Herkunftsfeld "geraet", lora_eingang.php)
    wetter_log/ (Herkunftsfeld "station", wetter_eingang.php)
und übernimmt jede Zeile mit "art": "uplink":
  * rohnachricht: Verweis auf Datei, Zeile und SHA-256 der Protokollzeile (nicht ihr Inhalt),
    Kennung = Feld "id" des Eingangs (ein_nachricht_id, SRV26-03).
  * messwert: jedes Zahlenfeld aus uplink_message.decoded_payload, für das zum Messzeitpunkt ein
    kanal (Gerät, Quellfeld) gilt. Verschachtelte Felder heißen "Status.zeit_ok", Listen "FFT_Baender_dB[0]";
    true/false werden 1/0. Gespeichert wird der Rohwert; faktor/versatz wendet die Sicht messwert_bezug an.
  * Felder ohne Kanal werden kein Messwert (K-06), nur in quellfeld_ohne_kanal gezählt.

Idempotent (R-5): Je Datei steht in import_position, bis zu welchem Byte gelesen ist, mit der SHA-256 dieser
Bytes. Ein neuer Lauf liest ab dort weiter; eine schon vorhandene Kennung wird verworfen, samt ihrer Messwerte.
Wird die Position gelöscht, liest der Importer die Datei neu und es entsteht dieselbe Datenbank.
Eine Datei, deren schon gelesener Anfang sich geändert hat, wird nicht weiter gelesen (R-4: nur anhängen).
Eine unvollständige letzte Zeile (Eingang schreibt gerade) bleibt für den nächsten Lauf liegen.

Messzeit wie lora_funktionen.php le_messzeit(): Gerätezeit (Messzeit_unix), wenn Status.zeit_ok und
höchstens --max-zeitabweichung Sekunden vor dem Empfang (30 s Vorgehen erlaubt), sonst Empfangszeit (TTN).
Der Wetter-Eingang kennt nur die Empfangszeit.

Unbekannte Geräte legt der Importer an (lora_log: art 'sonstiges', wetter_log: art 'wetter'), damit keine
Rohnachricht verloren geht; Art und Kanäle danach in den Stammdaten pflegen.

Aufruf (z. B. alle 1–5 min per systemd-Timer oder cron; ein zweiter gleichzeitiger Lauf beendet sich sofort):
    BIENEN_DSN="dbname=bienen user=bienen" python3 server/datenbank/importer.py \\
        --lora /var/www/html/lora/lora_log --wetter /var/www/html/wetter/wetter_log
Nachtragen, nachdem ein Kanal angelegt wurde (Werte vorher nur in quellfeld_ohne_kanal; Prüfsumme je Zeile):
    BIENEN_DSN=... python3 server/datenbank/importer.py --lora … --wetter … --nachtragen [--geraet beelogger-01]
Benötigt: Python ≥ 3.9, psycopg 3 (pip install "psycopg[binary]").
Rückgabe: 0 = alles gelesen, 1 = mindestens eine Datei nicht lesbar oder umgeschrieben, 2 = Aufruf/Verbindung.
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from psycopg import DataError    # z. B. NUL-Zeichen in einem Text, das PostgreSQL nicht speichern kann
except ImportError:                  # Hosttests ohne psycopg
    DataError = ValueError

# Eingang → Herkunftsfeld, Art neu angelegter Geräte, ob das Gerät eine eigene Messzeit sendet
QUELLEN = {
    "lora_log": {"feld": "geraet", "art": "sonstiges", "geraetezeit": True},
    "wetter_log": {"feld": "station", "art": "wetter", "geraetezeit": False},
}
DATEINAME = re.compile(r"^\d{4}-\d{2}\.jsonl$")
TTN_ZEIT = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?Z$")
MAX_ABWEICHUNG_S = 900          # wie 'max_zeitabweichung_s' in lora_config.beispiel.php
VORGEHEN_S = 30                 # wie le_messzeit(): Uhr darf 30 s vorgehen
SPERRE = 0x6265_656E_0001       # Schlüssel für pg_try_advisory_lock (ein Importer zur Zeit)
LESEBLOCK = 1 << 20
UNIX_MAX = 253402300799         # 9999-12-31 23:59:59 UTC, größter Wert für datetime
# Fehler, die nur an einer einzelnen Zeile liegen: Zeile überspringen statt die Datei bei jedem Lauf zu blockieren.
# Verbindungs- und Serverfehler gehören nicht dazu und brechen den Lauf ab (Datei bleibt ungelesen, nichts geht verloren).
ZEILENFEHLER = (ValueError, RecursionError, OverflowError, DataError)


class Umgeschrieben(Exception):
    """Der schon eingelesene Anfang einer Protokolldatei hat sich geändert (R-4)."""


@dataclass
class Bericht:
    zeilen: int = 0                 # neu gelesene vollständige Zeilen
    uplinks: int = 0
    neu: int = 0                    # neue Rohnachrichten
    doppelt: int = 0                # Kennung schon in der Datenbank
    andere: int = 0                 # Zeilen anderer Art (ergebnis, fehler, warnung …)
    ungueltig: int = 0              # kein JSON oder Uplink ohne Kennung/Nachricht/Herkunft/Empfangszeit
    uebersprungen: list = field(default_factory=list)   # 'datei:zeile Fehler' – Zeile nicht übernehmbar
    messwerte: int = 0
    messwert_belegt: int = 0        # (kanal, zeit) schon mit einem Wert aus einer anderen Nachricht belegt
    ohne_kanal: int = 0             # Zahlenfelder ohne Kanal (K-06)
    geraete_neu: list = field(default_factory=list)
    fehler: list = field(default_factory=list)

    def text(self):
        s = (f"{self.zeilen} Zeilen, {self.uplinks} Uplinks: {self.neu} neu, {self.doppelt} doppelt; "
             f"{self.messwerte} Messwerte, {self.ohne_kanal} Felder ohne Kanal, {self.messwert_belegt} belegt; "
             f"{self.andere} andere, {self.ungueltig} ungültig")
        if self.geraete_neu:
            s += "\nGeräte neu angelegt (Art und Kanäle pflegen): " + ", ".join(self.geraete_neu)
        for z in self.uebersprungen:
            s += "\nZeile übersprungen: " + z
        for f in self.fehler:
            s += "\nFEHLER " + f
        return s


# ---------------------------------------------------------------- reine Hilfen (ohne Datenbank)

def ttn_zeit(s):
    """TTN-Zeit '2026-10-08T12:00:03.123456789Z' → (Unix-Sekunden wie ein_ttn_zeit, datetime auf µs) oder None."""
    m = TTN_ZEIT.match(s) if isinstance(s, str) else None
    if not m:
        return None
    try:
        d = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    unix = int(d.timestamp())
    us = int((m.group(2) or "0")[:6].ljust(6, "0"))
    return unix, d + timedelta(microseconds=us)


def empfangszeit(msg):
    """uplink_message.received_at, sonst received_at der Nachricht (wie ein_empfangszeit)."""
    up = msg.get("uplink_message")
    if isinstance(up, dict) and "received_at" in up:
        return up["received_at"]
    return msg.get("received_at")


def zahl(v):
    """Wert als float für einen Messwert, sonst None. true/false → 1/0."""
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else None
    return None


def felder(daten, praefix=""):
    """Zahlenfelder des Formatter-JSON flach: [(quellfeld, wert)] in Dateireihenfolge."""
    aus = []
    if isinstance(daten, dict):
        teile = ((f"{praefix}.{k}" if praefix else str(k), v) for k, v in daten.items())
    elif isinstance(daten, list):
        teile = ((f"{praefix}[{i}]", v) for i, v in enumerate(daten))
    else:
        return aus
    for name, v in teile:
        if isinstance(v, (dict, list)):
            aus.extend(felder(v, name))
        else:
            w = zahl(v)
            if w is not None:
                aus.append((name, w))
    return aus


def geraetezeit(daten):
    """Messzeit_unix als int, falls gesendet (Zahl, kein Wahrheitswert), sonst None."""
    v = daten.get("Messzeit_unix") if isinstance(daten, dict) else None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= UNIX_MAX:
        return None
    return int(v)


def messzeit(daten, empfang_unix, max_abweichung_s=MAX_ABWEICHUNG_S):
    """Wie le_messzeit(): (unix, 'geraet') bei abgeglichener, plausibler Gerätezeit, sonst (empfang, 'empfang')."""
    t = geraetezeit(daten)
    status = daten.get("Status") if isinstance(daten, dict) else None
    if t is not None and isinstance(status, dict) and status.get("zeit_ok") is True:
        if t <= empfang_unix + VORGEHEN_S and empfang_unix - t <= max_abweichung_s:
            return t, "geraet"
    return empfang_unix, "empfang"


def utc(unix):
    return datetime.fromtimestamp(unix, timezone.utc)


def protokolldateien(verz):
    """Monatsdateien JJJJ-MM.jsonl eines Eingangs, zeitlich sortiert."""
    return sorted(p for p in Path(verz).iterdir() if p.is_file() and DATEINAME.match(p.name))


def neue_zeilen(pfad, bytes_bisher, sha_bisher):
    """Liest ab bytes_bisher. Rückgabe: (Liste vollständiger Zeilen ohne '\\n', hashlib-Objekt über alle gelesenen
    Bytes einschließlich der neuen Zeilen, neue Byteposition). Wirft Umgeschrieben bei geändertem Anfang."""
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        rest = bytes_bisher
        while rest > 0:
            b = f.read(min(rest, LESEBLOCK))
            if not b:
                raise Umgeschrieben(f"{pfad.name}: kürzer als die gespeicherte Position {bytes_bisher}")
            h.update(b)
            rest -= len(b)
        if bytes_bisher and h.hexdigest() != sha_bisher:
            raise Umgeschrieben(f"{pfad.name}: die ersten {bytes_bisher} Byte haben sich geändert")
        neu = f.read()
    ende = neu.rfind(b"\n") + 1          # unvollständige letzte Zeile bleibt liegen
    h.update(neu[:ende])
    zeilen = neu[:ende].split(b"\n")[:-1] if ende else []
    return zeilen, h, bytes_bisher + ende


# ---------------------------------------------------------------- Datenbank

class Importer:
    def __init__(self, con, max_abweichung_s=MAX_ABWEICHUNG_S):
        self.con = con
        self.max_abweichung_s = max_abweichung_s
        self.geraete = {}            # Name → id
        self.kanaele = {}            # geraet_id → {quellfeld: [(von, bis, kanal_id)]}

    def geraet(self, cur, name, art, bericht):
        if name in self.geraete:
            return self.geraete[name]
        cur.execute("SELECT id FROM geraet WHERE name = %s", (name,))
        r = cur.fetchone()
        if r is None:
            cur.execute("INSERT INTO geraet(name, art) VALUES (%s, %s) RETURNING id", (name, art))
            r = cur.fetchone()
            bericht.geraete_neu.append(name)
        self.geraete[name] = r[0]
        return r[0]

    def kanal(self, cur, geraet_id, quellfeld, zeit):
        if geraet_id not in self.kanaele:
            cur.execute("SELECT id, quellfeld, lower(gueltig), upper(gueltig) FROM kanal WHERE geraet_id = %s",
                        (geraet_id,))
            k = {}
            for kid, feld, von, bis in cur.fetchall():
                k.setdefault(feld, []).append((von, bis, kid))
            self.kanaele[geraet_id] = k
        for von, bis, kid in self.kanaele[geraet_id].get(quellfeld, ()):
            if von <= zeit and (bis is None or zeit < bis):
                return kid
        return None

    def zeile(self, cur, quelle, datei, nr, roh, bericht):
        """Eine Protokollzeile übernehmen."""
        try:
            e = json.loads(roh)
        except (ValueError, UnicodeDecodeError):
            bericht.ungueltig += 1
            return
        if not isinstance(e, dict):
            bericht.ungueltig += 1
            return
        if e.get("art") != "uplink":
            bericht.andere += 1
            return
        bericht.uplinks += 1
        q = QUELLEN[quelle]
        kennung, msg, name = e.get("id"), e.get("nachricht"), e.get(q["feld"])
        empf = ttn_zeit(empfangszeit(msg)) if isinstance(msg, dict) else None
        if not (isinstance(kennung, str) and kennung and isinstance(name, str) and name and empf):
            bericht.ungueltig += 1
            return
        empf_unix, empf_zeit = empf
        geraet_id = self.geraet(cur, name, q["art"], bericht)
        up = msg.get("uplink_message")
        daten = up.get("decoded_payload") if isinstance(up, dict) else None
        if not isinstance(daten, dict):
            daten = None
        gz = geraetezeit(daten) if (daten and q["geraetezeit"]) else None

        cur.execute("""INSERT INTO rohnachricht(id, geraet_id, empfangen, messzeit_quelle, datei, zeile, sha256)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING""",
                    (kennung, geraet_id, empf_zeit, utc(gz) if gz is not None else None, datei, nr,
                     hashlib.sha256(roh).hexdigest()))
        if cur.rowcount == 0:
            bericht.doppelt += 1
            return
        bericht.neu += 1
        if daten is not None:
            self.messwerte(cur, q, geraet_id, daten, empf_unix, kennung, bericht)

    def messwerte(self, cur, q, geraet_id, daten, empf_unix, kennung, bericht, ohne_kanal_zaehlen=True):
        """Zahlenfelder einer Nachricht als Messwerte (mit Kanal) bzw. als Feld ohne Kanal ablegen."""
        if q["geraetezeit"]:
            unix, zq = messzeit(daten, empf_unix, self.max_abweichung_s)
        else:
            unix, zq = empf_unix, "empfang"
        zeit = utc(unix)
        werte, ohne = [], []
        for feld, wert in felder(daten):
            kid = self.kanal(cur, geraet_id, feld, zeit)
            if kid is None:
                ohne.append((geraet_id, feld, zeit, zeit))
            else:
                werte.append((kid, zeit, wert, zq, kennung))
        if werte:
            cur.executemany("""INSERT INTO messwert(kanal_id, zeit, wert, zeitqualitaet, roh_id)
                               VALUES (%s, %s, %s, %s, %s) ON CONFLICT (kanal_id, zeit) DO NOTHING""", werte)
            bericht.messwerte += cur.rowcount
            bericht.messwert_belegt += len(werte) - cur.rowcount
        if not ohne_kanal_zaehlen:
            return
        for o in ohne:
            cur.execute("""INSERT INTO quellfeld_ohne_kanal AS q(geraet_id, quellfeld, zuerst, zuletzt)
                           VALUES (%s, %s, %s, %s)
                           ON CONFLICT (geraet_id, quellfeld) DO UPDATE
                           SET zuerst = least(q.zuerst, excluded.zuerst),
                               zuletzt = greatest(q.zuletzt, excluded.zuletzt), anzahl = q.anzahl + 1""", o)
        bericht.ohne_kanal += len(ohne)

    def datei(self, quelle, pfad, bericht):
        """Neue Zeilen einer Monatsdatei in einer Transaktion übernehmen, samt neuer Leseposition."""
        datei = f"{quelle}/{pfad.name}"
        with self.con.transaction(), self.con.cursor() as cur:
            cur.execute("SELECT bytes, zeilen, sha256 FROM import_position WHERE datei = %s", (datei,))
            r = cur.fetchone()
            bytes_bisher, nr, sha = r if r else (0, 0, "")
            zeilen, h, bytes_neu = neue_zeilen(pfad, bytes_bisher, sha)
            if not zeilen:
                return
            for roh in zeilen:
                nr += 1
                bericht.zeilen += 1
                neu_vorher = len(bericht.geraete_neu)
                zaehler = (bericht.uplinks, bericht.neu, bericht.doppelt, bericht.messwerte,
                           bericht.messwert_belegt, bericht.ohne_kanal)
                try:
                    with self.con.transaction():     # Sicherungspunkt je Zeile
                        self.zeile(cur, quelle, datei, nr, roh, bericht)
                except ZEILENFEHLER as e:
                    (bericht.uplinks, bericht.neu, bericht.doppelt, bericht.messwerte,
                     bericht.messwert_belegt, bericht.ohne_kanal) = zaehler
                    del bericht.geraete_neu[neu_vorher:]
                    self.geraete.clear()
                    bericht.ungueltig += 1
                    bericht.uebersprungen.append(f"{datei}:{nr} {type(e).__name__}: {str(e)[:120]}")
            cur.execute("""INSERT INTO import_position(datei, bytes, zeilen, sha256) VALUES (%s, %s, %s, %s)
                           ON CONFLICT (datei) DO UPDATE SET bytes = excluded.bytes, zeilen = excluded.zeilen,
                                                             sha256 = excluded.sha256, aktualisiert = now()""",
                        (datei, bytes_neu, nr, h.hexdigest()))

    def lauf(self, verzeichnisse):
        """verzeichnisse: {'lora_log': Pfad, 'wetter_log': Pfad}. Liefert den Bericht."""
        bericht = Bericht()
        self.con.execute("SET search_path = bienen, public")
        self.con.commit()
        for quelle, verz in verzeichnisse.items():
            if quelle not in QUELLEN:
                raise ValueError(f"unbekannter Eingang {quelle}")
            try:
                dateien = protokolldateien(verz)
            except OSError as e:
                bericht.fehler.append(f"{quelle}: Verzeichnis nicht lesbar: {e}")
                continue
            for pfad in dateien:
                try:
                    self.datei(quelle, pfad, bericht)
                except (Umgeschrieben, OSError) as e:
                    bericht.fehler.append(f"{quelle}/{e}" if isinstance(e, Umgeschrieben) else f"{quelle}: {e}")
                    self.kanaele.clear()          # Transaktion zurückgerollt: Caches neu aufbauen
                    self.geraete.clear()
        return bericht


    def nachtragen(self, verzeichnisse, geraet=None):
        """Messwerte für Kanäle nachtragen, die erst nach dem Import angelegt wurden.

        Liest jede schon übernommene Rohnachricht (ggf. nur eines Geräts) erneut aus ihrer Protokollzeile, prüft deren
        SHA-256 gegen rohnachricht.sha256 und legt fehlende Messwerte an (vorhandene bleiben, ON CONFLICT). Felder ohne
        Kanal werden dabei nicht erneut gezählt. Abweichende oder fehlende Zeilen stehen im Bericht unter fehler.
        """
        bericht = Bericht()
        self.con.execute("SET search_path = bienen, public")
        self.con.commit()
        with self.con.cursor() as cur:
            cur.execute("""SELECT r.id, r.datei, r.zeile, r.sha256, g.id FROM rohnachricht r
                           JOIN geraet g ON g.id = r.geraet_id
                           WHERE %(g)s::text IS NULL OR g.name = %(g)s
                           ORDER BY r.datei, r.zeile""", {"g": geraet})
            je_datei = {}
            for kennung, datei, nr, sha, gid in cur.fetchall():
                je_datei.setdefault(datei, []).append((nr, kennung, sha, gid))
        for datei, eintraege in je_datei.items():
            quelle, _, name = datei.partition("/")
            if quelle not in verzeichnisse or quelle not in QUELLEN:
                bericht.fehler.append(f"{datei}: Verzeichnis für {quelle} nicht angegeben")
                continue
            try:
                with open(Path(verzeichnisse[quelle]) / name, "rb") as f:
                    zeilen = f.read().split(b"\n")
            except OSError as e:
                bericht.fehler.append(f"{datei}: {e}")
                continue
            with self.con.transaction(), self.con.cursor() as cur:
                for nr, kennung, sha, gid in eintraege:
                    roh = zeilen[nr - 1] if 0 < nr <= len(zeilen) else b""
                    if hashlib.sha256(roh).hexdigest() != sha:
                        bericht.fehler.append(f"{datei}:{nr} Zeile weicht von der Prüfsumme ab, übersprungen")
                        continue
                    e = json.loads(roh)
                    msg = e["nachricht"]
                    up = msg.get("uplink_message")
                    daten = up.get("decoded_payload") if isinstance(up, dict) else None
                    if not isinstance(daten, dict):
                        continue
                    bericht.uplinks += 1
                    self.messwerte(cur, QUELLEN[quelle], gid, daten, ttn_zeit(empfangszeit(msg))[0], kennung, bericht,
                                   ohne_kanal_zaehlen=False)
        return bericht


def importieren(con, verzeichnisse, max_abweichung_s=MAX_ABWEICHUNG_S):
    return Importer(con, max_abweichung_s).lauf(verzeichnisse)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rohprotokolle der Eingänge in PostgreSQL übernehmen")
    ap.add_argument("--dsn", default=os.environ.get("BIENEN_DSN"), help="libpq-DSN (Vorgabe: $BIENEN_DSN)")
    ap.add_argument("--lora", type=Path, help="Verzeichnis lora_log des LoRa-Eingangs")
    ap.add_argument("--wetter", type=Path, help="Verzeichnis wetter_log des Wetter-Eingangs")
    ap.add_argument("--max-zeitabweichung", type=int, default=MAX_ABWEICHUNG_S,
                    help="wie max_zeitabweichung_s in lora_config.php (Vorgabe 900 s)")
    ap.add_argument("--nachtragen", action="store_true",
                    help="Messwerte für nachträglich angelegte Kanäle aus den schon übernommenen Zeilen ergänzen")
    ap.add_argument("--geraet", help="mit --nachtragen: nur dieses Gerät (TTN-Gerätename)")
    a = ap.parse_args(argv)
    verz = {k: v for k, v in (("lora_log", a.lora), ("wetter_log", a.wetter)) if v is not None}
    if not a.dsn or not verz:
        ap.error("--dsn (oder BIENEN_DSN) und mindestens --lora oder --wetter angeben")
    import psycopg
    try:
        con = psycopg.connect(a.dsn)
    except psycopg.Error as e:
        print(f"keine Verbindung zur Datenbank: {e}", file=sys.stderr)
        return 2
    with con:
        if not con.execute("SELECT pg_try_advisory_lock(%s)", (SPERRE,)).fetchone()[0]:
            print("Importer läuft bereits, nichts zu tun")
            return 0
        con.commit()
        imp = Importer(con, a.max_zeitabweichung)
        b = imp.nachtragen(verz, a.geraet) if a.nachtragen else imp.lauf(verz)
    print(b.text())
    return 1 if b.fehler else 0


if __name__ == "__main__":
    sys.exit(main())
