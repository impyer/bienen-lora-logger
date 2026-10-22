// TTN uplink formatter Dragino LSN50v2-D23 (soil temperature, 3 DS18B20 probes), FPort 2, 11 bytes.
// Probe colours per Dragino manual LSN50v2-D2x, 2.3.1 "Decode corresponding probe color" (D23):
//   C1 = white (bytes 2-3), C2 = red (bytes 7-8), C3 = black (bytes 9-10).
// The Dragino decoder names C1/C2 "Temp_Red"/"Temp_White" (only correct for the D20) - swapped on the D23.
// This formatter uses own names, so that no field name ever changes its meaning:
//   temp_weiss = white probe, temp_rot = red probe, temp_schwarz = black probe.
// Field test 22.10.2026 at Hauptstand: white = 5 cm, red = 20 cm, black = 50 cm (largest daily swing on C1).
// Source ASCII only (TTN console rejected pasted UTF-8 before, see formatter/README.md).
// SPDX-License-Identifier: GPL-3.0-or-later
function decodeUplink(input) {
  var b = input.bytes;
  if (input.fPort !== 2) return { errors: ['unknown FPort ' + input.fPort] };
  if (!b || b.length !== 11) return { errors: ['expected 11 bytes, got ' + (b ? b.length : 0)] };
  var mode = (b[6] & 0x7c) >> 2;
  function temp(hi, lo) {           // signed, 0.1 degC; FFFF = probe missing
    if (b[hi] === 0xff && b[lo] === 0xff) return null;
    return (((b[hi] << 24) >> 16) | b[lo]) / 10;
  }
  function s8(x) { return (x << 24) >> 24; }
  var data = {};
  if (mode === 3) {
    data.Work_mode = 'DS18B20';
    data.BatV = ((b[0] << 8) | b[1]) / 1000;
    data.ALARM_status = (b[6] & 0x01) ? 'TRUE' : 'FALSE';
    data.temp_weiss = temp(2, 3);
    data.temp_rot = temp(7, 8);
    data.temp_schwarz = temp(9, 10);
  } else if (mode === 31) {         // reply to alarm poll: limits only, no measurements
    data.Work_mode = 'ALARM';
    data.temp_weiss_min = s8(b[4]); data.temp_weiss_max = s8(b[5]);
    data.temp_rot_min = s8(b[7]); data.temp_rot_max = s8(b[8]);
    data.temp_schwarz_min = s8(b[9]); data.temp_schwarz_max = s8(b[10]);
  } else {
    return { errors: ['unknown mode ' + mode] };
  }
  return { data: data };
}
