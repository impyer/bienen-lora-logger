# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Standardkatalog der Messgrößen und Kanalvorlagen für bekannte Geräte.

Der Betrieb startet leer. Diese Listen übernimmt die Verwaltung erst auf Knopfdruck. Die Bedeutung der Quellfelder
folgt dem Kanalinventar (docs/architektur/messgroessen-kanalinventar.csv): Ein Feld wird nur dort vorgeschlagen, wo
seine Bedeutung belegt ist. FeuchteIn und Aux1–3 fehlen deshalb bewusst (Kanalinventar „OFFEN“).
"""

# code, name, einheit, semantik, verdichtung, achse, darstellung, farbe, öffentlich
MESSGROESSEN = [
    ("gewicht", "Gewicht", "kg", "momentan", "mittel", "gewicht", "linie", "#8a5a00", True),
    ("temperatur", "Temperatur", "°C", "momentan", "mittel", "temperatur", "linie", "#c0392b", True),
    ("feuchte", "Relative Feuchte", "%", "momentan", "mittel", "feuchte", "linie", "#2471a3", False),
    ("spannung", "Spannung", "V", "momentan", "letzter", "spannung", "stufe", "#7f8c8d", False),
    ("licht", "Helligkeit", "lx", "momentan", "max", "licht", "linie", "#d4ac0d", False),
    ("luftdruck", "Luftdruck", "hPa", "momentan", "mittel", "druck", "linie", "#5d6d7e", True),
    ("wind", "Windgeschwindigkeit", "m/s", "momentan", "mittel", "wind", "linie", "#17a589", True),
    ("windboe", "Windböe", "m/s", "spitze", "max", "wind", "punkte", "#0e6655", False),
    ("windrichtung", "Windrichtung", "°", "zirkulaer", "vektor", "richtung", "pfeile", "#117864", False),
    ("regen_summe", "Niederschlag (Zähler)", "mm", "unbekannte_summe", "keine", "regen", "balken", "#1f618d", False),
    ("regen_rate", "Regenrate", "mm/h", "momentan", "max", "regenrate", "balken", "#2e86c1", True),
    ("uv", "UV-Index", "", "momentan", "max", "uv", "linie", "#8e44ad", False),
]
MESSGROESSEN_FELDER = ("code", "name", "einheit", "semantik", "verdichtung", "achse", "darstellung", "farbe", "oeffentlich")

# Vorlage → Ziel der Zuordnung (volk/stand), Geräteart und Kanäle (Quellfeld, Messgröße, Zone der Messstelle)
VORLAGEN = {
    "beelogger": {
        "name": "beelogger LoRa (Funkformat 1/2, Formatter formatter/formatter.js)",
        "ziel": "volk", "art": "stockwaage",
        "kanaele": [("Gewicht", "gewicht", "waage"), ("TempIn", "temperatur", "brutnest"),
                    ("TempOut", "temperatur", "aussen"), ("FeuchteOut", "feuchte", "aussen"),
                    ("VBatt", "spannung", "elektronik")],
    },
    "s2120": {
        "name": "SenseCAP S2120 Wetterstation (Formatter formatter/s2120_beep_formatter.js)",
        "ziel": "stand", "art": "wetter",
        "kanaele": [("t", "temperatur", "luft_stand"), ("h", "feuchte", "luft_stand"), ("p_hpa", "luftdruck", "luft_stand"),
                    ("wind_ms", "wind", "luft_stand"), ("gust_ms", "windboe", "luft_stand"),
                    ("wind_dir_deg", "windrichtung", "luft_stand"), ("rain_mm", "regen_summe", "luft_stand"),
                    ("rain_mmh", "regen_rate", "luft_stand"), ("uv", "uv", "luft_stand"), ("l", "licht", "luft_stand")],
    },
}

# Standard-Checkliste der Durchsicht (Vorbild BEEP-Kategorien, Konzept 0.2 §5.2). Merkmal: (code, name, eingabetyp,
# einheit, optionen, gruppe). Eine geänderte Liste wird als neue Version angelegt; alte Durchsichten behalten ihre (K-10).
CHECKLISTE_NAME = "Durchsicht"
CHECKLISTE_GRUPPEN = [("g_koenigin_brut", "Königin und Brut"), ("g_volk", "Volk"), ("g_futter_raum", "Futter und Raum"),
                      ("g_gesundheit", "Gesundheit")]
CHECKLISTE = [
    ("koenigin_gesehen", "Königin gesehen", "janein", None, None, "g_koenigin_brut"),
    ("stifte", "Stifte (Eier)", "janein", None, None, "g_koenigin_brut"),
    ("offene_brut", "Offene Brut", "janein", None, None, "g_koenigin_brut"),
    ("verdeckelte_brut", "Verdeckelte Brut", "janein", None, None, "g_koenigin_brut"),
    ("brutwaben", "Brutwaben", "ganzzahl", "Waben", None, "g_koenigin_brut"),
    ("weiselzellen", "Weiselzellen", "liste", None, ["keine", "Spielnäpfchen", "bestiftet", "verdeckelt"], "g_koenigin_brut"),
    ("wabengassen", "Besetzte Wabengassen", "ganzzahl", "Gassen", None, "g_volk"),
    ("volksstaerke", "Volksstärke", "bewertung", None, None, "g_volk"),
    ("sanftmut", "Sanftmut", "bewertung", None, None, "g_volk"),
    ("wabensitz", "Wabensitz", "bewertung", None, None, "g_volk"),
    ("schwarmstimmung", "Schwarmstimmung", "janein", None, None, "g_volk"),
    ("futtervorrat", "Futtervorrat", "liste", None, ["knapp", "ausreichend", "reichlich"], "g_futter_raum"),
    ("futterwaben", "Futterwaben", "ganzzahl", "Waben", None, "g_futter_raum"),
    ("raum", "Platz im Volk", "liste", None, ["eng", "passend", "viel"], "g_futter_raum"),
    ("krankheitszeichen", "Auffälligkeiten / Krankheitszeichen", "text", None, None, "g_gesundheit"),
]
