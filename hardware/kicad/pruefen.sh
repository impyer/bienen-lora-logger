#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
# Erzeugt Symbole und Schaltpläne neu, prüft Reproduzierbarkeit, ERC (alle Schweregrade gegen
# erc_erwartet.json), Netzlisten und PDFs. Braucht KiCad 10 (kicad-cli).
# Aufruf: bash hardware/kicad/pruefen.sh              (normale Prüfung, so auch in der CI)
#         bash hardware/kicad/pruefen.sh --gegenprobe (zeigt, dass die Reproduzierbarkeitsprüfung
#                                                      einen nicht reproduzierbaren Erzeuger erkennt)
# In der CI danach: git diff --exit-code -- hardware/kicad  (eingecheckter Stand = erzeugter Stand)
set -e
HIER="$(cd "$(dirname "$0")" && pwd)"
cd "$HIER"
command -v kicad-cli >/dev/null || { echo "kicad-cli (KiCad 10) fehlt"; exit 1; }
kicad-cli version | grep -q '^10\.' || { echo "KiCad 10 erwartet, gefunden: $(kicad-cli version)"; exit 1; }
WURZELN="akku-platine/akku.kicad_sch hauptplatine/logger.kicad_sch"
erzeugen() { python3 werkzeug/symbole.py >/dev/null; python3 akku_platine.py >/dev/null; python3 hauptplatine.py >/dev/null; }

# SCH26-12: Alle erzeugten Schaltplanblätter gehen in die Doppelerzeugung, nicht eine feste Liste.
# Die Liste wird nach dem ersten Erzeugen gebildet, damit neue Blätter automatisch dabei sind.
dateiliste() { echo bienen.kicad_sym; ls akku-platine/*.kicad_sch hauptplatine/*.kicad_sch | LC_ALL=C sort; }
# Abdeckung: Jede Blattdatei, auf die ein Wurzelblatt verweist, muss in der Liste stehen,
# und jede .kicad_sch im Ordner muss Wurzel oder verwiesenes Blatt sein (keine verwaisten Dateien).
abdeckung() {
  local liste="$1" fehl=0 verweise f
  for w in $WURZELN; do
    verweise=$(grep -o '"Sheetfile" "[^"]*"' "$w" | sed 's/.*" "\(.*\)"/\1/' || true)
    for f in $verweise; do
      f="$(dirname "$w")/$f"
      echo "$liste" | grep -qx "$f" || { echo "FEHL: Blatt $f fehlt in der Reproduzierbarkeitsprüfung"; fehl=1; }
    done
  done
  for f in $(echo "$liste" | grep '\.kicad_sch$'); do
    case " $WURZELN " in *" $f "*) continue ;; esac
    grep -q "\"Sheetfile\" \"$(basename "$f")\"" "$(dirname "$f")"/*.kicad_sch 2>/dev/null \
      || { echo "FEHL: $f ist weder Wurzel noch von einem Wurzelblatt verwiesen"; fehl=1; }
  done
  return $fehl
}

if [ "${1:-}" = "--gegenprobe" ]; then
  # Erzeuger absichtlich nicht reproduzierbar machen (Zufalls-UUIDs) → die Prüfung muss scheitern,
  # und zwar für jede Blattdatei. Danach wird der echte Stand wieder erzeugt.
  BIENEN_GEGENPROBE_ZUFALL=1 erzeugen; DATEIEN=$(dateiliste); H1=$(sha256sum $DATEIEN)
  BIENEN_GEGENPROBE_ZUFALL=1 erzeugen; H2=$(sha256sum $DATEIEN)
  erzeugen
  fehl=0
  for f in $(echo "$DATEIEN" | grep '\.kicad_sch$'); do
    a=$(echo "$H1" | grep "  $f\$"); b=$(echo "$H2" | grep "  $f\$")
    if [ "$a" != "$b" ]; then echo "Gegenprobe ok: Abweichung in $f erkannt"; else echo "Gegenprobe FEHL: $f nicht als abweichend erkannt"; fehl=1; fi
  done
  exit $fehl
fi

erzeugen; DATEIEN=$(dateiliste); H1=$(sha256sum $DATEIEN)
abdeckung "$DATEIEN"
echo "Reproduzierbarkeit geprüft für: $(echo $DATEIEN)"
erzeugen; H2=$(sha256sum $DATEIEN)
[ "$H1" = "$H2" ] && echo "Reproduzierbar: zweimal erzeugt, identisch" || { echo "FEHL: Erzeugung nicht reproduzierbar"; diff <(echo "$H1") <(echo "$H2"); exit 1; }
python3 werkzeug/erc_pruefen.py
mkdir -p pdf netzliste
for f in $WURZELN; do
  n=$(basename "${f%.kicad_sch}")
  kicad-cli sch export pdf -o "pdf/$n.pdf" "$f" >/dev/null 2>&1
  kicad-cli sch export netlist --format kicadsexpr -o "netzliste/$n.net" "$f" >/dev/null 2>&1
done
echo "PDF und Netzlisten aktualisiert"
python3 werkzeug/netz_tests.py
