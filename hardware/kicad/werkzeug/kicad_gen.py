#!/usr/bin/env python3
"""Kleiner Erzeuger für KiCad-10-Schaltpläne aus einer Netzbeschreibung.

Idee: Jedes Blatt wird in Python beschrieben (Bauteil, Wert, Footprint, Pin → Netz).
Der Erzeuger setzt die Symbole in ein Raster und hängt an jedes Pin-Ende ein Netzlabel,
ein Versorgungssymbol oder ein No-Connect. Verbindungen entstehen über Netznamen, nicht über
gezeichnete Drähte. Ergebnis: ein ERC-prüfbarer Schaltplan, den man in KiCad weiter
bearbeiten (und schöner zeichnen) kann.

Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"""
import os
import re
import uuid as _uuid

KICAD_SYM_DIR = os.environ.get("KICAD9_SYMBOL_DIR", "/usr/share/kicad/symbols")
SCH_VERSION = "20260306"   # KiCad 10.0
GRID = 1.27

# ---------------------------------------------------------------------------
# S-Ausdrücke
# ---------------------------------------------------------------------------


class Sym(str):
    """Unquotiertes Atom (Schlüsselwort/Zahl)."""


def parse(text):
    tok = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)')
    pos, stack, cur = 0, [], []
    while pos < len(text):
        m = tok.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("Syntax bei %d" % pos)
        t = m.group(1)
        pos = m.end()
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif t.startswith('"'):
            cur.append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            cur.append(Sym(t))
    return cur[0] if len(cur) == 1 else cur


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(x, ind=0):
    if isinstance(x, list):
        if not x:
            return "()"
        einfach = all(not isinstance(e, list) for e in x)
        if einfach:
            return "(" + " ".join(dump(e) for e in x) + ")"
        out = "(" + dump(x[0])
        for e in x[1:]:
            if isinstance(e, list):
                out += "\n" + "\t" * (ind + 1) + dump(e, ind + 1)
            else:
                out += " " + dump(e)
        return out + "\n" + "\t" * ind + ")"
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int, float)):
        return fmt(x)
    return q(x)


def fmt(v):
    v = round(float(v), 4)
    if v == int(v):
        return str(int(v))
    return ("%.4f" % v).rstrip("0").rstrip(".")


def S(*a):
    return [Sym(a[0])] + list(a[1:])


def finde(liste, kopf):
    return [e for e in liste if isinstance(e, list) and e and e[0] == kopf]


def eins(liste, kopf):
    r = finde(liste, kopf)
    return r[0] if r else None


def neue_uuid(saat=None):
    if saat is None:
        return str(_uuid.uuid4())
    return str(_uuid.uuid5(_uuid.NAMESPACE_URL, "bienen-logger/" + saat))


# ---------------------------------------------------------------------------
# Symbol-Bibliotheken
# ---------------------------------------------------------------------------

_bib_cache = {}


def bibliothek(name, pfad=None):
    key = pfad or name
    if key not in _bib_cache:
        p = pfad or os.path.join(KICAD_SYM_DIR, name + ".kicad_sym")
        with open(p, encoding="utf-8") as f:
            baum = parse(f.read())
        _bib_cache[key] = {e[1]: e for e in finde(baum, "symbol")}
    return _bib_cache[key]


def _umbenennen(sym, alt, neu):
    """Untereinheiten 'ALT_0_1' → 'NEU_0_1'."""
    out = []
    for e in sym:
        if isinstance(e, list) and e and e[0] == "symbol" and isinstance(e[1], str) and e[1].startswith(alt + "_"):
            e = [e[0], neu + e[1][len(alt):]] + e[2:]
        out.append(e)
    return out


def lib_symbol(lib_id, eigene=None):
    """Symbol aus der Bibliothek holen, 'extends' auflösen, Namen auf 'Lib:Name' setzen."""
    lib, name = lib_id.split(":", 1)
    bib = bibliothek(lib, (eigene or {}).get(lib))
    sym = bib[name]
    ext = eins(sym, "extends")
    if ext:
        eltern = lib_symbol(lib + ":" + ext[1], eigene)
        ename = ext[1]
        # Eigenschaften des Kindes ersetzen die der Eltern
        kind_props = {p[1]: p for p in finde(sym, "property")}
        neu = [Sym("symbol"), lib_id]
        for e in eltern[2:]:
            if isinstance(e, list) and e and e[0] == "property" and e[1] in kind_props:
                neu.append(kind_props.pop(e[1]))
            else:
                neu.append(e)
        for p in kind_props.values():
            neu.insert(len(neu) - 1, p)
        neu = _umbenennen(neu, ename, name)
        return neu
    return [Sym("symbol"), lib_id] + list(sym[2:])


def pins_von(symdef):
    """Liste (nummer, name, typ, x, y, winkel, einheit) aus einer Symboldefinition."""
    out = []
    for unter in finde(symdef, "symbol"):
        m = re.match(r".*_(\d+)_(\d+)$", unter[1])
        einheit = int(m.group(1)) if m else 1
        for p in finde(unter, "pin"):
            at = eins(p, "at")
            name = eins(p, "name")[1]
            nummer = eins(p, "number")[1]
            out.append((nummer, name, str(p[1]), float(at[1]), float(at[2]),
                        int(float(at[3])) if len(at) > 3 else 0, einheit))
    return out


def koerper_box(symdef):
    xs, ys = [], []

    def lauf(e):
        if isinstance(e, list) and e:
            if e[0] in ("start", "end", "xy", "center", "at") and len(e) >= 3:
                try:
                    xs.append(float(e[1]))
                    ys.append(float(e[2]))
                except (TypeError, ValueError):
                    pass
            for k in e[1:]:
                if isinstance(k, list) and k and k[0] != "property":
                    lauf(k)

    for unter in finde(symdef, "symbol"):
        lauf(unter)
    if not xs:
        return (-2.54, -2.54, 2.54, 2.54)
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------------------
# Blatt
# ---------------------------------------------------------------------------

VERSORGUNGSNETZE = {
    # Netzname → Symbol aus 'power' (Richtung der Grafik: 'unten' bei GND, sonst 'oben')
    "GND": ("power:GND", "unten"),
    "+3V3": ("power:+3V3", "oben"),
}


def _txt(at, groesse=1.27, verbergen=False, justify=None):
    eff = S("effects", S("font", S("size", groesse, groesse)))
    if justify:
        eff.append(S("justify", *[Sym(j) for j in justify]))
    if verbergen:
        eff.append(S("hide", Sym("yes")))
    return eff


class Teil:
    def __init__(self, blatt, lib_id, ref, wert, fp="", lcsc="", netze=None, ds="", info="", dnp=False):
        self.blatt, self.lib_id, self.ref, self.wert = blatt, lib_id, ref, wert
        self.fp, self.lcsc, self.ds, self.info, self.dnp = fp, lcsc, ds, info, dnp
        self.netze = dict(netze or {})
        self.symdef = lib_symbol(lib_id, blatt.projekt.eigene_bibs)
        self.pins = pins_von(self.symdef)
        self.at = (0.0, 0.0)
        # Pins einem Netz zuordnen: Schlüssel = Nummer oder Name
        self.pin_netz = {}
        nummern = {p[0] for p in self.pins}
        for k, v in self.netze.items():
            treffer = [p for p in self.pins if p[0] == str(k)] if str(k) in nummern else \
                [p for p in self.pins if p[1] == str(k)]
            if not treffer:
                raise KeyError("%s: Pin %s gibt es in %s nicht" % (ref, k, lib_id))
            for p in treffer:
                self.pin_netz[p[0]] = v
        offen = [p for p in self.pins if p[0] not in self.pin_netz and p[2] != "no_connect"]
        if offen:
            raise KeyError("%s (%s): Pins ohne Netz: %s" % (ref, lib_id, ", ".join("%s/%s" % (p[0], p[1]) for p in offen)))

    def ausmass(self):
        """Breite/Höhe inkl. Platz für Labels (grob)."""
        x0, y0, x1, y1 = koerper_box(self.symdef)
        for (_, _, _, px, py, _, _) in self.pins:
            x0, x1, y0, y1 = min(x0, px), max(x1, px), min(y0, py), max(y1, py)
        links = rechts = oben = unten = 0.0
        for (nr, _, _, px, py, w, _) in self.pins:
            lab = len(str(self.pin_netz.get(nr, ""))) * 1.3 + 4
            if w == 0:
                links = max(links, lab)
            elif w == 180:
                rechts = max(rechts, lab)
            elif w == 90:
                unten = max(unten, lab)
            else:
                oben = max(oben, lab)
        if self.nur_vertikal():
            breit = max(len(self.ref), len(self.wert)) * 1.3 + 3
            return (x0 - 2, -y1 - oben - 2, x1 + breit, -y0 + unten + 2)
        return (x0 - links, -y1 - oben - 5, x1 + rechts, -y0 + unten + 4)

    def nur_vertikal(self):
        return all(p[5] % 180 == 90 for p in self.pins)


class Blatt:
    def __init__(self, projekt, name, datei, titel="", papier="A3"):
        self.projekt, self.name, self.datei = projekt, name, datei
        self.titel, self.papier = titel or name, papier
        self.teile = []
        self.texte = []
        self.uuid = neue_uuid(projekt.name + "/" + datei)
        self.sheet_uuid = neue_uuid(projekt.name + "/sheet/" + datei)

    def teil(self, *a, **k):
        t = Teil(self, *a, **k)
        self.teile.append(t)
        return t

    def text(self, inhalt, x, y, groesse=1.27):
        self.texte.append((inhalt, x, y, groesse))

    def gruppe(self, titel, teile, x, y, breite=400):
        """Teile in Reihen ab (x, y) setzen; Überschrift darüber."""
        self.text(titel, x, y - 6, 2.0)
        cx, cy, zeilen_h = x, y, 0
        for t in teile:
            lx0, ly0, lx1, ly1 = t.ausmass()
            w, h = lx1 - lx0, ly1 - ly0
            if cx + w > x + breite and cx > x:
                cx, cy, zeilen_h = x, cy + zeilen_h + 10, 0
            px = round((cx - lx0) / GRID) * GRID
            py = round((cy - ly0) / GRID) * GRID
            t.at = (px, py)
            cx += w + 8
            zeilen_h = max(zeilen_h, h)
        return cy + zeilen_h

    # ------------------------------------------------------------------
    def netze(self):
        n = {}
        for t in self.teile:
            for nr, netz in t.pin_netz.items():
                if netz is None:
                    continue
                n.setdefault(netz, []).append((t.ref, nr))
        return n

    def baue(self, globale_netze, root_uuid, seite):
        p = self.projekt
        body = [Sym("kicad_sch"), S("version", Sym(SCH_VERSION)), S("generator", "eeschema"),
                S("generator_version", "10.0"), S("uuid", self.uuid), S("paper", self.papier),
                S("title_block", S("title", self.titel), S("date", p.datum), S("rev", p.rev),
                  S("company", p.firma), S("comment", 1, "Erzeugt mit hardware/kicad/werkzeug – nicht von Hand ändern, sondern das Skript"))]
        libs = {}
        pwr_n = [0]
        objekte = []

        def pwr_symbol(netz, x, y, richtung):
            lib_id, grafik = VERSORGUNGSNETZE[netz]
            libs.setdefault(lib_id, lib_symbol(lib_id))
            # Grafik zeigt 'unten' (GND) bzw. 'oben' (+3V3); drehen in Label-Richtung
            dreh = {"unten": {"unten": 0, "rechts": 90, "oben": 180, "links": 270},
                    "oben": {"oben": 0, "links": 90, "unten": 180, "rechts": 270}}[grafik][richtung]
            pwr_n[0] += 1
            ref = "#PWR%s%03d" % (self.projekt.blatt_nr(self), pwr_n[0])
            u = neue_uuid(p.name + "/" + self.datei + "/" + ref)
            objekte.append(S("symbol", S("lib_id", lib_id), S("at", x, y, dreh), S("unit", 1),
                             S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")), S("on_board", Sym("yes")),
                             S("dnp", Sym("no")), S("uuid", u),
                             S("property", "Reference", ref, S("at", x, y, 0), _txt(None, verbergen=True)),
                             S("property", "Value", netz, S("at", x, y + (3.2 if grafik == "unten" else -3.2), 0), _txt(None)),
                             S("property", "Footprint", "", S("at", x, y, 0), _txt(None, verbergen=True)),
                             S("property", "Datasheet", "", S("at", x, y, 0), _txt(None, verbergen=True)),
                             S("pin", "1", S("uuid", neue_uuid(u + "/1"))),
                             S("instances", S("project", p.name, S("path", self._pfad(root_uuid), S("reference", ref), S("unit", 1))))))

        for t in self.teile:
            libs.setdefault(t.lib_id, t.symdef)
            x, y = t.at
            u = neue_uuid(p.name + "/" + self.datei + "/" + t.ref)
            x0, y0, x1, y1 = koerper_box(t.symdef)
            sym = S("symbol", S("lib_id", t.lib_id), S("at", x, y, 0), S("unit", 1),
                    S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")), S("on_board", Sym("yes")),
                    S("dnp", Sym("yes" if t.dnp else "no")), S("uuid", u),
                    S("property", "Reference", t.ref, *self._ref_pos(t, x, y, x0, y0, x1, y1, True)),
                    S("property", "Value", t.wert, *self._ref_pos(t, x, y, x0, y0, x1, y1, False)),
                    S("property", "Footprint", t.fp, S("at", x, y, 0), _txt(None, verbergen=True)),
                    S("property", "Datasheet", t.ds, S("at", x, y, 0), _txt(None, verbergen=True)),
                    S("property", "Description", t.info, S("at", x, y, 0), _txt(None, verbergen=True)))
            if t.lcsc:
                sym.append(S("property", "LCSC", t.lcsc, S("at", x, y, 0), _txt(None, verbergen=True)))
            for (nr, *_r) in t.pins:
                sym.append(S("pin", nr, S("uuid", neue_uuid(u + "/" + nr))))
            sym.append(S("instances", S("project", p.name, S("path", self._pfad(root_uuid), S("reference", t.ref), S("unit", 1)))))
            objekte.append(sym)

            gesehen = set()
            for (nr, name, typ, px, py, w, einheit) in t.pins:
                netz = t.pin_netz.get(nr)
                ex, ey = x + px, y - py
                key = (round(ex, 3), round(ey, 3))
                if key in gesehen:      # gestapelte Pins (z. B. mehrere GND an einer Stelle)
                    continue
                gesehen.add(key)
                richtung = {0: "links", 180: "rechts", 90: "unten", 270: "oben"}[w % 360]
                if netz is None or netz == "NC":
                    objekte.append(S("no_connect", S("at", ex, ey), S("uuid", neue_uuid(u + "/nc/" + nr))))
                    continue
                if netz in VERSORGUNGSNETZE:
                    pwr_symbol(netz, ex, ey, richtung)
                    continue
                winkel = {"links": 180, "rechts": 0, "oben": 90, "unten": 270}[richtung]
                lu = neue_uuid(u + "/lab/" + nr)
                if netz in globale_netze:
                    just = ["right"] if winkel in (180, 270) else ["left"]
                    objekte.append(S("global_label", netz, S("shape", Sym("bidirectional")), S("at", ex, ey, winkel),
                                     S("fields_autoplaced", Sym("yes")), _txt(None, justify=just), S("uuid", lu),
                                     S("property", "Intersheetrefs", "${INTERSHEET_REFS}", S("at", ex, ey, 0),
                                       _txt(None, verbergen=True))))
                else:
                    just = ["right", "bottom"] if winkel in (180, 270) else ["left", "bottom"]
                    objekte.append(S("label", netz, S("at", ex, ey, winkel), _txt(None, justify=just), S("uuid", lu)))

        for (inhalt, x, y, g) in self.texte:
            objekte.append(S("text", inhalt, S("exclude_from_sim", Sym("no")), S("at", x, y, 0),
                             _txt(None, groesse=g, justify=["left", "bottom"]), S("uuid", neue_uuid(self.datei + "/t/" + inhalt[:40] + str(x) + str(y)))))

        body.append([Sym("lib_symbols")] + list(libs.values()))
        body += objekte
        if self is p.wurzel:
            body += p.sheet_objekte(root_uuid)
            body.append(S("sheet_instances", S("path", "/", S("page", "1"))))
        body.append(S("embedded_fonts", Sym("no")))
        return dump(body) + "\n"

    @staticmethod
    def _ref_pos(t, x, y, x0, y0, x1, y1, ist_ref):
        if t.nur_vertikal():
            return [S("at", x + x1 + 1.0, y + (-1.27 if ist_ref else 1.27), 0), _txt(None, justify=["left"])]
        oben = max([p[4] for p in t.pins] + [y1])
        unten = min([p[4] for p in t.pins] + [y0])
        def ext(pins):
            e = 0.0
            for p in pins:
                netz = t.pin_netz.get(p[0])
                if netz in VERSORGUNGSNETZE:
                    e = max(e, 5.0)
                elif netz and netz != "NC":
                    e = max(e, len(str(netz)) * 1.3 + 1)
            return e
        if ist_ref:
            e = ext([p for p in t.pins if p[5] % 360 == 270])
            return [S("at", x + x0, y - oben - e - 1.6, 0), _txt(None, justify=["left"])]
        e = ext([p for p in t.pins if p[5] % 360 == 90])
        return [S("at", x + x0, y - unten + e + 2.2, 0), _txt(None, justify=["left"])]

    def _pfad(self, root_uuid):
        if self is self.projekt.wurzel:
            return "/" + root_uuid
        return "/" + root_uuid + "/" + self.sheet_uuid


class Projekt:
    def __init__(self, name, ordner, firma="", rev="0.1", datum="", eigene_bibs=None):
        self.name, self.ordner, self.firma, self.rev, self.datum = name, ordner, firma, rev, datum
        self.eigene_bibs = eigene_bibs or {}
        self.schnittstellen = set()   # Netze, die sicher blattübergreifend sind (globale Labels)
        self.wurzel = None
        self.blaetter = []

    def blatt(self, name, datei, **k):
        b = Blatt(self, name, datei, **k)
        if self.wurzel is None:
            self.wurzel = b
        else:
            self.blaetter.append(b)
        return b

    def blatt_nr(self, b):
        return 1 if b is self.wurzel else self.blaetter.index(b) + 2

    def sheet_objekte(self, root_uuid):
        out = []
        x, y = 30.0, 40.0
        for i, b in enumerate(self.blaetter):
            out.append(S("sheet", S("at", x, y), S("size", 45, 20), S("exclude_from_sim", Sym("no")),
                         S("in_bom", Sym("yes")), S("on_board", Sym("yes")), S("dnp", Sym("no")),
                         S("fields_autoplaced", Sym("yes")),
                         S("stroke", S("width", 0.1524), S("type", Sym("solid"))),
                         S("fill", S("color", 0, 0, 0, 0.0)), S("uuid", b.sheet_uuid),
                         S("property", "Sheetname", b.name, S("at", x, y - 0.7, 0), _txt(None, justify=["left", "bottom"])),
                         S("property", "Sheetfile", b.datei, S("at", x, y + 20.6, 0), _txt(None, justify=["left", "top"])),
                         S("instances", S("project", self.name, S("path", "/" + root_uuid, S("page", str(i + 2)))))))
            x += 55
            if x > 330:
                x, y = 30.0, y + 35
        return out

    def schreibe(self):
        os.makedirs(self.ordner, exist_ok=True)
        alle = [self.wurzel] + self.blaetter
        zaehl = {}
        for b in alle:
            for netz in b.netze():
                zaehl[netz] = zaehl.get(netz, 0) + 1
        globale = {n for n, c in zaehl.items() if c > 1} | (self.schnittstellen & set(zaehl))
        root_uuid = self.wurzel.uuid
        for b in alle:
            with open(os.path.join(self.ordner, b.datei), "w", encoding="utf-8") as f:
                f.write(b.baue(globale, root_uuid, None))
        self._projektdatei()
        self._kicad_normalisieren(alle)
        return globale

    def _kicad_normalisieren(self, alle):
        """Dateien einmal von KiCad selbst speichern lassen (kicad-cli sch upgrade --force),
        damit sie exakt im Format von KiCad 10 vorliegen."""
        import shutil
        import subprocess
        cli = shutil.which("kicad-cli")
        if not cli:
            print("Hinweis: kicad-cli fehlt – Dateien nicht von KiCad normalisiert")
            return
        for b in alle:
            subprocess.run([cli, "sch", "upgrade", "--force", os.path.join(self.ordner, b.datei)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _projektdatei(self):
        pro = os.path.join(self.ordner, self.name + ".kicad_pro")
        import json
        daten = {"meta": {"filename": self.name + ".kicad_pro", "version": 3},
                 "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
                 "sheets": [[self.wurzel.uuid, "Root"]] + [[b.sheet_uuid, b.name] for b in self.blaetter],
                 "text_variables": {}}
        with open(pro, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=2)
        if self.eigene_bibs:
            with open(os.path.join(self.ordner, "sym-lib-table"), "w", encoding="utf-8") as f:
                f.write("(sym_lib_table\n  (version 7)\n")
                for name, pfad in self.eigene_bibs.items():
                    rel = os.path.relpath(pfad, self.ordner).replace(os.sep, "/")
                    f.write('  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s")(options "")(descr "Projektsymbole Bienenlogger"))\n' % (name, rel))
                f.write(")\n")

    def stueckliste(self):
        zeilen = []
        for b in [self.wurzel] + self.blaetter:
            for t in b.teile:
                zeilen.append((t.ref, t.wert, t.lib_id, t.fp, t.lcsc, b.name, "DNP" if t.dnp else ""))
        return sorted(zeilen, key=lambda z: (re.sub(r"\d+", "", z[0]), int(re.sub(r"\D", "", z[0]) or 0)))
