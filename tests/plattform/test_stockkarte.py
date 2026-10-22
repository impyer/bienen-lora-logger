# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests der Stockkarte (server/plattform/api/stockkarte.py, stockkarte_api.py; Phase C, Teil 2).

Aufruf:
    pip install -r server/plattform/requirements.txt
    BIENEN_TEST_DSN="host=… dbname=bienen_test user=…" python3 tests/plattform/test_stockkarte.py

Teil 1 (ohne Datenbank): Werteprüfung je Eingabetyp, Schutz der schreibenden Endpunkte (auch DELETE), Eingaben.
Teil 2 (PostgreSQL ab 16): Checkliste mit Version (K-10), Durchsicht für mehrere Völker mit Werten, Korrektur der
Uhrzeit (K-03), Maßnahme als Zeitpunkt und Zeitraum (K-04), Varroa Windel und Puderzucker, Aufgaben mit Fälligkeit,
Löschen, Konflikte. Schema 'bienen' der Testdatenbank wird gelöscht. Ohne Datenbank: Teil 2 NICHT GELAUFEN, Rückgabe 2.
"""
import os
import pathlib
import sys
import traceback
from datetime import datetime, timedelta, timezone

WURZEL = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "server" / "plattform"))
from api import katalog  # noqa: E402
from api.anmeldung import passwort_hash  # noqa: E402
from api.stammdaten import Konflikt  # noqa: E402
from api.stockkarte import _wert_spalten  # noqa: E402

DSN = os.environ.get("BIENEN_TEST_DSN", "")
PASSWORT = "test-passwort-1234"
SCHLUESSEL = "s" * 40
TESTS, Z = [], {}
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc)


def test(name, db=False):
    def deko(fn):
        fn.testname, fn.db = name, db
        TESTS.append(fn)
        return fn
    return deko


def konflikt(fn, *a):
    try:
        fn(*a)
    except Konflikt as e:
        return str(e)
    raise AssertionError(f"kein Konflikt für {a}")


# ================================================================ Teil 1: ohne Datenbank

@test("Werte je Eingabetyp: ja/nein, Zahl, ganze Zahl, Bewertung 1–5, Liste, Datum, Text")
def _():
    m = lambda typ, optionen=None: {"eingabetyp": typ, "name": typ, "optionen": optionen}  # noqa: E731
    assert _wert_spalten(m("janein"), True) == (None, None, True)
    assert "ja oder nein" in konflikt(_wert_spalten, m("janein"), 1)
    assert _wert_spalten(m("zahl"), 2.5) == (2.5, None, None)
    assert "ganze Zahl" in konflikt(_wert_spalten, m("ganzzahl"), 2.5)
    assert "nicht negativ" in konflikt(_wert_spalten, m("ganzzahl"), -1)
    assert "Zahl erwartet" in konflikt(_wert_spalten, m("zahl"), True)
    assert _wert_spalten(m("bewertung"), 5) == (5, None, None)
    assert "1 bis 5" in konflikt(_wert_spalten, m("bewertung"), 6)
    assert _wert_spalten(m("liste", ["knapp", "reichlich"]), "knapp") == (None, "knapp", None)
    assert "unbekannte Auswahl" in konflikt(_wert_spalten, m("liste", ["knapp"]), "viel")
    assert _wert_spalten(m("datum"), "2026-10-20") == (None, "2026-10-20", None)
    assert "Datum" in konflikt(_wert_spalten, m("datum"), "20.10.2026")
    assert "keinen Wert" in konflikt(_wert_spalten, m("gruppe"), "x")
    codes = [c[0] for c in katalog.CHECKLISTE]
    assert len(codes) == len(set(codes)) and {c[5] for c in katalog.CHECKLISTE} <= {g for g, _ in katalog.CHECKLISTE_GRUPPEN}


class Keine:
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


@test("Schreiben: CSRF auch bei DELETE und PUT, Eingaben geprüft (422) ohne Datenbankzugriff")
def _():
    from fastapi.testclient import TestClient

    from api import app as app_modul
    k = {"dsn": "-", "passwort_hash": passwort_hash(PASSWORT), "sitzungsschluessel": SCHLUESSEL, "cookie_sicher": False}
    c = TestClient(app_modul.erstellen(k, verbinden=Keine(), verbinden_schreiben=Keine()))
    assert c.delete("/api/stockkarte/durchsichten/1").status_code == 401
    c.post("/api/anmelden", json={"passwort": PASSWORT})
    t = {"X-CSRF-Token": c.get("/api/sitzung").json()["csrf"]}
    assert c.delete("/api/stockkarte/durchsichten/1").status_code == 403
    assert c.put("/api/stockkarte/massnahmen/1", json={}).status_code == 403
    assert c.post("/api/stockkarte/durchsichten", json={"volk_ids": [], "zeit": "2026-10-01T10:00:00Z"}, headers=t).status_code == 422
    assert c.post("/api/stockkarte/durchsichten", json={"volk_ids": [1], "zeit": "2026-10-01T10:00:00"}, headers=t).status_code == 422
    assert c.post("/api/stockkarte/massnahmen", json={"volk_ids": [1], "art": "baden", "von": "2026-10-01T10:00:00Z"}, headers=t).status_code == 422
    assert c.post("/api/stockkarte/varroa", json={"volk_ids": [1], "methode": "windel", "von": "2026-10-01T10:00:00Z",
                                                  "bis": "2026-10-02T10:00:00Z", "milben": -1}, headers=t).status_code == 422
    assert c.post("/api/stockkarte/aufgaben", json={"faellig_am": "morgen", "text": "x"}, headers=t).status_code == 422


# ================================================================ Teil 2: mit Datenbank

def post(pfad, daten, soll=200, methode="post"):
    r = getattr(Z["c"], methode)("/api/" + pfad, json=daten, headers={"X-CSRF-Token": Z["csrf"]})
    assert r.status_code == soll, (pfad, r.status_code, r.text)
    return r.json()


def entfernen(pfad, soll=200):
    r = Z["c"].delete("/api/" + pfad, headers={"X-CSRF-Token": Z["csrf"]})
    assert r.status_code == soll, (pfad, r.status_code, r.text)
    return r.json()


def holen(pfad, **p):
    r = Z["c"].get("/api/" + pfad, params=p)
    assert r.status_code == 200, (pfad, r.status_code, r.text)
    return r.json()


def ereignisse(volk):
    return holen(f"voelker/{volk}/ereignisse", von="2026-09-01T00:00:00Z", bis="2026-12-01T00:00:00Z")


@test("Löschen nur aus Stockkarten-Tabellen (Weißliste), auch ohne Datenbank")
def _():
    from api import stockkarte as sk
    for tabelle in ("volk", "messwert", "massnahme; DROP TABLE volk"):
        try:
            sk.loeschen(None, tabelle, 1)
            raise AssertionError(f"{tabelle} nicht abgelehnt")
        except ValueError:
            pass


@test("Vorbereitung: zwei Völker am Stand, drittes aufgelöst; Standard-Checkliste, zweimal dieselbe Version", db=True)
def _():
    import psycopg
    from fastapi.testclient import TestClient

    from api import app as app_modul
    with psycopg.connect(DSN, autocommit=True) as con:
        con.execute((WURZEL / "server" / "datenbank" / "schema.sql").read_text(encoding="utf-8"))
    k = {"dsn": DSN, "passwort_hash": passwort_hash(PASSWORT), "sitzungsschluessel": SCHLUESSEL, "cookie_sicher": False}
    c = TestClient(app_modul.erstellen(k))
    c.post("/api/anmelden", json={"passwort": PASSWORT})
    Z.update(c=c, csrf=c.get("/api/sitzung").json()["csrf"])
    assert holen("stockkarte/checklisten") == []
    stand = post("verwaltung/staende", {"name": "Hauptstand"})["id"]
    for i in (1, 2, 3):
        Z[f"v{i}"] = post("verwaltung/voelker", {"name": f"Volk {i}", "zeit": T0.isoformat(), "stand_id": stand, "platz": i,
                                                 "beute": {"bezeichnung": f"Beute {i}"}})["id"]
    post(f"verwaltung/voelker/{Z['v3']}/aufloesen", {"zeit": "2026-10-10T00:00:00Z"})
    v1 = post("stockkarte/checkliste/standard", {"zeit": T0.isoformat()})["version_id"]
    assert post("stockkarte/checkliste/standard", {"zeit": T0.isoformat()})["version_id"] == v1
    liste = holen("stockkarte/checklisten")
    assert len(liste) == 1 and liste[0]["version"] == 1 and len(liste[0]["merkmale"]) == len(katalog.CHECKLISTE)
    assert liste[0]["merkmale"][0]["gruppe"] == "Königin und Brut"
    Z["version"] = v1


@test("Durchsicht für zwei Völker mit Werten; Werte in Reihenfolge der Checkliste im Cockpit", db=True)
def _():
    werte = {"koenigin_gesehen": True, "brutwaben": 6, "sanftmut": 4, "futtervorrat": "ausreichend", "krankheitszeichen": "",
             "schwarmstimmung": False}
    r = post("stockkarte/durchsichten", {"volk_ids": [Z["v1"], Z["v2"]], "zeit": "2026-10-05T14:30:00+02:00",
                                         "checkliste_version_id": Z["version"], "notiz": "ruhig", "werte": werte})
    assert len(r["ids"]) == 2
    Z["d1"] = r["ids"][0]
    d = ereignisse(Z["v1"])["durchsichten"]
    assert len(d) == 1 and d[0]["zeit"].startswith("2026-10-05T12:30") and d[0]["notiz"] == "ruhig"
    assert [w["code"] for w in d[0]["werte"]] == ["koenigin_gesehen", "brutwaben", "sanftmut", "schwarmstimmung", "futtervorrat"]
    assert d[0]["werte"][0]["wert"] is True and d[0]["werte"][1]["wert"] == 6 and d[0]["werte"][4]["wert"] == "ausreichend"
    assert len(ereignisse(Z["v2"])["durchsichten"]) == 1


@test("Durchsicht: falscher Wert, fremdes Merkmal, aufgelöstes Volk → 409 ohne Teilanlage", db=True)
def _():
    p = {"volk_ids": [Z["v1"]], "zeit": "2026-10-06T10:00:00Z", "checkliste_version_id": Z["version"]}
    assert "1 bis 5" in post("stockkarte/durchsichten", {**p, "werte": {"sanftmut": 9}}, 409)["detail"]
    assert "gehört nicht" in post("stockkarte/durchsichten", {**p, "werte": {"kaffee": 1}}, 409)["detail"]
    r = post("stockkarte/durchsichten", {**p, "volk_ids": [Z["v1"], Z["v3"]], "zeit": "2026-10-12T10:00:00Z"}, 409)
    assert "aufgelöst" in r["detail"]
    assert len(ereignisse(Z["v1"])["durchsichten"]) == 1, "Volk 1 darf keinen Teileintrag bekommen"
    assert "noch nicht entstanden" in post("stockkarte/durchsichten", {**p, "zeit": "2026-09-01T10:00:00Z"}, 409)["detail"]


@test("Korrektur: übernommene Uhrzeit (nur_datum) wird mit neuer Zeit exakt (K-03); Werte ersetzt", db=True)
def _():
    d = post("stockkarte/durchsichten", {"volk_ids": [Z["v2"]], "zeit": "2026-10-07T10:00:00Z", "zeitgenauigkeit": "nur_datum",
                                         "checkliste_version_id": Z["version"]})["ids"][0]
    r = post(f"stockkarte/durchsichten/{d}", {"zeit": "2026-10-07T14:00:00Z", "werte": {"brutwaben": 5}}, methode="put")
    assert r["zeitgenauigkeit"] == "exakt"
    e = holen(f"stockkarte/eintrag/durchsicht/{d}")
    assert e["zeit"].startswith("2026-10-07T14:00") and [w["code"] for w in e["werte"]] == ["brutwaben"]
    r = post(f"stockkarte/durchsichten/{d}", {"zeit": "2026-10-07T14:00:00Z", "zeitgenauigkeit": "geschaetzt"}, methode="put")
    assert r["zeitgenauigkeit"] == "geschaetzt"
    Z["d2"] = d


@test("Maßnahme: Zeitpunkt als 1-Minuten-Zeitraum, Behandlung als Band (K-04), Ende vor Beginn → 409", db=True)
def _():
    ids = post("stockkarte/massnahmen", {"volk_ids": [Z["v1"], Z["v2"]], "art": "behandlung", "von": "2026-10-01T08:00:00Z",
                                         "bis": "2026-10-11T08:00:00Z", "mittel": "Ameisensäure 60 %", "menge": 60, "einheit": "ml"})["ids"]
    f = post("stockkarte/massnahmen", {"volk_ids": [Z["v1"]], "art": "fuetterung", "von": "2026-10-03T15:00:00Z", "menge": 10,
                                       "einheit": "kg", "durchsicht_id": Z["d1"]})["ids"][0]
    m = {x["art"]: x for x in ereignisse(Z["v1"])["massnahmen"]}
    assert (m["behandlung"]["von"][:16], m["behandlung"]["bis"][:16]) == ("2026-10-01T08:00", "2026-10-11T08:00")
    assert m["fuetterung"]["bis"][:16] == "2026-10-03T15:01"
    assert "nach dem Beginn" in post("stockkarte/massnahmen", {"volk_ids": [Z["v1"]], "art": "ernte", "von": "2026-10-05T10:00:00Z",
                                                               "bis": "2026-10-05T09:00:00Z"}, 409)["detail"]
    post(f"stockkarte/massnahmen/{ids[1]}", {"art": "behandlung", "von": "2026-10-01T08:00:00Z", "bis": "2026-10-12T08:00:00Z",
                                             "mittel": "Ameisensäure 60 %"}, methode="put")
    assert ereignisse(Z["v2"])["massnahmen"][0]["bis"][:10] == "2026-10-12"
    Z["fuetterung"] = f


@test("Varroa: Windel mit Milben pro Tag, Puderzucker ohne; Ende vor Beginn → 409", db=True)
def _():
    post("stockkarte/varroa", {"volk_ids": [Z["v1"]], "methode": "windel", "von": "2026-10-12T10:00:00Z",
                               "bis": "2026-10-15T10:00:00Z", "milben": 45})
    post("stockkarte/varroa", {"volk_ids": [Z["v1"]], "methode": "puderzucker", "von": "2026-10-16T10:00:00Z",
                               "bis": "2026-10-16T10:20:00Z", "milben": 3, "anmerkung": "50 g Bienen"})
    v = {x["methode"]: x for x in ereignisse(Z["v1"])["varroa"]}
    assert float(v["windel"]["milben_pro_tag"]) == 15.0 and v["windel"]["berechnung"] == "varroa_pro_tag@1"
    assert v["puderzucker"]["milben_pro_tag"] is None and v["puderzucker"]["milben"] == 3
    assert "nach dem Beginn" in post("stockkarte/varroa", {"volk_ids": [Z["v1"]], "methode": "windel", "von": "2026-10-15T10:00:00Z",
                                                           "bis": "2026-10-12T10:00:00Z", "milben": 1}, 409)["detail"]
    Z["puder"] = v["puderzucker"]["id"]


@test("Ändern: Varroa (Milben, Ende), Maßnahme (Ende eines Bands); Eintrag zum Bearbeiten liest die neuen Werte", db=True)
def _():
    w = [v for v in ereignisse(Z["v1"])["varroa"] if v["methode"] == "windel"][0]
    post(f"stockkarte/varroa/{w['id']}", {"methode": "windel", "von": "2026-10-12T10:00:00Z", "bis": "2026-10-16T10:00:00Z",
                                           "milben": 60}, methode="put")
    n = holen(f"stockkarte/eintrag/varroa/{w['id']}")
    assert n["milben"] == 60 and n["bis"].startswith("2026-10-16T10:00"), n
    w2 = [v for v in ereignisse(Z["v1"])["varroa"] if v["id"] == w["id"]][0]
    assert float(w2["milben_pro_tag"]) == 15.0, w2               # 60 Milben in 4 Tagen
    b = [m for m in ereignisse(Z["v1"])["massnahmen"] if m["art"] == "behandlung"][0]
    post(f"stockkarte/massnahmen/{b['id']}", {"art": "behandlung", "von": b["von"], "bis": "2026-10-30T08:00:00Z",
                                                "mittel": "Oxalsäure"}, methode="put")
    m = holen(f"stockkarte/eintrag/massnahme/{b['id']}")
    assert m["bis"].startswith("2026-10-30T08:00") and m["mittel"] == "Oxalsäure", m
    post(f"stockkarte/varroa/{w['id']}", {"methode": "windel", "von": "2026-10-16T10:00:00Z", "bis": "2026-10-12T10:00:00Z",
                                           "milben": 1}, 409, methode="put")


@test("Aufgaben: fällig in der Übersicht, erledigt, Stand-Aufgabe; Völker und Stand zugleich → 409", db=True)
def _():
    a = post("stockkarte/aufgaben", {"faellig_am": "2026-10-20", "text": "Windel auszählen", "volk_ids": [Z["v1"]]})["ids"][0]
    post("stockkarte/aufgaben", {"faellig_am": "2026-11-20", "text": "Gitter einlegen", "volk_ids": [Z["v1"]]})
    s = holen("staende", zeit="2026-10-21T08:00:00Z")[0]
    v1 = [v for v in s["voelker"] if v["id"] == Z["v1"]][0]
    assert v1["aufgaben_faellig"] == 1 and v1["letzte_durchsicht"].startswith("2026-10-05T12:30"), v1
    assert len(holen("stockkarte/aufgaben")) == 2
    post(f"stockkarte/aufgaben/{a}/erledigt", {"zeit": "2026-10-21T09:00:00Z"})
    assert [x["text"] for x in holen("stockkarte/aufgaben")] == ["Gitter einlegen"]
    assert len(holen("stockkarte/aufgaben", alle="true")) == 2
    assert "Völker oder" in post("stockkarte/aufgaben", {"faellig_am": "2026-10-20", "text": "x", "volk_ids": [Z["v1"]], "stand_id": 1}, 409)["detail"]
    post("stockkarte/aufgaben", {"faellig_am": "2026-10-25", "text": "Mäusegitter", "stand_id": 1})
    assert "Mäusegitter" in {x["text"] for x in holen("stockkarte/aufgaben")}
    assert [x["text"] for x in ereignisse(Z["v1"])["aufgaben"]] == ["Gitter einlegen", "Windel auszählen"]


@test("Löschen: Durchsicht mit verknüpfter Maßnahme (Maßnahme bleibt), Varroa; unbekannt → 404", db=True)
def _():
    entfernen(f"stockkarte/durchsichten/{Z['d1']}")
    e = ereignisse(Z["v1"])
    assert e["durchsichten"] == [] and "fuetterung" in {m["art"] for m in e["massnahmen"]}
    entfernen(f"stockkarte/varroa/{Z['puder']}")
    assert {v["methode"] for v in ereignisse(Z["v1"])["varroa"]} == {"windel"}
    entfernen(f"stockkarte/varroa/{Z['puder']}", 404)
    entfernen("stockkarte/durchsichten/99999", 404)


@test("Checkliste geändert: neue Version, alte Durchsichten behalten ihre Version (K-10)", db=True)
def _():
    import psycopg
    alt = Z["version"]
    katalog.CHECKLISTE.append(("bauerneuerung", "Bauerneuerung", "janein", None, None, "g_volk"))
    try:
        neu = post("stockkarte/checkliste/standard", {"zeit": "2027-03-01T00:00:00Z"})["version_id"]
    finally:
        katalog.CHECKLISTE.pop()
    assert neu != alt
    liste = holen("stockkarte/checklisten")[0]
    assert liste["version"] == 2 and liste["merkmale"][-1]["code"] == "bauerneuerung"
    with psycopg.connect(DSN) as con:
        v = con.execute("SELECT checkliste_version_id FROM bienen.durchsicht WHERE id = %s", (Z["d2"],)).fetchone()[0]
    assert v == alt


# ================================================================ Ablauf

def melden(name, fehler):
    print(f"FEHLER     {name}: {fehler}")
    if os.environ.get("GITHUB_ACTIONS"):
        text = f"{name}: {fehler}".replace("%", "%25").replace("\r", "").replace("\n", "%0A")[:900]
        print(f"::error title=test_stockkarte::{text}")


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
