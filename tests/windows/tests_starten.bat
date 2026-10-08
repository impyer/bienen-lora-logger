@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Stufe 1: Unit-Tests der Zeitlogik ===
test_zeitsync.exe
echo.
echo === Stufe 2: Simulation 10 Logger, 30 Tage ===
echo --- Original-Firmware ---
sim_orig.exe --tage 30
echo --- Zeitabgleich ohne Versatz ---
sim_sync.exe --tage 30 --slots 0
echo --- Zeitabgleich mit 10 s Versatz (Vorschlag) ---
sim_sync.exe --tage 30
echo.
echo Weitere Varianten: sim_sync.exe --hilfe
pause
