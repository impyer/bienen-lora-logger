// TTN uplink formatter SenseCAP S2120 (blocks 4A/4B/4C, battery 03/04) -> BEEP keys t, h, p, l
function s16(b, i) { var v = (b[i] << 8) | b[i + 1]; return v > 32767 ? v - 65536 : v; }
function u16(b, i) { return (b[i] << 8) | b[i + 1]; }
function u32(b, i) { return b[i] * 16777216 + b[i + 1] * 65536 + b[i + 2] * 256 + b[i + 3]; }
function blockLen(id) {
  if ([0x01, 0x20, 0x21, 0x30, 0x31, 0x33, 0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x4A].indexOf(id) >= 0) return 10;
  if (id === 0x02 || id === 0x4B) return 8;
  if (id === 0x03 || id === 0x06) return 1;
  if (id === 0x05 || id === 0x34) return 4;
  if ([0x04, 0x10, 0x32, 0x35, 0x36, 0x37, 0x38, 0x39].indexOf(id) >= 0) return 9;
  if (id === 0x4C) return 6;
  return -1;
}
function decodeUplink(input) {
  var b = input.bytes, i = 0, d = {}, warnings = [];
  while (i < b.length) {
    var id = b[i], n = blockLen(id), o = i + 1;
    if (n < 0 || o + n > b.length) { warnings.push("unknown block or too short at byte " + i); break; }
    if (id === 0x4A) {
      d.t = s16(b, o) / 10;
      d.h = b[o + 2];
      d.l = u32(b, o + 3);
      d.uv = b[o + 7] / 10;
      d.wind_ms = u16(b, o + 8) / 10;
    } else if (id === 0x4B) {
      d.wind_dir_deg = u16(b, o);
      d.rain_mmh = u32(b, o + 2) / 1000;
      d.p = u16(b, o + 6) / 10;
    } else if (id === 0x4C) {
      d.gust_ms = u16(b, o) / 10;
      d.rain_mm = u32(b, o + 2) / 1000;
    } else if (id === 0x03) {
      d.battery_pct = b[o];
    } else if (id === 0x04) {
      d.battery_pct = b[o];
      d.interval_min = u16(b, o + 5);
    }
    i = o + n;
  }
  return { data: d, warnings: warnings };
}
