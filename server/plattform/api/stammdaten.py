# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Stammdaten pflegen (Phase C, Teil 1): fachliche Aktionen statt Rohtabellen.

Grundsatz des Schemas: Historie wird nie überschrieben. Eine Änderung „ab Zeitpunkt z“ beendet die offene Zeile
bei z und legt eine neue an. Liegt z vor dem Beginn der offenen Zeile, wird abgelehnt (Konflikt): Rückwirkende
Korrekturen der Historie gehören nicht in diese Masken.
Alle Funktionen laufen in der Transaktion des Aufrufers (app.py: Commit nur bei Erfolg).
"""
from datetime import timedelta

from .katalog import MESSGROESSEN, VORLAGEN, ist_steuerfeld


class Konflikt(Exception):
    """Fachlich nicht möglich (HTTP 409); der Text geht an die Oberfläche."""


class NichtGefunden(Exception):
    """Objekt fehlt (HTTP 404)."""


# Tabellen mit Zeitraum 'gueltig' und der Spalte, über die ihre offene Zeile gefunden wird
_ZEITRAUM = {"belegung": ("volk_id", "beute_id"), "aufstellung": ("beute_id",), "beute_konfiguration": ("beute_id",),
             "geraet_zuordnung": ("geraet_id", "volk_id"), "kanal": ("id", "geraet_id")}


def _eins(cur, sql_text, p=None):
    cur.execute(sql_text, p)
    r = cur.fetchone()
    return None if r is None else (r["id"] if isinstance(r, dict) and "id" in r else next(iter(r.values())))


def _gibt_es(cur, tabelle, id_):
    from psycopg import sql
    cur.execute(sql.SQL("SELECT 1 FROM {} WHERE id = %s").format(sql.Identifier(tabelle)), (id_,))
    if cur.fetchone() is None:
        raise NichtGefunden(f"{tabelle} {id_} unbekannt")


def offene_beenden(cur, tabelle, spalte, wert, zeit, pflicht=False):
    """Offene Zeile(n) von tabelle mit spalte = wert zum Zeitpunkt zeit beenden. Rückgabe: Anzahl beendeter Zeilen."""
    from psycopg import sql
    if tabelle not in _ZEITRAUM or spalte not in _ZEITRAUM[tabelle]:
        raise ValueError((tabelle, spalte))
    ident = {"t": sql.Identifier(tabelle), "s": sql.Identifier(spalte)}
    cur.execute(sql.SQL("SELECT id, lower(gueltig) AS von FROM {t} WHERE {s} = %s AND upper_inf(gueltig)").format(**ident), (wert,))
    offen = cur.fetchall()
    for r in offen:
        if r["von"] >= zeit:
            raise Konflikt(f"{tabelle}: die bestehende Angabe beginnt erst {r['von']:%d.%m.%Y %H:%M} UTC; "
                           "eine Änderung davor würde die Historie umschreiben")
    if pflicht and not offen:
        raise Konflikt(f"{tabelle}: keine offene Angabe, die beendet werden könnte")
    cur.execute(sql.SQL("UPDATE {t} SET gueltig = tstzrange(lower(gueltig), %s, '[)') WHERE {s} = %s AND upper_inf(gueltig)")
                .format(**ident), (zeit, wert))
    return len(offen)


# ---------------------------------------------------------------- Messgrößen

def katalog_uebernehmen(cur):
    """Fehlende Messgrößen des Standardkatalogs anlegen; vorhandene bleiben unverändert. Rückgabe: Anzahl neu."""
    neu = 0
    for zeile in MESSGROESSEN:
        cur.execute("""INSERT INTO messgroesse(code, name, einheit, semantik, verdichtung, achse, darstellung, farbe, oeffentlich)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (code) DO NOTHING""", zeile)
        neu += cur.rowcount
    return neu


def messgroesse_speichern(cur, d):
    cur.execute("""INSERT INTO messgroesse(code, name, einheit, semantik, verdichtung, achse, darstellung, farbe, oeffentlich)
                   VALUES (%(code)s, %(name)s, %(einheit)s, %(semantik)s, %(verdichtung)s, %(achse)s, %(darstellung)s,
                           %(farbe)s, %(oeffentlich)s)
                   ON CONFLICT (code) DO UPDATE SET name = excluded.name, einheit = excluded.einheit,
                     semantik = excluded.semantik, verdichtung = excluded.verdichtung, achse = excluded.achse,
                     darstellung = excluded.darstellung, farbe = excluded.farbe, oeffentlich = excluded.oeffentlich""", d)


# ---------------------------------------------------------------- Stände, Völker, Beuten

def stand_anlegen(cur, name, ort_oeffentlich):
    return _eins(cur, "INSERT INTO stand(name, ort_oeffentlich) VALUES (%s, %s) RETURNING id", (name, ort_oeffentlich))


def stand_aendern(cur, stand_id, name, ort_oeffentlich):
    _gibt_es(cur, "stand", stand_id)
    cur.execute("UPDATE stand SET name = %s, ort_oeffentlich = %s WHERE id = %s", (name, ort_oeffentlich, stand_id))


def beute_anlegen(cur, beute, ab, stand_id, platz):
    """Neue Beute mit Konfiguration und Aufstellung ab 'ab'."""
    b = _eins(cur, "INSERT INTO beute(bezeichnung, beutentyp, rahmenmass) VALUES (%s, %s, %s) RETURNING id",
              (beute["bezeichnung"], beute.get("beutentyp"), beute.get("rahmenmass")))
    cur.execute("""INSERT INTO beute_konfiguration(beute_id, gueltig, brutzargen, honigzargen, rahmen)
                   VALUES (%s, tstzrange(%s, NULL, '[)'), %s, %s, %s)""",
                (b, ab, beute.get("brutzargen"), beute.get("honigzargen"), beute.get("rahmen")))
    cur.execute("INSERT INTO aufstellung(beute_id, stand_id, gueltig, platz) VALUES (%s, %s, tstzrange(%s, NULL, '[)'), %s)",
                (b, stand_id, ab, platz))
    return b


def volk_anlegen(cur, name, ab, stand_id, platz, beute, notiz=None):
    """Volk mit eigener, neuer Beute am Stand anlegen (wie ein neuer Hive in BEEP). Rückgabe: (volk_id, beute_id)."""
    _gibt_es(cur, "stand", stand_id)
    v = _eins(cur, "INSERT INTO volk(name, entstanden_am, notiz) VALUES (%s, %s, %s) RETURNING id", (name, ab, notiz))
    b = beute_anlegen(cur, beute, ab, stand_id, platz)
    cur.execute("INSERT INTO belegung(volk_id, beute_id, gueltig) VALUES (%s, %s, tstzrange(%s, NULL, '[)'))", (v, b, ab))
    return v, b


def volk_aendern(cur, volk_id, name, notiz):
    _gibt_es(cur, "volk", volk_id)
    cur.execute("UPDATE volk SET name = %s, notiz = %s WHERE id = %s", (name, notiz, volk_id))


def _aktuelle_beute(cur, volk_id, zeit):
    cur.execute("""SELECT b.beute_id, a.stand_id, a.platz FROM belegung b
                   LEFT JOIN aufstellung a ON a.beute_id = b.beute_id AND a.gueltig @> %(z)s
                   WHERE b.volk_id = %(v)s AND b.gueltig @> %(z)s""", {"v": volk_id, "z": zeit})
    return cur.fetchone()


def volk_umsetzen(cur, volk_id, zeit, neue_beute=None, beute_id=None, stand_id=None, platz=None):
    """Volk ab zeit in eine neue (neue_beute = Angaben) oder eine leere vorhandene Beute (beute_id) setzen.
    Ohne Angabe von Stand/Platz kommt die neue Beute an Stand und Platz der alten. Legt die Maßnahme 'umsetzen' an,
    damit ein Gewichtssprung auf derselben Waage erklärt ist (Leitplanke L8)."""
    _gibt_es(cur, "volk", volk_id)
    alt = _aktuelle_beute(cur, volk_id, zeit)
    if alt is None:
        raise Konflikt("Volk hat zu diesem Zeitpunkt keine Beute")
    stand = stand_id or alt["stand_id"]
    platz = platz if platz is not None else alt["platz"]
    offene_beenden(cur, "belegung", "volk_id", volk_id, zeit, pflicht=True)
    if beute_id is None:
        offene_beenden(cur, "aufstellung", "beute_id", alt["beute_id"], zeit)     # alte Beute räumt den Platz
        beute_id = beute_anlegen(cur, neue_beute, zeit, stand, platz)
    else:
        _gibt_es(cur, "beute", beute_id)
    cur.execute("INSERT INTO belegung(volk_id, beute_id, gueltig) VALUES (%s, %s, tstzrange(%s, NULL, '[)'))",
                (volk_id, beute_id, zeit))
    cur.execute("""INSERT INTO massnahme(volk_id, art, zeitraum, notiz)
                   VALUES (%s, 'umsetzen', tstzrange(%s, %s, '[)'), 'aus der Verwaltung')""",
                (volk_id, zeit - timedelta(minutes=1), zeit + timedelta(minutes=1)))
    return beute_id


def volk_aufloesen(cur, volk_id, zeit, ziel_volk_id=None, art="aufloesung", notiz=None):
    """Volk ab zeit auflösen ('aufloesung') oder mit ziel_volk_id vereinigen ('vereinigung').
    Beendet Belegung und Waagenzuordnung, damit keine Messwerte mehr einem aufgelösten Volk zufallen (HB-09)."""
    if art not in ("aufloesung", "vereinigung"):
        raise Konflikt("Art muss aufloesung oder vereinigung sein")
    _gibt_es(cur, "volk", volk_id)
    cur.execute("SELECT aufgeloest_am, entstanden_am FROM volk WHERE id = %s", (volk_id,))
    v = cur.fetchone()
    if v["aufgeloest_am"] is not None:
        raise Konflikt("Volk ist bereits aufgelöst")
    if v["entstanden_am"] is not None and zeit <= v["entstanden_am"]:
        raise Konflikt("Auflösung liegt vor der Entstehung des Volks")
    if art == "vereinigung":
        if not ziel_volk_id or ziel_volk_id == volk_id:
            raise Konflikt("Vereinigung braucht ein anderes Zielvolk")
        _gibt_es(cur, "volk", ziel_volk_id)
    cur.execute("UPDATE volk SET aufgeloest_am = %s WHERE id = %s", (zeit, volk_id))
    offene_beenden(cur, "belegung", "volk_id", volk_id, zeit)
    zuordnungen = offene_beenden(cur, "geraet_zuordnung", "volk_id", volk_id, zeit)
    e = _eins(cur, "INSERT INTO volk_ereignis(art, zeit, notiz) VALUES (%s, %s, %s) RETURNING id", (art, zeit, notiz))
    cur.execute("INSERT INTO volk_ereignis_teil(ereignis_id, volk_id, rolle) VALUES (%s, %s, 'quelle')", (e, volk_id))
    if ziel_volk_id:
        cur.execute("INSERT INTO volk_ereignis_teil(ereignis_id, volk_id, rolle) VALUES (%s, %s, 'bleibt')", (e, ziel_volk_id))
    return zuordnungen


def beute_aufstellen(cur, beute_id, zeit, stand_id, platz):
    _gibt_es(cur, "beute", beute_id)
    _gibt_es(cur, "stand", stand_id)
    offene_beenden(cur, "aufstellung", "beute_id", beute_id, zeit)
    cur.execute("INSERT INTO aufstellung(beute_id, stand_id, gueltig, platz) VALUES (%s, %s, tstzrange(%s, NULL, '[)'), %s)",
                (beute_id, stand_id, zeit, platz))


def beute_konfigurieren(cur, beute_id, zeit, brutzargen, honigzargen, rahmen=None, notiz=None):
    _gibt_es(cur, "beute", beute_id)
    offene_beenden(cur, "beute_konfiguration", "beute_id", beute_id, zeit)
    cur.execute("""INSERT INTO beute_konfiguration(beute_id, gueltig, brutzargen, honigzargen, rahmen, notiz)
                   VALUES (%s, tstzrange(%s, NULL, '[)'), %s, %s, %s, %s)""",
                (beute_id, zeit, brutzargen, honigzargen, rahmen, notiz))


# ---------------------------------------------------------------- Geräte und Kanäle

def geraet_anlegen(cur, name, art, modell=None, dev_eui=None):
    return _eins(cur, "INSERT INTO geraet(name, art, modell, dev_eui) VALUES (%s, %s, %s, %s) RETURNING id",
                 (name, art, modell, dev_eui or None))


def geraet_aendern(cur, geraet_id, art, modell=None, dev_eui=None):
    _gibt_es(cur, "geraet", geraet_id)
    cur.execute("UPDATE geraet SET art = %s, modell = %s, dev_eui = %s WHERE id = %s", (art, modell, dev_eui or None, geraet_id))


def geraet_zuordnen(cur, geraet_id, zeit, volk_id=None, stand_id=None):
    """Gerät ab zeit einem Volk (Stockwaage) oder Stand (Umweltgerät) zuordnen; ohne Ziel nur die Zuordnung beenden."""
    _gibt_es(cur, "geraet", geraet_id)
    if volk_id and stand_id:
        raise Konflikt("entweder Volk oder Stand")
    if volk_id:
        _gibt_es(cur, "volk", volk_id)
        cur.execute("SELECT aufgeloest_am FROM volk WHERE id = %s", (volk_id,))
        a = cur.fetchone()["aufgeloest_am"]
        if a is not None and zeit >= a:
            raise Konflikt("Volk ist zu diesem Zeitpunkt aufgelöst")
    if stand_id:
        _gibt_es(cur, "stand", stand_id)
    n = offene_beenden(cur, "geraet_zuordnung", "geraet_id", geraet_id, zeit, pflicht=not (volk_id or stand_id))
    if volk_id or stand_id:
        cur.execute("""INSERT INTO geraet_zuordnung(geraet_id, volk_id, stand_id, gueltig)
                       VALUES (%s, %s, %s, tstzrange(%s, NULL, '[)'))""", (geraet_id, volk_id, stand_id, zeit))
    return n


def _ziel_zum_zeitpunkt(cur, geraet_id, zeit):
    cur.execute("SELECT volk_id, stand_id FROM geraet_zuordnung WHERE geraet_id = %s AND gueltig @> %s::timestamptz",
                (geraet_id, zeit))
    r = cur.fetchone()
    if r is None:
        raise Konflikt("Gerät ist zu diesem Zeitpunkt nicht zugeordnet; zuerst einem Volk oder Stand zuordnen")
    return r


def _messstelle(cur, ziel, zone, bezeichnung=None, hoehe_cm=None, tiefe_cm=None):
    """Vorhandene Messstelle desselben Ziels mit gleicher Zone und Bezeichnung, sonst neu."""
    cur.execute("""SELECT id FROM messstelle WHERE volk_id IS NOT DISTINCT FROM %(v)s AND stand_id IS NOT DISTINCT FROM %(s)s
                     AND zone = %(z)s AND bezeichnung IS NOT DISTINCT FROM %(b)s
                     AND hoehe_cm IS NOT DISTINCT FROM %(h)s AND tiefe_cm IS NOT DISTINCT FROM %(t)s ORDER BY id LIMIT 1""",
                {"v": ziel["volk_id"], "s": ziel["stand_id"], "z": zone, "b": bezeichnung, "h": hoehe_cm, "t": tiefe_cm})
    r = cur.fetchone()
    if r:
        return r["id"]
    return _eins(cur, """INSERT INTO messstelle(volk_id, stand_id, zone, bezeichnung, hoehe_cm, tiefe_cm)
                         VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                 (ziel["volk_id"], ziel["stand_id"], zone, bezeichnung, hoehe_cm, tiefe_cm))


def kanal_anlegen(cur, geraet_id, ab, quellfeld, messgroesse, zone, bezeichnung=None, hoehe_cm=None, tiefe_cm=None,
                  faktor=1.0, versatz=0.0, sensor=None, kalibrierung=None, kalibriert_am=None, status="ungeprueft"):
    """Deutung eines Quellfelds ab 'ab'. Eine bisher offene Deutung desselben Felds endet dort (neue Zeile, z. B. nach
    Sensortausch oder neuer Kalibrierung). Die Messstelle gehört zum Ziel der Gerätezuordnung zum Zeitpunkt 'ab'."""
    _gibt_es(cur, "geraet", geraet_id)
    if zone == "boden" and tiefe_cm is None and not bezeichnung:
        raise Konflikt("Zone Boden braucht eine Tiefe in cm (z. B. 5, 20, 50), damit jede Tiefe eine eigene Messstelle bekommt")
    if tiefe_cm is not None and not 0 <= tiefe_cm <= 1000:
        raise Konflikt("Tiefe muss zwischen 0 und 1000 cm liegen")
    cur.execute("SELECT 1 FROM messgroesse WHERE code = %s", (messgroesse,))
    if cur.fetchone() is None:
        raise Konflikt(f"Messgröße {messgroesse} fehlt im Katalog")
    ziel = _ziel_zum_zeitpunkt(cur, geraet_id, ab)
    cur.execute("SELECT id FROM kanal WHERE geraet_id = %s AND quellfeld = %s AND upper_inf(gueltig)", (geraet_id, quellfeld))
    for r in cur.fetchall():
        offene_beenden(cur, "kanal", "id", r["id"], ab)
    ms = _messstelle(cur, ziel, zone, bezeichnung, hoehe_cm, tiefe_cm)
    return _eins(cur, """INSERT INTO kanal(geraet_id, quellfeld, messgroesse_code, messstelle_id, faktor, versatz, gueltig,
                                          status, sensor, kalibrierung, kalibriert_am)
                         VALUES (%s, %s, %s, %s, %s, %s, tstzrange(%s, NULL, '[)'), %s, %s, %s, %s) RETURNING id""",
                 (geraet_id, quellfeld, messgroesse, ms, faktor, versatz, ab, status, sensor, kalibrierung, kalibriert_am))


def vorlage_anwenden(cur, geraet_id, vorlage, ab):
    """Kanäle einer Gerätevorlage anlegen; Felder mit schon offener Deutung bleiben unverändert. Rückgabe: neue Kanäle."""
    if vorlage not in VORLAGEN:
        raise Konflikt(f"unbekannte Vorlage {vorlage}")
    v = VORLAGEN[vorlage]
    ziel = _ziel_zum_zeitpunkt(cur, geraet_id, ab)
    if (v["ziel"] == "volk") != (ziel["volk_id"] is not None):
        raise Konflikt(f"Vorlage {vorlage} gilt für Geräte an einem {'Volk' if v['ziel'] == 'volk' else 'Stand'}")
    fehlend = [g for _, g, _ in v["kanaele"]]
    cur.execute("SELECT code FROM messgroesse WHERE code = ANY(%s)", (fehlend,))
    fehlend = sorted(set(fehlend) - {r["code"] for r in cur.fetchall()})
    if fehlend:
        raise Konflikt("Messgrößen fehlen im Katalog (zuerst Standardkatalog übernehmen): " + ", ".join(fehlend))
    cur.execute("SELECT quellfeld FROM kanal WHERE geraet_id = %s AND upper_inf(gueltig)", (geraet_id,))
    vorhanden = {r["quellfeld"] for r in cur.fetchall()}
    neu = []
    for feld, groesse, zone in v["kanaele"]:
        if feld not in vorhanden:
            neu.append(kanal_anlegen(cur, geraet_id, ab, feld, groesse, zone))
    cur.execute("UPDATE geraet SET art = %s WHERE id = %s AND art = 'sonstiges'", (v["art"], geraet_id))
    return neu


def kanal_beenden(cur, kanal_id, zeit):
    _gibt_es(cur, "kanal", kanal_id)
    offene_beenden(cur, "kanal", "id", kanal_id, zeit, pflicht=True)


# ---------------------------------------------------------------- Übersicht für die Verwaltung

def uebersicht(cur, zeit):
    p = {"t": zeit}
    cur.execute("SELECT id, name, ort_oeffentlich FROM stand ORDER BY name")
    staende = cur.fetchall()
    cur.execute("""SELECT v.id, v.name, v.notiz, v.entstanden_am, v.aufgeloest_am,
                          b.beute_id, be.bezeichnung AS beute, be.beutentyp, k.brutzargen, k.honigzargen,
                          a.stand_id, a.platz
                   FROM volk v
                   LEFT JOIN belegung b ON b.volk_id = v.id AND b.gueltig @> %(t)s
                   LEFT JOIN beute be ON be.id = b.beute_id
                   LEFT JOIN beute_konfiguration k ON k.beute_id = b.beute_id AND k.gueltig @> %(t)s
                   LEFT JOIN aufstellung a ON a.beute_id = b.beute_id AND a.gueltig @> %(t)s
                   ORDER BY v.aufgeloest_am IS NOT NULL, v.name""", p)
    voelker = cur.fetchall()
    cur.execute("""SELECT g.id, g.name, g.art, g.modell, g.dev_eui,
                          z.volk_id, z.stand_id, lower(z.gueltig) AS zugeordnet_ab,
                          (SELECT max(empfangen) FROM rohnachricht r WHERE r.geraet_id = g.id) AS letzte
                   FROM geraet g LEFT JOIN geraet_zuordnung z ON z.geraet_id = g.id AND z.gueltig @> %(t)s
                   ORDER BY g.name""", p)
    geraete = cur.fetchall()
    cur.execute("""SELECT k.id, k.geraet_id, k.quellfeld, k.messgroesse_code, k.faktor, k.versatz, k.status, k.sensor,
                          lower(k.gueltig) AS von, upper(k.gueltig) AS bis, ms.zone, ms.bezeichnung, ms.tiefe_cm
                   FROM kanal k LEFT JOIN messstelle ms ON ms.id = k.messstelle_id
                   ORDER BY k.geraet_id, k.quellfeld, lower(k.gueltig)""")
    kanaele = cur.fetchall()
    cur.execute("""SELECT q.geraet_id, q.quellfeld, q.anzahl, q.zuerst, q.zuletzt FROM quellfeld_ohne_kanal q
                   WHERE NOT EXISTS (SELECT 1 FROM kanal k WHERE k.geraet_id = q.geraet_id AND k.quellfeld = q.quellfeld)
                   ORDER BY q.geraet_id, q.quellfeld""")
    unbenannt = cur.fetchall()
    for g in geraete:
        g["kanaele"] = [k for k in kanaele if k["geraet_id"] == g["id"]]
        g["unbenannt"] = [u for u in unbenannt if u["geraet_id"] == g["id"] and not ist_steuerfeld(u["quellfeld"])]
    cur.execute("SELECT code, name, einheit, semantik, verdichtung, achse, darstellung, farbe, oeffentlich "
                "FROM messgroesse ORDER BY achse, code")
    return {"zeit": zeit, "staende": staende, "voelker": voelker, "geraete": geraete, "messgroessen": cur.fetchall(),
            "vorlagen": {k: {"name": v["name"], "ziel": v["ziel"], "felder": [f for f, _, _ in v["kanaele"]]}
                         for k, v in VORLAGEN.items()}}
