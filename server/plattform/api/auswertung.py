# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Auswertungen für Cockpit und Völkervergleich (Vorbild beelogger; Konzept 0.2 §5.4 und §6).

* vorher_nachher(): Kennzahlen eines Volks in einem Fenster vor dem Beginn und nach dem Ende eines Ereignisses
  (Maßnahme, Durchsicht, Varroa-Messung). Gewicht als mittlere Tagesbilanz (Sicht gewicht_tagesbilanz),
  Temperaturen als Mittelwert je Messstelle, Luft am Stand, Milbenfall pro Tag. Nur Mittelwerte, keine Deutung.
* vergleich(): mehrere Völker über denselben Zeitraum – Nachtmedian (Tagesreferenz), Tagesbilanz, Summen und
  Plausibilitätshinweise (Sprünge ohne Eingriff, Sensor-Fehlercodes; vgl. Befund PLT26-11).
Die Kennwerte kommen aus den Sichten des Schemas (berechnung@version), nicht aus Python.
"""
from datetime import timedelta

from .stammdaten import NichtGefunden

SPRUNG_KG = 1.0                       # |Tagesbilanz| darüber ohne Eingriff = Hinweis (keine biologische Diagnose)
FEHLCODES_DS18B20 = (-127.0, 85.0)    # Fehlerwerte des Temperatursensors DS18B20


def ereignis_zeitraum(cur, art, id_):
    """Zeitraum und Beschreibung eines Stockkarten-Ereignisses: (volk_id, beginn, ende, text)."""
    if art == "massnahme":
        cur.execute("""SELECT volk_id, lower(zeitraum) AS a, upper(zeitraum) AS b, art AS text, mittel
                       FROM massnahme WHERE id = %s""", (id_,))
    elif art == "varroa":
        cur.execute("""SELECT volk_id, lower(zeitraum) AS a, upper(zeitraum) AS b, 'Varroa ' || methode AS text, NULL AS mittel
                       FROM varroa_messung WHERE id = %s""", (id_,))
    elif art == "durchsicht":
        cur.execute("SELECT volk_id, zeit AS a, zeit AS b, 'Durchsicht' AS text, NULL AS mittel FROM durchsicht WHERE id = %s", (id_,))
    else:
        raise NichtGefunden(f"Ereignisart {art} unbekannt")
    r = cur.fetchone()
    if r is None:
        raise NichtGefunden(f"{art} {id_} unbekannt")
    return r


def _mittel(cur, spalte, bezug_id, von, bis, messgroesse):
    from psycopg import sql
    cur.execute(sql.SQL("""SELECT m.messstelle_id, ms.zone, ms.bezeichnung, avg(m.wert) AS mittel, count(*) AS n
                           FROM messwert_bezug m LEFT JOIN messstelle ms ON ms.id = m.messstelle_id
                           WHERE m.{} = %(id)s AND m.messgroesse_code = %(g)s AND m.zeit >= %(von)s AND m.zeit < %(bis)s
                             AND m.qualitaet <> 'ungueltig'
                           GROUP BY 1, 2, 3 ORDER BY 1""").format(sql.Identifier(spalte)),
                {"id": bezug_id, "g": messgroesse, "von": von, "bis": bis})
    return {r["messstelle_id"]: r for r in cur.fetchall()}


ZONEN = {"brutnest": "Brutnest", "deckel": "Deckel", "aussen": "außen", "waage": "Waage", "flugloch": "Flugloch",
         "boden": "Boden", "luft_stand": "Luft am Stand", "elektronik": "Elektronik", "funk": "Funk"}


def _ort(groesse, r):
    """'Temperatur Boden 5 cm', 'Temperatur Luft am Stand' – Messgröße, Zone und Bezeichnung wie in der Oberfläche."""
    teile = [groesse, ZONEN.get(r.get("zone"), r.get("zone") or "")]
    if r.get("bezeichnung") and r["bezeichnung"] not in teile:
        teile.append(r["bezeichnung"])
    return " ".join(t for t in teile if t)


def vorher_nachher(cur, volk_id, art, id_, tage):
    e = ereignis_zeitraum(cur, art, id_)
    if e["volk_id"] != volk_id:
        raise NichtGefunden("Ereignis gehört zu einem anderen Volk")
    f = timedelta(days=tage)
    vorher, nachher = (e["a"] - f, e["a"]), (e["b"], e["b"] + f)
    zeilen = []

    def zeile(name, einheit, v, n, nv, nn, berechnung=None, **mehr):
        zeilen.append({"name": name, "einheit": einheit, "vorher": v, "nachher": n, "n_vorher": nv, "n_nachher": nn,
                       "delta": (n - v) if v is not None and n is not None else None, "berechnung": berechnung, **mehr})

    # Gewicht: mittlere Tagesbilanz der Tage im Fenster (Tag t = Referenz t − Referenz t−1, Ortszeit). Tage mit
    # Eingriff (auch der des Ereignisses selbst, z. B. Tarieren) zählen nicht: ihr Sprung ist keine Wirkung (L8).
    def bilanz(a, b):
        cur.execute("""SELECT avg(bilanz_kg) FILTER (WHERE NOT mit_eingriff) AS m, count(*) FILTER (WHERE NOT mit_eingriff) AS n,
                              count(*) FILTER (WHERE mit_eingriff) AS eingriff
                       FROM gewicht_tagesbilanz
                       WHERE volk_id = %(v)s AND tag > (%(a)s AT TIME ZONE 'Europe/Berlin')::date
                         AND tag <= (%(b)s AT TIME ZONE 'Europe/Berlin')::date""", {"v": volk_id, "a": a, "b": b})
        return cur.fetchone()
    bv, bn = bilanz(*vorher), bilanz(*nachher)
    zeile("Gewicht, Tagesbilanz", "kg/Tag", bv["m"], bn["m"], bv["n"], bn["n"], "gewicht_tagesbilanz@1",
          eingriff_vorher=bv["eingriff"], eingriff_nachher=bn["eingriff"])

    # Temperaturen je Messstelle des Volks
    tv, tn = _mittel(cur, "volk_id", volk_id, *vorher, "temperatur"), _mittel(cur, "volk_id", volk_id, *nachher, "temperatur")
    for ms in sorted(set(tv) | set(tn), key=lambda x: (x is None, x)):
        r = tv.get(ms) or tn.get(ms)
        zeile(_ort("Temperatur", r), "°C",
              tv[ms]["mittel"] if ms in tv else None, tn[ms]["mittel"] if ms in tn else None,
              tv[ms]["n"] if ms in tv else 0, tn[ms]["n"] if ms in tn else 0)

    # Luft am Stand des Volks (zum Beginn des Ereignisses)
    cur.execute("SELECT stand_von_volk(%s, %s) AS s", (volk_id, e["a"]))
    stand = cur.fetchone()["s"]
    if stand is not None:
        lv, ln = _mittel(cur, "stand_id", stand, *vorher, "temperatur"), _mittel(cur, "stand_id", stand, *nachher, "temperatur")
        for ms in sorted(set(lv) | set(ln), key=lambda x: (x is None, x)):
            r = lv.get(ms) or ln.get(ms)
            zeile(_ort("Temperatur", r), "°C",
                  lv[ms]["mittel"] if ms in lv else None, ln[ms]["mittel"] if ms in ln else None,
                  lv[ms]["n"] if ms in lv else 0, ln[ms]["n"] if ms in ln else 0)

    # Milbenfall pro Tag (Windel), Messungen, die das Fenster überlappen
    def milben(a, b):
        cur.execute("""SELECT avg(milben_pro_tag)::float8 AS m, count(*) AS n FROM varroa_pro_tag
                       WHERE volk_id = %(v)s AND tstzrange(von, bis) && tstzrange(%(a)s, %(b)s)""", {"v": volk_id, "a": a, "b": b})
        return cur.fetchone()
    mv, mn = milben(*vorher), milben(*nachher)
    if mv["n"] or mn["n"]:
        zeile("Milbenfall", "Milben/Tag", mv["m"], mn["m"], mv["n"], mn["n"], "varroa_pro_tag@1")
    return {"ereignis": {"art": art, "id": id_, "text": e["text"], "mittel": e["mittel"], "von": e["a"], "bis": e["b"]},
            "fenster_tage": tage, "vorher": {"von": vorher[0], "bis": vorher[1]}, "nachher": {"von": nachher[0], "bis": nachher[1]},
            "kennzahlen": zeilen}


def vergleich(cur, volk_ids, von, bis):
    p = {"ids": volk_ids, "von": von, "bis": bis}
    cur.execute("SELECT id, name, aufgeloest_am FROM volk WHERE id = ANY(%(ids)s) ORDER BY name", p)
    voelker = {v["id"]: {**v, "tagesreferenz": [], "tagesbilanz": [], "messpunkte": 0, "fehlcodes": 0} for v in cur.fetchall()}
    if not voelker:
        return []
    cur.execute("""SELECT volk_id, tag, referenz_kg, werte, berechnung FROM gewicht_tagesreferenz
                   WHERE volk_id = ANY(%(ids)s) AND tag >= (%(von)s AT TIME ZONE 'Europe/Berlin')::date
                     AND tag < (%(bis)s AT TIME ZONE 'Europe/Berlin')::date ORDER BY volk_id, tag""", p)
    for r in cur.fetchall():
        voelker[r.pop("volk_id")]["tagesreferenz"].append(r)
    cur.execute("""SELECT volk_id, tag, bilanz_kg, mit_eingriff, berechnung FROM gewicht_tagesbilanz
                   WHERE volk_id = ANY(%(ids)s) AND tag >= (%(von)s AT TIME ZONE 'Europe/Berlin')::date
                     AND tag < (%(bis)s AT TIME ZONE 'Europe/Berlin')::date ORDER BY volk_id, tag""", p)
    for r in cur.fetchall():
        voelker[r.pop("volk_id")]["tagesbilanz"].append(r)
    cur.execute("""SELECT volk_id, count(*) FILTER (WHERE messgroesse_code = 'gewicht') AS messpunkte,
                          count(*) FILTER (WHERE messgroesse_code = 'temperatur' AND wert = ANY(%(codes)s)) AS fehlcodes
                   FROM messwert_bezug WHERE volk_id = ANY(%(ids)s) AND zeit >= %(von)s AND zeit < %(bis)s
                   GROUP BY volk_id""", {**p, "codes": list(FEHLCODES_DS18B20)})
    for r in cur.fetchall():
        voelker[r["volk_id"]].update(messpunkte=r["messpunkte"], fehlcodes=r["fehlcodes"])
    aus = []
    for v in voelker.values():
        b = v["tagesbilanz"]
        v["summe_kg"] = sum(x["bilanz_kg"] for x in b) if b else None
        v["summe_ohne_eingriff_kg"] = sum(x["bilanz_kg"] for x in b if not x["mit_eingriff"]) if b else None
        v["spruenge"] = [x["tag"] for x in b if not x["mit_eingriff"] and abs(x["bilanz_kg"]) > SPRUNG_KG]
        v["letzte_referenz"] = v["tagesreferenz"][-1] if v["tagesreferenz"] else None
        aus.append(v)
    return aus
