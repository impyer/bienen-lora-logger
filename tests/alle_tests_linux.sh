#!/bin/sh
# Linux/macOS/WSL: alle PC-Tests übersetzen und starten
set -e
cd "$(dirname "$0")"
g++ -std=c++11 -Wall -Wextra -O2 -o host/test_zeitsync host/test_zeitsync.cpp
./host/test_zeitsync
g++ -std=c++17 -O2 -DZEITSYNC_AKTIV=1 -o sim/sim_sync sim/sim_zeitsync.cpp
g++ -std=c++17 -O2 -DZEITSYNC_AKTIV=0 -o sim/sim_orig sim/sim_zeitsync.cpp
./sim/sim_orig --tage 30
./sim/sim_sync --tage 30 --slots 0
./sim/sim_sync --tage 30
./sim/sim_sync --tage 7 --csv /tmp/zs_sim.csv > /dev/null
python3 ttn_auswertung/ttn_zeitanalyse.py /tmp/zs_sim.csv
g++ -std=c++11 -Wall -Wextra -O2 -o firmware/test_bee_fft firmware/test_bee_fft.cpp && ./firmware/test_bee_fft
if command -v node >/dev/null 2>&1; then
  node firmware/vektoren_v2.js > firmware/ff2_vektoren.h
  g++ -std=c++11 -Wall -Wextra -O2 -o firmware/test_funkformat_v2 firmware/test_funkformat_v2.cpp && ./firmware/test_funkformat_v2
  node formatter/test_formatter.js
  node formatter/test_formatter.js ../formatter/ttn_formatter.min.js
else
  echo "Node.js fehlt: Formatter-Tests übersprungen"
fi
if command -v php >/dev/null 2>&1; then
  php server/test_lora_funktionen.php
  if command -v node >/dev/null 2>&1; then bash server/test_lora_eingang.sh; fi
else
  echo "PHP fehlt: Server-Tests übersprungen"
fi
