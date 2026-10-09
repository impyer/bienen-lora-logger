#!/bin/bash
# Erzeugt Symbole und Schaltpläne neu, prüft sie mit dem KiCad-ERC und exportiert PDFs.
# Braucht KiCad 10 (kicad-cli). Aufruf: bash hardware/kicad/pruefen.sh
set -e
HIER="$(cd "$(dirname "$0")" && pwd)"
cd "$HIER"
command -v kicad-cli >/dev/null || { echo "kicad-cli (KiCad 10) fehlt"; exit 1; }
kicad-cli version | grep -q '^10\.' || { echo "KiCad 10 erwartet, gefunden: $(kicad-cli version)"; exit 1; }
python3 werkzeug/symbole.py
python3 akku_platine.py
python3 hauptplatine.py
mkdir -p pdf
FEHLER=0
for f in akku-platine/akku.kicad_sch hauptplatine/logger.kicad_sch; do
  kicad-cli sch erc --severity-error -o /tmp/erc_$$.rpt "$f" >/dev/null 2>&1 || true
  Z=$(grep -o "Errors [0-9]*" /tmp/erc_$$.rpt | grep -o "[0-9]*")
  echo "ERC $f: $Z Fehler"
  [ "$Z" = "0" ] || { grep -v "^\s*;" /tmp/erc_$$.rpt; FEHLER=1; }
  kicad-cli sch export pdf -o "pdf/$(basename "${f%.kicad_sch}").pdf" "$f" >/dev/null 2>&1
done
rm -f /tmp/erc_$$.rpt
exit $FEHLER
