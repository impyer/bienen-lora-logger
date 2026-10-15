# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests für server/datenbank/schema.sql gegen PostgreSQL (ab 16).

Aufruf:
    BIENEN_TEST_DSN="host=/tmp/pg port=5433 user=bienen dbname=t" python3 tests/datenbank/test_schema.py

Jeder Test läuft in einer eigenen Transaktion, die am Ende zurückgerollt wird.
Zeitangaben immer mit Zeitzone schreiben: Ohne Angabe gilt die Zeitzone der Sitzung
(Testinstanz: Europe/Berlin), und ein Wechsel um Mitternacht läge zwei Stunden daneben.
Benötigt: psycopg 3 (pip install "psycopg[binary]") und die Erweiterung btree_gist.
Prüfart: T1 (Datenbanktest auf Testinstanz), keine Produktivdaten.
"""
import os
import sys
import pathlib
import psycopg
from psycopg import errors

DSN = os.environ.get("BIENEN_TEST_DSN", "host=/tmp/pg port=5433 user=bienen dbname=t")
SCHEMA = pathlib.Path(__file__).resolve().parents[2] / "server" / "datenbank" / "schema.sql"

ERGEBNISSE = []


def test(name):
    def deko(fn):
        fn.testname = name
        return fn
    return deko


def abgelehnt(cur, sql, params=None):
    """True, wenn PostgreSQL die Anweisung mit einer Integritätsverletzung ablehnt."""
    cur.execute("SAVEPOINT sp")
    try:
        cur.execute(sql, params)
    except (errors.IntegrityError, errors.CheckViolation, errors.ExclusionViolation,
            errors.UniqueViolation, errors.ForeignKeyViolation, errors.NotNullViolation) as e:
        cur.execute("ROLLBACK TO SAVEPOINT sp")
        return True
    cur.execute("RELEASE SAVEPOINT sp")
    return False


def eins(cur, sql, params=None):
    cur.execute(sql, params)
    return cur.fetchone()[0]


# ---------------------------------------------------------------- Hilfen
def stand(cur, name="Hauptstand am Haus"):
    return eins(cur, "INSERT INTO stand(name, ort_oeffentlich) VALUES (%s,'Radeberg') RETURNING id", (name,))


def volk(cur, name):
    return eins(cur, "INSERT INTO volk(name) VALUES (%s) RETURNING id", (name,))


def beute(cur, name, typ="Segeberger 1,5"):
    return eins(cur, "INSERT INTO beute(bezeichnung, beutentyp) VALUES (%s,%s) RETURNING id", (name, typ))


def geraet(cur, name, art="stockwaage"):
    return eins(cur, "INSERT INTO geraet(name, art) VALUES (%s,%s) RETURNING id", (name, art))


def messgroessen(cur):
    cur.execute("""INSERT INTO messgroesse(code,name,einheit,semantik,verdichtung,achse,darstellung) VALUES
      ('gewicht','Gewicht','kg','momentan','mittel','gewicht','linie'),
      ('temperatur','Temperatur','°C','momentan','mittel','temperatur','linie'),
      ('feuchte','Relative Feuchte','%','momentan','mittel','feuchte','linie'),
      ('regen_summe','Niederschlag','mm','unbekannte_summe','keine','regen','balken')""")


def kanal(cur, geraet_id, feld, groesse, von, bis=None, messstelle=None):
    return eins(cur, """INSERT INTO kanal(geraet_id, quellfeld, messgroesse_code, messstelle_id, gueltig)
                       VALUES (%s,%s,%s,%s,tstzrange(%s,%s,'[)')) RETURNING id""",
                (geraet_id, feld, groesse, messstelle, von, bis))


def mw(cur, kanal_id, zeit, wert):
    cur.execute("INSERT INTO messwert(kanal_id, zeit, wert, zeitqualitaet) VALUES (%s,%s,%s,'geraet')",
                (kanal_id, zeit, wert))


# ---------------------------------------------------------------- Tests
@test("ER-01 Ableger: neue ID, Herkunft dokumentiert, Muttervolk bleibt")
def t_ableger(cur):
    a, b = volk(cur, "Volk 1"), volk(cur, "Ableger 14")
    e = eins(cur, "INSERT INTO volk_ereignis(art, zeit) VALUES ('ableger','2026-05-31 10:00+02') RETURNING id")
    cur.execute("INSERT INTO volk_ereignis_teil VALUES (%s,%s,'bleibt'),(%s,%s,'ergebnis')", (e, a, e, b))
    herkunft = eins(cur, """SELECT q.volk_id FROM volk_ereignis_teil q JOIN volk_ereignis_teil r USING (ereignis_id)
                            WHERE r.volk_id=%s AND r.rolle='ergebnis' AND q.rolle IN ('bleibt','quelle')""", (b,))
    assert a != b and herkunft == a


@test("Beute = Volk: 1:1 in beide Richtungen, nacheinander erlaubt")
def t_belegung(cur):
    v1, v2 = volk(cur, "Volk 1"), volk(cur, "Volk 2")
    b1, b2 = beute(cur, "B1"), beute(cur, "B2")
    cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-01-01,2026-06-01)')", (v1, b1))
    assert abgelehnt(cur, "INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-03-01,)')", (v2, b1)), \
        "zweites Volk in derselben Beute"
    assert abgelehnt(cur, "INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-03-01,)')", (v1, b2)), \
        "dasselbe Volk in zwei Beuten"
    assert not abgelehnt(cur, "INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-06-01,)')", (v2, b1)), \
        "Wiederbelegung nach Ende muss gehen"


@test("ER-03 Höchstens ein Stockmesssystem je Volk; Wechsel nacheinander erlaubt")
def t_ein_system(cur):
    v = volk(cur, "Volk 8")
    l08, base = geraet(cur, "L08"), geraet(cur, "BEEP-Base-1", "beep_base")
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2026-11-01,2027-05-01)')", (l08, v))
    assert abgelehnt(cur, "INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2027-04-01,)')", (base, v))
    assert not abgelehnt(cur, "INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2027-05-01,)')", (base, v))


@test("Gerät nicht gleichzeitig an zwei Zielen; genau ein Ziel (Volk oder Stand)")
def t_geraet_ziel(cur):
    v1, v2, s = volk(cur, "Volk 1"), volk(cur, "Volk 2"), stand(cur)
    g = geraet(cur, "L01")
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2026-11-01,)')", (g, v1))
    assert abgelehnt(cur, "INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2026-12-01,)')", (g, v2))
    assert abgelehnt(cur, "INSERT INTO geraet_zuordnung(geraet_id,volk_id,stand_id,gueltig) VALUES (%s,%s,%s,'[2028-01-01,)')", (g, v2, s))


@test("HB-01 Waage am Volk: Umsetzen in neue Beute ändert die Zuordnung der Messwerte nicht")
def t_umsetzen(cur):
    messgroessen(cur)
    s1, s2 = stand(cur), stand(cur, "Außenstand")
    v = volk(cur, "Volk 9")
    b1, b2 = beute(cur, "Ableger-Box", "Miniplus"), beute(cur, "City-Box", "Einraumbeute DNM")
    cur.execute("INSERT INTO aufstellung(beute_id,stand_id,gueltig) VALUES (%s,%s,'[2026-01-01,)'),(%s,%s,'[2026-01-01,)')", (b1, s1, b2, s2))
    cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-05-01,2026-07-01 10:00+02)'),(%s,%s,'[2026-07-01 10:00+02,)')", (v, b1, v, b2))
    g = geraet(cur, "L09")
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2026-05-01,)')", (g, v))
    k = kanal(cur, g, "Gewicht", "gewicht", "2026-05-01")
    mw(cur, k, "2026-06-30 12:00+02", 18.0)
    mw(cur, k, "2026-07-02 12:00+02", 31.5)
    cur.execute("SELECT volk_id FROM messwert_bezug ORDER BY zeit")
    assert [r[0] for r in cur.fetchall()] == [v, v]
    assert eins(cur, "SELECT stand_von_volk(%s,'2026-06-30 12:00+02')", (v,)) == s1
    assert eins(cur, "SELECT stand_von_volk(%s,'2026-07-02 12:00+02')", (v,)) == s2


@test("Zeitraum halb offen: Wert genau am Wechselzeitpunkt gehört zum neuen Volk")
def t_grenze(cur):
    messgroessen(cur)
    v1, v2 = volk(cur, "Volk 1"), volk(cur, "Volk 21")
    g = geraet(cur, "L01")
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2026-05-01 00:00+00,2026-05-16 00:00+00)'),(%s,%s,'[2026-05-16 00:00+00,)')", (g, v1, g, v2))
    k = kanal(cur, g, "Gewicht", "gewicht", "2026-05-01")
    mw(cur, k, "2026-05-15 23:59:59+00", 40)
    mw(cur, k, "2026-05-16 00:00:00+00", 41)
    cur.execute("SELECT volk_id FROM messwert_bezug ORDER BY zeit")
    assert [r[0] for r in cur.fetchall()] == [v1, v2]


@test("ER-04 Wetterstation am Stand, für alle Völker des Standes nutzbar")
def t_wetter(cur):
    messgroessen(cur)
    s = stand(cur)
    g = geraet(cur, "wetterstation-01", "wetter")
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,stand_id,gueltig) VALUES (%s,%s,'[2026-10-08,)')", (g, s))
    k = kanal(cur, g, "t", "temperatur", "2026-10-08")
    mw(cur, k, "2026-10-15 09:00+02", 11.4)
    row = cur.execute("SELECT volk_id, stand_id FROM messwert_bezug").fetchone()
    assert row == (None, s)


@test("ER-05/K-05 Drei Bodensonden: drei Messstellen, getrennte Reihen, ohne Codeänderung")
def t_boden(cur):
    messgroessen(cur)
    s = stand(cur)
    g = geraet(cur, "lsn50v2-d23", "boden")
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,stand_id,gueltig) VALUES (%s,%s,'[2026-10-14,)')", (g, s))
    ids = []
    for i, (tiefe, farbe) in enumerate(((5, "weiß"), (20, "rot"), (50, "schwarz")), start=1):  # bestätigt 15.10.2026
        ms = eins(cur, "INSERT INTO messstelle(stand_id,zone,tiefe_cm,bezeichnung) VALUES (%s,'boden',%s,%s) RETURNING id",
                  (s, tiefe, f"Sonde {farbe}"))
        ids.append(kanal(cur, g, f"Temp{i}", "temperatur", "2026-10-14", messstelle=ms))
    for k, w in zip(ids, (11.9, 12.6, 13.1)):
        mw(cur, k, "2026-10-15 09:00+02", w)
    assert eins(cur, "SELECT count(DISTINCT messstelle_id) FROM messwert_bezug") == 3
    assert abgelehnt(cur, "INSERT INTO messstelle(stand_id,zone) VALUES (%s,'boden')", (s,)), "Boden ohne Tiefe/Bezeichnung"


@test("ER-07 Quellfeld wechselt seine Deutung; Überlappung desselben Feldes abgelehnt")
def t_kanal_deutung(cur):
    messgroessen(cur)
    g = geraet(cur, "beelogger1")
    kanal(cur, g, "FeuchteIn", "feuchte", "2026-01-01", "2026-06-01")
    kanal(cur, g, "FeuchteIn", "temperatur", "2026-06-01")
    assert abgelehnt(cur, """INSERT INTO kanal(geraet_id,quellfeld,messgroesse_code,gueltig)
                             VALUES (%s,'FeuchteIn','feuchte','[2026-05-01,2026-07-01)')""", (g,))


@test("ER-12 Doppelte Nachricht erzeugt keinen doppelten Messwert")
def t_idempotent(cur):
    messgroessen(cur)
    g = geraet(cur, "L01")
    k = kanal(cur, g, "Gewicht", "gewicht", "2026-01-01")
    for _ in range(2):
        cur.execute("""INSERT INTO rohnachricht(id,geraet_id,empfangen,datei,zeile,sha256)
                       VALUES ('L01-2-1234-ab-2026-10-15T07:00:05Z',%s,'2026-10-15 07:00:05+00','lora_log/2026-10.jsonl',17,'x')
                       ON CONFLICT DO NOTHING""", (g,))
        cur.execute("""INSERT INTO messwert(kanal_id,zeit,wert,zeitqualitaet,roh_id)
                       VALUES (%s,'2026-10-15 07:00+00',38.4,'geraet','L01-2-1234-ab-2026-10-15T07:00:05Z')
                       ON CONFLICT DO NOTHING""", (k,))
    assert eins(cur, "SELECT count(*) FROM messwert") == 1
    assert eins(cur, "SELECT count(*) FROM rohnachricht") == 1


@test("K-01 BEEP-Hive 87155 wird Volk 8; Kennung nur einmal vergeben")
def t_extern(cur):
    v8 = volk(cur, "Volk 8")
    cur.execute("INSERT INTO extern_ref VALUES ('beep','hive','87155','volk',%s)", (v8,))
    assert abgelehnt(cur, "INSERT INTO extern_ref VALUES ('beep','hive','87155','volk',%s)", (volk(cur, "X"),))
    assert eins(cur, "SELECT intern_id FROM extern_ref WHERE system='beep' AND typ='hive' AND extern_id='87155'") == v8


@test("K-02 Vereinigung: Volk 3 aufgelöst, Herkunft und Ende der Belegung")
def t_vereinigung(cur):
    v3, v5 = volk(cur, "Volk 3"), volk(cur, "Volk 5")
    b3 = beute(cur, "Beute Volk 3")
    cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-03-01,2026-08-20)')", (v3, b3))
    cur.execute("UPDATE volk SET aufgeloest_am='2026-08-20' WHERE id=%s", (v3,))
    e = eins(cur, "INSERT INTO volk_ereignis(art,zeit) VALUES ('vereinigung','2026-08-20') RETURNING id")
    cur.execute("INSERT INTO volk_ereignis_teil VALUES (%s,%s,'quelle'),(%s,%s,'bleibt')", (e, v3, e, v5))
    assert eins(cur, "SELECT count(*) FROM belegung WHERE volk_id=%s AND gueltig @> '2026-09-01'::timestamptz", (v3,)) == 0


@test("K-04 Behandlung als Zeitraum; Zeitraum-Regeln der Domain")
def t_massnahme(cur):
    v8 = volk(cur, "Volk 8")
    cur.execute("""INSERT INTO massnahme(volk_id,art,zeitraum,menge,einheit,mittel,notiz,quelle)
                   VALUES (%s,'behandlung','[2026-10-01 12:00+02,2026-10-11 12:00+02)',300,'ml','Ameisensäure','Docht 3','beep_import')""", (v8,))
    tage = eins(cur, "SELECT extract(day FROM upper(zeitraum)-lower(zeitraum)) FROM massnahme")
    assert tage == 10
    for falsch in ("'(2026-10-01,2026-10-02]'", "'empty'", "'(,2026-10-02)'"):
        assert abgelehnt(cur, f"INSERT INTO massnahme(volk_id,art,zeitraum) VALUES (%s,'behandlung',{falsch})", (v8,)), falsch


@test("Durchsichtswert: genau ein Wert je Merkmal")
def t_durchsicht_wert(cur):
    v = volk(cur, "Volk 1")
    m = eins(cur, "INSERT INTO merkmal(code,name,eingabetyp) VALUES ('brutwaben','Brutwaben','ganzzahl') RETURNING id")
    d = eins(cur, "INSERT INTO durchsicht(volk_id,zeit,quelle) VALUES (%s,'2026-10-07 12:00+02','beep_import') RETURNING id", (v,))
    assert not abgelehnt(cur, "INSERT INTO durchsicht_wert(durchsicht_id,merkmal_id,wert_zahl) VALUES (%s,%s,6)", (d, m))
    m2 = eins(cur, "INSERT INTO merkmal(code,name,eingabetyp) VALUES ('notiz_x','X','text') RETURNING id")
    assert abgelehnt(cur, "INSERT INTO durchsicht_wert(durchsicht_id,merkmal_id) VALUES (%s,%s)", (d, m2))
    assert abgelehnt(cur, "INSERT INTO durchsicht_wert(durchsicht_id,merkmal_id,wert_zahl,wert_text) VALUES (%s,%s,1,'a')", (d, m2))


@test("K-10 Checklisten-Versionen: alte Durchsicht behält Version 1")
def t_checkliste(cur):
    v = volk(cur, "Volk 1")
    c = eins(cur, "INSERT INTO checkliste(name) VALUES ('Herbst/Winter') RETURNING id")
    v1 = eins(cur, "INSERT INTO checkliste_version(checkliste_id,version,gueltig_ab) VALUES (%s,1,'2026-09-01') RETURNING id", (c,))
    eins(cur, "INSERT INTO checkliste_version(checkliste_id,version,gueltig_ab) VALUES (%s,2,'2027-09-01') RETURNING id", (c,))
    assert abgelehnt(cur, "INSERT INTO checkliste_version(checkliste_id,version,gueltig_ab) VALUES (%s,2,'2027-10-01')", (c,))
    cur.execute("INSERT INTO durchsicht(volk_id,zeit,checkliste_version_id) VALUES (%s,'2026-10-07 12:00+02',%s)", (v, v1))
    assert eins(cur, "SELECT cv.version FROM durchsicht d JOIN checkliste_version cv ON cv.id=d.checkliste_version_id") == 1


@test("Königin: höchstens eine je Volk zur selben Zeit")
def t_koenigin(cur):
    v = volk(cur, "Volk 2")
    k1 = eins(cur, "INSERT INTO koenigin(jahrgang,farbe) VALUES (2026,'weiß') RETURNING id")
    k2 = eins(cur, "INSERT INTO koenigin(jahrgang,farbe) VALUES (2026,'weiß') RETURNING id")
    cur.execute("INSERT INTO koenigin_volk VALUES (%s,%s,'[2026-05-10,2026-06-02)','zugesetzt')", (k1, v))
    assert abgelehnt(cur, "INSERT INTO koenigin_volk VALUES (%s,%s,'[2026-06-01,)','Nachschaffung')", (k2, v))
    assert not abgelehnt(cur, "INSERT INTO koenigin_volk VALUES (%s,%s,'[2026-06-02,)','Nachschaffung')", (k2, v))


@test("Tagesbilanz über die Zeitumstellung (25.10.2026) und Eingriffsmarke (L8)")
def t_tagesbilanz(cur):
    messgroessen(cur)
    v = volk(cur, "Volk 8")
    g = geraet(cur, "L08")
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2026-10-20,)')", (g, v))
    k = kanal(cur, g, "Gewicht", "gewicht", "2026-10-20")
    # 15-min-Werte in UTC; Nacht 24.10. konstant 40,0 kg, Nacht 25.10. (25 h, Umstellung) konstant 39,8 kg
    cur.execute("""INSERT INTO messwert(kanal_id,zeit,wert,zeitqualitaet)
                   SELECT %s, t, CASE WHEN t < '2026-10-24 12:00+02' THEN 40.0 ELSE 39.8 END, 'geraet'
                   FROM generate_series('2026-10-23 22:00+00'::timestamptz,'2026-10-25 06:00+00','15 min') t""", (k,))
    cur.execute("SELECT tag, referenz_kg, werte FROM gewicht_tagesreferenz ORDER BY tag")
    ref = {str(t): (round(r, 2), n) for t, r, n in cur.fetchall()}
    assert ref["2026-10-24"] == (40.0, 16), ref   # 00–04 MESZ = 4 h = 16 Werte
    assert ref["2026-10-25"] == (39.8, 20), ref   # 00–04 bei Umstellung = 5 h = 20 Werte
    bil = cur.execute("SELECT round(bilanz_kg::numeric,2), mit_eingriff FROM gewicht_tagesbilanz WHERE tag='2026-10-25'").fetchone()
    assert (float(bil[0]), bil[1]) == (-0.2, False), bil
    cur.execute("INSERT INTO massnahme(volk_id,art,zeitraum) VALUES (%s,'tarieren','[2026-10-24 15:00+02,2026-10-24 15:05+02)')", (v,))
    assert eins(cur, "SELECT mit_eingriff FROM gewicht_tagesbilanz WHERE tag='2026-10-25'") is True


@test("Milbenfall pro Tag aus Windelzeitraum")
def t_varroa(cur):
    v = volk(cur, "Volk 8")
    cur.execute("INSERT INTO varroa_messung(volk_id,zeitraum,methode,milben) VALUES (%s,'[2026-10-10 12:00+02,2026-10-13 12:00+02)','windel',201)", (v,))
    assert float(eins(cur, "SELECT milben_pro_tag FROM varroa_pro_tag")) == 67.0


@test("K-06 Quellfeld ohne Kanal wird vermerkt, nicht als Messwert gespeichert")
def t_unbekannt(cur):
    g = geraet(cur, "L01")
    sql = """INSERT INTO quellfeld_ohne_kanal(geraet_id,quellfeld,zuerst,zuletzt) VALUES (%s,'FFT_Baender_dB',%s,%s)
             ON CONFLICT (geraet_id,quellfeld) DO UPDATE SET zuletzt=EXCLUDED.zuletzt, anzahl=quellfeld_ohne_kanal.anzahl+1"""
    cur.execute(sql, (g, "2026-10-15 07:00+00", "2026-10-15 07:00+00"))
    cur.execute(sql, (g, "2026-10-15 07:15+00", "2026-10-15 07:15+00"))
    assert cur.execute("SELECT anzahl FROM quellfeld_ohne_kanal").fetchone()[0] == 2
    assert eins(cur, "SELECT count(*) FROM messwert") == 0


@test("HB-02/HB-03 Beute wird leer und neu besetzt: keine Vermischung der Völker")
def t_hb02_03(cur):
    messgroessen(cur)
    v1, v2 = volk(cur, "Volk 11"), volk(cur, "Volk 22")
    b = beute(cur, "B11")
    cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-04-01 00:00+00,2026-08-20 00:00+00)'),(%s,%s,'[2026-09-01 00:00+00,)')", (v1, b, v2, b))
    g = geraet(cur, "L05")
    cur.execute("""INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES
                   (%s,%s,'[2026-04-01 00:00+00,2026-08-20 00:00+00)'),(%s,%s,'[2026-09-01 00:00+00,)')""", (g, v1, g, v2))
    k = kanal(cur, g, "Gewicht", "gewicht", "2026-04-01 00:00+00")
    mw(cur, k, "2026-08-10 00:00+00", 45.0)   # Volk 11
    mw(cur, k, "2026-08-25 00:00+00", 12.0)   # leere Beute
    mw(cur, k, "2026-09-05 00:00+00", 20.0)   # Volk 22
    cur.execute("SELECT volk_id FROM messwert_bezug ORDER BY zeit")
    assert [r[0] for r in cur.fetchall()] == [v1, None, v2]


@test("HB-04 Beute wechselt den Stand: Umweltbezug folgt dem Stand zum Zeitpunkt")
def t_hb04(cur):
    s1, s2 = stand(cur), stand(cur, "Wanderstand Raps")
    v = volk(cur, "Volk 6")
    b = beute(cur, "B6")
    cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-01-01 00:00+00,)')", (v, b))
    cur.execute("""INSERT INTO aufstellung(beute_id,stand_id,gueltig) VALUES
                   (%s,%s,'[2026-01-01 00:00+00,2026-04-20 00:00+00)'),(%s,%s,'[2026-04-20 00:00+00,2026-05-20 00:00+00)'),
                   (%s,%s,'[2026-05-20 00:00+00,)')""", (b, s1, b, s2, b, s1))
    assert [eins(cur, "SELECT stand_von_volk(%s,%s)", (v, t)) for t in
            ("2026-04-01 00:00+00", "2026-05-01 00:00+00", "2026-06-01 00:00+00")] == [s1, s2, s1]


@test("HB-09 Volk aufgelöst, Waagenzuordnung vergessen: Prüfsicht meldet es")
def t_hb09(cur):
    v = volk(cur, "Volk 3")
    b = beute(cur, "B3")
    cur.execute("INSERT INTO belegung(volk_id,beute_id,gueltig) VALUES (%s,%s,'[2026-03-01 00:00+00,2026-08-20 00:00+00)')", (v, b))
    g = geraet(cur, "L03")
    cur.execute("INSERT INTO geraet_zuordnung(geraet_id,volk_id,gueltig) VALUES (%s,%s,'[2026-03-01 00:00+00,)')", (g, v))
    assert eins(cur, "SELECT count(*) FROM pruefung_geraet_zuordnung") == 0
    cur.execute("UPDATE volk SET aufgeloest_am='2026-08-20 00:00+00' WHERE id=%s", (v,))
    assert eins(cur, "SELECT befund FROM pruefung_geraet_zuordnung") == "volk_aufgeloest"


@test("Zeitgenauigkeit: neue Einträge exakt, Altdaten als nur_datum kennzeichenbar")
def t_zeitgenau(cur):
    v = volk(cur, "Volk 8")
    cur.execute("INSERT INTO durchsicht(volk_id,zeit) VALUES (%s,'2026-11-02 14:35+01')", (v,))
    cur.execute("INSERT INTO durchsicht(volk_id,zeit,quelle,zeitgenauigkeit) VALUES (%s,'2026-10-07 12:00+02','beep_import','nur_datum')", (v,))
    cur.execute("SELECT quelle, zeitgenauigkeit FROM durchsicht ORDER BY zeit")
    assert cur.fetchall() == [("beep_import", "nur_datum"), ("eigen", "exakt")]
    assert abgelehnt(cur, "INSERT INTO durchsicht(volk_id,zeit,zeitgenauigkeit) VALUES (%s,now(),'ungefaehr')", (v,))


@test("Provenienz: abgeleitete Werte tragen ihre Berechnungsversion")
def t_berechnung(cur):
    v = volk(cur, "Volk 8")
    cur.execute("INSERT INTO varroa_messung(volk_id,zeitraum,methode,milben) VALUES (%s,'[2026-10-12 12:00+02,2026-10-13 12:00+02)','windel',67)", (v,))
    code = eins(cur, "SELECT berechnung FROM varroa_pro_tag")
    name, ver = code.split("@")
    assert eins(cur, "SELECT count(*) FROM berechnung WHERE code=%s AND version=%s", (name, int(ver))) == 1


def main():
    with psycopg.connect(DSN, autocommit=True) as con:
        con.execute(SCHEMA.read_text(encoding="utf-8"))
    tests = [f for f in globals().values() if callable(f) and hasattr(f, "testname")]
    fehler = 0
    with psycopg.connect(DSN) as con:
        for t in tests:
            with con.cursor() as cur:
                cur.execute("SET search_path = bienen, public")
                try:
                    t(cur)
                    print(f"bestanden  {t.testname}")
                except Exception as e:  # noqa: BLE001
                    fehler += 1
                    print(f"FEHLER     {t.testname}: {type(e).__name__}: {e}")
                finally:
                    con.rollback()
    print(f"\n{len(tests) - fehler} von {len(tests)} bestanden")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
