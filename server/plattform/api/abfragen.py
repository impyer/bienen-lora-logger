# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Alle Datenbankabfragen der Lese-API an einer Stelle (Schema server/datenbank/schema.sql).

Jede Funktion bekommt einen Cursor mit dict_row in einer READ-ONLY-Transaktion (app.py) und liefert einfache
Python-Werte. Kennwerte (Tagesbilanz, Varroa pro Tag) kommen aus den Sichten des Schemas, nicht aus Python,
damit API, Auswertung und Wochenbericht dieselbe Berechnung zeigen (berechnung@version).
"""
from .verdichtung import aggregat, mit_luecken


def _sql():
    """psycopg.sql erst bei Bedarf laden: die Hosttests ersetzen die Abfragen und brauchen keinen Treiber."""
    from psycopg import sql
    return sql


def messgroessen(cur):
    cur.execute("""SELECT code, name, einheit, semantik, verdichtung, achse, darstellung, farbe
                   FROM messgroesse ORDER BY achse, code""")
    return cur.fetchall()


def messgroessen_codes(cur):
    cur.execute("SELECT code, verdichtung FROM messgroesse")
    return {r["code"]: r["verdichtung"] for r in cur.fetchall()}


def gibt_es(cur, tabelle, id_):
    if tabelle not in ("volk", "stand"):
        raise ValueError(tabelle)
    sql = _sql()
    cur.execute(sql.SQL("SELECT 1 FROM {} WHERE id = %s").format(sql.Identifier(tabelle)), (id_,))
    return cur.fetchone() is not None


# ---------------------------------------------------------------- Dashboard

def staende(cur, zeit):
    """Stände mit ihren Völkern zum Zeitpunkt (Aufstellung → Belegung) und Kurzwerten je Volk."""
    cur.execute("SELECT id, name, ort_oeffentlich FROM stand ORDER BY name")
    aus = {r["id"]: {**r, "voelker": []} for r in cur.fetchall()}
    cur.execute("""SELECT a.stand_id, a.platz, v.id, v.name, a.beute_id
                   FROM aufstellung a
                   JOIN belegung b ON b.beute_id = a.beute_id AND b.gueltig @> %(t)s
                   JOIN volk v ON v.id = b.volk_id
                   WHERE a.gueltig @> %(t)s
                   ORDER BY a.stand_id, a.platz NULLS LAST, v.name""", {"t": zeit})
    voelker = cur.fetchall()
    ids = [v["id"] for v in voelker]
    gewicht, bilanz, letzte = {}, {}, {}
    if ids:
        cur.execute("""SELECT DISTINCT ON (volk_id) volk_id, zeit, wert FROM messwert_bezug
                       WHERE messgroesse_code = 'gewicht' AND volk_id = ANY(%(ids)s) AND zeit <= %(t)s
                         AND qualitaet <> 'ungueltig'
                       ORDER BY volk_id, zeit DESC""", {"ids": ids, "t": zeit})
        gewicht = {r["volk_id"]: r for r in cur.fetchall()}
        cur.execute("""SELECT DISTINCT ON (volk_id) volk_id, tag, bilanz_kg, mit_eingriff, berechnung
                       FROM gewicht_tagesbilanz
                       WHERE volk_id = ANY(%(ids)s) AND tag < (%(t)s AT TIME ZONE 'Europe/Berlin')::date
                       ORDER BY volk_id, tag DESC""", {"ids": ids, "t": zeit})
        bilanz = {r["volk_id"]: r for r in cur.fetchall()}
        cur.execute("""SELECT volk_id, max(zeit) AS zeit FROM messwert_bezug
                       WHERE volk_id = ANY(%(ids)s) AND zeit <= %(t)s GROUP BY volk_id""", {"ids": ids, "t": zeit})
        letzte = {r["volk_id"]: r["zeit"] for r in cur.fetchall()}
    for v in voelker:
        g, b = gewicht.get(v["id"]), bilanz.get(v["id"])
        aus[v["stand_id"]]["voelker"].append({
            "id": v["id"], "name": v["name"], "platz": v["platz"],
            "gewicht_kg": g["wert"] if g else None, "gewicht_zeit": g["zeit"] if g else None,
            "tagesbilanz": ({"tag": b["tag"], "bilanz_kg": b["bilanz_kg"], "mit_eingriff": b["mit_eingriff"],
                             "berechnung": b["berechnung"]} if b else None),
            "letzte_messung": letzte.get(v["id"]),
        })
    return list(aus.values())


# ---------------------------------------------------------------- Volk

def volk(cur, volk_id, zeit):
    cur.execute("SELECT id, name, entstanden_am, aufgeloest_am, notiz FROM volk WHERE id = %s", (volk_id,))
    v = cur.fetchone()
    if v is None:
        return None
    p = {"v": volk_id, "t": zeit}
    cur.execute("""SELECT s.id, s.name FROM stand s WHERE s.id = stand_von_volk(%(v)s, %(t)s)""", p)
    v["stand"] = cur.fetchone()
    cur.execute("""SELECT be.id, be.bezeichnung, be.beutentyp, k.brutzargen, k.honigzargen, k.rahmen
                   FROM belegung b JOIN beute be ON be.id = b.beute_id
                   LEFT JOIN beute_konfiguration k ON k.beute_id = be.id AND k.gueltig @> %(t)s
                   WHERE b.volk_id = %(v)s AND b.gueltig @> %(t)s""", p)
    v["beute"] = cur.fetchone()
    cur.execute("""SELECT k.jahrgang, k.farbe, k.rasse, k.gezeichnet, k.geschnitten
                   FROM koenigin_volk kv JOIN koenigin k ON k.id = kv.koenigin_id
                   WHERE kv.volk_id = %(v)s AND kv.gueltig @> %(t)s""", p)
    v["koenigin"] = cur.fetchone()
    cur.execute("""SELECT g.name, g.art, lower(z.gueltig) AS von, upper(z.gueltig) AS bis
                   FROM geraet_zuordnung z JOIN geraet g ON g.id = z.geraet_id
                   WHERE z.volk_id = %(v)s ORDER BY lower(z.gueltig)""", p)
    v["geraete"] = cur.fetchall()
    return v


# ---------------------------------------------------------------- Messreihen

def messreihen(cur, bezug, bezug_id, von, bis, groessen, raster_weite):
    """Verdichtete Reihen je (Messgröße, Messstelle) für ein Volk (bezug='volk') oder einen Stand ('stand').

    groessen: {code: verdichtung}; leer = alle Messgrößen mit Werten im Zeitraum. Werte mit qualitaet='ungueltig'
    bleiben draußen; 'verdaechtig' wird mitgezählt und je Punkt nicht unterschieden (Anzahl in 'verdaechtig').
    """
    sql = _sql()
    spalte = sql.Identifier({"volk": "volk_id", "stand": "stand_id"}[bezug])
    p = {"id": bezug_id, "von": von, "bis": bis, "r": raster_weite}
    if not groessen:
        cur.execute(sql.SQL("""SELECT DISTINCT m.messgroesse_code, g.verdichtung FROM messwert_bezug m
                               JOIN messgroesse g ON g.code = m.messgroesse_code
                               WHERE m.{} = %(id)s AND m.zeit >= %(von)s AND m.zeit < %(bis)s""").format(spalte), p)
        groessen = {r["messgroesse_code"]: r["verdichtung"] for r in cur.fetchall()}
    reihen = []
    for code in sorted(groessen):
        abfrage = sql.SQL("""
            SELECT m.messstelle_id, ms.zone, ms.bezeichnung, ms.hoehe_cm, ms.tiefe_cm,
                   date_bin(%(r)s, m.zeit, TIMESTAMPTZ '2000-01-01 00:00+00') AS t,
                   {agg} AS wert, count(*) AS n,
                   count(*) FILTER (WHERE m.qualitaet = 'verdaechtig') AS verdaechtig,
                   count(*) FILTER (WHERE m.zeitqualitaet <> 'geraet') AS ohne_geraetezeit
            FROM messwert_bezug m LEFT JOIN messstelle ms ON ms.id = m.messstelle_id
            WHERE m.{spalte} = %(id)s AND m.messgroesse_code = %(g)s
              AND m.zeit >= %(von)s AND m.zeit < %(bis)s AND m.qualitaet <> 'ungueltig'
            GROUP BY 1, 2, 3, 4, 5, 6 ORDER BY 1, 6""").format(
            agg=sql.SQL(aggregat(groessen[code])), spalte=spalte)   # "wert"/"zeit" gibt es nur in messwert_bezug
        cur.execute(abfrage, {**p, "g": code})
        je_stelle = {}
        for r in cur.fetchall():
            s = je_stelle.setdefault(r["messstelle_id"], {
                "messgroesse": code, "messstelle_id": r["messstelle_id"], "zone": r["zone"],
                "bezeichnung": r["bezeichnung"], "hoehe_cm": r["hoehe_cm"], "tiefe_cm": r["tiefe_cm"],
                "punkte": [], "werte": 0, "verdaechtig": 0, "ohne_geraetezeit": 0})
            s["punkte"].append((r["t"], r["wert"]))
            s["werte"] += r["n"]
            s["verdaechtig"] += r["verdaechtig"]
            s["ohne_geraetezeit"] += r["ohne_geraetezeit"]
        for s in je_stelle.values():
            s["punkte"] = mit_luecken(s["punkte"], raster_weite)
            reihen.append(s)
    return reihen


def tagesbilanz(cur, volk_id, von, bis):
    cur.execute("""SELECT tag, referenz_kg, bilanz_kg, mit_eingriff, berechnung FROM gewicht_tagesbilanz
                   WHERE volk_id = %(v)s AND tag >= (%(von)s AT TIME ZONE 'Europe/Berlin')::date
                     AND tag < (%(bis)s AT TIME ZONE 'Europe/Berlin')::date
                   ORDER BY tag""", {"v": volk_id, "von": von, "bis": bis})
    return cur.fetchall()


def ereignisse(cur, volk_id, von, bis):
    p = {"v": volk_id, "von": von, "bis": bis}
    cur.execute("""SELECT id, zeit, zeitgenauigkeit, notiz, quelle FROM durchsicht
                   WHERE volk_id = %(v)s AND zeit >= %(von)s AND zeit < %(bis)s ORDER BY zeit""", p)
    durchsichten = cur.fetchall()
    cur.execute("""SELECT id, art, lower(zeitraum) AS von, upper(zeitraum) AS bis, zeitgenauigkeit,
                          menge, einheit, mittel, notiz, quelle
                   FROM massnahme WHERE volk_id = %(v)s AND zeitraum && tstzrange(%(von)s, %(bis)s)
                   ORDER BY lower(zeitraum)""", p)
    massnahmen = cur.fetchall()
    cur.execute("""SELECT id, von, bis, milben, milben_pro_tag, anmerkung, zeitgenauigkeit, berechnung
                   FROM varroa_pro_tag
                   WHERE volk_id = %(v)s AND tstzrange(von, bis) && tstzrange(%(von)s, %(bis)s) ORDER BY von""", p)
    varroa = cur.fetchall()
    cur.execute("""SELECT e.id, e.art, e.zeit, e.notiz, t.rolle,
                          (SELECT json_agg(json_build_object('volk_id', t2.volk_id, 'name', v2.name, 'rolle', t2.rolle))
                           FROM volk_ereignis_teil t2 JOIN volk v2 ON v2.id = t2.volk_id
                           WHERE t2.ereignis_id = e.id) AS beteiligte
                   FROM volk_ereignis e JOIN volk_ereignis_teil t ON t.ereignis_id = e.id
                   WHERE t.volk_id = %(v)s AND e.zeit >= %(von)s AND e.zeit < %(bis)s ORDER BY e.zeit""", p)
    return {"durchsichten": durchsichten, "massnahmen": massnahmen, "varroa": varroa, "volk_ereignisse": cur.fetchall()}


# ---------------------------------------------------------------- Prüfungen und Betrieb

def pruefungen(cur):
    cur.execute("SELECT zuordnung_id, geraet, volk, lower(gueltig) AS von, upper(gueltig) AS bis, befund "
                "FROM pruefung_geraet_zuordnung ORDER BY geraet")
    zuordnung = cur.fetchall()
    cur.execute("""SELECT g.name AS geraet, q.quellfeld, q.zuerst, q.zuletzt, q.anzahl
                   FROM quellfeld_ohne_kanal q JOIN geraet g ON g.id = q.geraet_id ORDER BY g.name, q.quellfeld""")
    unbenannt = cur.fetchall()
    cur.execute("""SELECT g.name, g.art, (SELECT max(empfangen) FROM rohnachricht r WHERE r.geraet_id = g.id) AS letzte
                   FROM geraet g
                   WHERE NOT EXISTS (SELECT 1 FROM geraet_zuordnung z WHERE z.geraet_id = g.id AND upper_inf(z.gueltig))
                   ORDER BY g.name""")
    ohne_ziel = cur.fetchall()
    cur.execute("""SELECT g.name, max(r.empfangen) AS letzte, count(*) AS nachrichten
                   FROM geraet g JOIN rohnachricht r ON r.geraet_id = g.id GROUP BY g.name ORDER BY g.name""")
    geraete = cur.fetchall()
    cur.execute("SELECT datei, zeilen, bytes, aktualisiert FROM import_position ORDER BY datei")
    importe = cur.fetchall()
    return {"zuordnung": zuordnung, "unbenannt": unbenannt, "geraete_ohne_ziel": ohne_ziel,
            "geraete": geraete, "importe": importe}


def gesundheit(cur):
    cur.execute("SELECT max(aktualisiert) AS letzter_import FROM import_position")
    return cur.fetchone()
