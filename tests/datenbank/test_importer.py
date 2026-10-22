# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests für server/datenbank/importer.py (Konzept §4a R-4/R-5, Akzeptanzfälle K-06, K-09).

Aufruf:
    BIENEN_TEST_DSN="host=/tmp/pg port=5433 user=bienen dbname=t" python3 tests/datenbank/test_importer.py

Teil 1 (ohne Datenbank, T0/T1-Host): Zeitlesen, Felder, Messzeitwahl, Lesen ab Position.
Teil 2 (PostgreSQL ab 16, T1): Jeder Fall legt das Schema neu an (schema.sql löscht das Schema 'bienen'!),
schreibt Protokollzeilen wie ein_protokoll() in ein temporäres Verzeichnis und ruft den Importer auf.
Ohne erreichbare Datenbank meldet der Test Teil 2 als NICHT GELAUFEN und endet mit Rückgabe 2.
Benötigt: psycopg ≥ 3.1 (pip install "psycopg[binary]") und die Erweiterung btree_gist.
Keine Produktivdaten; Gerätenamen und Werte sind erfunden.
"""
import hashlib
import json
import os
import pathlib
import sys
import tempfile
from datetime import datetime, timezone

WURZEL = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "server" / "datenbank"))
import importer as imp  # noqa: E402

DSN = os.environ.get("BIENEN_TEST_DSN", "host=/tmp/pg port=5433 user=bienen dbname=t")
SCHEMA = WURZEL / "server" / "datenbank" / "schema.sql"
OKT = "2026-10.jsonl"


def test(name, db=False):
    def deko(fn):
        fn.testname, fn.db = name, db
        return fn
    return deko


# ---------------------------------------------------------------- Protokollzeilen wie die PHP-Eingänge

def iso(unix, ns="123456789"):
    return datetime.fromtimestamp(unix, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "." + ns + "Z"


def u(text):
    """'2026-10-15 06:00' (UTC) → Unix-Sekunden."""
    return int(datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())


def nachricht(geraet, fcnt, empfang, daten, fport=2):
    payload = f"AQ{fcnt:04d}"
    up = {"f_port": fport, "f_cnt": fcnt, "frm_payload": payload, "received_at": iso(empfang)}
    if daten is not None:
        up["decoded_payload"] = daten
    return {"end_device_ids": {"device_id": geraet}, "received_at": iso(empfang, "000000000"), "uplink_message": up}


def kennung(msg):
    """Nachbau von ein_nachricht_id()."""
    up = msg.get("uplink_message", {})
    teile = [msg["end_device_ids"]["device_id"], str(up.get("f_port", "")), str(up.get("f_cnt", "")),
             str(up.get("frm_payload", "")), str(imp.empfangszeit(msg) or "")]
    return hashlib.sha1("|".join(teile).encode(), usedforsecurity=False).hexdigest()  # Kennung wie PHP sha1(), keine Sicherheit


def zeile(eintrag):
    """Wie ein_protokoll(): JSON ohne Unicode-/Slash-Escapes, log_zeit angehängt, Zeilenende."""
    e = dict(eintrag, log_zeit="2026-10-15T06:00:05Z")
    return (json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def uplink(msg, herkunft="geraet"):
    return zeile({herkunft: msg["end_device_ids"]["device_id"], "art": "uplink", "id": kennung(msg),
                  "roh_sha256": hashlib.sha256(json.dumps(msg).encode()).hexdigest(), "nachricht": msg})


def v2(gewicht, temp, messzeit=None, zeit_ok=True, feuchte=55.5):
    d = {"Gewicht": gewicht, "TempIn": temp, "FeuchteIn": feuchte, "Format": 2}
    if messzeit is not None:
        d["Status"] = {"zeit_ok": zeit_ok, "akku_niedrig": False}
        d["Messzeit_unix"] = messzeit
        d["Messzeit"] = iso(messzeit)[:19] + ".000Z"
    return d


def anhaengen(pfad, *teile):
    with open(pfad, "ab") as f:
        for t in teile:
            f.write(t)


# ---------------------------------------------------------------- Teil 1: ohne Datenbank

@test("TTN-Zeit: Sekunden wie ein_ttn_zeit, Nanosekunden auf µs gekürzt, falsches Format → None")
def t_ttn_zeit():
    unix, d = imp.ttn_zeit("2026-10-08T12:00:03.123456789Z")
    assert unix == u("2026-10-08 12:00") + 3
    assert d == datetime(2026, 10, 8, 12, 0, 3, 123456, tzinfo=timezone.utc)
    assert imp.ttn_zeit("2026-10-08T12:00:03Z")[1].microsecond == 0
    assert imp.ttn_zeit("2026-10-08 12:00:03") is None and imp.ttn_zeit(None) is None


@test("Felder flach: Verschachtelung mit Punkt, Listen mit Index, Wahrheitswerte 1/0, Texte weg")
def t_felder():
    d = {"Gewicht": 31.25, "Messzeit": "2026-10-15T06:00:00.000Z", "Status": {"zeit_ok": True, "akku_niedrig": False},
         "FFT_Baender_dB": [-10.5, -20], "leer": None}
    assert imp.felder(d) == [("Gewicht", 31.25), ("Status.zeit_ok", 1.0), ("Status.akku_niedrig", 0.0),
                             ("FFT_Baender_dB[0]", -10.5), ("FFT_Baender_dB[1]", -20.0)]


@test("Messzeit: Gerätezeit nur abgeglichen, höchstens 30 s vor und 30 Tage nach, sonst Empfang; gleich für alle Eingänge")
def t_messzeit():
    e = u("2026-10-15 06:00")
    tag = 86400
    assert imp.messzeit(v2(1, 1, e - 60), e) == (e - 60, "geraet")
    assert imp.messzeit(v2(1, 1, e + 30), e) == (e + 30, "geraet")
    assert imp.messzeit(v2(1, 1, e + 31), e) == (e, "empfang"), "Uhr mehr als 30 s vor"
    assert imp.messzeit(v2(1, 1, e - 900), e) == (e - 900, "geraet")
    assert imp.messzeit(v2(1, 1, e - 901), e) == (e - 901, "geraet"), "nachgesendeter Wert (früher 900-s-Grenze)"
    assert imp.messzeit(v2(1, 1, e - 30 * tag), e) == (e - 30 * tag, "geraet"), "genau 30 Tage"
    assert imp.messzeit(v2(1, 1, e - 30 * tag - 1), e) == (e, "empfang"), "älter als 30 Tage"
    assert imp.messzeit(v2(1, 1, e - 3 * tag), e, max_alter_s=2 * tag) == (e, "empfang"), "Grenze einstellbar"
    assert imp.MAX_ALTER_TAGE == 30
    assert imp.messzeit(v2(1, 1, e - 60, zeit_ok=False), e) == (e, "empfang")
    assert imp.messzeit(v2(1, 1), e) == (e, "empfang"), "FPort 1 ohne Messzeit"
    assert imp.messzeit(dict(v2(1, 1, e - 60), Messzeit_unix=True), e) == (e, "empfang")
    assert imp.messzeit(dict(v2(1, 1, e - 60), Messzeit_unix=1e300), e) == (e, "empfang")
    assert imp.messzeit({"Messzeit_unix": e - 60, "Status": {"zeit_ok": 1}}, e) == (e, "empfang"), "zeit_ok muss true sein"
    assert imp.geraetezeit({"Messzeit_unix": -1}) is None and imp.geraetezeit({"Messzeit_unix": imp.UNIX_MAX}) == imp.UNIX_MAX


@test("Mehrere Messungen je Uplink: Liste Eintraege, Felder außerhalb als eigene Messung, Unbrauchbares übersprungen")
def t_messungen():
    d = {"BatV": 3.6, "Eintraege": [{"TempC1": 1.0, "Messzeit_unix": 10}, "kaputt", None, {"TempC1": 2.0}]}
    m = imp.messungen(d)
    assert m == [{"BatV": 3.6}, {"TempC1": 1.0, "Messzeit_unix": 10}, {"TempC1": 2.0}], m
    assert imp.messungen({"t": 1}) == [{"t": 1}]
    assert imp.messungen({"t": 1, "Eintraege": "keine Liste"}) == [{"t": 1, "Eintraege": "keine Liste"}]
    assert imp.messungen(None) == [] and imp.messungen([1]) == []


@test("Lesen ab Position: unvollständige letzte Zeile bleibt liegen, geänderter Anfang wird erkannt (R-4)")
def t_neue_zeilen():
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / OKT
        p.write_bytes(b'{"a":1}\n{"b":2}\n{"c":')
        z, h, pos = imp.neue_zeilen(p, 0, "")
        assert z == [b'{"a":1}', b'{"b":2}'] and pos == 16 and h.hexdigest() == hashlib.sha256(p.read_bytes()[:16]).hexdigest()
        anhaengen(p, b'3}\n')
        z2, h2, pos2 = imp.neue_zeilen(p, pos, h.hexdigest())
        assert z2 == [b'{"c":3}'] and pos2 == len(p.read_bytes())
        assert h2.hexdigest() == hashlib.sha256(p.read_bytes()).hexdigest()
        assert imp.neue_zeilen(p, pos2, h2.hexdigest())[0] == []
        p.write_bytes(b'{"a":9}\n{"b":2}\n{"c":3}\n')            # gleich lang, Anfang geändert
        for args in ((pos2, h2.hexdigest()), (pos2 + 10, h2.hexdigest())):
            try:
                imp.neue_zeilen(p, *args)
                raise AssertionError("Umschreiben nicht erkannt")
            except imp.Umgeschrieben:
                pass


# ---------------------------------------------------------------- Teil 2: mit PostgreSQL

def stamm(con, kanaele=(("L08", "Gewicht", "gewicht"), ("L08", "TempIn", "temperatur")), von="2026-10-01 00:00+00"):
    con.execute("""INSERT INTO messgroesse(code,name,einheit,semantik,verdichtung,achse) VALUES
        ('gewicht','Gewicht','kg','momentan','mittel','gewicht'),
        ('temperatur','Temperatur','°C','momentan','mittel','temperatur')""")
    ids = {}
    for g, feld, groesse in kanaele:
        if g not in ids:
            ids[g] = con.execute("INSERT INTO geraet(name, art) VALUES (%s,'stockwaage') RETURNING id", (g,)).fetchone()[0]
        con.execute("INSERT INTO kanal(geraet_id,quellfeld,messgroesse_code,gueltig) VALUES (%s,%s,%s,tstzrange(%s,NULL,'[)'))",
                    (ids[g], feld, groesse, von))
    return ids


def abbild(con):
    """Datenbankinhalt ohne Zeitpunkt des Imports, für den Vergleich zweier Läufe."""
    sql = {
        "geraet": "SELECT id, name, art FROM geraet ORDER BY id",
        "rohnachricht": "SELECT id, geraet_id, empfangen, messzeit_quelle, datei, zeile, sha256 FROM rohnachricht ORDER BY id",
        "messwert": "SELECT kanal_id, zeit, wert, qualitaet, zeitqualitaet, roh_id FROM messwert ORDER BY kanal_id, zeit",
        "quellfeld_ohne_kanal": "SELECT * FROM quellfeld_ohne_kanal ORDER BY geraet_id, quellfeld",
        "import_position": "SELECT datei, bytes, zeilen, sha256 FROM import_position ORDER BY datei",
    }
    return {k: con.execute(q).fetchall() for k, q in sql.items()}


def eins(con, sql, params=None):
    return con.execute(sql, params).fetchone()[0]


@test("Grundfall: Rohnachricht als Verweis (Datei/Zeile/SHA-256), Messwerte nur über Kanal, Gerätezeit", db=True)
def t_grundfall(con, verz):
    stamm(con)
    e = u("2026-10-15 06:00")
    msg = nachricht("L08", 1, e, v2(31.25, 34.5, e - 120))
    z1 = uplink(msg)
    erg = zeile({"geraet": "L08", "art": "ergebnis", "klasse": "gespeichert", "id": kennung(msg)})
    anhaengen(verz["lora_log"] / OKT, zeile({"art": "nachgeholt", "datei": "x"}), z1, erg)
    b = imp.importieren(con, verz)
    assert (b.zeilen, b.uplinks, b.neu, b.andere, b.messwerte, b.fehler) == (3, 1, 1, 2, 2, []), b.text()
    r = con.execute("SELECT id, datei, zeile, sha256, empfangen, messzeit_quelle FROM rohnachricht").fetchall()
    assert r == [(kennung(msg), "lora_log/" + OKT, 2, hashlib.sha256(z1[:-1]).hexdigest(),
                  datetime.fromtimestamp(e, timezone.utc).replace(microsecond=123456), imp.utc(e - 120))], r
    mw = con.execute("""SELECT k.quellfeld, m.zeit, m.wert, m.zeitqualitaet, m.roh_id FROM messwert m
                        JOIN kanal k ON k.id = m.kanal_id ORDER BY 1""").fetchall()
    assert mw == [("Gewicht", imp.utc(e - 120), 31.25, "geraet", kennung(msg)),
                  ("TempIn", imp.utc(e - 120), 34.5, "geraet", kennung(msg))], mw
    assert eins(con, "SELECT count(*) FROM rohnachricht WHERE sha256 IS NULL OR datei = ''") == 0


@test("K-06 Quellfeld ohne Kanal: Rohnachricht vorhanden, kein Messwert, als unbenannt gezählt", db=True)
def t_k06(con, verz):
    stamm(con)
    e = u("2026-10-15 06:00")
    anhaengen(verz["lora_log"] / OKT, uplink(nachricht("L08", 1, e, v2(30.0, 34.0, e - 60, feuchte=50))),
              uplink(nachricht("L08", 2, e + 900, v2(30.1, 34.1, e + 840, feuchte=51))))
    imp.importieren(con, verz)
    assert eins(con, "SELECT count(*) FROM rohnachricht") == 2
    assert eins(con, "SELECT count(*) FROM messwert m JOIN kanal k ON k.id=m.kanal_id WHERE k.quellfeld='FeuchteIn'") == 0
    q = con.execute("SELECT zuerst, zuletzt, anzahl FROM quellfeld_ohne_kanal WHERE quellfeld='FeuchteIn'").fetchone()
    assert q == (imp.utc(e - 60), imp.utc(e + 840), 2), q
    felder = {r[0] for r in con.execute("SELECT quellfeld FROM quellfeld_ohne_kanal")}
    assert felder == {"FeuchteIn", "Format", "Status.zeit_ok", "Status.akku_niedrig", "Messzeit_unix"}, felder
    # zweiter Lauf mit einer neuen Nachricht: Anzahl wird addiert, nicht ersetzt; zuerst bleibt (PLT26-12)
    anhaengen(verz["lora_log"] / OKT, uplink(nachricht("L08", 3, e + 1800, v2(30.2, 34.2, e + 1740, feuchte=52))))
    imp.importieren(con, verz)
    q = con.execute("SELECT zuerst, zuletzt, anzahl FROM quellfeld_ohne_kanal WHERE quellfeld='FeuchteIn'").fetchone()
    assert q == (imp.utc(e - 60), imp.utc(e + 1740), 3), q


@test("R-5 Doppelimport: zweiter Lauf, Neulesen ohne Position und andere Sitzungszeitzone → dieselbe Datenbank", db=True)
def t_doppelimport(con, verz):
    stamm(con)
    e = u("2026-10-15 06:00")
    m1 = nachricht("L08", 1, e, v2(30.0, 34.0, e - 60))
    anhaengen(verz["lora_log"] / OKT, uplink(m1), uplink(nachricht("L08", 2, e + 900, v2(30.2, 34.2))),
              uplink(m1),                                         # TTN stellt dieselbe Nachricht erneut zu
              uplink(nachricht("L99", 7, e + 60, {"Gewicht": 12.0})))
    anhaengen(verz["wetter_log"] / OKT, uplink(nachricht("s2120-1", 3, e, {"t": 11.5, "h": 80}, fport=3), "station"))
    b1 = imp.importieren(con, verz)
    assert b1.neu == 4 and b1.doppelt == 1, b1.text()
    erst = abbild(con)
    b2 = imp.importieren(con, verz)
    assert b2.zeilen == 0 and abbild(con) == erst, b2.text()
    con.execute("DELETE FROM import_position")
    con.execute("SET TIME ZONE 'America/New_York'")
    b3 = imp.importieren(con, verz)
    assert b3.neu == 0 and b3.doppelt == 5, b3.text()
    assert abbild(con) == erst


@test("K-09 Datenbank zwei Tage aus: alle neuen Zeilen nachgeholt, ohne Dubletten, über Monatswechsel", db=True)
def t_k09(con, verz):
    stamm(con)
    t0, n, alle = u("2026-10-29 00:00"), 0, []
    lora = verz["lora_log"]

    def tag(von, bis):
        nonlocal n
        for t in range(von, bis, 900):
            n += 1
            m = nachricht("L08", n, t, v2(30 + n / 1000, 34.0, t - 30))
            alle.append(kennung(m))
            anhaengen(lora / ("2026-11.jsonl" if t >= u("2026-11-01 00:00") else OKT), uplink(m))

    tag(t0, t0 + 86400)
    assert imp.importieren(con, verz).neu == 96
    tag(t0 + 86400, t0 + 4 * 86400)                               # 30.10.–01.11., Datenbank aus
    b = imp.importieren(con, verz)
    assert b.neu == 3 * 96 and b.doppelt == 0 and b.fehler == [], b.text()
    assert sorted(r[0] for r in con.execute("SELECT id FROM rohnachricht")) == sorted(alle)
    assert eins(con, "SELECT count(*) FROM messwert") == 2 * 4 * 96
    assert [r[0] for r in con.execute("SELECT datei FROM import_position ORDER BY 1")] == ["lora_log/2026-10.jsonl",
                                                                                          "lora_log/2026-11.jsonl"]


@test("Unvollständige letzte Zeile: erst nach dem Zeilenende übernommen, genau einmal", db=True)
def t_halbe_zeile(con, verz):
    stamm(con)
    e = u("2026-10-15 06:00")
    z = uplink(nachricht("L08", 1, e, v2(30.0, 34.0)))
    p = verz["lora_log"] / OKT
    anhaengen(p, z[:50])
    assert imp.importieren(con, verz).zeilen == 0
    assert eins(con, "SELECT count(*) FROM import_position") == 0
    anhaengen(p, z[50:])
    assert imp.importieren(con, verz).neu == 1
    assert eins(con, "SELECT zeilen FROM import_position") == 1


@test("R-4 umgeschriebene Datei: Fehler gemeldet, Datenbank unverändert, andere Dateien weiter gelesen", db=True)
def t_umgeschrieben(con, verz):
    stamm(con)
    e = u("2026-10-15 06:00")
    p = verz["lora_log"] / OKT
    anhaengen(p, uplink(nachricht("L08", 1, e, v2(30.0, 34.0))))
    imp.importieren(con, verz)
    vorher = abbild(con)
    p.write_bytes(uplink(nachricht("L08", 1, e, v2(99.0, 34.0))) + uplink(nachricht("L08", 2, e + 900, v2(1.0, 1.0))))
    anhaengen(verz["wetter_log"] / OKT, uplink(nachricht("s2120-1", 1, e, {"t": 11.5}), "station"))
    b = imp.importieren(con, verz)
    assert len(b.fehler) == 1 and "lora_log/2026-10.jsonl" in b.fehler[0], b.text()
    nachher = abbild(con)
    assert nachher["messwert"] == vorher["messwert"]
    assert [r for r in nachher["rohnachricht"] if r[4].startswith("lora_log")] == vorher["rohnachricht"]
    assert eins(con, "SELECT count(*) FROM rohnachricht WHERE datei LIKE 'wetter_log/%%'") == 1


@test("Zeitqualität und Herkunft: Empfangszeit ohne Abgleich, Wetter mit 'station', neue Geräte angelegt", db=True)
def t_zeit_herkunft(con, verz):
    ids = stamm(con)
    e = u("2026-10-15 06:00")
    anhaengen(verz["lora_log"] / OKT,
              uplink(nachricht("L08", 1, e, v2(30.0, 34.0, e - 60, zeit_ok=False))),
              uplink(nachricht("L08", 2, e + 900, v2(30.1, 34.0, e - 31 * 86400))),  # Uhr weit daneben (> 30 Tage)
              uplink(nachricht("L08", 3, e + 1800, None)),                         # Formatter-Fehler
              zeile({"geraet": "L08", "art": "uplink", "nachricht": {}}),          # ohne Kennung
              b"kein json\n")
    anhaengen(verz["wetter_log"] / OKT, uplink(nachricht("s2120-1", 1, e, {"t": 11.5}), "station"))
    b = imp.importieren(con, verz)
    assert (b.neu, b.ungueltig, b.geraete_neu) == (4, 2, ["s2120-1"]), b.text()
    q = con.execute("SELECT zeit, zeitqualitaet FROM messwert WHERE kanal_id IN (SELECT id FROM kanal WHERE quellfeld='Gewicht') ORDER BY zeit").fetchall()
    assert q == [(imp.utc(e), "empfang"), (imp.utc(e + 900), "empfang")], q
    assert eins(con, "SELECT messzeit_quelle FROM rohnachricht WHERE zeile = 2") == imp.utc(e - 31 * 86400)
    assert eins(con, "SELECT art FROM geraet WHERE name='s2120-1'") == "wetter"
    assert eins(con, "SELECT count(*) FROM rohnachricht WHERE geraet_id = %s", (ids["L08"],)) == 3


@test("Fehlerhafte Einzelzeilen (NUL, riesige Gerätezeit, zu tiefe Verschachtelung) blockieren die Datei nicht", db=True)
def t_giftzeilen(con, verz):
    stamm(con)
    e = u("2026-10-15 06:00")
    anhaengen(verz["lora_log"] / OKT,
              uplink(nachricht("L\u0000X", 1, e, v2(1.0, 1.0))),                   # NUL im Gerätenamen
              uplink(nachricht("L08", 2, e, dict(v2(1.0, 1.0, e), Messzeit_unix=1e300))),
              b'{"art":"uplink","id":"t","geraet":"L08","nachricht":' + b"[" * 100000 + b"]" * 100000 + b"}\n",
              uplink(nachricht("L08", 4, e + 900, v2(30.0, 34.0))))
    b = imp.importieren(con, verz)
    assert b.fehler == [] and b.zeilen == 4 and b.neu == 2, b.text()
    assert len(b.uebersprungen) == 2 and b.ungueltig == 2 and b.geraete_neu == [], b.text()
    assert eins(con, "SELECT count(*) FROM geraet") == 1
    assert eins(con, "SELECT messzeit_quelle FROM rohnachricht WHERE zeile = 2") is None
    assert eins(con, "SELECT zeilen FROM import_position") == 4
    assert eins(con, "SELECT count(*) FROM messwert") == 4
    assert imp.importieren(con, verz).zeilen == 0


@test("Kanal mit Zeitraum: Werte vor Gültigkeitsbeginn ohne Kanal, danach Messwert; Faktor in messwert_bezug", db=True)
def t_kanal_zeitraum(con, verz):
    stamm(con, von="2026-10-16 00:00+00")
    con.execute("UPDATE kanal SET faktor = 2 WHERE quellfeld = 'Gewicht'")
    anhaengen(verz["lora_log"] / OKT, uplink(nachricht("L08", 1, u("2026-10-15 23:45"), v2(10.0, 30.0))),
              uplink(nachricht("L08", 2, u("2026-10-16 00:00"), v2(10.5, 30.0))))
    imp.importieren(con, verz)
    assert con.execute("SELECT zeit, wert FROM messwert_bezug WHERE messgroesse_code='gewicht'").fetchall() == \
        [(imp.utc(u("2026-10-16 00:00")), 21.0)]
    assert eins(con, "SELECT anzahl FROM quellfeld_ohne_kanal WHERE quellfeld='Gewicht'") == 1


@test("Zwei Eingänge: gleiche Zeitregel, Umweltgerät mit Uhr behält Gerätezeit, Altbestand wetter_log + umwelt_log nur einmal", db=True)
def t_zwei_eingaenge(con, verz):
    ids = stamm(con, kanaele=(("L08", "Gewicht", "gewicht"), ("s2120-1", "t", "temperatur"),
                              ("boden-1", "TempC1", "temperatur")))
    e = u("2026-10-22 06:00")
    # Bienen-Eingang: abgeglichene Gerätezeit 60 s vor dem Empfang wird übernommen
    anhaengen(verz["bienen_log"] / OKT, uplink(nachricht("L08", 1, e, v2(30.0, 34.0, e - 60))))
    # Umwelt-Eingang: abgeglichene Gerätezeit gilt genauso (z. B. Dragino mit SYNCMOD)
    boden = nachricht("boden-1", 4, e, {"TempC1": 12.5, "Status": {"zeit_ok": True}, "Messzeit_unix": e - 600})
    anhaengen(verz["umwelt_log"] / OKT, uplink(boden))
    # dieselbe S2120-Nachricht im Altbestand (Herkunft "station") und im neuen Umwelt-Protokoll (Herkunft "geraet")
    w = nachricht("s2120-1", 3, e, {"t": 11.5, "h": 80}, fport=3)
    anhaengen(verz["wetter_log"] / OKT, uplink(w, "station"))
    anhaengen(verz["umwelt_log"] / OKT, uplink(w))
    # unbekanntes Gerät im Umwelt-Eingang (z. B. neue Bodensonde): wird angelegt, Felder „unbenannt“
    anhaengen(verz["umwelt_log"] / OKT, uplink(nachricht("boden-2", 1, e, {"Temp_Red": 9.75})))
    b = imp.importieren(con, verz)
    assert b.neu == 4 and b.doppelt == 1, b.text()
    zeiten = dict(con.execute("""SELECT g.name, m.zeit FROM messwert m JOIN kanal k ON k.id = m.kanal_id
                                 JOIN geraet g ON g.id = k.geraet_id""").fetchall())
    assert zeiten == {"L08": imp.utc(e - 60), "boden-1": imp.utc(e - 600), "s2120-1": imp.utc(e)}, zeiten
    zq = dict(con.execute("""SELECT g.name, m.zeitqualitaet FROM messwert m JOIN kanal k ON k.id = m.kanal_id
                             JOIN geraet g ON g.id = k.geraet_id""").fetchall())
    assert zq == {"L08": "geraet", "boden-1": "geraet", "s2120-1": "empfang"}, zq
    assert eins(con, "SELECT count(*) FROM messwert m JOIN kanal k ON k.id=m.kanal_id WHERE k.geraet_id=%s",
                (ids["s2120-1"],)) == 1
    assert eins(con, "SELECT art FROM geraet WHERE name='boden-2'") == "sonstiges"
    assert eins(con, "SELECT count(*) FROM quellfeld_ohne_kanal q JOIN geraet g ON g.id=q.geraet_id "
                     "WHERE g.name='boden-2' AND q.quellfeld='Temp_Red'") == 1
    dateien = {r[0] for r in con.execute("SELECT datei FROM import_position")}
    assert dateien == {"bienen_log/" + OKT, "umwelt_log/" + OKT, "wetter_log/" + OKT}, dateien


@test("Datalog: mehrere Einträge je Uplink mit eigener Gerätezeit, Nachsenden nach Tagen, zu alt → Empfangszeit", db=True)
def t_datalog(con, verz):
    stamm(con, kanaele=(("boden-1", "TempC1", "temperatur"), ("boden-1", "BatV", "gewicht")))
    e = u("2026-10-22 06:00")
    tag = 86400
    ok = {"zeit_ok": True}
    d = {"BatV": 3.6, "Eintraege": [
        {"TempC1": 10.0, "Messzeit_unix": e - 3 * tag, "Status": ok},          # nach drei Tagen Netzausfall nachgesendet
        {"TempC1": 10.5, "Messzeit_unix": e - 3 * tag + 1200, "Status": ok},
        {"TempC1": 11.0, "Messzeit_unix": e - 3 * tag + 2400},                  # ohne zeit_ok → Empfangszeit
        {"TempC1": 9.0, "Messzeit_unix": e - 31 * tag, "Status": ok},          # älter als 30 Tage → Empfangszeit
    ]}
    anhaengen(verz["umwelt_log"] / OKT, uplink(nachricht("boden-1", 9, e, d)))
    b = imp.importieren(con, verz)
    assert b.neu == 1, b.text()
    r = con.execute("""SELECT k.quellfeld, m.zeit, m.wert, m.zeitqualitaet FROM messwert m JOIN kanal k ON k.id = m.kanal_id
                       ORDER BY m.zeit, k.quellfeld""").fetchall()
    assert r == [("TempC1", imp.utc(e - 3 * tag), 10.0, "geraet"),
                 ("TempC1", imp.utc(e - 3 * tag + 1200), 10.5, "geraet"),
                 ("BatV", imp.utc(e), 3.6, "empfang"),
                 ("TempC1", imp.utc(e), 11.0, "empfang")], r
    # der vierte Eintrag fällt auf dieselbe Empfangszeit und wird nicht doppelt gespeichert (sichtbar im Bericht)
    assert b.messwert_belegt == 1, b.text()
    # zweiter Lauf und Neulesen ändern nichts (R-5 auch mit Einträgen)
    vorher = abbild(con)
    con.execute("DELETE FROM import_position")
    assert imp.importieren(con, verz).doppelt == 1 and abbild(con) == vorher


@test("Boden-Altbestand: umgesetzte Zeilen (boden_alt) landen mit Empfangszeit in den Kanälen der neuen Namen", db=True)
def t_boden_alt(con, verz):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "server" / "datenbank"))
    import altbestand_boden as ab
    stamm(con, kanaele=(("erdboden-temperatur", "temp_weiss", "temperatur"), ("erdboden-temperatur", "temp_rot", "temperatur")))
    alt = verz["boden_alt"].parent / "alt.jsonl"
    alt.write_text('{"time_utc":"2026-10-14T17:27:13.795443Z","device_id":"erdboden-temperatur","f_cnt":21,"f_port":2,'
                   '"payload_base64":"DigAewAADAB8AIM=","temp_5cm":12.4}\n')
    assert ab.main([str(alt), "--ziel", str(verz["boden_alt"])]) == 0
    b = imp.importieren(con, verz)
    assert b.neu == 1 and b.messwerte == 2, b.text()
    r = con.execute("""SELECT k.quellfeld, m.wert, m.zeit, m.zeitqualitaet FROM messwert m JOIN kanal k ON k.id = m.kanal_id
                       ORDER BY k.quellfeld""").fetchall()
    assert r == [("temp_rot", 12.4, imp.utc(u("2026-10-14 17:27") + 13), "empfang"),
                 ("temp_weiss", 12.3, imp.utc(u("2026-10-14 17:27") + 13), "empfang")], r
    assert eins(con, "SELECT datei FROM rohnachricht") == "boden_alt/2026-10.jsonl"


# ---------------------------------------------------------------- Ablauf

def main():
    tests = [f for f in globals().values() if callable(f) and hasattr(f, "testname")]
    fehler, gelaufen = 0, 0

    def melden(t, lauf):
        nonlocal fehler, gelaufen
        gelaufen += 1
        try:
            lauf()
            print(f"bestanden  {t.testname}")
        except Exception as e:  # noqa: BLE001
            fehler += 1
            print(f"FEHLER     {t.testname}: {type(e).__name__}: {e}")

    for t in (t for t in tests if not t.db):
        melden(t, t)

    db_tests = [t for t in tests if t.db]
    try:
        import psycopg
        psycopg.connect(DSN, connect_timeout=5).close()
    except Exception as e:  # noqa: BLE001
        print(f"\nNICHT GELAUFEN: {len(db_tests)} Datenbanktests (keine Verbindung über BIENEN_TEST_DSN: "
              f"{type(e).__name__}: {str(e).strip().splitlines()[0] if str(e).strip() else ''})")
        print(f"{gelaufen - fehler} von {gelaufen} Hosttests bestanden")
        return 1 if fehler else 2

    schema = SCHEMA.read_text(encoding="utf-8")
    for t in db_tests:
        def lauf(t=t):
            with psycopg.connect(DSN, autocommit=True) as con, tempfile.TemporaryDirectory() as d:
                con.execute(schema)
                con.execute("SET search_path = bienen, public")
                verz = {q: pathlib.Path(d) / q for q in ("bienen_log", "umwelt_log", "lora_log", "wetter_log", "boden_alt")}
                for v in verz.values():
                    v.mkdir()
                t(con, verz)
        melden(t, lauf)
    print(f"\n{gelaufen - fehler} von {gelaufen} bestanden")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
