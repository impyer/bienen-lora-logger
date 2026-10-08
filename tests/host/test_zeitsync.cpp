// PC-Test für beelogger_zeitsync.h
// Übersetzen und starten (Linux, macOS, Windows mit MSYS2/MinGW oder WSL):
//   g++ -std=c++11 -Wall -Wextra -O2 -o test_zeitsync test_zeitsync.cpp && ./test_zeitsync
// Rückgabewert 0 = alle Tests bestanden
#include <cstdio>
#include "../../firmware/STM32_LORA_261008_ZS/beelogger_zeitsync.h"
#include "../zs_testvektoren.h"
#include "../zs_testfaelle.h"

#ifdef _WIN32
extern "C" __declspec(dllimport) int __stdcall SetConsoleOutputCP(unsigned int);
#endif
static void ausgabe(const char *s) { std::puts(s); }

int main() {
#ifdef _WIN32
  SetConsoleOutputCP(65001);
#endif
  int fehler = zs_tests_ausfuehren(ausgabe);
  return fehler == 0 ? 0 : 1;
}
