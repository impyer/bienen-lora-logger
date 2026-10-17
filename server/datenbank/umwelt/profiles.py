# SPDX-License-Identifier: GPL-3.0-or-later
"""Versioned field semantics. Device and apiary identities come from configuration."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    quantity: str
    name: str
    unit: str
    semantics: str = 'momentan'
    aggregation: str = 'mittel'
    display: str = 'linie'
    depth: int | None = None


WEATHER = {
    't': Field('temperatur', 'Lufttemperatur', '°C'),
    'h': Field('feuchte', 'Relative Luftfeuchte', '%'),
    'p_hpa': Field('luftdruck', 'Luftdruck', 'hPa'),
    'l': Field('beleuchtungsstaerke', 'Beleuchtungsstärke', 'lx'),
    'uv': Field('uv_index', 'UV-Index', 'Index'),
    'wind_ms': Field('windgeschwindigkeit', 'Windgeschwindigkeit', 'm/s'),
    'wind_dir_deg': Field('windrichtung', 'Windrichtung', '°', 'zirkulaer', 'vektor', 'punkte'),
    'gust_ms': Field('windboee', 'Windböe', 'm/s', 'spitze', 'max'),
    'rain_mmh': Field('regenrate', 'Regenrate', 'mm/h', display='balken'),
    # Reset/observation support of this source counter is not established.
    'rain_mm': Field('regen_summe', 'Regenzähler (Reset unbekannt)', 'mm', 'unbekannte_summe', 'keine', 'stufe'),
    'battery_pct': Field('batterie_prozent', 'Batterieladung', '%', aggregation='letzter'),
    'interval_min': Field('sendeintervall', 'Sendeintervall', 'min', aggregation='letzter'),
}
SOIL = {
    f'temp_{depth}cm': Field('temperatur', f'Bodentemperatur {depth} cm', '°C', depth=depth)
    for depth in (5, 20, 50)
}
SOIL.update({
    'battery_v': Field('batteriespannung', 'Batteriespannung', 'V', aggregation='letzter'),
    'alarm_status': Field('alarm_status', 'Alarmstatus', 'Status', 'status', 'letzter', 'stufe'),
})
PROFILES = {'s2120': WEATHER, 'boden': SOIL}
TIME_FIELD = {'s2120': 'zeit_utc', 'boden': 'time_utc'}
DEVICE_FIELD = {'s2120': 'station', 'boden': 'device_id'}
REQUIRED = {
    's2120': {'zeit_utc', 'stand', 'station', *list(WEATHER)[:10]},
    'boden': {'time_utc', 'stand', 'device_id', 'temp_5cm', 'temp_20cm', 'temp_50cm'},
}
TELEMETRY = {'unix', 'ortszeit', 'f_cnt', 'f_port', 'rssi', 'snr', 'gateways',
             'sf', 'payload_hex', 'payload_base64', 'message_id', 'warnungen'}
