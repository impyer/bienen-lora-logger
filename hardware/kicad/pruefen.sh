#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
# Erzeugt Symbole und Schaltpläne neu, prüft Reproduzierbarkeit, ERC (alle Schweregrade gegen
# erc_erwartet.json), Netzlisten und PDFs. Braucht KiCad 10 (kicad-cli).
# Aufruf: bash hardware/kicad/pruefen.sh
# In der CI danach: git diff --exit-code -- hardware/kicad  (eingecheckter Stand = erzeugter Stand)
set -e
HIER="$(cd "$(dirname "$0")" && pwd)"
cd "$HIER"
command -v kicad-cli >/dev/null || { echo "kicad-cli (KiCad 10) fehlt"; exit 1; }
kicad-cli version | grep -q '^10\.' || { echo "KiCad 10 erwartet, gefunden: $(kicad-cli version)"; exit 1; }
DATEIEN="bienen.kicad_sym akku-platine/akku.kicad_sch hauptplatine/logger.kicad_sch hauptplatine/versorgung.kicad_sch"
erzeugen() { python3 werkzeug/symbole.py >/dev/null; python3 akku_platine.py >/dev/null; python3 hauptplatine.py >/dev/null; }
erzeugen; H1=$(sha256sum $DATEIEN)
erzeugen; H2=$(sha256sum $DATEIEN)
[ "$H1" = "$H2" ] && echo "Reproduzierbar: zweimal erzeugt, identisch" || { echo "FEHL: Erzeugung nicht reproduzierbar"; diff <(echo "$H1") <(echo "$H2"); exit 1; }
python3 werkzeug/erc_pruefen.py
mkdir -p pdf netzliste
for f in akku-platine/akku.kicad_sch hauptplatine/logger.kicad_sch; do
  n=$(basename "${f%.kicad_sch}")
  kicad-cli sch export pdf -o "pdf/$n.pdf" "$f" >/dev/null 2>&1
  kicad-cli sch export netlist --format kicadsexpr -o "netzliste/$n.net" "$f" >/dev/null 2>&1
done
echo "PDF und Netzlisten aktualisiert"
python3 werkzeug/netz_tests.py
