# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests der Stammdaten-Pflege (server/plattform/api/verwaltung.py, stammdaten.py) und des Nachtragens im Importer.

Aufruf:
    pip install -r server/plattform/requirements.txt
    BIENEN_TEST_DSN="host=… dbname=bienen_test user=…" python3 tests/plattform/test_verwaltung.py

Teil 1 (ohne Datenbank): CSRF-Token, Schutz der schreibenden Endpunkte, Eingabeprüfung, Ortszeit.
Teil 2 (PostgreSQL ab 16): leerer Start wie im Betrieb – Katalog, Stand, Volk, ein Logger sendet, bevor er
zugeordnet ist (Importer legt ihn an), Zuordnung und Vorlage, Nachtragen, Zargen, Umsetzen, Vereinigung,
Konflikte (409) ohne Teiländerungen. Schema 'bienen' der Testdatenbank wird gelöscht.
Ohne Datenbank: Teil 2 NICHT GELAUFEN, Rückgabe 2.
"""
import os
import pathlib
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone

WURZEL = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "server" / "plattform"))
sys.path.insert(0, str(WURZEL / "server" / "datenbank"))
import synthetisch as syn  # noqa: E402
from api.anmeldung import csrf_gueltig, csrf_token, passwort_hash, sitzung_erzeugen  # noqa: E402

DSN = os.environ.get("BIENEN_TEST_DSN", "")
PASSWORT = "test-passwort-1234"
SCHLUESSEL = "k" * 40
TESTS, ZUSTAND = [], {}
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc)


def test(name, db=False):
    def deko(fn):
        fn.testname, fn.db = name, db
        TESTS.append(fn)
        return fn
    return deko


def iso(t):
    return t.isoformat()


# ================================================================ Teil 1: ohne Datenbank

@test("CSRF-Token an die Sitzung gebunden")
def _():
    s1, s2 = sitzung_erzeugen(SCHLUESSEL, 60), sitzung_erzeugen(SCHLUESSEL, 60)
    t = csrf_token(SCHLUESSEL, s1)
    assert csrf_gueltig(SCHLUESSEL, s1, t) and not csrf_gueltig(SCHLUESSEL, s2, t)
    assert not csrf_gueltig(SCHLUESSEL, s1, "") and not csrf_gueltig(SCHLUESSEL, s1, None)


class Keine:
    """Verbindung, über die nie eine Abfrage laufen darf: Schutz- und Eingabeprüfungen müssen vorher greifen.
    (FastAPI öffnet die Abhängigkeit vor der Prüfung des Inhalts; ausgeführt werden darf aber nichts.)"""

    def __call__(self):
        return self

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **k):
        raise AssertionError("Datenbank angesprochen, obwohl die Anfrage abgelehnt werden musste")

    def commit(self):
        raise AssertionError("Commit bei abgelehnter Anfrage")

    def rollback(self):
        pass

    def close(self):
        pass


@test("Schreiben: ohne Sitzung 401, ohne/mit falschem CSRF-Token 403, fremde Herkunft 403, ohne Zeitzone 422")
def _():
    from fastapi.testclient import TestClient

    from api import app as app_modul
    k = {"dsn": "-", "passwort_hash": passwort_hash(PASSWORT), "sitzungsschluessel": SCHLUESSEL, "cookie_sicher": False}
    c = TestClient(app_modul.erstellen(k, verbinden=Keine(), verbinden_schreiben=Keine()))
    u = "/api/verwaltung/staende"
    assert c.post(u, json={"name": "A"}).status_code == 401
    assert c.post("/api/anmelden", json={"passwort": PASSWORT}).status_code == 200
    token = c.get("/api/sitzung").json()["csrf"]
    assert c.post(u, json={"name": "A"}).status_code == 403
    assert c.post(u, json={"name": "A"}, headers={"X-CSRF-Token": "falsch"}).status_code == 403
    assert c.post(u, json={"name": "A"}, headers={"X-CSRF-Token": token, "Origin": "https://boese.example"}).status_code == 403
    r = c.post("/api/verwaltung/voelker/1/aufloesen", json={"zeit": "2026-10-01T00:00:00"}, headers={"X-CSRF-Token": token})
    assert r.status_code == 422, r.text
    assert c.post(u, json={"name": ""}, headers={"X-CSRF-Token": token}).status_code == 422


# ================================================================ Teil 2: mit Datenbank

def cl():
    return ZUSTAND["c"]


def post(pfad, daten, soll=200, methode="post"):
    r = getattr(cl(), methode)("/api/verwaltung/" + pfad, json=daten, headers={"X-CSRF-Token": ZUSTAND["csrf"]})
    assert r.status_code == soll, (pfad, r.status_code, r.text)
    return r.json()


def uebersicht():
    return cl().get("/api/verwaltung", params={"zeit": "2026-11-15T00:00:00Z"}).json()


def protokoll_schreiben(verz, geraet, von, anzahl, start_fcnt=0):
    """Uplinks eines beelogger alle 30 min, wie sie der LoRa-Eingang protokolliert"""
    d = pathlib.Path(verz) / "bienen_log"
    d.mkdir(parents=True, exist_ok=True)
    zeilen = []
    for i in range(anzahl):
        t = von + timedelta(minutes=30 * i)
        daten = {"Format": 2, "Gewicht": 30 + i / 100, "TempIn": 33.0, "TempOut": 10.0, "FeuchteOut": 80, "FeuchteIn": 61,
                 "VBatt": 3.9, "Status": {"zeit_ok": True}, "Messzeit_unix": int(t.timestamp())}
        msg = syn.uplink(geraet, 2, start_fcnt + i, syn.ttn_text(t + timedelta(seconds=5)), daten)
        zeilen.append(syn.protokollzeile("geraet", geraet, msg, syn.ttn_text(t)[:19] + "Z"))
    with open(d / "2026-10.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(zeilen) + "\n")


def importieren():
    import importer
    import psycopg
    with psycopg.connect(DSN) as con:
        return importer.importieren(con, {"bienen_log": pathlib.Path(ZUSTAND["verz"]) / "bienen_log"})


@test("Leerer Start: Katalog, Stand, Volk (409 bei doppeltem Stand)", db=True)
def _():
    import psycopg
    from fastapi.testclient import TestClient

    from api import app as app_modul
    with psycopg.connect(DSN, autocommit=True) as con:
        con.execute((WURZEL / "server" / "datenbank" / "schema.sql").read_text(encoding="utf-8"))
    verz = tempfile.mkdtemp(prefix="bienen_verw_")
    k = {"dsn": DSN, "passwort_hash": passwort_hash(PASSWORT), "sitzungsschluessel": SCHLUESSEL, "cookie_sicher": False,
         "protokolle": {"bienen_log": str(pathlib.Path(verz) / "bienen_log")}}
    c = TestClient(app_modul.erstellen(k))
    assert c.post("/api/anmelden", json={"passwort": PASSWORT}).status_code == 200
    ZUSTAND.update(c=c, csrf=c.get("/api/sitzung").json()["csrf"], verz=verz)
    assert post("katalog/standard", {})["neu"] == 12
    assert post("katalog/standard", {})["neu"] == 0
    ZUSTAND["stand"] = post("staende", {"name": "Hauptstand", "ort_oeffentlich": "Radeberg"})["id"]
    assert "schon vergeben" in post("staende", {"name": "Hauptstand"}, 409)["detail"]
    for i in (1, 2):
        r = post("voelker", {"name": f"Volk {i}", "zeit": iso(T0), "stand_id": ZUSTAND["stand"], "platz": i,
                             "beute": {"bezeichnung": f"Beute {i}", "beutentyp": "Segeberger 1,5", "brutzargen": 1, "honigzargen": 0}})
        ZUSTAND[f"volk{i}"], ZUSTAND[f"beute{i}"] = r["id"], r["beute_id"]
    s = cl().get("/api/staende", params={"zeit": "2026-10-02T00:00:00Z"}).json()
    assert [v["name"] for v in s[0]["voelker"]] == ["Volk 1", "Volk 2"], s


@test("Umbenennen von Stand und Volk; eigene Messgröße mit Verdichtung min; ungültige Verdichtung 422", db=True)
def _():
    post(f"staende/{ZUSTAND['stand']}", {"name": "Hauptstand Nord", "ort_oeffentlich": "Radeberg"}, methode="put")
    post(f"voelker/{ZUSTAND['volk1']}", {"name": "Volk Eins", "notiz": "ruhig"}, methode="put")
    s = cl().get("/api/staende", params={"zeit": "2026-10-02T00:00:00Z"}).json()
    assert s[0]["name"] == "Hauptstand Nord" and s[0]["voelker"][0]["name"] == "Volk Eins", s
    post(f"staende/{ZUSTAND['stand']}", {"name": "Hauptstand", "ort_oeffentlich": "Radeberg"}, methode="put")
    post(f"voelker/{ZUSTAND['volk1']}", {"name": "Volk 1"}, methode="put")
    post("staende/99999", {"name": "x"}, 404, methode="put")
    post("messgroessen", {"code": "bodenfrost", "name": "Bodenfrost", "einheit": "°C", "semantik": "momentan",
                          "verdichtung": "min", "achse": "temperatur"})
    g = {m["code"]: m for m in cl().get("/api/messgroessen").json()}
    assert g["bodenfrost"]["verdichtung"] == "min" and g["bodenfrost"]["name"] == "Bodenfrost"
    post("messgroessen", {"code": "x", "name": "x", "einheit": "", "semantik": "momentan", "verdichtung": "avg", "achse": "x"}, 422)


@test("Logger sendet vor der Zuordnung: Importer legt ihn an, Werte nur als unbenannte Felder", db=True)
def _():
    protokoll_schreiben(ZUSTAND["verz"], "beelogger-01", T0, 96)
    b = importieren()
    assert b.neu == 96 and b.messwerte == 0 and b.geraete_neu == ["beelogger-01"], b.text()
    g = {x["name"]: x for x in uebersicht()["geraete"]}["beelogger-01"]
    assert g["art"] == "sonstiges" and g["volk_id"] is None
    assert {u["quellfeld"] for u in g["unbenannt"]} >= {"Gewicht", "TempIn", "FeuchteIn"}
    ZUSTAND["geraet1"] = g["id"]


@test("Zuordnen und Vorlage: Kanäle ab Beginn, Art wird Stockwaage; Vorlage passt nicht zu Stand → 409", db=True)
def _():
    g = ZUSTAND["geraet1"]
    post(f"geraete/{g}/zuordnen", {"zeit": iso(T0), "volk_id": ZUSTAND["volk1"]})
    assert "Stand" in post(f"geraete/{g}/vorlage", {"zeit": iso(T0), "vorlage": "s2120"}, 409)["detail"]
    assert len(post(f"geraete/{g}/vorlage", {"zeit": iso(T0), "vorlage": "beelogger"})["kanaele"]) == 5
    assert post(f"geraete/{g}/vorlage", {"zeit": iso(T0), "vorlage": "beelogger"})["kanaele"] == []    # schon vorhanden
    gg = {x["name"]: x for x in uebersicht()["geraete"]}["beelogger-01"]
    assert gg["art"] == "stockwaage" and len(gg["kanaele"]) == 5
    assert {u["quellfeld"] for u in gg["unbenannt"]} >= {"FeuchteIn"} and "Gewicht" not in {u["quellfeld"] for u in gg["unbenannt"]}


@test("Nachtragen: ältere Nachrichten werden nach dem Anlegen der Kanäle zu Messwerten, zweimal gleich", db=True)
def _():
    u = f"/api/voelker/{ZUSTAND['volk1']}/messreihen"
    p = {"von": "2026-10-01T00:00:00Z", "bis": "2026-10-03T00:00:00Z", "groessen": "gewicht"}
    assert cl().get(u, params=p).json()["reihen"] == []
    r = post(f"geraete/{ZUSTAND['geraet1']}/nachtragen", {})
    assert r["messwerte"] == 96 * 5 and not r["fehler"], r
    assert post(f"geraete/{ZUSTAND['geraet1']}/nachtragen", {})["messwerte"] == 0
    punkte = [x for x in cl().get(u, params=p).json()["reihen"][0]["punkte"] if x[1] is not None]
    assert len(punkte) == 96 and abs(punkte[0][1] - 30) < 1e-6
    unb = {(x["geraet"], x["quellfeld"]) for x in cl().get("/api/pruefungen").json()["unbenannt"]}
    assert ("beelogger-01", "FeuchteIn") in unb and ("beelogger-01", "Gewicht") not in unb


@test("Nachtragen erkennt veränderte Protokollzeilen (Prüfsumme)", db=True)
def _():
    import importer
    import psycopg
    datei = pathlib.Path(ZUSTAND["verz"]) / "bienen_log" / "2026-10.jsonl"
    original = datei.read_bytes()
    zeilen = original.split(b"\n")
    zeilen[0] = zeilen[0].replace(b'"Gewicht":30.0', b'"Gewicht":99.0')
    datei.write_bytes(b"\n".join(zeilen))
    try:
        with psycopg.connect(DSN) as con:
            b = importer.Importer(con).nachtragen({"bienen_log": datei.parent}, "beelogger-01")
        assert len(b.fehler) == 1 and "Prüfsumme" in b.fehler[0], b.fehler
    finally:
        datei.write_bytes(original)


@test("Zargen ändern: neue Konfiguration ab Zeitpunkt, alte bleibt; Änderung vor dem Beginn → 409", db=True)
def _():
    b = ZUSTAND["beute1"]
    post(f"beuten/{b}/konfiguration", {"zeit": "2026-10-05T10:00:00Z", "brutzargen": 1, "honigzargen": 1})
    v = ZUSTAND["volk1"]
    alt = cl().get(f"/api/voelker/{v}", params={"zeit": "2026-10-04T00:00:00Z"}).json()["beute"]
    neu = cl().get(f"/api/voelker/{v}", params={"zeit": "2026-10-06T00:00:00Z"}).json()["beute"]
    assert (alt["honigzargen"], neu["honigzargen"]) == (0, 1)
    assert "Historie" in post(f"beuten/{b}/konfiguration", {"zeit": "2026-10-05T09:00:00Z", "brutzargen": 2}, 409)["detail"]


@test("Konflikte: zweite Waage am selben Volk, belegte Beute – 409 ohne Teiländerung", db=True)
def _():
    g2 = post("geraete", {"name": "beelogger-02", "art": "stockwaage"})["id"]
    ZUSTAND["geraet2"] = g2
    r = post(f"geraete/{g2}/zuordnen", {"zeit": iso(T0 + timedelta(days=1)), "volk_id": ZUSTAND["volk1"]}, 409)
    assert "überschneidet" in r["detail"], r
    post(f"geraete/{g2}/zuordnen", {"zeit": iso(T0 + timedelta(days=1)), "volk_id": ZUSTAND["volk2"]})
    # Volk 1 in die belegte Beute 2 setzen: abgelehnt, die alte Belegung von Volk 1 bleibt offen
    post(f"voelker/{ZUSTAND['volk1']}/umsetzen", {"zeit": "2026-10-10T08:00:00Z", "beute_id": ZUSTAND["beute2"]}, 409)
    v = cl().get(f"/api/voelker/{ZUSTAND['volk1']}", params={"zeit": "2026-10-11T00:00:00Z"}).json()
    assert v["beute"]["bezeichnung"] == "Beute 1", v["beute"]
    assert "entweder" in post(f"voelker/{ZUSTAND['volk1']}/umsetzen", {"zeit": "2026-10-10T08:00:00Z"}, 422)["detail"]


@test("Umsetzen in neue Beute: gleicher Stand und Platz, Maßnahme 'umsetzen' erklärt den Sprung", db=True)
def _():
    z = "2026-10-12T08:00:00+02:00"
    post(f"voelker/{ZUSTAND['volk1']}/umsetzen", {"zeit": z, "beute": {"bezeichnung": "Beute 1b", "brutzargen": 1, "honigzargen": 1}})
    s = cl().get("/api/staende", params={"zeit": "2026-10-13T00:00:00Z"}).json()[0]
    v1 = [v for v in s["voelker"] if v["id"] == ZUSTAND["volk1"]][0]
    assert v1["platz"] == 1
    assert cl().get(f"/api/voelker/{ZUSTAND['volk1']}", params={"zeit": "2026-10-13T00:00:00Z"}).json()["beute"]["bezeichnung"] == "Beute 1b"
    e = cl().get(f"/api/voelker/{ZUSTAND['volk1']}/ereignisse", params={"von": "2026-10-12T00:00:00Z", "bis": "2026-10-13T00:00:00Z"}).json()
    assert [m["art"] for m in e["massnahmen"]] == ["umsetzen"]


@test("Kanal neu ab Zeitpunkt (Sensortausch mit Versatz): alter Kanal endet dort; Kanal beenden", db=True)
def _():
    g = ZUSTAND["geraet1"]
    w = "2026-10-01T20:00:00Z"
    neu = post(f"geraete/{g}/kanaele", {"zeit": w, "quellfeld": "TempIn", "messgroesse": "temperatur", "zone": "brutnest",
                                        "versatz": -0.5, "kalibrierung": "Referenzthermometer"})["id"]
    k = [x for x in {y["name"]: y for y in uebersicht()["geraete"]}["beelogger-01"]["kanaele"] if x["quellfeld"] == "TempIn"]
    assert len(k) == 2 and k[0]["bis"] is not None and k[1]["id"] == neu and k[1]["versatz"] == -0.5
    post(f"kanaele/{neu}/beenden", {"zeit": "2026-10-20T00:00:00Z"})
    assert "keine offene" in post(f"kanaele/{neu}/beenden", {"zeit": "2026-10-21T00:00:00Z"}, 409)["detail"]
    assert "Katalog" in post(f"geraete/{g}/kanaele", {"zeit": w, "quellfeld": "Aux1", "messgroesse": "kaffee", "zone": "aussen"}, 409)["detail"]


@test("Vereinigung: Belegung und Waagenzuordnung enden, keine HB-09-Meldung, Gerät ohne Ziel gemeldet", db=True)
def _():
    z = "2026-10-15T12:00:00Z"
    r = post(f"voelker/{ZUSTAND['volk2']}/aufloesen", {"zeit": z, "art": "vereinigung", "ziel_volk_id": ZUSTAND["volk1"]})
    assert r["zuordnungen_beendet"] == 1
    p = cl().get("/api/pruefungen").json()
    assert p["zuordnung"] == [], p["zuordnung"]
    assert "beelogger-02" in {g["name"] for g in p["geraete_ohne_ziel"]}
    assert "bereits aufgelöst" in post(f"voelker/{ZUSTAND['volk2']}/aufloesen", {"zeit": z}, 409)["detail"]
    assert "aufgelöst" in post(f"geraete/{ZUSTAND['geraet2']}/zuordnen", {"zeit": "2026-10-16T00:00:00Z", "volk_id": ZUSTAND["volk2"]}, 409)["detail"]
    s = cl().get("/api/staende", params={"zeit": "2026-10-16T00:00:00Z"}).json()[0]
    assert [v["name"] for v in s["voelker"]] == ["Volk 1"]


@test("Wetterstation am Stand mit Vorlage s2120; Umwelt-Messgrößen im Katalog vorhanden", db=True)
def _():
    w = post("geraete", {"name": "wetterstation-01", "art": "wetter", "modell": "SenseCAP S2120"})["id"]
    post(f"geraete/{w}/zuordnen", {"zeit": iso(T0), "stand_id": ZUSTAND["stand"]})
    assert len(post(f"geraete/{w}/vorlage", {"zeit": iso(T0), "vorlage": "s2120"})["kanaele"]) == 10
    assert post(f"geraete/{w}/zuordnen", {"zeit": "2026-10-20T00:00:00Z"}) == {"beendet": 1}


# ================================================================ Ablauf

def melden(name, fehler):
    print(f"FEHLER     {name}: {fehler}")
    if os.environ.get("GITHUB_ACTIONS"):
        text = f"{name}: {fehler}".replace("%", "%25").replace("\r", "").replace("\n", "%0A")[:900]
        print(f"::error title=test_verwaltung::{text}")


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
    print(f"\n{gelaufen - fehler} von {gelaufen} bestanden" + ("" if db_ok else " (Datenbankteil NICHT GELAUFEN)"))
    if fehler:
        return 1
    return 0 if db_ok else 2


if __name__ == "__main__":
    sys.exit(main())
