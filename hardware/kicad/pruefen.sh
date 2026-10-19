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
WURZELN="hauptplatine/logger.kicad_sch"            # Akku-Platine seit HW-06 als Blatt in der Hauptplatine
erzeugen() { python3 werkzeug/symbole.py >/dev/null; python3 werkzeug/footprints.py >/dev/null; python3 hauptplatine.py >/dev/null; }

# SCH26-12: Alle erzeugten Schaltplanblätter gehen in die Doppelerzeugung, nicht eine feste Liste.
# Die Liste wird nach dem ersten Erzeugen gebildet, damit neue Blätter automatisch dabei sind.
dateiliste() { echo bienen.kicad_sym; printf '%s\n' Bienen.pretty/*.kicad_mod; printf '%s\n' hauptplatine/*.kicad_sch | LC_ALL=C sort; }
dateien_lesen() { DATEIEN=(); while IFS= read -r z; do DATEIEN+=("$z"); done < <(dateiliste); }   # Feld DATEIEN füllen
# Abdeckung: Jede Blattdatei, auf die ein Wurzelblatt verweist, muss in der Liste stehen,
# und jede .kicad_sch im Ordner muss Wurzel oder verwiesenes Blatt sein (keine verwaisten Dateien).
abdeckung() {   # Argumente: alle Dateien der Reproduzierbarkeitsprüfung
  local fehl=0 verweise f w
  local -a liste=("$@")
  for w in $WURZELN; do
    verweise=$(grep -o '"Sheetfile" "[^"]*"' "$w" | sed 's/.*" "\(.*\)"/\1/' || true)
    for f in $verweise; do
      f="$(dirname "$w")/$f"
      printf '%s\n' "${liste[@]}" | grep -qx "$f" || { echo "FEHL: Blatt $f fehlt in der Reproduzierbarkeitsprüfung"; fehl=1; }
    done
  done
  for f in "${liste[@]}"; do
    case "$f" in *.kicad_sch) ;; *) continue ;; esac
    case " $WURZELN " in *" $f "*) continue ;; esac
    grep -q "\"Sheetfile\" \"$(basename "$f")\"" "$(dirname "$f")"/*.kicad_sch 2>/dev/null \
      || { echo "FEHL: $f ist weder Wurzel noch von einem Wurzelblatt verwiesen"; fehl=1; }
  done
  return $fehl
}

if [ "${1:-}" = "--gegenprobe" ]; then
  # Erzeuger absichtlich nicht reproduzierbar machen (Zufalls-UUIDs) → die Prüfung muss scheitern,
  # und zwar für jede Blattdatei. Danach wird der echte Stand wieder erzeugt.
  BIENEN_GEGENPROBE_ZUFALL=1 erzeugen; dateien_lesen; H1=$(sha256sum "${DATEIEN[@]}")
  BIENEN_GEGENPROBE_ZUFALL=1 erzeugen; H2=$(sha256sum "${DATEIEN[@]}")
  erzeugen
  fehl=0
  for f in "${DATEIEN[@]}"; do
    case "$f" in *.kicad_sch) ;; *) continue ;; esac
    # sha256sum trennt mit zwei Leerzeichen, unter Windows (Binärmodus) mit " *"; ohne Treffer leer statt Abbruch (set -e)
    a=$(echo "$H1" | grep " [ *]$f\$" || true); b=$(echo "$H2" | grep " [ *]$f\$" || true)
    if [ "$a" != "$b" ]; then echo "Gegenprobe ok: Abweichung in $f erkannt"; else echo "Gegenprobe FEHL: $f nicht als abweichend erkannt"; fehl=1; fi
  done
  exit $fehl
fi

erzeugen; dateien_lesen; H1=$(sha256sum "${DATEIEN[@]}")
abdeckung "${DATEIEN[@]}"
echo "Reproduzierbarkeit geprüft für: ${DATEIEN[*]}"
erzeugen; H2=$(sha256sum "${DATEIEN[@]}")
if [ "$H1" = "$H2" ]; then
  echo "Reproduzierbar: zweimal erzeugt, identisch"
else
  echo "FEHL: Erzeugung nicht reproduzierbar"; diff <(echo "$H1") <(echo "$H2"); exit 1
fi
python3 werkzeug/erc_pruefen.py
mkdir -p pdf netzliste
for f in $WURZELN; do
  n=$(basename "${f%.kicad_sch}")
  kicad-cli sch export pdf -o "pdf/$n.pdf" "$f" >/dev/null 2>&1
  kicad-cli sch export netlist --format kicadsexpr -o "netzliste/$n.net" "$f" >/dev/null 2>&1
done
echo "PDF und Netzlisten aktualisiert"
python3 werkzeug/netz_tests.py
# REG26-08: Pin-/Footprint-Abgleich (schreibt pin_footprint.md, Exit 1 bei Abweichung)
python3 werkzeug/pin_footprint.py
