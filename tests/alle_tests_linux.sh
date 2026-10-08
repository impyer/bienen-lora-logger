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
