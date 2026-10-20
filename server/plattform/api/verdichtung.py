# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Verdichtung von Messreihen für die Anzeige (ohne Datenbank, testbar).

Die Verdichtung einer Messgröße steht im Katalog (messgroesse.verdichtung). Hier wird sie nur in einen SQL-Ausdruck
übersetzt (Weißliste, nie Text aus der Anfrage) und die Rasterweite aus dem Zeitraum gewählt.
"""
from datetime import timedelta

MAX_PUNKTE = 2000
MAX_ZEITRAUM = timedelta(days=400)

# Rasterweiten, aus denen gewählt wird (kleinste, die höchstens MAX_PUNKTE Punkte je Reihe ergibt)
RASTER = [timedelta(minutes=m) for m in (1, 5, 10, 15, 30, 60, 120, 180, 360, 720, 1440)]

# messgroesse.verdichtung → Aggregat über die Spalten "wert" und "zeit" einer Rastergruppe
AGGREGATE = {
    "mittel": "avg(wert)",
    "median": "percentile_cont(0.5) WITHIN GROUP (ORDER BY wert)",
    "summe": "sum(wert)",
    "max": "max(wert)",
    "min": "min(wert)",
    "letzter": "(array_agg(wert ORDER BY zeit DESC))[1]",
    # Kreismittel für Richtungen: 350° und 10° ergeben 0°, nicht 180°
    "vektor": "mod((degrees(atan2(avg(sin(radians(wert))), avg(cos(radians(wert))))) + 360)::numeric, 360)::float8",
    # Zähler mit unbekanntem Rücksetzzeitpunkt (z. B. Regen): nie summieren, letzter Zählerstand der Gruppe
    "keine": "(array_agg(wert ORDER BY zeit DESC))[1]",
}


def aggregat(verdichtung):
    """SQL-Ausdruck zur Verdichtung; ValueError bei unbekannter Verdichtung."""
    try:
        return AGGREGATE[verdichtung]
    except KeyError:
        raise ValueError(f"unbekannte Verdichtung {verdichtung!r}") from None


def raster(von, bis, max_punkte=MAX_PUNKTE):
    """Kleinste Rasterweite, mit der der Zeitraum höchstens max_punkte Gruppen hat."""
    dauer = bis - von
    for r in RASTER:
        if dauer / r <= max_punkte:
            return r
    return RASTER[-1]


def mit_luecken(punkte, raster_weite, faktor=3):
    """Fügt null zwischen zwei Punkten ein, die weiter als faktor × max(Raster, üblicher Abstand) auseinander liegen.

    punkte: [(datetime, wert)] aufsteigend. So zeigt die Kurve eine Lücke statt einer Verbindungslinie,
    und eine fehlende Messung wird nie zu 0 (Konzept 0.2, §3.1: Lücke ≠ 0).
    """
    if len(punkte) < 2:
        return list(punkte)
    abstaende = sorted(b[0] - a[0] for a, b in zip(punkte, punkte[1:]))
    ueblich = abstaende[len(abstaende) // 2]
    grenze = faktor * max(raster_weite, ueblich)
    aus = [punkte[0]]
    for a, b in zip(punkte, punkte[1:]):
        if b[0] - a[0] > grenze:
            aus.append((a[0] + (b[0] - a[0]) / 2, None))
        aus.append(b)
    return aus
