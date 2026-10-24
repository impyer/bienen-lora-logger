# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Decoder für Messnachrichten der BEEP Base (Firmware 1.2+, FPort 3), eigene Umsetzung nach dem Nachrichtenaufbau.

Die BEEP Base sendet über TTN an BEEP und an den Bienen-Eingang. In TTN darf für sie KEIN Payload-Formatter
stehen: BEEP übernimmt ein vorhandenes decoded_payload statt selbst zu dekodieren (BEEP-Quelltext,
MeasurementLoRaDecoderTrait). Deshalb dekodiert der Importer die Rohdaten selbst – nur für Geräte der Art
'beep_base' und nur, wenn die Nachricht kein decoded_payload hat.

Aufbau (Blöcke mit Kennbyte, Zahlen big-endian):
  1B  vcc[2] bv[2] bat_perc[1]          Spannungen in mV, Ladestand in %
  0A  n[1]  n × Rohwert Waage[3]       vorzeichenbehaftet 24 bit: w_v (n=1) bzw. w_v_1 … w_v_n
  04  n[1]  n × Temperatur[2]          vorzeichenbehaftet, 1/100 °C: t_i (n=1) bzw. t_0 … t_(n-1)
  0C  n[1] start[1] stop[1] n × Wert[2]  Schallspektrum, Felder s_bin_<von Hz>_<bis Hz>
  07  t[2] h[2] p[2]                   BME280 (t vorzeichenbehaftet 1/100 °C, h 1/100 %, p hPa); alles 0 = keiner
  25|26|2D|2E  Unixzeit[4]             Gerätezeit (26/2D/2E: Echtzeituhr), nur in nachgesendeten Nachrichten
Die Feldnamen sind die BEEP-Kürzel, damit Historie aus BEEP und eigene Daten in denselben Kanälen landen.
Das Gewicht in kg rechnet nicht dieser Decoder, sondern der Kanal: kg = (w_v − Versatz_BEEP) × Faktor_BEEP,
also Kanal-Faktor = Faktor_BEEP und Kanal-Versatz = −Versatz_BEEP × Faktor_BEEP (Werte aus BEEP, Sensordefinition).
"""
import math

FFT_HZ_JE_BIN = 3.937752016          # ≈ 2000 / 510, wie in der BEEP-Firmware
UHR_KENNUNG = {0x25: "mcu", 0x26: "rtc", 0x2D: "rtc", 0x2E: "rtc"}
UNIX_2019 = 1546300800


def _s(b, i, n):
    """vorzeichenbehaftete Ganzzahl aus n Bytes ab i (big-endian)"""
    return int.from_bytes(b[i:i + n], "big", signed=True)


def _u(b, i, n):
    return int.from_bytes(b[i:i + n], "big")


def dekodieren(b, f_port):
    """dict mit BEEP-Kürzeln oder None, wenn es keine Messnachricht im bekannten Aufbau ist."""
    if f_port != 3 or not isinstance(b, (bytes, bytearray)) or len(b) < 6 or b[0] != 0x1B:
        return None
    d = {"vcc": _u(b, 1, 2) / 1000, "bv": _u(b, 3, 2) / 1000, "bat_perc": b[5]}
    i = 6
    try:
        if i < len(b) and b[i] == 0x0A:                     # Waage
            n = b[i + 1]
            if not 0 <= n <= 2 or i + 2 + 3 * n > len(b):
                return None
            for k in range(n):
                d["w_v" if n == 1 else f"w_v_{k + 1}"] = _s(b, i + 2 + 3 * k, 3)
            i += 2 + 3 * n
        if i < len(b) and b[i] == 0x04:                     # Temperaturfühler DS18B20
            n = b[i + 1]
            if not 0 <= n <= 10 or i + 2 + 2 * n > len(b):
                return None
            for k in range(n):
                d["t_i" if n == 1 else f"t_{k}"] = _s(b, i + 2 + 2 * k, 2) / 100
            i += 2 + 2 * n
        if i < len(b) and b[i] == 0x0C:                     # Schallspektrum
            n, start, stop = b[i + 1], b[i + 2], b[i + 3]
            if i + 4 + 2 * n > len(b):
                return None
            if 0 < n < 13 and stop > start:
                breite = math.ceil((stop - start) * 2 / n)
                for k in range(n):
                    von = round((start * 2 + k * breite) * FFT_HZ_JE_BIN)
                    bis = round((start * 2 + (k + 1) * breite) * FFT_HZ_JE_BIN)
                    d[f"s_bin_{von}_{bis}"] = _u(b, i + 4 + 2 * k, 2)
            i += 4 + 2 * n
        if i < len(b) and b[i] == 0x07 and i + 7 <= len(b):  # BME280
            t, h, p = _s(b, i + 1, 2), _u(b, i + 3, 2), _u(b, i + 5, 2)
            if t or h or p:
                d.update(t=t / 100, h=h / 100, p=p)
            i += 7
        if i + 5 <= len(b) and b[i] in UHR_KENNUNG:          # Gerätezeit (nachgesendete Werte)
            ts = _u(b, i + 1, 4)
            if ts >= UNIX_2019:
                d["Messzeit_unix"] = ts
                d["Status"] = {"zeit_ok": UHR_KENNUNG[b[i]] == "rtc"}
    except IndexError:
        return None
    return d
