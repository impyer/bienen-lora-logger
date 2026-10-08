#!/bin/sh
# Erzeugt formatter/ttn_formatter.min.js aus formatter/formatter.js (für das Eingabefeld in TTN).
# Grund: TTN begrenzt eigene Formatter-Skripte (Community-Forum 2021: 4 KB je Applikation/Gerät).
# Benötigt Node.js; terser wird in der festen Version geholt.
set -e
cd "$(dirname "$0")"
{
  echo "// bienen-lora-logger TTN-Formatter, GPL-3.0-or-later. Erzeugt aus formatter.js – dort bearbeiten."
  npx --yes terser@5.36.0 formatter.js --ecma 5 --compress passes=2 --mangle --comments false
} > ttn_formatter.min.js
GROESSE=$(wc -c < ttn_formatter.min.js)
echo "ttn_formatter.min.js: $GROESSE Byte"
if [ "$GROESSE" -gt 4096 ]; then echo "zu groß für die TTN-Grenze von 4096 Byte"; exit 1; fi
