# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests der Lese-API (server/plattform/) mit synthetischen Daten.

Aufruf:
    pip install -r server/plattform/requirements.txt
    BIENEN_TEST_DSN="host=… dbname=bienen_test user=…" python3 tests/plattform/test_plattform.py

Teil 1 (ohne Datenbank): Verdichtung, Lücken, Anmeldung, Parameterprüfung, Generator.
Teil 2 (PostgreSQL ab 16): leere Datenbank, dann synthetischer Oktober 2026 (server/plattform/synthetisch.py)
→ Importer → API; feste Sollwerte für die eingebauten Fehler und Grenzfälle.
Schema 'bienen' der Testdatenbank wird gelöscht. Ohne Datenbank: Teil 2 NICHT GELAUFEN, Rückgabe 2.
"""
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone

WURZEL = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "server" / "plattform"))
import synthetisch as syn  # noqa: E402
from api import verdichtung as vd  # noqa: E402
from api.anmeldung import Bremse, passwort_hash, passwort_pruefen, sitzung_erzeugen, sitzung_gueltig  # noqa: E402

DSN = os.environ.get("BIENEN_TEST_DSN", "")
PASSWORT = "test-passwort-1234"
SCHLUESSEL = "s" * 40
TESTS = []


def test(name, db=False):
    def deko(fn):
        fn.testname, fn.db = name, db
        TESTS.append(fn)
        return fn
    return deko


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ================================================================ Teil 1: ohne Datenbank

@test("Raster: Punktzahl je Reihe höchstens 2000")
def _():
    assert vd.raster(t("2026-10-01T00:00Z"), t("2026-10-02T00:00Z")) == timedelta(minutes=1)
    assert vd.raster(t("2026-10-01T00:00Z"), t("2026-10-15T00:00Z")) == timedelta(minutes=15)
    assert vd.raster(t("2025-10-01T00:00Z"), t("2026-11-05T00:00Z")) == timedelta(minutes=360)


@test("Verdichtung: jede Verdichtung des Schemas hat ein Aggregat, sonst ValueError")
def _():
    schema = (WURZEL / "server" / "datenbank" / "schema.sql").read_text(encoding="utf-8")
    m = re.search(r"verdichtung text NOT NULL CHECK \(verdichtung IN\s*\(([^)]*)\)", schema)
    werte = re.findall(r"'([a-z_]+)'", m.group(1))
    assert sorted(werte) == sorted(vd.AGGREGATE), werte
    try:
        vd.aggregat("x; DROP TABLE messwert")
        raise AssertionError("keine Ablehnung")
    except ValueError:
        pass


@test("Lücken: null zwischen weit entfernten Punkten, keine 0, keine Lücke im üblichen Takt")
def _():
    a = t("2026-10-10T00:00Z")
    punkte = [(a + timedelta(minutes=30 * i), 1.0) for i in range(10)]
    punkte += [(a + timedelta(days=2, minutes=30 * i), 2.0) for i in range(10)]
    r = vd.mit_luecken(punkte, timedelta(minutes=15))
    assert len(r) == 21 and sum(1 for _, w in r if w is None) == 1
    assert all(w != 0 for _, w in r)
    assert vd.mit_luecken(punkte[:10], timedelta(minutes=15)) == punkte[:10]


@test("Anmeldung: Passwort-Hash, falsches Passwort, beschädigter Hash")
def _():
    h = passwort_hash(PASSWORT)
    assert h.startswith("scrypt$") and PASSWORT not in h
    assert passwort_pruefen(PASSWORT, h) and not passwort_pruefen("falsch", h)
    assert not passwort_pruefen(PASSWORT, "md5$abc") and not passwort_pruefen(PASSWORT, "")


@test("Anmeldung: Sitzung signiert, Ablauf, Manipulation, fremder Schlüssel")
def _():
    s = sitzung_erzeugen(SCHLUESSEL, 3600, jetzt=1000)
    assert sitzung_gueltig(SCHLUESSEL, s, jetzt=1001)
    assert not sitzung_gueltig(SCHLUESSEL, s, jetzt=4601)
    teile = s.split(".")
    teile[1] = str(int(teile[1]) + 10 ** 6)                       # Ablauf verlängert, Signatur alt
    assert not sitzung_gueltig(SCHLUESSEL, ".".join(teile), jetzt=1001)
    assert not sitzung_gueltig("x" * 40, s, jetzt=1001)
    assert not sitzung_gueltig(SCHLUESSEL, None) and not sitzung_gueltig(SCHLUESSEL, "a.b")


@test("Anmeldung: Bremse nach 5 Fehlversuchen für 60 s, auch bei gleichzeitigen Anfragen")
def _():
    b = Bremse()
    assert all(b.versuch("1.2.3.4", jetzt=100 + i) for i in range(5))
    assert not b.versuch("1.2.3.4", jetzt=110) and b.versuch("5.6.7.8", jetzt=110)
    assert b.versuch("1.2.3.4", jetzt=200)
    b.erfolg("1.2.3.4")
    assert all(b.versuch("1.2.3.4", jetzt=300) for _ in range(5)) and not b.versuch("1.2.3.4", jetzt=301)
    import threading
    p = Bremse()
    erlaubt = []
    def los():
        erlaubt.append(p.versuch("9.9.9.9"))
    threads = [threading.Thread(target=los) for _ in range(50)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert erlaubt.count(True) == 5, erlaubt.count(True)


@test("Generator: gleiche Ausgabe bei gleichem Seed, Format wie ein_rohprotokoll()")
def _():
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        a, b = syn.protokolle_schreiben(d1), syn.protokolle_schreiben(d2)
        for q in a:
            assert (a[q] / "2026-10.jsonl").read_bytes() == (b[q] / "2026-10.jsonl").read_bytes(), q
        zeilen = (a["bienen_log"] / "2026-10.jsonl").read_text(encoding="utf-8").split("\n")
    assert zeilen[-1].startswith('{"geraet":"beelogger-01","art":"uplink","id":"halb'), "halbe letzte Zeile fehlt"
    ups = []
    for z in zeilen[:-1]:
        try:
            e = json.loads(z)
        except ValueError:
            continue
        if e.get("art") == "uplink":
            ups.append(e)
            assert list(e) == ["geraet", "art", "id", "roh_sha256", "nachricht", "log_zeit"], list(e)
            assert re.fullmatch(r"[0-9a-f]{40}", e["id"]) and e["id"] == syn.nachricht_id(e["nachricht"])
            roh = json.dumps(e["nachricht"], ensure_ascii=False, separators=(",", ":"))
            assert e["roh_sha256"] == hashlib.sha256(roh.encode()).hexdigest()
    ids = [e["id"] for e in ups]
    assert len(ids) - len(set(ids)) > 50, "zu wenige doppelte Zustellungen"
    l2 = [e for e in ups if e["geraet"] == "beelogger-02"]
    a0, a1 = syn.FAELLE["luecke"]
    assert not any(a0.timestamp() <= e["nachricht"]["uplink_message"]["decoded_payload"]["Messzeit_unix"] < a1.timestamp()
                   for e in l2), "Lücke nicht leer"
    fcnt = [e["nachricht"]["uplink_message"]["f_cnt"] for e in ups if e["geraet"] == "beelogger-01"]
    assert max(fcnt) == 16383 and 0 in fcnt, "FCnt-Rücksprung fehlt"


# ---------------------------------------------------------------- API ohne Datenbank (Abfragen ersetzt)

class FalscheVerbindung:
    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def rollback(self):
        pass

    def close(self):
        pass


ERSATZ = {"gesundheit": lambda cur: {"letzter_import": None}, "messgroessen": lambda cur: [{"code": "gewicht"}],
          "messgroessen_codes": lambda cur: {"gewicht": "mittel"}, "gibt_es": lambda cur, tab, i: i == 1,
          "messreihen": lambda cur, *a: []}


class ErsetzteAbfragen:
    """Abfragen für die Dauer eines Tests durch feste Antworten ersetzen (danach wieder die echten)."""

    def __enter__(self):
        from api import abfragen
        self.alt = {n: getattr(abfragen, n) for n in ERSATZ}
        for n, f in ERSATZ.items():
            setattr(abfragen, n, f)
        return falsche_app()

    def __exit__(self, *a):
        from api import abfragen
        for n, f in self.alt.items():
            setattr(abfragen, n, f)
        return False


def falsche_app():
    from fastapi.testclient import TestClient

    from api import app as app_modul
    k = {"dsn": "-", "passwort_hash": passwort_hash(PASSWORT), "sitzungsschluessel": SCHLUESSEL,
         "cookie_sicher": False, "sitzung_tage": 1}
    return TestClient(app_modul.erstellen(k, verbinden=FalscheVerbindung))


def mit_ersatz(fn):
    def lauf():
        with ErsetzteAbfragen() as c:
            fn(c)
    return lauf


@test("API: ohne Sitzung 401, Anmeldung setzt Cookie, Abmelden löscht es")
@mit_ersatz
def _(c):
    assert c.get("/api/gesundheit").status_code == 200
    assert c.get("/api/messgroessen").status_code == 401
    assert c.post("/api/anmelden", json={"passwort": "falsch"}).status_code == 401
    r = c.post("/api/anmelden", json={"passwort": PASSWORT})
    assert r.status_code == 200 and "bienen_sitzung" in r.cookies
    sc = r.headers["set-cookie"].lower()
    assert "httponly" in sc and "samesite=strict" in sc
    assert c.get("/api/messgroessen").json() == [{"code": "gewicht"}]
    c.cookies.set("bienen_sitzung", r.cookies["bienen_sitzung"][:-2] + "xx")
    assert c.get("/api/messgroessen").status_code == 401
    c.post("/api/anmelden", json={"passwort": PASSWORT})
    c.post("/api/abmelden")
    assert c.get("/api/messgroessen").status_code == 401


@test("API: fremde Herkunft 403, Bremse 429, Sicherheitskopfzeilen, unbekannter Endpunkt 404")
@mit_ersatz
def _(c):
    assert c.post("/api/anmelden", json={"passwort": PASSWORT}, headers={"Origin": "https://boese.example"}).status_code == 403
    for _ in range(5):
        c.post("/api/anmelden", json={"passwort": "falsch"})
    assert c.post("/api/anmelden", json={"passwort": PASSWORT}).status_code == 429
    r = c.get("/api/gesundheit")
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"] and r.headers["cache-control"] == "no-store"
    assert c.get("/api/gibtsnicht").status_code in (401, 404)
    assert c.get("/").status_code == 200 and "<title>" in c.get("/").text


@test("API: Zeitraum und Messgrößen werden geprüft (400/404)")
@mit_ersatz
def _(c):
    c.post("/api/anmelden", json={"passwort": PASSWORT})
    u = "/api/voelker/1/messreihen"
    assert c.get(u, params={"von": "2026-10-01T00:00:00Z", "bis": "2026-10-02T00:00:00Z"}).status_code == 200
    assert c.get(u, params={"von": "2026-10-01T00:00:00", "bis": "2026-10-02T00:00:00Z"}).status_code == 400   # ohne Zone
    assert c.get(u, params={"von": "gestern"}).status_code == 400
    assert c.get(u, params={"von": "2026-10-02T00:00:00Z", "bis": "2026-10-01T00:00:00Z"}).status_code == 400
    assert c.get(u, params={"von": "2025-01-01T00:00:00Z", "bis": "2026-10-01T00:00:00Z"}).status_code == 400
    assert c.get(u, params={"groessen": "gewicht,kaffee"}).status_code == 400
    assert c.get("/api/voelker/2/messreihen").status_code == 404
    assert c.get("/api/gibtsnicht").status_code == 404


# ================================================================ Teil 2: mit Datenbank

ZUSTAND = {}


def db_app():
    from fastapi.testclient import TestClient

    from api import app as app_modul
    k = {"dsn": DSN, "passwort_hash": passwort_hash(PASSWORT), "sitzungsschluessel": SCHLUESSEL,
         "cookie_sicher": False, "sitzung_tage": 1}
    c = TestClient(app_modul.erstellen(k))
    assert c.post("/api/anmelden", json={"passwort": PASSWORT}).status_code == 200
    return c


@test("Leere Datenbank: alle Seiten liefern 200 mit leeren Listen", db=True)
def _():
    import psycopg
    with psycopg.connect(DSN, autocommit=True) as con:
        con.execute((WURZEL / "server" / "datenbank" / "schema.sql").read_text(encoding="utf-8"))
    c = db_app()
    assert c.get("/api/staende").json() == []
    assert c.get("/api/messgroessen").json() == []
    p = c.get("/api/pruefungen").json()
    assert all(v == [] for v in p.values()), p
    assert c.get("/api/gesundheit").json()["letzter_import"] is None
    assert c.get("/api/voelker/1").status_code == 404


@test("Synthetischer Oktober: Import ohne Fehler, Doppelte und defekte Zeilen erkannt", db=True)
def _():
    import psycopg
    verz = tempfile.mkdtemp(prefix="bienen_syn_")
    with psycopg.connect(DSN) as con:
        k, b = syn.aufbauen(con, verz)
    ZUSTAND.update(k=k, verz=verz, client=db_app())
    print("       Import:", b.text().replace("\n", " | "))
    assert not b.fehler, b.fehler
    assert b.doppelt > 50 and b.ungueltig >= 1 and b.geraete_neu == ["beelogger-99"], b.text()
    assert b.messwerte > 35000 and b.ohne_kanal > 0


def k_(name):
    return ZUSTAND["k"][name]


def c_():
    return ZUSTAND["client"]


def reihe(antwort, groesse, zone=None):
    r = [x for x in antwort["reihen"] if x["messgroesse"] == groesse and (zone is None or x["zone"] == zone)]
    assert len(r) == 1, (groesse, zone, [(x["messgroesse"], x["zone"]) for x in antwort["reihen"]])
    return r[0]


@test("Dashboard: Völker je Stand nach Vereinigung und Umsetzen", db=True)
def _():
    s = {x["name"]: x for x in c_().get("/api/staende", params={"zeit": "2026-10-31T23:00:00Z"}).json()}
    haupt = [v["name"] for v in s["Hauptstand (synthetisch)"]["voelker"]]
    assert haupt == ["Volk 1 (syn)", "Volk 2 (syn)"], haupt                  # Volk 3 aufgelöst
    assert [v["name"] for v in s["Wiese (synthetisch)"]["voelker"]] == ["Volk 4 (syn)"]
    v1 = s["Hauptstand (synthetisch)"]["voelker"][0]
    assert 10 < v1["gewicht_kg"] < 25 and v1["tagesbilanz"]["berechnung"] == "gewicht_tagesbilanz@1", v1
    v4 = c_().get(f"/api/voelker/{k_('volk4')}", params={"zeit": "2026-10-25T00:00:00Z"}).json()
    assert v4["beute"]["bezeichnung"] == "Beute 5" and v4["stand"]["name"] == "Wiese (synthetisch)"
    v1d = c_().get(f"/api/voelker/{k_('volk1')}", params={"zeit": "2026-10-25T00:00:00Z"}).json()
    assert v1d["koenigin"]["farbe"] == "grün"


@test("Dashboard (Design v0.3): Beute, Königin, Messquelle, Varroa, offene Aufgaben je Volk; Standleiste mit Regen trotz Zähler-Neustart", db=True)
def _():
    from api import abfragen
    s = {x["name"]: x for x in c_().get("/api/staende", params={"zeit": "2026-10-16T08:00:00Z"}).json()}
    haupt = s["Hauptstand (synthetisch)"]
    v1 = {v["name"]: v for v in haupt["voelker"]}["Volk 1 (syn)"]
    assert v1["beute"] and v1["beute"]["bezeichnung"] and "brutzargen" in v1["beute"], v1["beute"]
    assert v1["koenigin"]["farbe"] == "grün" and v1["messquellen"] == 1 and isinstance(v1["aufgaben_offen"], list), v1
    u = haupt["umwelt"]
    codes = {w["messgroesse"] for w in u["werte"]}
    assert {"temperatur", "feuchte", "luftdruck", "wind"} <= codes, codes
    assert not any(w["zone"] in ("elektronik", "funk") for w in u["werte"]), u["werte"]
    import psycopg
    # Regen: unabhängig nachgerechnet aus den Zählerständen der 24 h (Neustart der Station am 16.10. 06:00 UTC)
    with psycopg.connect(DSN) as con:
        z = [r[0] for r in con.execute("""SELECT wert FROM bienen.messwert_bezug WHERE messgroesse_code = 'regen_summe'
                 AND stand_id = (SELECT id FROM bienen.stand WHERE name = 'Hauptstand (synthetisch)')
                 AND zeit > '2026-10-15T08:00:00Z' AND zeit <= '2026-10-16T08:00:00Z' ORDER BY zeit""").fetchall()]
    assert any(b < a for a, b in zip(z, z[1:])), "Testfall braucht einen Zähler-Neustart im Fenster"
    soll = round(sum((b - a) if b >= a else b for a, b in zip(z, z[1:])), 1)
    assert u["regen_24h"] == soll and u["regen_24h"] >= 0, (u["regen_24h"], soll)
    assert abfragen.regen_zuwachs([1.0, 2.5, None, 0.5, 1.0]) == 2.5 and abfragen.regen_zuwachs([]) == 0
    alt = {x["name"]: x for x in c_().get("/api/staende", params={"zeit": "2026-12-31T12:00:00Z"}).json()}
    assert alt["Hauptstand (synthetisch)"]["umwelt"]["werte"] == [], "Werte älter als 3 h gehören nicht in die Standleiste"


@test("Winterzeit-Nacht 25.10.: alle 7 Messungen in UTC, aufsteigend", db=True)
def _():
    r = c_().get(f"/api/voelker/{k_('volk1')}/messreihen",
                 params={"von": "2026-10-24T23:15:00Z", "bis": "2026-10-25T03:00:00Z", "groessen": "gewicht"}).json()
    zeiten = [p[0] for p in reihe(r, "gewicht")["punkte"] if p[1] is not None]
    soll = [(syn.FAELLE["winterzeit"][0] + timedelta(minutes=30 * i)) for i in range(7)]
    assert [t(x) for x in zeiten] == soll, zeiten


@test("Lücke von Logger 2 bleibt Lücke (null, keine 0)", db=True)
def _():
    r = c_().get(f"/api/voelker/{k_('volk2')}/messreihen",
                 params={"von": "2026-10-09T00:00:00Z", "bis": "2026-10-13T00:00:00Z", "groessen": "gewicht"}).json()
    p = reihe(r, "gewicht")["punkte"]
    luecken = [x for x in p if x[1] is None]
    assert len(luecken) == 1 and syn.FAELLE["luecke"][0] < t(luecken[0][0]) < syn.FAELLE["luecke"][1], luecken
    assert all(x[1] != 0 for x in p)


@test("Uhr nicht abgeglichen: Werte mit Empfangszeit gekennzeichnet", db=True)
def _():
    r = c_().get(f"/api/voelker/{k_('volk2')}/messreihen",
                 params={"von": "2026-10-05T00:00:00Z", "bis": "2026-10-06T00:00:00Z", "groessen": "gewicht"}).json()
    g = reihe(r, "gewicht")
    assert g["ohne_geraetezeit"] == g["werte"] == 48, (g["werte"], g["ohne_geraetezeit"])


@test("Tagesbilanz: Tarieren erklärt den Sprung (mit_eingriff), Vortag ohne Eingriff", db=True)
def _():
    r = {x["tag"]: x for x in c_().get(f"/api/voelker/{k_('volk1')}/tagesbilanz",
                                       params={"von": "2026-10-20T00:00:00Z", "bis": "2026-10-26T00:00:00Z"}).json()}
    assert r["2026-10-23"]["mit_eingriff"] is True and r["2026-10-23"]["bilanz_kg"] < -25, r["2026-10-23"]
    assert r["2026-10-22"]["mit_eingriff"] is False and abs(r["2026-10-22"]["bilanz_kg"]) < 0.5, r["2026-10-22"]


@test("Vereinigung: Volk 3 hat Werte nur bis zum Ende der Waagenzuordnung", db=True)
def _():
    r = c_().get(f"/api/voelker/{k_('volk3')}/messreihen",
                 params={"von": "2026-10-01T00:00:00Z", "bis": "2026-11-01T00:00:00Z", "groessen": "gewicht"}).json()
    letzte = max(t(p[0]) for p in reihe(r, "gewicht")["punkte"] if p[1] is not None)
    assert letzte < syn.FAELLE["vereinigung"], letzte
    e = c_().get(f"/api/voelker/{k_('volk3')}/ereignisse",
                 params={"von": "2026-10-01T00:00:00Z", "bis": "2026-11-01T00:00:00Z"}).json()
    assert [x["art"] for x in e["volk_ereignisse"]] == ["vereinigung"]


@test("Kanalwechsel: Versatz des neuen Sensors gleicht den Sprung aus", db=True)
def _():
    w = syn.FAELLE["kanalwechsel"]
    r = c_().get(f"/api/voelker/{k_('volk1')}/messreihen",
                 params={"von": (w - timedelta(days=2)).isoformat(), "bis": (w + timedelta(days=2)).isoformat(),
                         "groessen": "temperatur"}).json()
    p = [(t(a), b) for a, b in reihe(r, "temperatur", "brutnest")["punkte"] if b is not None]
    vor = [b for a, b in p if a < w]
    nach = [b for a, b in p if a >= w]
    assert abs(sum(vor) / len(vor) - sum(nach) / len(nach)) < 0.15, (sum(vor) / len(vor), sum(nach) / len(nach))


@test("Fehlwerte DS18B20 −127/85 °C und Gewichtsspitze bleiben sichtbar (keine stille Korrektur)", db=True)
def _():
    r = c_().get(f"/api/voelker/{k_('volk2')}/messreihen",
                 params={"von": "2026-10-08T02:00:00Z", "bis": "2026-10-08T05:00:00Z", "groessen": "temperatur"}).json()
    werte = {t(a): b for a, b in reihe(r, "temperatur", "brutnest")["punkte"]}
    assert werte[syn.FAELLE["ds18b20_minus127"]] == -127 and werte[syn.FAELLE["ds18b20_85"]] == 85
    print("       Hinweis: Fehlcodes werden als qualitaet 'ok' gespeichert – keine Plausibilitätsprüfung (Befund PLT26-11)")


@test("Wind: Kreismittel um 0/360° (nie 180°); Regenzähler wird nicht summiert", db=True)
def _():
    r = c_().get(f"/api/staende/{k_('stand1')}/umwelt",
                 params={"von": "2026-06-01T00:00:00Z", "bis": "2026-11-01T00:00:00Z",
                         "groessen": "windrichtung,regen_summe"}).json()
    assert r["raster_s"] == 7200
    richtung = [b for _, b in reihe(r, "windrichtung")["punkte"] if b is not None]
    assert richtung and all(b <= 15 or b >= 345 for b in richtung), [b for b in richtung if 15 < b < 345][:5]
    regen = [b for _, b in reihe(r, "regen_summe")["punkte"] if b is not None]
    zeilen = (pathlib.Path(ZUSTAND["verz"]) / "umwelt_log" / "2026-10.jsonl").read_text(encoding="utf-8").splitlines()
    roh = [json.loads(z)["nachricht"]["uplink_message"].get("decoded_payload", {}).get("rain_mm") for z in zeilen]
    roh = [x for x in roh if x is not None]
    assert max(regen) <= max(roh) + 1e-9, (max(regen), max(roh))
    assert any(b < a for a, b in zip(regen, regen[1:])), "Rücksetzung des Zählers nicht sichtbar"


@test("Ereignisse: Behandlung als Zeitraum (K-04), Durchsicht nur mit Datum (K-03), Varroa pro Tag", db=True)
def _():
    e = c_().get(f"/api/voelker/{k_('volk2')}/ereignisse",
                 params={"von": "2026-10-01T00:00:00Z", "bis": "2026-11-01T00:00:00Z"}).json()
    b = [m for m in e["massnahmen"] if m["art"] == "behandlung"][0]
    assert (t(b["von"]), t(b["bis"])) == syn.FAELLE["behandlung"]
    d = e["durchsichten"][0]
    assert d["zeitgenauigkeit"] == "nur_datum" and d["quelle"] == "beep_import"
    v = e["varroa"][0]
    assert float(v["milben_pro_tag"]) == 15.0 and v["berechnung"] == "varroa_pro_tag@1", v


@test("Datenquellen: unbenannte Felder (K-06), Geräte ohne Ziel, Importstand", db=True)
def _():
    p = c_().get("/api/pruefungen").json()
    unbenannt = {(x["geraet"], x["quellfeld"]) for x in p["unbenannt"]}
    assert ("beelogger-01", "FeuchteIn") in unbenannt and ("wetterstation-01", "l") in unbenannt, unbenannt
    assert ("beelogger-01", "Gewicht") not in unbenannt
    ohne = {x["name"] for x in p["geraete_ohne_ziel"]}
    assert ohne == {"beelogger-03", "beelogger-99"}, ohne
    assert {x["datei"] for x in p["importe"]} == {"bienen_log/2026-10.jsonl", "umwelt_log/2026-10.jsonl"}


@test("Unbekanntes Volk 404, unbekannte Messgröße 400, alle Messgrößen ohne Auswahl", db=True)
def _():
    assert c_().get("/api/voelker/99999/messreihen").status_code == 404
    assert c_().get(f"/api/voelker/{k_('volk1')}/messreihen", params={"groessen": "kaffee"}).status_code == 400
    r = c_().get(f"/api/voelker/{k_('volk1')}/messreihen",
                 params={"von": "2026-10-10T00:00:00Z", "bis": "2026-10-11T00:00:00Z"}).json()
    assert {x["messgroesse"] for x in r["reihen"]} == {"gewicht", "temperatur", "feuchte", "spannung"}


@test("Vorher/Nachher: Tarieren-Tag (−30 kg) zählt nicht als Wirkung (PLT26-13), Δ = nachher − vorher; 404, 400", db=True)
def _():
    e = c_().get(f"/api/voelker/{k_('volk1')}/ereignisse", params={"von": "2026-10-20T00:00:00Z", "bis": "2026-10-25T00:00:00Z"}).json()
    tarieren = [m for m in e["massnahmen"] if m["art"] == "tarieren"][0]["id"]
    r = c_().get(f"/api/voelker/{k_('volk1')}/vorher_nachher", params={"art": "massnahme", "ereignis_id": tarieren, "tage": 3}).json()
    g = {x["name"]: x for x in r["kennzahlen"]}
    b = g["Gewicht, Tagesbilanz"]
    assert b["n_vorher"] == 3 and b["eingriff_vorher"] == 0 and abs(b["vorher"]) < 0.2, b
    # Tag nach dem Tarieren (Bilanz −30 kg) ist Eingriffstag: ausgenommen, gezählt; übrig bleiben 2 normale Tage
    assert b["n_nachher"] == 2 and b["eingriff_nachher"] == 1 and abs(b["nachher"]) < 0.2, b
    assert b["berechnung"] == "gewicht_tagesbilanz@1"
    for k in r["kennzahlen"]:
        if k["vorher"] is not None and k["nachher"] is not None:
            assert abs(k["delta"] - (k["nachher"] - k["vorher"])) < 1e-9, k
    assert t(r["vorher"]["von"]) == syn.FAELLE["tarieren"] - timedelta(minutes=1) - timedelta(days=3)
    assert "Temperatur Brutnest" in g and "Temperatur Luft am Stand" in g and "Temperatur außen" in g, list(g)
    # Im Vorher-Fenster liegt der als ungültig markierte Wert 99,9 °C (20.10. 03:00): Mittel bleibt beim Sensorwert
    # 33,0 °C (Logger 1: 33,5 − 0,5; nach dem Sensortausch +0,5 roh, Versatz −0,5)
    brut = g["Temperatur Brutnest"]
    assert abs(brut["vorher"] - 33.0) < 0.05 and brut["n_vorher"] == 143, brut
    assert c_().get(f"/api/voelker/{k_('volk2')}/vorher_nachher", params={"art": "massnahme", "ereignis_id": tarieren}).status_code == 404
    assert c_().get(f"/api/voelker/{k_('volk1')}/vorher_nachher", params={"art": "massnahme", "ereignis_id": tarieren, "tage": 5}).status_code == 400


@test("Vorher/Nachher Behandlung: Milbenfall nach der Behandlung aus der Windelzählung", db=True)
def _():
    e = c_().get(f"/api/voelker/{k_('volk2')}/ereignisse", params={"von": "2026-10-01T00:00:00Z", "bis": "2026-10-20T00:00:00Z"}).json()
    b = [m for m in e["massnahmen"] if m["art"] == "behandlung"][0]["id"]
    r = c_().get(f"/api/voelker/{k_('volk2')}/vorher_nachher", params={"art": "massnahme", "ereignis_id": b, "tage": 7}).json()
    m = {x["name"]: x for x in r["kennzahlen"]}["Milbenfall"]
    assert m["nachher"] == 15.0 and m["n_nachher"] == 1 and m["vorher"] is None, m


@test("Völkervergleich: Nachtmedian je Tag, Summen, Sprung ohne Eingriff (Vereinigung), Fehlcodes, 400", db=True)
def _():
    ids = f"{k_('volk1')},{k_('volk2')},{k_('volk4')}"
    r = c_().get("/api/vergleich", params={"volk_ids": ids, "von": "2026-10-01T00:00:00Z", "bis": "2026-11-01T00:00:00Z"}).json()
    v = {x["name"]: x for x in r["voelker"]}
    v1, v2, v4 = v["Volk 1 (syn)"], v["Volk 2 (syn)"], v["Volk 4 (syn)"]
    assert len(v1["tagesreferenz"]) == 31 and len(v1["tagesbilanz"]) == 30, (len(v1["tagesreferenz"]), len(v1["tagesbilanz"]))
    assert v1["spruenge"] == ["2026-10-16"], v1["spruenge"]                 # Vereinigung +6 kg ohne erfasste Maßnahme
    assert v2["fehlcodes"] == 2 and v1["fehlcodes"] == 0
    # Umsetzen ist als Maßnahme erfasst (kein Sprung); −3 kg am 27.10. ohne Maßnahme zeigt sich am 28.10. (negativ!)
    assert v4["spruenge"] == ["2026-10-28"], v4["spruenge"]
    assert abs([b for b in v4["tagesbilanz"] if b["tag"] == "2026-10-28"][0]["bilanz_kg"] + 3) < 0.2
    assert abs(v1["summe_kg"] - sum(b["bilanz_kg"] for b in v1["tagesbilanz"])) < 1e-9
    assert v1["summe_ohne_eingriff_kg"] > v1["summe_kg"]                     # Tarieren (−30 kg) ausgenommen
    assert v1["messpunkte"] == 1488 and v1["letzte_referenz"]["tag"] == "2026-10-31"
    assert c_().get("/api/vergleich", params={"volk_ids": "a,b"}).status_code == 400
    assert c_().get("/api/vergleich", params={"volk_ids": ""}).status_code == 400


@test("Verdichtung in SQL: jedes Aggregat rechnet, was es heißt (mittel, median, summe, max, min, letzter, vektor, keine)", db=True)
def _():
    import psycopg
    werte = "(1.0, '2026-10-01T00:00Z'::timestamptz), (5.0, '2026-10-01T00:10Z'), (3.0, '2026-10-01T00:20Z'), (2.0, '2026-10-01T00:05Z')"
    soll = {"mittel": 2.75, "median": 2.5, "summe": 11.0, "max": 5.0, "min": 1.0, "letzter": 3.0, "keine": 3.0}
    with psycopg.connect(DSN) as con:
        for v, s in soll.items():
            w = con.execute(f"SELECT ({vd.aggregat(v)})::float8 FROM (VALUES {werte}) AS x(wert, zeit)").fetchone()[0]
            assert abs(w - s) < 1e-9, (v, w, s)
        w = con.execute(f"SELECT ({vd.aggregat('vektor')})::float8 FROM (VALUES (350.0, now()), (20.0, now())) AS x(wert, zeit)").fetchone()[0]
        assert abs(w - 5.0) < 1e-6, w


@test("Ungültig markierter Wert fehlt in Kurve und Mittelwert; kurzer Ausfall (120 min) wird Lücke", db=True)
def _():
    r = c_().get(f"/api/voelker/{k_('volk1')}/messreihen", params={"von": "2026-10-19T12:00:00Z", "bis": "2026-10-20T12:00:00Z",
                                                                 "groessen": "temperatur"}).json()
    brut = [x for x in r["reihen"] if x["zone"] == "brutnest"][0]
    assert all(w is None or w < 40 for _, w in brut["punkte"]), max(w for _, w in brut["punkte"] if w is not None)
    assert not any(t(z) == syn.FAELLE["ungueltig"] for z, _ in brut["punkte"])
    r = c_().get(f"/api/voelker/{k_('volk4')}/messreihen", params={"von": "2026-10-27T00:00:00Z", "bis": "2026-10-27T12:00:00Z",
                                                                 "groessen": "gewicht"}).json()
    p = r["reihen"][0]["punkte"]
    nullen = [t(z) for z, w in p if w is None]
    assert len(nullen) == 1 and syn.FAELLE["kurzausfall"][0] - timedelta(minutes=30) < nullen[0] < syn.FAELLE["kurzausfall"][1], nullen
    assert all(w is None or w != 0 for _, w in p)


@test("Verdichtung max über einen Monat: Windböe zeigt die größte Böe, nicht den Mittelwert", db=True)
def _():
    import psycopg
    r = c_().get(f"/api/staende/{k_('stand1')}/umwelt", params={"von": "2026-09-01T00:00:00Z", "bis": "2026-12-01T00:00:00Z",
                                                              "groessen": "windboe"}).json()
    hoechst = max(w for _, w in r["reihen"][0]["punkte"] if w is not None)
    with psycopg.connect(DSN) as con:
        soll = con.execute("SELECT max(wert) FROM bienen.messwert_bezug WHERE messgroesse_code = 'windboe'").fetchone()[0]
    assert abs(hoechst - soll) < 1e-9 and r["raster_s"] > 1800, (hoechst, soll, r.get("raster_s"))


@test("Vergleich: Tagesgrenzen in Ortszeit (von 11.10. 00:00 MESZ = 10.10. 22:00 UTC)", db=True)
def _():
    r = c_().get("/api/vergleich", params={"volk_ids": k_("volk1"), "von": "2026-10-10T22:00:00Z", "bis": "2026-10-12T22:00:00Z"}).json()
    v = r["voelker"][0]
    assert [x["tag"] for x in v["tagesreferenz"]] == ["2026-10-11", "2026-10-12"], v["tagesreferenz"]
    assert [x["tag"] for x in v["tagesbilanz"]] == ["2026-10-11", "2026-10-12"], v["tagesbilanz"]


@test("Vorher/Nachher: Durchsicht und Varroa als Bezug; Windel, die ins Fenster hineinreicht, zählt; Luft am Stand ≠ außen", db=True)
def _():
    e = c_().get(f"/api/voelker/{k_('volk2')}/ereignisse", params={"von": "2026-10-01T00:00:00Z", "bis": "2026-10-20T00:00:00Z"}).json()
    w = e["varroa"][0]
    r = c_().get(f"/api/voelker/{k_('volk2')}/vorher_nachher", params={"art": "varroa", "ereignis_id": w["id"], "tage": 3}).json()
    assert t(r["vorher"]["bis"]) == syn.FAELLE["windel"][0] and t(r["nachher"]["von"]) == syn.FAELLE["windel"][1], r["vorher"]
    assert r["ereignis"]["text"] == "Varroa windel"
    d = e["durchsichten"][0]
    r = c_().get(f"/api/voelker/{k_('volk2')}/vorher_nachher", params={"art": "durchsicht", "ereignis_id": d["id"], "tage": 1}).json()
    assert r["vorher"]["bis"] == r["nachher"]["von"] == d["zeit"] and r["ereignis"]["text"] == "Durchsicht"
    b = [m for m in e["massnahmen"] if m["art"] == "behandlung"][0]["id"]
    # Behandlung endet 11.10. 08:00, Fenster ± 3 Tage bis 14.10.; die Windel (12.–15.10.) reicht hinein
    r = c_().get(f"/api/voelker/{k_('volk2')}/vorher_nachher", params={"art": "massnahme", "ereignis_id": b, "tage": 3}).json()
    m = {x["name"]: x for x in r["kennzahlen"]}["Milbenfall"]
    assert m["n_nachher"] == 1 and m["nachher"] == 15.0, m
    g = {x["name"]: x for x in r["kennzahlen"]}
    aussen = g["Temperatur außen"]
    luft = g["Temperatur Luft am Stand"]
    assert abs((luft["vorher"] - aussen["vorher"]) - syn.VERSATZ_STATION) < 0.05, (luft, aussen)
    assert c_().get(f"/api/voelker/{k_('volk2')}/vorher_nachher", params={"art": "x", "ereignis_id": b}).status_code == 404


@test("Felder ohne Kanal: Anzahl je Gerät und Feld (31 Tage × 48 Werte; Logger 4 mit 3 fehlenden)", db=True)
def _():
    u = {(x["geraet"], x["quellfeld"]): x for x in c_().get("/api/pruefungen").json()["unbenannt"]}
    assert u[("beelogger-01", "FeuchteIn")]["anzahl"] == 1488, u[("beelogger-01", "FeuchteIn")]
    assert u[("beelogger-04", "FeuchteIn")]["anzahl"] == 1485, u[("beelogger-04", "FeuchteIn")]
    assert t(u[("beelogger-01", "FeuchteIn")]["zuerst"]) == syn.START
    # Steuerfelder (Format, Messzeit_unix, Status.*) getrennt geführt, keine Hinweise (M-05)
    p = c_().get("/api/pruefungen").json()
    assert not [x for x in p["unbenannt"] if x["quellfeld"] in ("Format", "Messzeit_unix") or x["quellfeld"].startswith("Status.")]
    assert {"Format", "Messzeit_unix", "Status.zeit_ok"} <= {x["quellfeld"] for x in p["steuerfelder"]}
    assert sorted({x["quellfeld"] for x in p["unbenannt"]}) == ["FeuchteIn", "Gewicht", "TempIn", "l"], sorted({x["quellfeld"] for x in p["unbenannt"]})


@test("Oberfläche und API führen denselben API_STAND; /api/gesundheit liefert ihn (PLT26-17)")
def _():
    from api import app as app_modul
    js = (pathlib.Path(__file__).resolve().parents[2] / "server/plattform/web/api.js").read_text(encoding="utf-8")
    m = re.search(r"export const API_STAND = (\d+);", js)
    assert m and int(m.group(1)) == app_modul.API_STAND, (m and m.group(1), app_modul.API_STAND)


@test("Gesundheit nennt den API-Stand", db=True)
def _():
    from api import app as app_modul
    assert c_().get("/api/gesundheit").json()["api_stand"] == app_modul.API_STAND


# ================================================================ Ablauf

def melden(name, fehler):
    print(f"FEHLER     {name}: {fehler}")
    if os.environ.get("GITHUB_ACTIONS"):
        text = f"{name}: {fehler}".replace("%", "%25").replace("\r", "").replace("\n", "%0A")[:900]
        print(f"::error title=test_plattform::{text}")


def main():
    fehler, gelaufen, db_ok = 0, 0, False
    if DSN:
        try:
            import psycopg
            psycopg.connect(DSN, connect_timeout=5).close()
            db_ok = True
        except Exception as e:  # noqa: BLE001
            print(f"Datenbank nicht erreichbar: {e}")
    for fn in TESTS:
        if fn.db and not db_ok:
            print(f"NICHT GELAUFEN {fn.testname}")
            continue
        gelaufen += 1
        try:
            fn()
            print(f"bestanden  {fn.testname}")
        except Exception as e:  # noqa: BLE001
            fehler += 1
            melden(fn.testname, f"{type(e).__name__}: {e}")
            traceback.print_exc()
            if fn.db and not ZUSTAND.get("client") and "Synthetischer" in fn.testname:
                break
    print(f"\n{gelaufen - fehler} von {gelaufen} bestanden" + ("" if db_ok else " (Datenbankteil NICHT GELAUFEN)"))
    if fehler:
        return 1
    return 0 if db_ok else 2


if __name__ == "__main__":
    sys.exit(main())
