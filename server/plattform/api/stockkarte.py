# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Stockkarte erfassen (Phase C, Teil 2): Durchsicht mit Checkliste, Maßnahme, Varroa-Messung, Aufgabe.

Die Einträge sind Ereignisse, keine Stammdaten-Historie: Sie dürfen korrigiert und gelöscht werden (wie in BEEP).
Eine korrigierte Uhrzeit setzt die Zeitgenauigkeit auf 'exakt', sofern nichts anderes angegeben ist (K-03).
Mehrere Völker zugleich ergeben je Volk einen eigenen Eintrag (Konzept 0.2 §5.2).
Alle Funktionen laufen in der Transaktion des Aufrufers.
"""
import json
from datetime import date, timedelta

from .katalog import CHECKLISTE, CHECKLISTE_GRUPPEN, CHECKLISTE_NAME
from .stammdaten import Konflikt, NichtGefunden

EINE_MINUTE = timedelta(minutes=1)


def _eins(cur, sql_text, p=None):
    cur.execute(sql_text, p)
    r = cur.fetchone()
    return None if r is None else next(iter(r.values()))


def volk_pruefen(cur, volk_id, zeit):
    """Volk muss existieren und zum Zeitpunkt bestehen (nicht vor der Entstehung, nicht nach der Auflösung)."""
    cur.execute("SELECT name, entstanden_am, aufgeloest_am FROM volk WHERE id = %s", (volk_id,))
    v = cur.fetchone()
    if v is None:
        raise NichtGefunden(f"Volk {volk_id} unbekannt")
    if v["entstanden_am"] is not None and zeit < v["entstanden_am"]:
        raise Konflikt(f"{v['name']} ist zu diesem Zeitpunkt noch nicht entstanden")
    if v["aufgeloest_am"] is not None and zeit >= v["aufgeloest_am"]:
        raise Konflikt(f"{v['name']} ist zu diesem Zeitpunkt aufgelöst")


# ---------------------------------------------------------------- Checkliste

def checkliste_uebernehmen(cur, gueltig_ab):
    """Merkmale der Standard-Checkliste anlegen (vorhandene Codes bleiben) und die Checkliste anlegen bzw. eine neue
    Version, wenn sich die Merkmalsfolge gegenüber der aktuellen Version unterscheidet. Rückgabe: Version (id)."""
    gruppen = {}
    for code, name in CHECKLISTE_GRUPPEN:
        cur.execute("INSERT INTO merkmal(code, name, eingabetyp) VALUES (%s, %s, 'gruppe') ON CONFLICT (code) DO NOTHING",
                    (code, name))
        gruppen[code] = _eins(cur, "SELECT id FROM merkmal WHERE code = %s", (code,))
    ids = []
    for code, name, typ, einheit, optionen, gruppe in CHECKLISTE:
        cur.execute("""INSERT INTO merkmal(code, name, eltern_id, eingabetyp, einheit, optionen)
                       VALUES (%s, %s, %s, %s, %s, %s::jsonb) ON CONFLICT (code) DO NOTHING""",
                    (code, name, gruppen[gruppe], typ, einheit, json.dumps(optionen, ensure_ascii=False) if optionen else None))
        ids.append(_eins(cur, "SELECT id FROM merkmal WHERE code = %s", (code,)))
    cur.execute("INSERT INTO checkliste(name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (CHECKLISTE_NAME,))
    liste = _eins(cur, "SELECT id FROM checkliste WHERE name = %s", (CHECKLISTE_NAME,))
    cur.execute("""SELECT v.id, v.version, array_agg(m.merkmal_id ORDER BY m.reihenfolge) AS merkmale
                   FROM checkliste_version v LEFT JOIN checkliste_merkmal m ON m.version_id = v.id
                   WHERE v.checkliste_id = %s GROUP BY v.id ORDER BY v.version DESC LIMIT 1""", (liste,))
    aktuell = cur.fetchone()
    if aktuell and list(aktuell["merkmale"]) == ids:
        return aktuell["id"]
    version = (aktuell["version"] + 1) if aktuell else 1
    vid = _eins(cur, "INSERT INTO checkliste_version(checkliste_id, version, gueltig_ab) VALUES (%s, %s, %s) RETURNING id",
                (liste, version, gueltig_ab))
    cur.executemany("INSERT INTO checkliste_merkmal(version_id, merkmal_id, reihenfolge) VALUES (%s, %s, %s)",
                    [(vid, mid, i) for i, mid in enumerate(ids, start=1)])
    return vid


def checklisten(cur):
    """Aktuelle Version jeder Checkliste mit ihren Merkmalen (Gruppe, Eingabetyp, Optionen)."""
    cur.execute("""SELECT DISTINCT ON (c.id) c.id AS checkliste_id, c.name, v.id AS version_id, v.version, v.gueltig_ab
                   FROM checkliste c JOIN checkliste_version v ON v.checkliste_id = c.id
                   ORDER BY c.id, v.version DESC""")
    aus = cur.fetchall()
    for c in aus:
        cur.execute("""SELECT m.id, m.code, m.name, m.eingabetyp, m.einheit, m.optionen, g.name AS gruppe, cm.pflicht
                       FROM checkliste_merkmal cm JOIN merkmal m ON m.id = cm.merkmal_id
                       LEFT JOIN merkmal g ON g.id = m.eltern_id
                       WHERE cm.version_id = %s ORDER BY cm.reihenfolge""", (c["version_id"],))
        c["merkmale"] = cur.fetchall()
    return aus


def _wert_spalten(merkmal, wert):
    """Eingabe → (wert_zahl, wert_text, wert_bool) nach Eingabetyp; Konflikt bei unpassendem Wert."""
    typ, name = merkmal["eingabetyp"], merkmal["name"]
    if typ == "janein":
        if not isinstance(wert, bool):
            raise Konflikt(f"{name}: ja oder nein erwartet")
        return None, None, wert
    if typ in ("zahl", "ganzzahl", "bewertung"):
        if isinstance(wert, bool) or not isinstance(wert, (int, float)):
            raise Konflikt(f"{name}: Zahl erwartet")
        if typ != "zahl" and int(wert) != wert:
            raise Konflikt(f"{name}: ganze Zahl erwartet")
        if typ == "bewertung" and not 1 <= wert <= 5:
            raise Konflikt(f"{name}: Bewertung 1 bis 5")
        if typ == "ganzzahl" and wert < 0:
            raise Konflikt(f"{name}: nicht negativ")
        return wert, None, None
    if typ == "liste":
        if wert not in (merkmal["optionen"] or []):
            raise Konflikt(f"{name}: unbekannte Auswahl {wert!r}")
        return None, wert, None
    if typ == "datum":
        try:
            date.fromisoformat(str(wert))
        except ValueError:
            raise Konflikt(f"{name}: Datum JJJJ-MM-TT erwartet") from None
        return None, str(wert), None
    if typ == "text":
        if not isinstance(wert, str) or len(wert) > 2000:
            raise Konflikt(f"{name}: Text bis 2000 Zeichen erwartet")
        return None, wert, None
    raise Konflikt(f"{name}: Merkmal vom Typ {typ} nimmt keinen Wert an")


def _werte_schreiben(cur, durchsicht_id, version_id, werte):
    """werte: {merkmal_code: wert}; leere Werte (None, '') werden nicht gespeichert. Nur Merkmale der Checkliste."""
    if not werte:
        return 0
    if version_id is None:
        raise Konflikt("Werte brauchen eine Checkliste")
    cur.execute("""SELECT m.id, m.code, m.name, m.eingabetyp, m.optionen FROM checkliste_merkmal cm
                   JOIN merkmal m ON m.id = cm.merkmal_id WHERE cm.version_id = %s""", (version_id,))
    merkmale = {m["code"]: m for m in cur.fetchall()}
    n = 0
    for code, wert in werte.items():
        if wert is None or wert == "":
            continue
        if code not in merkmale:
            raise Konflikt(f"Merkmal {code} gehört nicht zur Checkliste")
        z, t, b = _wert_spalten(merkmale[code], wert)
        cur.execute("INSERT INTO durchsicht_wert(durchsicht_id, merkmal_id, wert_zahl, wert_text, wert_bool) VALUES (%s, %s, %s, %s, %s)",
                    (durchsicht_id, merkmale[code]["id"], z, t, b))
        n += 1
    return n


# ---------------------------------------------------------------- Durchsicht

def durchsicht_anlegen(cur, volk_ids, zeit, zeitgenauigkeit="exakt", version_id=None, notiz=None, werte=None):
    if not volk_ids:
        raise Konflikt("mindestens ein Volk wählen")
    if version_id is not None and _eins(cur, "SELECT id FROM checkliste_version WHERE id = %s", (version_id,)) is None:
        raise NichtGefunden("Checkliste unbekannt")
    ids = []
    for v in volk_ids:
        volk_pruefen(cur, v, zeit)
        d = _eins(cur, """INSERT INTO durchsicht(volk_id, zeit, zeitgenauigkeit, checkliste_version_id, notiz)
                          VALUES (%s, %s, %s, %s, %s) RETURNING id""", (v, zeit, zeitgenauigkeit, version_id, notiz))
        _werte_schreiben(cur, d, version_id, werte)
        ids.append(d)
    return ids


def durchsicht_aendern(cur, durchsicht_id, zeit, zeitgenauigkeit=None, notiz=None, werte=None):
    """Zeit, Notiz und Werte ersetzen. Eine geänderte Zeit gilt als exakt, wenn keine Zeitgenauigkeit angegeben ist."""
    cur.execute("SELECT volk_id, zeit, zeitgenauigkeit, checkliste_version_id FROM durchsicht WHERE id = %s", (durchsicht_id,))
    alt = cur.fetchone()
    if alt is None:
        raise NichtGefunden("Durchsicht unbekannt")
    volk_pruefen(cur, alt["volk_id"], zeit)
    genau = zeitgenauigkeit or ("exakt" if zeit != alt["zeit"] else alt["zeitgenauigkeit"])
    cur.execute("UPDATE durchsicht SET zeit = %s, zeitgenauigkeit = %s, notiz = %s WHERE id = %s",
                (zeit, genau, notiz, durchsicht_id))
    cur.execute("DELETE FROM durchsicht_wert WHERE durchsicht_id = %s", (durchsicht_id,))
    _werte_schreiben(cur, durchsicht_id, alt["checkliste_version_id"], werte)
    return genau


def durchsicht_loeschen(cur, durchsicht_id):
    if _eins(cur, "SELECT id FROM durchsicht WHERE id = %s", (durchsicht_id,)) is None:
        raise NichtGefunden("Durchsicht unbekannt")
    # Verweise lösen: Maßnahmen und Aufgaben bleiben bestehen, nur ohne Bezug zur gelöschten Durchsicht
    cur.execute("UPDATE massnahme SET durchsicht_id = NULL WHERE durchsicht_id = %s", (durchsicht_id,))
    cur.execute("UPDATE aufgabe SET durchsicht_id = NULL WHERE durchsicht_id = %s", (durchsicht_id,))
    if _eins(cur, "SELECT count(*) FROM anhang WHERE durchsicht_id = %s", (durchsicht_id,)):
        raise Konflikt("Durchsicht hat Anhänge; zuerst die Anhänge entfernen")
    cur.execute("DELETE FROM durchsicht WHERE id = %s", (durchsicht_id,))   # Werte per ON DELETE CASCADE


def durchsicht(cur, durchsicht_id):
    cur.execute("""SELECT d.id, d.volk_id, v.name AS volk, d.zeit, d.zeitgenauigkeit, d.notiz, d.quelle,
                          d.checkliste_version_id FROM durchsicht d JOIN volk v ON v.id = d.volk_id WHERE d.id = %s""",
                (durchsicht_id,))
    d = cur.fetchone()
    if d is None:
        raise NichtGefunden("Durchsicht unbekannt")
    d["werte"] = durchsicht_werte(cur, [durchsicht_id]).get(durchsicht_id, [])
    return d


def durchsicht_werte(cur, ids):
    """{durchsicht_id: [{code, name, eingabetyp, einheit, wert}]} in der Reihenfolge der Checkliste."""
    if not ids:
        return {}
    cur.execute("""SELECT w.durchsicht_id, m.code, m.name, m.eingabetyp, m.einheit,
                          coalesce(to_jsonb(w.wert_bool), to_jsonb(w.wert_zahl), to_jsonb(w.wert_text)) AS wert
                   FROM durchsicht_wert w JOIN merkmal m ON m.id = w.merkmal_id
                   JOIN durchsicht d ON d.id = w.durchsicht_id
                   LEFT JOIN checkliste_merkmal cm ON cm.version_id = d.checkliste_version_id AND cm.merkmal_id = m.id
                   WHERE w.durchsicht_id = ANY(%s) ORDER BY w.durchsicht_id, cm.reihenfolge NULLS LAST, m.code""", (ids,))
    aus = {}
    for r in cur.fetchall():
        aus.setdefault(r.pop("durchsicht_id"), []).append(r)
    return aus


# ---------------------------------------------------------------- Maßnahme, Varroa

def _zeitraum(von, bis):
    """Zeitpunkt (bis fehlt) als kurzer Zeitraum [t, t+1 min), wie im Schema vorgesehen."""
    if bis is None:
        return von, von + EINE_MINUTE
    if bis <= von:
        raise Konflikt("Ende muss nach dem Beginn liegen")
    return von, bis


def massnahme_anlegen(cur, volk_ids, art, von, bis=None, zeitgenauigkeit="exakt", menge=None, einheit=None, mittel=None,
                      notiz=None, durchsicht_id=None):
    if not volk_ids:
        raise Konflikt("mindestens ein Volk wählen")
    a, b = _zeitraum(von, bis)
    ids = []
    for v in volk_ids:
        volk_pruefen(cur, v, a)
        ids.append(_eins(cur, """INSERT INTO massnahme(volk_id, art, zeitraum, zeitgenauigkeit, menge, einheit, mittel, notiz, durchsicht_id)
                                 VALUES (%s, %s, tstzrange(%s, %s, '[)'), %s, %s, %s, %s, %s, %s) RETURNING id""",
                         (v, art, a, b, zeitgenauigkeit, menge, einheit, mittel, notiz, durchsicht_id)))
    return ids


def massnahme_aendern(cur, massnahme_id, art, von, bis=None, zeitgenauigkeit=None, menge=None, einheit=None, mittel=None, notiz=None):
    cur.execute("SELECT volk_id, lower(zeitraum) AS von, zeitgenauigkeit FROM massnahme WHERE id = %s", (massnahme_id,))
    alt = cur.fetchone()
    if alt is None:
        raise NichtGefunden("Maßnahme unbekannt")
    a, b = _zeitraum(von, bis)
    volk_pruefen(cur, alt["volk_id"], a)
    genau = zeitgenauigkeit or ("exakt" if a != alt["von"] else alt["zeitgenauigkeit"])
    cur.execute("""UPDATE massnahme SET art = %s, zeitraum = tstzrange(%s, %s, '[)'), zeitgenauigkeit = %s, menge = %s,
                     einheit = %s, mittel = %s, notiz = %s WHERE id = %s""",
                (art, a, b, genau, menge, einheit, mittel, notiz, massnahme_id))


def varroa_anlegen(cur, volk_ids, methode, von, bis, milben, anmerkung=None, zeitgenauigkeit="exakt"):
    if not volk_ids:
        raise Konflikt("mindestens ein Volk wählen")
    a, b = _zeitraum(von, bis)
    ids = []
    for v in volk_ids:
        volk_pruefen(cur, v, a)
        ids.append(_eins(cur, """INSERT INTO varroa_messung(volk_id, zeitraum, zeitgenauigkeit, methode, milben, anmerkung)
                                 VALUES (%s, tstzrange(%s, %s, '[)'), %s, %s, %s, %s) RETURNING id""",
                         (v, a, b, zeitgenauigkeit, methode, milben, anmerkung)))
    return ids


def varroa_aendern(cur, varroa_id, methode, von, bis, milben, anmerkung=None, zeitgenauigkeit=None):
    cur.execute("SELECT volk_id, lower(zeitraum) AS von, zeitgenauigkeit FROM varroa_messung WHERE id = %s", (varroa_id,))
    alt = cur.fetchone()
    if alt is None:
        raise NichtGefunden("Varroa-Messung unbekannt")
    a, b = _zeitraum(von, bis)
    volk_pruefen(cur, alt["volk_id"], a)
    genau = zeitgenauigkeit or ("exakt" if a != alt["von"] else alt["zeitgenauigkeit"])
    cur.execute("""UPDATE varroa_messung SET methode = %s, zeitraum = tstzrange(%s, %s, '[)'), milben = %s, anmerkung = %s,
                     zeitgenauigkeit = %s WHERE id = %s""", (methode, a, b, milben, anmerkung, genau, varroa_id))


def loeschen(cur, tabelle, id_):
    if tabelle not in ("massnahme", "varroa_messung", "aufgabe"):
        raise ValueError(tabelle)
    from psycopg import sql
    cur.execute(sql.SQL("DELETE FROM {} WHERE id = %s").format(sql.Identifier(tabelle)), (id_,))
    if cur.rowcount == 0:
        raise NichtGefunden(f"{tabelle} {id_} unbekannt")


def eintrag(cur, art, id_):
    """Einzelner Eintrag zum Bearbeiten (art: durchsicht, massnahme, varroa)."""
    if art == "durchsicht":
        return durchsicht(cur, id_)
    if art == "massnahme":
        cur.execute("""SELECT m.id, m.volk_id, v.name AS volk, m.art, lower(m.zeitraum) AS von, upper(m.zeitraum) AS bis,
                              m.zeitgenauigkeit, m.menge, m.einheit, m.mittel, m.notiz, m.quelle
                       FROM massnahme m JOIN volk v ON v.id = m.volk_id WHERE m.id = %s""", (id_,))
    elif art == "varroa":
        cur.execute("""SELECT m.id, m.volk_id, v.name AS volk, m.methode, lower(m.zeitraum) AS von, upper(m.zeitraum) AS bis,
                              m.milben, m.anmerkung, m.zeitgenauigkeit, m.quelle
                       FROM varroa_messung m JOIN volk v ON v.id = m.volk_id WHERE m.id = %s""", (id_,))
    else:
        raise NichtGefunden(f"Art {art} unbekannt")
    r = cur.fetchone()
    if r is None:
        raise NichtGefunden(f"{art} {id_} unbekannt")
    return r


# ---------------------------------------------------------------- Aufgaben

def aufgabe_anlegen(cur, faellig_am, text, volk_ids=None, stand_id=None, durchsicht_id=None):
    if bool(volk_ids) == bool(stand_id):
        raise Konflikt("Aufgabe für Völker oder für einen Stand")
    ziele = [(v, None) for v in volk_ids] if volk_ids else [(None, stand_id)]
    ids = []
    for v, s in ziele:
        ids.append(_eins(cur, """INSERT INTO aufgabe(volk_id, stand_id, faellig_am, text, durchsicht_id)
                                 VALUES (%s, %s, %s, %s, %s) RETURNING id""", (v, s, faellig_am, text, durchsicht_id)))
    return ids


def aufgabe_erledigt(cur, aufgabe_id, zeit, erledigt=True):
    cur.execute("UPDATE aufgabe SET erledigt_am = %s WHERE id = %s", (zeit if erledigt else None, aufgabe_id))
    if cur.rowcount == 0:
        raise NichtGefunden("Aufgabe unbekannt")


def aufgaben(cur, nur_offen=True, volk_id=None):
    cur.execute("""SELECT a.id, a.faellig_am, a.text, a.erledigt_am, a.volk_id, v.name AS volk, a.stand_id, s.name AS stand
                   FROM aufgabe a LEFT JOIN volk v ON v.id = a.volk_id LEFT JOIN stand s ON s.id = a.stand_id
                   WHERE (NOT %(offen)s OR a.erledigt_am IS NULL) AND (%(v)s::int IS NULL OR a.volk_id = %(v)s)
                   ORDER BY a.erledigt_am IS NOT NULL, a.faellig_am, a.id""", {"offen": nur_offen, "v": volk_id})
    return cur.fetchall()
