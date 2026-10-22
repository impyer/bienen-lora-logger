#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Gezielte Mutationstests der Plattform (PLT26-16): Erkennen die Tests eingebaute Fehler?

Je Mutant wird genau eine Quelltextstelle geändert, die zuständige Testsuite ausgeführt und die Datei wieder
hergestellt. Ein Mutant „überlebt“, wenn alle seine Tests grün bleiben – dann prüft keine Test diese Stelle genau.

Aufruf (aus dem Repo-Wurzelverzeichnis, Testdatenbank wie für die übrigen Plattformtests):
    BIENEN_TEST_DSN="..." python3 tests/plattform/mutation.py            # alle Mutanten
    BIENEN_TEST_DSN="..." python3 tests/plattform/mutation.py 3 17 40    # nur diese Nummern
    python3 tests/plattform/mutation.py --liste                           # Mutanten anzeigen
Braucht: wie tests/plattform/oberflaeche_testen.sh (PostgreSQL, Python-Pakete, node mit Playwright).
Dauer: etwa eine Stunde für alle; Browser- und Datenbankfälle je 40 s bis 1 min.
Rückgabe: 0 = Erkennungsrate ≥ --ziel (Vorgabe 80 %), 1 = darunter oder Stelle nicht eindeutig, 2 = Aufruf.
Ändert Quelltext nur vorübergehend; nach Abbruch mit Strg+C „git status“ prüfen.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
PY = sys.executable
A = "server/plattform/api/"
W = "server/plattform/web/"
TESTS = {
    "plattform": [PY, "tests/plattform/test_plattform.py"],
    "verwaltung": [PY, "tests/plattform/test_verwaltung.py"],
    "stockkarte": [PY, "tests/plattform/test_stockkarte.py"],
    "importer": [PY, "tests/datenbank/test_importer.py"],
    "diagramm": ["node", "tests/plattform/test_diagramm.mjs"],
    "ui": ["bash", "tests/plattform/oberflaeche_testen.sh"],
}

# (Datei, alter Text – genau einmal vorhanden, neuer Text, Tests in Reihenfolge des Aufwands)
MUTANTEN = [
    # Auswertung: Vorher/Nachher und Völkervergleich
    (A + "auswertung.py", 'vorher, nachher = (e["a"] - f, e["a"]), (e["b"], e["b"] + f)', 'vorher, nachher = (e["a"] - f, e["a"]), (e["a"], e["a"] + f)', ["plattform"]),
    (A + "auswertung.py", "AND tag <= (%(b)s AT TIME ZONE", "AND tag < (%(b)s AT TIME ZONE", ["plattform"]),
    (A + "auswertung.py", '"delta": (n - v) if', '"delta": (v - n) if', ["plattform"]),
    (A + "auswertung.py", "AND m.qualitaet <> 'ungueltig'", "", ["plattform"]),
    (A + "auswertung.py", 'abs(x["bilanz_kg"]) > SPRUNG_KG', 'x["bilanz_kg"] > SPRUNG_KG', ["plattform"]),
    (A + "auswertung.py", 'sum(x["bilanz_kg"] for x in b if not x["mit_eingriff"])', 'sum(x["bilanz_kg"] for x in b)', ["plattform"]),
    (A + "auswertung.py", "AND tag >= (%(von)s AT TIME ZONE 'Europe/Berlin')::date\n                     AND tag < (%(bis)s AT TIME ZONE 'Europe/Berlin')::date ORDER BY volk_id, tag\"\"\", p)\n    for r in cur.fetchall():\n        voelker[r.pop(\"volk_id\")][\"tagesreferenz\"]",
     "AND tag >= (%(von)s AT TIME ZONE 'UTC')::date\n                     AND tag < (%(bis)s AT TIME ZONE 'UTC')::date ORDER BY volk_id, tag\"\"\", p)\n    for r in cur.fetchall():\n        voelker[r.pop(\"volk_id\")][\"tagesreferenz\"]", ["plattform"]),
    (A + "auswertung.py", 'if e["volk_id"] != volk_id:', 'if False:', ["plattform"]),
    (A + "auswertung.py", "tstzrange(von, bis) && tstzrange(%(a)s, %(b)s)", "tstzrange(von, bis) <@ tstzrange(%(a)s, %(b)s)", ["plattform"]),
    (A + "auswertung.py", "SELECT avg(bilanz_kg) FILTER (WHERE NOT mit_eingriff) AS m", "SELECT avg(bilanz_kg) AS m", ["plattform", "ui"]),
    # Verdichtung und Lücken
    (A + "verdichtung.py", "if b[0] - a[0] > grenze:", "if b[0] - a[0] > 2 * grenze:", ["plattform"]),
    (A + "verdichtung.py", "ueblich = abstaende[len(abstaende) // 2]", "ueblich = abstaende[-1]", ["plattform"]),
    (A + "verdichtung.py", '"max": "max(wert)"', '"max": "avg(wert)"', ["plattform"]),
    (A + "verdichtung.py", '"min": "min(wert)"', '"min": "avg(wert)"', ["plattform"]),
    (A + "verdichtung.py", '"summe": "sum(wert)"', '"summe": "avg(wert)"', ["plattform"]),
    (A + "verdichtung.py", "if dauer / r <= max_punkte:", "if dauer / r < max_punkte / 4:", ["plattform"]),
    # Anmeldung und Schnittstelle
    (A + "anmeldung.py", "return hmac.compare_digest(ist, _unb64(soll))", "return True", ["plattform"]),
    (A + "anmeldung.py", "if not hmac.compare_digest(sig, _signatur(schluessel, inhalt)):", "if False:", ["plattform"]),
    (A + "anmeldung.py", "and hmac.compare_digest(token, csrf_token(schluessel, sitzung))", "", ["verwaltung"]),
    (A + "app.py", '"api_stand": API_STAND, ', "", ["plattform"]),
    # Stockkarte und Stammdaten
    (A + "stockkarte.py", '    genau = zeitgenauigkeit or ("exakt" if zeit != alt["zeit"] else alt["zeitgenauigkeit"])', '    genau = alt["zeitgenauigkeit"]', ["stockkarte"]),
    (A + "stockkarte.py", "UPDATE varroa_messung SET methode = %s, zeitraum = tstzrange(%s, %s, '[)'), milben = %s, anmerkung = %s,",
     "UPDATE varroa_messung SET methode = %s, zeitraum = tstzrange(%s, %s, '[)'), milben = %s + 1, anmerkung = %s,", ["stockkarte"]),
    (A + "stockkarte.py", 'if tabelle not in ("massnahme", "varroa_messung", "aufgabe"):', "if False:", ["stockkarte"]),
    (A + "stammdaten.py", 'cur.execute("UPDATE stand SET name = %s, ort_oeffentlich = %s WHERE id = %s", (name, ort_oeffentlich, stand_id))', "pass", ["verwaltung"]),
    (A + "stammdaten.py", 'cur.execute("UPDATE volk SET name = %s, notiz = %s WHERE id = %s", (name, notiz, volk_id))', "pass", ["verwaltung"]),
    # Importer
    ("server/datenbank/importer.py", "anzahl = q.anzahl + excluded.anzahl", "anzahl = excluded.anzahl", ["importer", "plattform"]),
    ("server/datenbank/importer.py", "summe[(gid, feld)] = (min(z[0], zeit), max(z[1], zeit), z[2] + 1)", "summe[(gid, feld)] = (z[0], z[1], z[2] + 1)", ["importer", "plattform"]),
    # nicht aufgenommen: „del self.ohne_puffer[ohne_vorher:]“ im Importer ist eine Absicherung; heute wirft keine Zeile
    # nach dem Sammeln der Felder ohne Kanal mehr, der Mutant wäre gleichwertig (Mutationstest 22.10.2026)
    # Diagrammlogik und Zeit
    (W + "stapel.js", "    } while (morgen.getTime() <= ende);", "    } while (morgen.getTime() < ende);", ["diagramm"]),
    (W + "stapel.js", "if (relativ && punkte.length) { const a = punkte[0][1];", "if (relativ && punkte.length) { const a = punkte[punkte.length - 1][1];", ["diagramm"]),
    (W + "stapel.js", "if (!(ohneEingriff && b.mit_eingriff)) s += b.bilanz_kg;", "s += b.bilanz_kg;", ["diagramm"]),
    (W + "stapel.js", "value: [min ? Math.max(e.zeit, min) : e.zeit, 0.5]", "value: [e.zeit, 0.5]", ["diagramm"]),
    (W + "stapel.js", "const erster = punkte.find((p) => p[1] !== null);", "const erster = punkte[0];", ["diagramm"]),
    (W + "stapel.js", "scale: f.achse !== 'milbenfall'", "scale: true", ["diagramm"]),
    (W + "stapel.js", "zoomOnMouseWheel: 'ctrl'", "zoomOnMouseWheel: true", ["diagramm"]),
    (W + "stapel.js", "axisLabel: { show: i === fs.length - 1,", "axisLabel: { show: true,", ["diagramm"]),
    (W + "diagramm.js", "export function zahl(w, stellen = 1) {", "export function zahl(w, stellen = 1) { stellen = 0;", ["diagramm"]),
    (W + "diagramm.js", "return mitternacht(new Date(Date.parse(tag + 'T00:00:00Z') + 86400000).toISOString().slice(0, 10)).toISOString();",
     "return tag + 'T23:59:59Z';", ["diagramm", "ui"]),
    (W + "diagramm.js", "export function bisTag(bis) { return bis ? ortText(Date.parse(bis) - 1).slice(0, 10) : ''; }",
     "export function bisTag(bis) { return bis ? bis.slice(0, 10) : ''; }", ["diagramm"]),
    # Rechenteile der Seiten
    (W + "kennzahlen.js", "bilanz: bilanz && bilanz.length ? bilanz[bilanz.length - 1] : null", "bilanz: bilanz && bilanz.length ? bilanz[0] : null", ["diagramm", "ui"]),
    (W + "kennzahlen.js", "const brut = r.find((x) => x.messgroesse === 'temperatur' && x.zone === 'brutnest');", "const brut = r.find((x) => x.messgroesse === 'temperatur');", ["diagramm", "ui"]),
    (W + "kennzahlen.js", "  return z.sort((a, b) => Date.parse(b.t) - Date.parse(a.t));", "  return z;", ["diagramm", "ui"]),
    (W + "kennzahlen.js", "return w.length ? w.reduce((a, b) => a + b, 0) / w.length : null;", "return w.length ? w.reduce((a, b) => a + b, 0) : null;", ["diagramm", "ui"]),
    (W + "kennzahlen.js", "const w = voelker.map((v) => [...v.tagesbilanz].reverse().find((b) => !b.mit_eingriff))", "const w = voelker.map((v) => [...v.tagesbilanz].reverse()[0])", ["diagramm", "ui"]),
    (W + "kennzahlen.js", "export const VERALTET_MS = 3 * 3600 * 1000;", "export const VERALTET_MS = 300 * 3600 * 1000;", ["diagramm", "ui"]),
    (W + "kennzahlen.js", "export function istZeitpunkt(von, bis) { return !bis || Date.parse(bis) - Date.parse(von) <= MASSNAHME_ZEITPUNKT_MS; }",
     "export function istZeitpunkt(von, bis) { return true; }", ["diagramm", "ui"]),
    # Seiten und Oberfläche (nur im Browser prüfbar)
    (W + "seiten/komponenten.js", "export function zeitraumParameter(route, vorgabeTage = 14) { return zeitraum(route.query, vorgabeTage); }",
     "export function zeitraumParameter(route, vorgabeTage = 14) { return zeitraum(route.query, 7); }", ["ui"]),
    (W + "api.js", "    await anmeldungAnfordern();               // wirft NichtAngemeldet, wenn abgebrochen\n    antwort = await versuchen(machen);\n", "", ["ui"]),
    (W + "api.js", "    if (g.api_stand === API_STAND) return null;", "    return null;", ["ui"]),
    (W + "api.js", "if (e instanceof TypeError) throw new Error(", "if (false) throw new Error(", ["ui"]),
    (W + "seiten/volk.js", "      return g ? (g.eingriff_vorher || 0) + (g.eingriff_nachher || 0) : 0;", "      return 0;", ["ui"]),
]


def lauf(befehl):
    if befehl[0] in ("bash", "node"):      # über PATH auflösen (unter Windows sonst bash.exe der WSL aus System32)
        ganz = shutil.which(befehl[0])
        if not ganz:
            raise SystemExit(f"{befehl[0]} fehlt")
        befehl = [ganz, *befehl[1:]]
    umgebung = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run(befehl, cwd=WURZEL, capture_output=True, text=True, encoding="utf-8", errors="replace", env=umgebung, timeout=1800)
    fehler = [z for z in (p.stdout + p.stderr).splitlines() if z.startswith("FEHLER") or "Error" in z]
    return p.returncode, (fehler[-1] if fehler else (p.stdout + p.stderr).strip()[-200:])[:160]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("nummern", nargs="*", type=int)
    ap.add_argument("--liste", action="store_true")
    ap.add_argument("--ziel", type=float, default=80.0, help="Mindestanteil erkannter Mutanten in Prozent")
    a = ap.parse_args(argv)
    if a.liste:
        for i, (datei, alt, _, tests) in enumerate(MUTANTEN):
            print(f"{i:3d} {datei}: {alt.strip()[:70]} [{', '.join(tests)}]")
        return 0
    if not os.environ.get("BIENEN_TEST_DSN"):
        print("BIENEN_TEST_DSN fehlt (Testdatenbank, wird geleert)")
        return 2
    # Grundlauf: ohne Mutation müssen alle benötigten Tests grün sein, sonst zählt jeder Mutant falsch als erkannt
    for t in sorted({t for i, (_, _, _, ts) in enumerate(MUTANTEN) if not a.nummern or i in a.nummern for t in ts}):
        rc, zeile = lauf(TESTS[t])
        if rc != 0:
            print(f"Grundlauf {t} nicht grün ({zeile}) – erst die Tests reparieren")
            return 1
    ergebnisse, kaputt = [], 0
    for i, (datei, alt, neu, tests) in enumerate(MUTANTEN):
        if a.nummern and i not in a.nummern:
            continue
        pfad = WURZEL / datei
        roh = pfad.read_bytes()                    # unverändert zurückschreiben (Zeilenenden wie ausgecheckt)
        crlf = b"\r\n" in roh
        text = roh.decode("utf-8").replace("\r\n", "\n")
        if text.count(alt) != 1:
            print(f"{i:3d} STELLE {text.count(alt)}x  {datei}: {alt.strip()[:60]}", flush=True)
            kaputt += 1
            continue
        t0 = time.time()
        mutiert = text.replace(alt, neu)
        pfad.write_bytes((mutiert.replace("\n", "\r\n") if crlf else mutiert).encode("utf-8"))
        try:
            erkannt, grund = None, ""
            for t in tests:
                rc, zeile = lauf(TESTS[t])
                if rc != 0:
                    erkannt, grund = t, zeile
                    break
        finally:
            pfad.write_bytes(roh)
        ergebnisse.append({"nr": i, "datei": datei, "erkannt": erkannt})
        print(f"{i:3d} {'erkannt von ' + erkannt if erkannt else 'ÜBERLEBT':24s} {datei}: {alt.strip()[:60]} ({time.time() - t0:.0f} s)", flush=True)
        if erkannt:
            print(f"      ↳ {grund}", flush=True)
    n = len(ergebnisse)
    erkannt = sum(1 for e in ergebnisse if e["erkannt"])
    quote = 100.0 * erkannt / n if n else 100.0
    print(f"\n{erkannt} von {n} Mutanten erkannt ({quote:.0f} %), Ziel {a.ziel:.0f} %" + (f"; {kaputt} Stelle(n) nicht eindeutig" if kaputt else ""))
    print(json.dumps({"erkannt": erkannt, "mutanten": n, "ueberlebt": [e["nr"] for e in ergebnisse if not e["erkannt"]]}))
    return 0 if quote >= a.ziel and not kaputt else 1


if __name__ == "__main__":
    sys.exit(main())
