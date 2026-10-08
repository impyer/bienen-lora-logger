// PC-Test: C-Kodierer funkformat_v2.h gegen den JavaScript-Referenz-Kodierer
// Vektoren: node tests/firmware/vektoren_v2.js > tests/firmware/ff2_vektoren.h
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
#include <cstdio>
#include <cstring>
#include "../../firmware/STM32_LORA_261008_ZS/funkformat_v2.h"
#include "ff2_vektoren.h"

int main() {
  ff2_faelle_fuellen();
  int fehler = 0, n = (int)(sizeof(ff2_faelle) / sizeof(ff2_faelle[0]));
  uint8_t puffer[64];
  for (int i = 0; i < n; i++) {
    size_t len = ff2_kodiere(&ff2_faelle[i].w, puffer, sizeof(puffer));
    if (len != ff2_faelle[i].n || memcmp(puffer, ff2_faelle[i].b, len) != 0) {
      if (++fehler <= 5) {
        printf("Fall %d: Länge %u statt %u\n  C:  ", i, (unsigned)len, (unsigned)ff2_faelle[i].n);
        for (size_t j = 0; j < len; j++) printf("%02x", puffer[j]);
        printf("\n  JS: ");
        for (unsigned j = 0; j < ff2_faelle[i].n; j++) printf("%02x", ff2_faelle[i].b[j]);
        printf("\n");
      }
    }
  }
  // zu kleiner Puffer -> 0
  uint8_t klein[10];
  if (ff2_kodiere(&ff2_faelle[0].w, klein, sizeof(klein)) != 0) { printf("zu kleiner Puffer nicht erkannt\n"); fehler++; }
  // reservierte Bits werden nicht gesendet
  FunkWerteV2 w; ff2_leeren(&w); w.vorhanden = 0xFFF80000UL;
  if (ff2_kodiere(&w, puffer, sizeof(puffer)) != 5 || puffer[1] || puffer[2] || puffer[3] || puffer[4]) { printf("reservierte Bits gesendet\n"); fehler++; }
  printf("Funkformat v2: %d von %d Fällen gleich wie der JavaScript-Kodierer%s\n", n - (fehler > n ? n : fehler), n,
         fehler ? " – FEHLER" : "");
  return fehler ? 1 : 0;
}
