#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Tests für server/plattform/beep_stockkarte_import.py (BEEP-Kontoexport → Stand, Völker, Durchsichten).
Teil 1 ohne Datenbank (xlsx-Leser, Umrechnungen), Teil 2 mit leerer Datenbank:
    BIENEN_TEST_DSN="host=… dbname=bienen_test user=…" python3 tests/plattform/test_beep_stockkarte.py
Die Testdatei wird hier erzeugt; Spaltennamen und Wertformen wie im echten Export vom 23.10.2026.
"""
import os
import pathlib
import sys
import tempfile
import zipfile
from datetime import date, datetime, timedelta, timezone
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

HIER = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parents[1] / "server" / "plattform"))
import beep_stockkarte_import as bi  # noqa: E402

DSN = os.environ.get("BIENEN_TEST_DSN", "")
anz = fehler = 0


def pruefe(name, ok, info=""):
    global anz, fehler
    anz += 1
    if not ok:
        fehler += 1
        print(f"FEHL - {name}\n       {info}")


def xlsx(pfad, blaetter):
    """Minimale xlsx wie BEEP (gemeinsame Texte, Zahlen, Wahrheitswerte)."""
    texte, idx = [], {}

    def zelle(r, c, w):
        ref = f"{chr(65 + c) if c < 26 else 'A' + chr(65 + c - 26)}{r}"
        if isinstance(w, bool):
            return f'<c r="{ref}" t="b"><v>{int(w)}</v></c>'
        if isinstance(w, (int, float)):
            return f'<c r="{ref}"><v>{w}</v></c>'
        if w not in idx:
            idx[w] = len(texte)
            texte.append(w)
        return f'<c r="{ref}" t="s"><v>{idx[w]}</v></c>'
    m = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    r_ns = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    with zipfile.ZipFile(pfad, "w") as z:
        sheets, rels = [], []
        for n, (name, zeilen) in enumerate(blaetter.items(), start=1):
            kopf = list(dict.fromkeys(k for zl in zeilen for k in zl))
            xml_zeilen = ["<row>" + "".join(zelle(1, c, k) for c, k in enumerate(kopf)) + "</row>"]
            for r, zl in enumerate(zeilen, start=2):
                xml_zeilen.append("<row>" + "".join(zelle(r, c, zl[k]) for c, k in enumerate(kopf) if zl.get(k) is not None) + "</row>")
            z.writestr(f"xl/worksheets/sheet{n}.xml", f'<worksheet {m}><sheetData>{"".join(xml_zeilen)}</sheetData></worksheet>')
            sheets.append(f'<sheet name="{escape(name)}" sheetId="{n}" r:id="rId{n}"/>')
            rels.append(f'<Relationship Id="rId{n}" Target="worksheets/sheet{n}.xml" Type="x"/>')
        z.writestr("xl/workbook.xml", f'<workbook {m} {r_ns}><sheets>{"".join(sheets)}</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<sst {m}>' + "".join(f"<si><t>{escape(t)}</t></si>" for t in texte) + "</sst>")


V = "Störungen > Zählung > Varroa > "
EXPORT = {
    "Apiaries": [{"Location_id": 14746, "Name": "Hauptstand am Haus", "City": "Radeberg", "Created at": "2026-10-04 04:25:29"}],
    "Hives": [
        {"Hive_id": 87152, "Name": "Volk 5", "Type": "segeberger", "Location_id": 14746, "Queen name": "Blau 2025",
         "Queen fertilized": 1, "Brood layers": 1, "Honey layers": 0, "Frames total": 11, "Created at": "2026-10-04 04:25:30"},
        {"Hive_id": 87155, "Name": "Volk 8", "Type": "segeberger", "Location_id": 14746, "Queen name": "Weiß 2026",
         "Queen birth": "2025-05-01", "Brood layers": 2, "Frames total": 22, "Created at": "2026-10-04 04:25:30"},
        {"Hive_id": 87203, "Name": "Wetterstation", "Type": "custom", "Location_id": 14746, "Created at": "2026-10-10 07:01:48"},
    ],
    "Inspections": [
        {"Inspection_id": 1, "Created at": "2026-10-03 12:00:00", "Hive_id": 87152, "Hive name": "Volk 5",
         "Störungen > Varroa > Zählung": "Yes", V + "Anmerkung": "Natürlicher Milbenfall (Windel), Milben pro Tag",
         V + "natürlicher Fall": "89 p/d"},
        {"Inspection_id": 2, "Created at": "2026-10-07 12:00:00", "Hive_id": 87152, "Hive name": "Volk 5",
         "General impression": "8-|", "Notes": "Stocktemperatur oben: 26 °C", "Bienenvolk > Brut > Brutwaben": 2,
         "Bienenvolk > Königin > Anwesenheit": "Yes", "Futter > Vorrat > Honig > Anzahl der Rähmchen": 8},
        {"Inspection_id": 3, "Created at": "2026-10-08 12:00:00", "Hive_id": 87152, "Hive name": "Volk 5",
         "Störungen > Varroa > Behandlung": "Yes", "Störungen > Behandlung > Varroa > Heilmittel": "Ameisensäure",
         "Störungen > Behandlung > Varroa > Anmerkung": "AS-Behandlung (Verdunster) beendet"},
        {"Inspection_id": 4, "Created at": "2026-10-15 17:44:15", "Hive_id": 87155, "Hive name": "Volk 8",
         "Notes": "Königin gekäfigt", "Reminder": "Königin gekäfigt", "Reminder date": "2026-11-05 07:00:00",
         "Needs attention": "Yes", "Bienenvolk > Brut > Status > Alle Stadien": "Yes"},
        {"Inspection_id": 5, "Created at": "2026-10-17 08:00:02", "Hive_id": 87152, "Hive name": "Volk 5",
         "Notes": "ca. 20 kg Futtergabe", "Futter > Fütterung > Menge (Gewicht)": "20000 gr",
         "Futter > Fütterung > Typ": "Inverzuckersirup"},
        {"Inspection_id": 6, "Created at": "2026-10-18 12:00:00", "Hive_id": 87155, "Hive name": "Volk 8",
         V + "natürlicher Fall": "viele"},
        {"Inspection_id": 7, "Created at": "2026-10-18 12:00:00", "Hive_id": 87152, "Hive name": "Volk 5",
         "Notes": "gelöscht", "Deleted at": "2026-10-19 10:00:00"},
    ],
}

# ---------------------------------------------------------------- ohne Datenbank
with tempfile.TemporaryDirectory() as tmp:
    pfad = pathlib.Path(tmp) / "export.xlsx"
    xlsx(pfad, EXPORT)
    gelesen = bi.blaetter(pfad)
pruefe("xlsx-Leser: Blätter, Zahlen, Texte", gelesen["Hives"][0]["Frames total"] == 11 and gelesen["Hives"][1]["Name"] == "Volk 8"
       and gelesen["Inspections"][1]["Notes"] == "Stocktemperatur oben: 26 °C" and len(gelesen["Inspections"]) == 7, gelesen["Hives"][0])
pruefe("xlsx-Leser: echter BEEP-Export", (lambda p: not p.exists() or len(bi.blaetter(p)["Inspections"]) == 175)(
       pathlib.Path("/mnt/user-data/uploads/beep-export-user-9925-a0mtB9m0YS8YlZBxFtdI.xlsx")))
t, g = bi.zeit_ortszeit("2026-10-17 08:00:02")
pruefe("Durchsichtszeit = Ortszeit (MESZ)", t == datetime(2026, 10, 17, 6, 0, 2, tzinfo=timezone.utc) and g == "exakt", t)
pruefe("12:00:00 = nur Datum", bi.zeit_ortszeit("2026-10-18 12:00:00")[1] == "nur_datum")
pruefe("Königin aus Name", bi.koenigin_aus_name("Blau 2025") == ("Blau", 2025) and bi.koenigin_aus_name("Weiß 2026") == ("Weiß", 2026)
       and bi.koenigin_aus_name("X") == (None, None))
pruefe("Futtermenge", bi.menge_kg("20000 gr") == (20.0, "kg") and bi.menge_kg("2,5 kg") == (2.5, "kg") and bi.menge_kg("viel") == (None, None))
pruefe("Milben je Tag", bi.milben_je_tag("89 p/d") == 89 and bi.milben_je_tag("viele") is None)

# ---------------------------------------------------------------- mit Datenbank
if not DSN:
    print("NICHT GELAUFEN: Datenbankteil (BIENEN_TEST_DSN fehlt)")
else:
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute((HIER.parents[1] / "server" / "datenbank" / "schema.sql").read_text(encoding="utf-8"))
        c.execute("INSERT INTO bienen.stand(name) VALUES ('Hauptstand am Haus')")
        c.execute("INSERT INTO bienen.volk(name) VALUES ('Volk 8')")          # von Hand angelegt: wird verknüpft
    with tempfile.TemporaryDirectory() as tmp:
        pfad = pathlib.Path(tmp) / "export.xlsx"
        xlsx(pfad, EXPORT)
        pruefe("Prüflauf nimmt alles zurück", bi.main([str(pfad), "--dsn", DSN, "--pruefen"]) == 0)
        with psycopg.connect(DSN) as c:
            pruefe("… nichts gespeichert", c.execute("SELECT count(*) FROM bienen.durchsicht").fetchone()[0] == 0)
        pruefe("Übernahme", bi.main([str(pfad), "--dsn", DSN]) == 0)
        with psycopg.connect(DSN, row_factory=dict_row) as c:
            c.execute("SET search_path = bienen, public")
            q = lambda s, p=None: c.execute(s, p).fetchall()  # noqa: E731
            pruefe("Stand verknüpft, kein zweiter", q("SELECT count(*) AS n FROM stand")[0]["n"] == 1)
            v = {r["name"]: r["id"] for r in q("SELECT id, name FROM volk")}
            pruefe("Völker: von Hand angelegtes Volk 8 verknüpft, Wetterstation übergangen", sorted(v) == ["Volk 5", "Volk 8"], v)
            b = q("""SELECT v.name, lower(be.gueltig) AS ab, bk.brutzargen, bk.rahmen, a.stand_id FROM volk v JOIN belegung be ON be.volk_id = v.id
                     JOIN beute_konfiguration bk ON bk.beute_id = be.beute_id JOIN aufstellung a ON a.beute_id = be.beute_id ORDER BY 1""")
            pruefe("Beute ab erster (rückwirkender) Durchsicht bzw. Anlage in BEEP",
                   [(r["name"], r["ab"], r["brutzargen"], r["rahmen"]) for r in b] ==
                   [("Volk 5", datetime(2026, 10, 3, 10, tzinfo=timezone.utc), 1, 11),
                    ("Volk 8", datetime(2026, 10, 4, 4, 25, 30, tzinfo=timezone.utc), 2, 22)], b)
            k = {r["name"]: (r["farbe"], r["jahrgang"], r["begattet"]) for r in
                 q("SELECT v.name, k.farbe, k.jahrgang, k.begattet FROM koenigin k JOIN koenigin_volk kv ON kv.koenigin_id = k.id JOIN volk v ON v.id = kv.volk_id")}
            pruefe("Königinnen (Jahrgang aus Geburtsdatum vor Name)", k == {"Volk 5": ("Blau", 2025, True), "Volk 8": ("Weiß", 2025, None)}, k)
            d = q("""SELECT d.id, v.name, d.zeit, d.zeitgenauigkeit, d.notiz, d.quelle FROM durchsicht d JOIN volk v ON v.id = d.volk_id ORDER BY d.zeit""")
            pruefe("Durchsichten: reine Varroa-Zählung und gelöschte ohne Durchsicht", len(d) == 4 and all(x["quelle"] == "beep_import" for x in d), d)
            w = {r["code"]: r["w"] for r in q("""SELECT m.code, coalesce(x.wert_zahl::text, x.wert_bool::text, x.wert_text) AS w
                     FROM durchsicht_wert x JOIN merkmal m ON m.id = x.merkmal_id WHERE x.durchsicht_id = %s""", (d[0]["id"],))}
            pruefe("Werte: Brutwaben, Futterwaben", w == {"brutwaben": "2", "futterwaben": "8"}, w)
            pruefe("Notiz: Original + alles ohne Gegenstück wörtlich", d[0]["notiz"].splitlines() ==
                   ["Stocktemperatur oben: 26 °C", "BEEP: General impression: 8-|", "BEEP: Bienenvolk > Königin > Anwesenheit: ja"], d[0]["notiz"])
            pruefe("Alle Stadien → Stifte, offene und verdeckelte Brut", {r["code"] for r in q("""SELECT m.code FROM durchsicht_wert x
                     JOIN merkmal m ON m.id = x.merkmal_id WHERE x.durchsicht_id = %s AND x.wert_bool""", (d[2]["id"],))}
                   == {"stifte", "offene_brut", "verdeckelte_brut"})
            pruefe("Zeit Volk 8 exakt (Ortszeit)", d[2]["zeit"] == datetime(2026, 10, 15, 15, 44, 15, tzinfo=timezone.utc)
                   and d[2]["zeitgenauigkeit"] == "exakt", d[2])
            m = q("SELECT art, menge, einheit, mittel, notiz, durchsicht_id, quelle FROM massnahme ORDER BY lower(zeitraum)")
            pruefe("Behandlung und Fütterung mit Durchsicht verknüpft", [(x["art"], x["menge"], x["einheit"], x["mittel"]) for x in m] ==
                   [("behandlung", None, None, "Ameisensäure"), ("fuetterung", 20, "kg", "Inverzuckersirup")]
                   and all(x["durchsicht_id"] and x["quelle"] == "beep_import" for x in m), m)
            vm = q("SELECT lower(zeitraum) AS von, upper(zeitraum) AS bis, milben, methode, zeitgenauigkeit, anmerkung FROM varroa_messung")
            pruefe("Varroa: Rate als Ein-Tages-Windel, geschätzt, Original in der Anmerkung", len(vm) == 1 and vm[0]["milben"] == 89
                   and vm[0]["bis"] - vm[0]["von"] == timedelta(days=1) and vm[0]["zeitgenauigkeit"] == "geschaetzt"
                   and "89 p/d" in vm[0]["anmerkung"] and vm[0]["methode"] == "windel", vm)
            a = q("SELECT faellig_am, text, volk_id FROM aufgabe")
            pruefe("Erinnerung → Aufgabe", [(x["faellig_am"], x["text"], x["volk_id"]) for x in a] == [(date(2026, 11, 5), "Königin gekäfigt", v["Volk 8"])], a)
        pruefe("zweiter Lauf", bi.main([str(pfad), "--dsn", DSN]) == 0)
        with psycopg.connect(DSN) as c:
            n = c.execute("""SELECT (SELECT count(*) FROM bienen.volk), (SELECT count(*) FROM bienen.durchsicht), (SELECT count(*) FROM bienen.massnahme),
                             (SELECT count(*) FROM bienen.varroa_messung), (SELECT count(*) FROM bienen.aufgabe), (SELECT count(*) FROM bienen.koenigin)""").fetchone()
        pruefe("zweiter Lauf legt nichts doppelt an", n == (2, 4, 2, 1, 1, 2), n)

print(f"{'OK' if not fehler else 'FEHLER'}: BEEP-Stockkarte {anz - fehler} von {anz} Prüfungen bestanden")
sys.exit(1 if fehler else 0)
