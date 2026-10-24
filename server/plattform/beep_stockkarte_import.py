#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Stand, Völker, Beuten, Königinnen und Durchsichten aus dem BEEP-Kontoexport (xlsx) übernehmen.

Wiederholbar: Jedes übernommene BEEP-Objekt steht in extern_ref (system 'beep'); ein zweiter Lauf legt nichts
doppelt an. Vorhandene Völker gleichen Namens (z. B. von Hand angelegt) werden verknüpft statt verdoppelt.
Läuft in einer Transaktion; --pruefen zeigt das Ergebnis und nimmt alles zurück.

Abbildung (Annahmen sind markiert):
- Apiary → Stand (gleicher Name wird verknüpft).
- Hive → Volk ohne Entstehungsdatum (unbekannt) mit eigener Beute; Beute, Konfiguration (Brut-/Honigzargen,
  Rähmchen), Belegung und Aufstellung ab dem Anlegen in BEEP bzw. ab der ersten (rückwirkend erfassten) Durchsicht. Hives vom Typ 'custom' (z. B. die Wetterstation)
  sind keine Völker und werden übergangen.
- Queen → Königin (Farbe und Jahrgang aus dem Namen, z. B. 'Blau 2025'; begattet).
- Inspection → Durchsicht (quelle 'beep_import') nur, wenn sie mehr als eine Varroa-Zählung enthält:
  Brutwaben → brutwaben; 'Alle Stadien' → stifte, offene und verdeckelte Brut; Honig-Rähmchen im Vorrat →
  futterwaben. Alles ohne Gegenstück in der Checkliste steht wörtlich in der Notiz ('BEEP: Feld: Wert').
- Varroa 'natürlicher Fall n p/d' → Windel-Messung über einen Tag bis zur Durchsicht, n Milben
  (ANNAHME: Rate je Tag als Ein-Tages-Fenster; Zeitgenauigkeit 'geschaetzt'; Originaltext in der Anmerkung).
- Behandlung (Heilmittel) und Fütterung (Menge, Typ) → Maßnahme zum Zeitpunkt der Durchsicht.
- Erinnerung → Aufgabe zum Erinnerungsdatum.
- Zeiten: Durchsichten wie in der App eingegeben, also Ortszeit Europe/Berlin (Beleg: Fütterung 17.10. 08:00
  gegen Gewichtssprung 08:10–08:20 MESZ); '12:00:00' ist BEEPs Uhrzeit für reine Datumsangaben → 'nur_datum'.
  Systemzeiten (Hive angelegt) sind UTC.

Aufruf (als Benutzer bienen):
    python3 server/plattform/beep_stockkarte_import.py --dsn "dbname=bienen user=bienen" beep-export-….xlsx [--pruefen]
"""
import argparse
import re
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api import stammdaten as sd  # noqa: E402
from api import stockkarte as sk  # noqa: E402

ORTSZEIT = ZoneInfo("Europe/Berlin")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
BEUTENTYP = {"segeberger": "Segeberger", "einraumbeute": "Einraumbeute", "dadant": "Dadant", "zander": "Zander",
             "langstroth": "Langstroth", "deutsch_normal": "Deutsch Normal"}
FARBEN = ("Weiß", "Gelb", "Rot", "Grün", "Blau")


# ---------------------------------------------------------------- xlsx lesen (ohne Zusatzpaket)

def _spalte(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def blaetter(pfad):
    """{Blattname: [ {Spalte: Wert}, … ]} – erste Zeile ist die Kopfzeile; Zahlen als int/float, Wahrheitswerte als bool."""
    with zipfile.ZipFile(pfad) as z:
        texte = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                texte.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        aus = {}
        for s in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", NS):
            ziel = rels[s.get(f"{{{NS['r']}}}id")].lstrip("/")
            ziel = ziel if ziel.startswith("xl/") else "xl/" + ziel
            zeilen = []
            for row in ET.fromstring(z.read(ziel)).iter(f"{{{NS['m']}}}row"):
                werte = {}
                for c in row.findall("m:c", NS):
                    t, v = c.get("t"), c.find("m:v", NS)
                    if t == "inlineStr":
                        w = "".join(x.text or "" for x in c.iter(f"{{{NS['m']}}}t"))
                    elif v is None:
                        continue
                    elif t == "s":
                        w = texte[int(v.text)]
                    elif t == "b":
                        w = v.text == "1"
                    elif t == "str":
                        w = v.text
                    else:
                        w = float(v.text)
                        w = int(w) if w.is_integer() else w
                    werte[_spalte(c.get("r"))] = w
                zeilen.append(werte)
            if zeilen:
                kopf = zeilen[0]
                aus[s.get("name")] = [{kopf[i]: w for i, w in z_.items() if i in kopf} for z_ in zeilen[1:]]
            else:
                aus[s.get("name")] = []
    return aus


# ---------------------------------------------------------------- Umrechnungen

def zeit_utc(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def zeit_ortszeit(text):
    """Durchsichtszeit (Ortszeit) → (Zeitpunkt, Zeitgenauigkeit)."""
    t = datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ORTSZEIT)
    return t, ("nur_datum" if text.endswith(" 12:00:00") else "exakt")


def koenigin_aus_name(name):
    """'Blau 2025' → (Farbe, Jahrgang); unbekannte Teile None."""
    farbe = next((f for f in FARBEN if name and f.lower() in name.lower()), None)
    jahr = re.search(r"\b(19|20)\d\d\b", name or "")
    return farbe, int(jahr.group(0)) if jahr else None


def menge_kg(text):
    """'20000 gr' → (20.0, 'kg'); '2 kg' → (2.0, 'kg'); sonst (None, None)."""
    m = re.match(r"^\s*([\d.,]+)\s*(gr|g|kg)\s*$", str(text or ""))
    if not m:
        return None, None
    wert = float(m.group(1).replace(",", "."))
    return (wert / 1000 if m.group(2) in ("g", "gr") else wert), "kg"


def milben_je_tag(text):
    m = re.match(r"^\s*(\d+)\s*p/d\s*$", str(text or ""))
    return int(m.group(1)) if m else None


JA = ("Yes", True, 1)
BELEGT = {"Bienenvolk > Brut > Brutwaben", "Bienenvolk > Brut > Status > Alle Stadien",
          "Futter > Vorrat > Honig > Anzahl der Rähmchen", "Notes", "Reminder", "Reminder date",
          "Störungen > Varroa > Zählung", "Störungen > Zählung > Varroa > natürlicher Fall",
          "Störungen > Zählung > Varroa > Anmerkung", "Störungen > Varroa > Behandlung",
          "Störungen > Behandlung > Varroa > Heilmittel", "Störungen > Behandlung > Varroa > Anmerkung",
          "Futter > Fütterung > Menge (Gewicht)", "Futter > Fütterung > Typ"}
OHNE_INHALT = {"Inspection_id", "Owner", "Created at", "Hive_id", "Hive name", "Location_id", "Deleted at"}


# ---------------------------------------------------------------- Übernahme

class Import:
    def __init__(self, cur):
        self.cur = cur
        self.b = {k: 0 for k in ("stand_neu", "stand_verknuepft", "volk_neu", "volk_verknuepft", "koenigin",
                                 "durchsicht", "varroa", "behandlung", "fuetterung", "aufgabe", "schon_da",
                                 "uebergangen")}
        self.hinweise = []

    def ref(self, typ, extern_id):
        self.cur.execute("SELECT intern_id FROM extern_ref WHERE system = 'beep' AND typ = %s AND extern_id = %s",
                         (typ, str(extern_id)))
        r = self.cur.fetchone()
        return None if r is None else r["intern_id"]

    def ref_setzen(self, typ, extern_id, intern_typ, intern_id):
        self.cur.execute("INSERT INTO extern_ref(system, typ, extern_id, intern_typ, intern_id) VALUES ('beep', %s, %s, %s, %s)",
                         (typ, str(extern_id), intern_typ, intern_id))

    def stand(self, a):
        s = self.ref("apiary", a["Location_id"])
        if s:
            return s
        self.cur.execute("SELECT id FROM stand WHERE name = %s", (a["Name"],))
        r = self.cur.fetchone()
        if r:
            s = r["id"]
            self.b["stand_verknuepft"] += 1
        else:
            s = sd.stand_anlegen(self.cur, a["Name"], a.get("City"))
            self.b["stand_neu"] += 1
        self.ref_setzen("apiary", a["Location_id"], "stand", s)
        return s

    def volk(self, h, stand_id, platz, erste_durchsicht=None):
        v = self.ref("hive", h["Hive_id"])
        if v:
            self.b["schon_da"] += 1
            return v
        ab = zeit_utc(h["Created at"])
        if erste_durchsicht is not None and erste_durchsicht < ab:   # in BEEP rückwirkend erfasste Durchsichten
            ab = erste_durchsicht
        self.cur.execute("SELECT id FROM volk WHERE name = %s AND aufgeloest_am IS NULL", (h["Name"],))
        gleich = self.cur.fetchall()
        if len(gleich) == 1:
            v = gleich[0]["id"]
            self.b["volk_verknuepft"] += 1
        else:
            if len(gleich) > 1:
                self.hinweise.append(f"{h['Name']}: mehrere Völker gleichen Namens – neues Volk angelegt")
            v = sk._eins(self.cur, "INSERT INTO volk(name, notiz) VALUES (%s, %s) RETURNING id",
                         (h["Name"], f"aus BEEP übernommen (Hive {h['Hive_id']}); Entstehung unbekannt"))
            self.b["volk_neu"] += 1
        self.cur.execute("SELECT 1 FROM belegung WHERE volk_id = %s", (v,))
        if self.cur.fetchone() is None:
            beute = {"bezeichnung": f"Beute {h['Name']}", "beutentyp": BEUTENTYP.get(h.get("Type"), h.get("Type")),
                     "brutzargen": h.get("Brood layers"), "honigzargen": h.get("Honey layers"),
                     "rahmen": h.get("Frames total")}
            b = sd.beute_anlegen(self.cur, beute, ab, stand_id, platz)
            self.cur.execute("INSERT INTO belegung(volk_id, beute_id, gueltig) VALUES (%s, %s, tstzrange(%s, NULL, '[)'))",
                             (v, b, ab))
        if h.get("Queen name"):
            self.cur.execute("SELECT 1 FROM koenigin_volk WHERE volk_id = %s", (v,))
            if self.cur.fetchone() is None:
                farbe, jahr = koenigin_aus_name(h["Queen name"])
                if h.get("Queen birth"):
                    jahr = int(str(h["Queen birth"])[:4])
                k = sk._eins(self.cur, """INSERT INTO koenigin(jahrgang, farbe, begattet, herkunft) VALUES (%s, %s, %s, %s)
                                          RETURNING id""", (jahr, farbe, bool(h.get("Queen fertilized")) or None,
                                                            f"BEEP: {h['Queen name']}"))
                self.cur.execute("""INSERT INTO koenigin_volk(koenigin_id, volk_id, gueltig, grund)
                                    VALUES (%s, %s, tstzrange(%s, NULL, '[)'), 'aus BEEP übernommen')""", (k, v, ab))
                self.b["koenigin"] += 1
        self.ref_setzen("hive", h["Hive_id"], "volk", v)
        return v

    def durchsicht(self, i, volk_id, version_id):
        if self.ref("inspection", i["Inspection_id"]) or self.ref("inspection_varroa", i["Inspection_id"]):
            self.b["schon_da"] += 1
            return
        zeit, genau = zeit_ortszeit(i["Created at"])
        werte = {}
        if isinstance(i.get("Bienenvolk > Brut > Brutwaben"), int):
            werte["brutwaben"] = i["Bienenvolk > Brut > Brutwaben"]
        if i.get("Bienenvolk > Brut > Status > Alle Stadien") in JA:
            werte.update(stifte=True, offene_brut=True, verdeckelte_brut=True)
        if isinstance(i.get("Futter > Vorrat > Honig > Anzahl der Rähmchen"), int):
            werte["futterwaben"] = i["Futter > Vorrat > Honig > Anzahl der Rähmchen"]
        zeilen = [i["Notes"]] if i.get("Notes") else []
        for k, w in i.items():
            if k in BELEGT or k in OHNE_INHALT or w in (None, ""):
                continue
            text = f"BEEP: {k}: {'ja' if w in JA else w}"
            if text not in zeilen and w != i.get("Notes"):
                zeilen.append(text)
        notiz = "\n".join(zeilen) or None
        behandlung = i.get("Störungen > Varroa > Behandlung") in JA or i.get("Störungen > Behandlung > Varroa > Heilmittel")
        fuetterung = i.get("Futter > Fütterung > Menge (Gewicht)") or i.get("Futter > Fütterung > Typ")
        d_id = None
        if werte or notiz or behandlung or fuetterung or i.get("Reminder"):
            d_id = sk.durchsicht_anlegen(self.cur, [volk_id], zeit, genau, version_id, notiz, werte)[0]
            self.cur.execute("UPDATE durchsicht SET quelle = 'beep_import' WHERE id = %s", (d_id,))
            self.ref_setzen("inspection", i["Inspection_id"], "durchsicht", d_id)
            self.b["durchsicht"] += 1
        n = milben_je_tag(i.get("Störungen > Zählung > Varroa > natürlicher Fall"))
        if n is not None:
            anm = "; ".join(x for x in (i.get("Störungen > Zählung > Varroa > Anmerkung"),
                                        f"BEEP: natürlicher Fall {n} p/d, als ein Tag übernommen") if x)
            m = sk.varroa_anlegen(self.cur, [volk_id], "windel", zeit - timedelta(days=1), zeit, n, anm, "geschaetzt")[0]
            self.cur.execute("UPDATE varroa_messung SET quelle = 'beep_import' WHERE id = %s", (m,))
            self.ref_setzen("inspection_varroa", i["Inspection_id"], "varroa_messung", m)
            self.b["varroa"] += 1
        elif i.get("Störungen > Zählung > Varroa > natürlicher Fall"):
            self.hinweise.append(f"Durchsicht {i['Inspection_id']}: Varroa-Wert "
                                 f"{i['Störungen > Zählung > Varroa > natürlicher Fall']!r} nicht verstanden – nur in BEEP")
        if behandlung:
            m = sk.massnahme_anlegen(self.cur, [volk_id], "behandlung", zeit, None, genau,
                                     mittel=i.get("Störungen > Behandlung > Varroa > Heilmittel"),
                                     notiz=i.get("Störungen > Behandlung > Varroa > Anmerkung"), durchsicht_id=d_id)[0]
            self.cur.execute("UPDATE massnahme SET quelle = 'beep_import' WHERE id = %s", (m,))
            self.ref_setzen("inspection_behandlung", i["Inspection_id"], "massnahme", m)
            self.b["behandlung"] += 1
        if fuetterung:
            menge, einheit = menge_kg(i.get("Futter > Fütterung > Menge (Gewicht)"))
            m = sk.massnahme_anlegen(self.cur, [volk_id], "fuetterung", zeit, None, genau, menge=menge, einheit=einheit,
                                     mittel=i.get("Futter > Fütterung > Typ"), durchsicht_id=d_id)[0]
            self.cur.execute("UPDATE massnahme SET quelle = 'beep_import' WHERE id = %s", (m,))
            self.ref_setzen("inspection_fuetterung", i["Inspection_id"], "massnahme", m)
            self.b["fuetterung"] += 1
        if i.get("Reminder"):
            faellig = date.fromisoformat(str(i.get("Reminder date") or i["Created at"])[:10])
            a = sk.aufgabe_anlegen(self.cur, faellig, i["Reminder"], volk_ids=[volk_id], durchsicht_id=d_id)[0]
            self.ref_setzen("inspection_aufgabe", i["Inspection_id"], "aufgabe", a)
            self.b["aufgabe"] += 1

    def lauf(self, daten):
        staende = {a["Location_id"]: self.stand(a) for a in daten.get("Apiaries", [])}
        erste = {}
        for i in daten.get("Inspections", []):
            if not i.get("Deleted at"):
                t = zeit_ortszeit(i["Created at"])[0]
                erste[i["Hive_id"]] = min(t, erste.get(i["Hive_id"], t))
        voelker = {}
        for platz, h in enumerate(sorted(daten.get("Hives", []), key=lambda x: str(x.get("Created at"))), start=1):
            if h.get("Deleted at") or h.get("Type") == "custom":
                self.b["uebergangen"] += 1
                self.hinweise.append(f"Hive {h.get('Name')!r} (Typ {h.get('Type')}) ist kein Volk – übergangen")
                continue
            if h.get("Location_id") not in staende:
                raise SystemExit(f"ABBRUCH: Hive {h.get('Name')}: Stand {h.get('Location_id')} fehlt im Export")
            voelker[h["Hive_id"]] = self.volk(h, staende[h["Location_id"]], platz, erste.get(h["Hive_id"]))
        inspektionen = sorted((i for i in daten.get("Inspections", []) if not i.get("Deleted at")),
                              key=lambda x: str(x["Created at"]))
        if inspektionen:
            beginn = zeit_ortszeit(inspektionen[0]["Created at"])[0]
            version_id = sk.checkliste_uebernehmen(self.cur, beginn)
            for i in inspektionen:
                if i["Hive_id"] not in voelker:
                    self.b["uebergangen"] += 1
                    self.hinweise.append(f"Durchsicht {i['Inspection_id']}: Hive {i['Hive_id']} nicht übernommen")
                    continue
                self.durchsicht(i, voelker[i["Hive_id"]], version_id)
        return self.b


def main(argv=None):
    import psycopg
    from psycopg.rows import dict_row
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("xlsx", type=Path, help="BEEP-Kontoexport (beep-export-user-….xlsx)")
    ap.add_argument("--dsn", required=True)
    ap.add_argument("--pruefen", action="store_true", help="nur prüfen: alles ausführen, dann zurücknehmen")
    a = ap.parse_args(argv)
    daten = blaetter(a.xlsx)
    for blatt in ("Apiaries", "Hives", "Inspections"):
        if blatt not in daten:
            raise SystemExit(f"ABBRUCH: Blatt {blatt!r} fehlt – ist das ein BEEP-Kontoexport?")
    with psycopg.connect(a.dsn, row_factory=dict_row) as con:
        with con.cursor() as cur:
            cur.execute("SET search_path = bienen, public")
            imp = Import(cur)
            b = imp.lauf(daten)
        if a.pruefen:
            con.rollback()
        else:
            con.commit()
    print(("PRÜFLAUF (zurückgenommen): " if a.pruefen else "übernommen: ") +
          ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in b.items()))
    for h in imp.hinweise:
        print("Hinweis:", h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
