# SPDX-License-Identifier: GPL-3.0-or-later
"""Transaktionaler PostgreSQL-Speicher der nativen Bienenlogger-Stockkarte.

Kein HTTP-Endpunkt; Authentifizierung und Rollen gehören in eine spätere API.
Keine BEEP-Laufzeitabhängigkeit. Eingaben werden auch serverseitig validiert.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
import re

from psycopg.types.json import Jsonb

BERLIN = ZoneInfo("Europe/Berlin")
DECIMALS = re.compile(r"^number_([0-3])_decimals$")
CHOICES = {"select", "options", "bee_subspecies"}
MULTI = {"list"}
BOOL = {"boolean", "boolean_yes_red", "list_item"}
NUMBERS = {"number", "number_positive", "number_negative", "number_percentage",
           "number_degrees", "score", "grade", "score_amount", "score_quality",
           "square_25cm2", "smileys_3", "slider"}
TEXT = {"text", "string"}
UNSUPPORTED = {"file", "image"}


def _calendar(value):
    if isinstance(value, datetime):
        raise ValueError("Ein Kalendertag darf keine Uhrzeit enthalten")
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Datum nur im Format YYYY-MM-DD")
    try:
        result = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Ungültiges Kalenderdatum") from error
    if result.isoformat() != value:
        raise ValueError("Ungültiges Kalenderdatum")
    return result


def _moment(day, value, accuracy):
    if accuracy not in {"nur_datum", "exakt", "geschaetzt"}:
        raise ValueError("Ungültige Zeitgenauigkeit")
    if accuracy == "nur_datum":
        if value is not None:
            raise ValueError("Nur-Datum-Eintrag darf keine künstliche Uhrzeit erhalten")
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("Ungültiger Zeitpunkt") from error
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Für eine Uhrzeit ist ein Zeitzonen-Offset erforderlich")
    if value.astimezone(BERLIN).date() != day:
        raise ValueError("Uhrzeit und lokaler Kalendertag widersprechen sich")
    return value


def _value(cur, field, raw):
    kind, meta, required = field
    if kind in UNSUPPORTED:
        raise ValueError("Dateianhänge benötigen eigene geschützte Speicherung")
    if kind in BOOL:
        if not isinstance(raw, bool):
            raise ValueError("Ja/Nein muss ein boolescher Wert sein, nicht 0 oder Text")
        return raw
    if kind in CHOICES | MULTI:
        cur.execute(
            "SELECT id FROM bienen.sk_option WHERE kategorie_id=%s AND NOT inaktiv",
            (meta["field_id"],),
        )
        allowed = {row[0] for row in cur.fetchall()}
        if kind in MULTI:
            if not isinstance(raw, list) or any(not isinstance(v, str) or v not in allowed for v in raw):
                raise ValueError("Ungültige Mehrfachauswahl")
            return list(dict.fromkeys(raw))
        if not isinstance(raw, str) or raw not in allowed:
            raise ValueError("Ungültige Auswahl-ID")
        return raw
    if kind == "date":
        return _calendar(raw).isoformat()
    number_match = DECIMALS.fullmatch(kind)
    if kind in NUMBERS or number_match:
        if isinstance(raw, bool) or not isinstance(raw, (int, float, Decimal)):
            raise ValueError("Zahl erwartet")
        try:
            number = Decimal(str(raw))
        except InvalidOperation as error:
            raise ValueError("Ungültige Zahl") from error
        if not number.is_finite():
            raise ValueError("Nicht endliche Zahl")
        minimum = meta.get("min")
        maximum = meta.get("max")
        if minimum is not None and number < Decimal(str(minimum)):
            raise ValueError("Zahlenwert unterhalb Minimum")
        if maximum is not None and number > Decimal(str(maximum)):
            raise ValueError("Zahlenwert oberhalb Maximum")
        if kind in {"number_positive", "number_percentage"} and number < 0:
            raise ValueError("Negative Zahl unzulässig")
        if kind == "number_percentage" and number > 100:
            raise ValueError("Prozentwert > 100")
        if kind == "smileys_3" and (number < 1 or number > 3):
            raise ValueError("Bewertung nur 1 bis 3")
        if kind in {"score", "grade", "score_amount", "score_quality", "smileys_3"} and number != number.to_integral_value():
            raise ValueError("Bewertung muss ganzzahlig sein")
        digits = meta.get("decimals")
        if digits is None and number_match:
            digits = int(number_match.group(1))
        if digits is not None:
            if not isinstance(digits, int) or digits < 0 or digits > 8:
                raise ValueError("Ungültige Nachkommastellen-Vorgabe")
            if number.as_tuple().exponent < -digits and number != number.quantize(Decimal(1).scaleb(-digits)):
                raise ValueError("Zu viele Nachkommastellen")
        return int(number) if number == number.to_integral_value() else float(number)
    if kind in TEXT:
        if not isinstance(raw, str) or len(raw) > (4000 if kind == "text" else 600):
            raise ValueError("Textfeld ungültig oder zu lang")
        return raw
    raise ValueError("Nicht unterstützter Eingabetyp: " + kind)


def validate_values(cur, values, checklist=None):
    """Prüft Kategorie-/Options-IDs und Typen auch bei direktem API-Zugriff."""
    if not isinstance(values, dict) or len(values) > 300:
        raise ValueError("Werte müssen ein Objekt mit maximal 300 Kategorien sein")
    if any(not isinstance(k, str) for k in values):
        raise ValueError("Kategorie-IDs müssen Strings sein")
    ids = list(values.keys())
    cur.execute("SELECT id, eingabetyp, pflicht, meta FROM bienen.sk_kategorie WHERE id=ANY(%s)", (ids,))
    definitions = {row[0]: (row[1], row[3], row[2]) for row in cur.fetchall()}
    if set(ids) != set(definitions):
        raise ValueError("Unbekannte Kategorie-ID")
    if checklist is not None:
        cur.execute(
            """SELECT kategorie_id, pflicht FROM bienen.sk_checkliste_feld
               WHERE checkliste_id=%s AND version=%s""", checklist,
        )
        selections = dict(cur.fetchall())
        if not selections:
            raise ValueError("Checklisten-Version nicht vorhanden oder leer")
        if not set(ids).issubset(selections):
            raise ValueError("Wert gehört nicht zur gewählten Checkliste")
        for key, required in selections.items():
            if required and (key not in values or values[key] is None or values[key] == ""):
                raise ValueError("Pflichtfeld fehlt: " + key)
    checked = {}
    for key, raw in values.items():
        if raw is None:
            if definitions[key][2]:
                raise ValueError("Pflichtkategorie darf nicht NULL sein")
            continue
        kind, meta, required = definitions[key]
        # Metadaten werden nicht mit einer fremden Feld-ID vertraut.
        info = dict(meta)
        info["field_id"] = key
        checked[key] = _value(cur, (kind, info, required), raw)
    return checked


def write_inspection(conn, *, volk_id=None, entry_id=None, source="eigen",
                     external_id=None, event_date, event_time=None,
                     accuracy="nur_datum", checklist=None, values=None,
                     note="", author, reason, expected_revision=None):
    """Erstellt oder revidiert atomar. Rückgabe (id, revision, neu_geschrieben).

    Bei gleichem BEEP-Quellschlüssel ist erneuter Import idempotent; keine
    Revision wird geschrieben. Revisionen benutzen eine Row-Lock auf sk_durchsicht.
    """
    day = _calendar(event_date)
    instant = _moment(day, event_time, accuracy)
    if not isinstance(author, str) or not author.strip():
        raise ValueError("Erfasser erforderlich")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Änderungsgrund erforderlich")
    if not isinstance(note, str) or len(note) > 10000:
        raise ValueError("Notiz ungültig")
    if checklist is not None and (
        not isinstance(checklist, (tuple, list)) or len(checklist) != 2
    ):
        raise ValueError("Checkliste benötigt (ID, Version)")
    if source not in {"eigen", "beep_import"}:
        raise ValueError("Ungültige Quelle")
    if source == "beep_import" and (not isinstance(external_id, str) or not external_id.strip()):
        raise ValueError("BEEP-Import benötigt Quell-ID")
    with conn.transaction():
        with conn.cursor() as cur:
            checked = validate_values(cur, values or {}, checklist)
            if entry_id is None:
                if not isinstance(volk_id, int) or isinstance(volk_id, bool):
                    raise ValueError("Volk-ID erforderlich")
                cur.execute(
                    """INSERT INTO bienen.sk_durchsicht(volk_id,quelle,quelle_id)
                       VALUES (%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id""",
                    (volk_id, source, external_id),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """SELECT id,volk_id FROM bienen.sk_durchsicht
                           WHERE quelle=%s AND quelle_id=%s""",
                        (source, external_id),
                    )
                    existing = cur.fetchone()
                    if existing is None or existing[1] != volk_id:
                        raise ValueError("Quell-ID gehört bereits zu anderem Volk")
                    cur.execute(
                        "SELECT max(revision) FROM bienen.sk_durchsicht_revision WHERE durchsicht_id=%s",
                        (existing[0],),
                    )
                    return existing[0], cur.fetchone()[0], False
                entry_id, revision = row[0], 1
            else:
                cur.execute(
                    "SELECT id,volk_id FROM bienen.sk_durchsicht WHERE id=%s FOR UPDATE",
                    (entry_id,),
                )
                existing = cur.fetchone()
                if existing is None:
                    raise ValueError("Durchsicht nicht gefunden")
                if volk_id is not None and volk_id != existing[1]:
                    raise ValueError("Volk-Zuordnung darf nicht verändert werden")
                cur.execute(
                    "SELECT max(revision) FROM bienen.sk_durchsicht_revision WHERE durchsicht_id=%s",
                    (entry_id,),
                )
                current = cur.fetchone()[0]
                if current is None:
                    raise ValueError("Durchsicht ohne Erstversion")
                if expected_revision is None or expected_revision != current:
                    raise ValueError("Versionskonflikt: aktuelle Revision ist " + str(current))
                revision = current + 1
            cl_id, cl_version = checklist if checklist else (None, None)
            cur.execute(
                """INSERT INTO bienen.sk_durchsicht_revision
                   (durchsicht_id,revision,ereignis_datum,ereignis_zeit,zeitgenauigkeit,
                    checkliste_id,checkliste_version,werte,notiz,aenderungsgrund,autor)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (entry_id, revision, day, instant, accuracy, cl_id, cl_version,
                 Jsonb(checked), note, reason, author),
            )
            return entry_id, revision, True


def write_queen_revision(conn, *, queen_id, details, author, reason, expected_revision=None):
    """Historisierte Königinnenangaben. Die Beziehung zum Volk liegt in koenigin_volk."""
    if not isinstance(details, dict) or not details:
        raise ValueError("Königinnenangaben fehlen")
    if not isinstance(author, str) or not author.strip() or not isinstance(reason, str) or not reason.strip():
        raise ValueError("Erfasser und Änderungsgrund erforderlich")
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM bienen.koenigin WHERE id=%s FOR UPDATE", (queen_id,))
            if cur.fetchone() is None:
                raise ValueError("Königin nicht gefunden")
            cur.execute(
                "SELECT max(revision) FROM bienen.sk_koenigin_revision WHERE koenigin_id=%s",
                (queen_id,),
            )
            prev = cur.fetchone()[0]
            if prev is not None and expected_revision != prev:
                raise ValueError("Versionskonflikt bei Königin")
            if prev is None and expected_revision not in (None, 0):
                raise ValueError("Erstversion erforderlich")
            revision = (prev or 0) + 1
            cur.execute(
                """INSERT INTO bienen.sk_koenigin_revision
                   (koenigin_id,revision,daten,aenderungsgrund,autor)
                   VALUES (%s,%s,%s,%s,%s)""",
                (queen_id, revision, Jsonb(details), reason, author),
            )
            return revision


def current_inspections(conn, volk_id):
    """Nur lesend; liefert die letzte, nicht gelöschte Fassung pro Durchsicht."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id,revision,ereignis_datum,ereignis_zeit,zeitgenauigkeit,
                      werte,notiz,quelle,quelle_id
               FROM bienen.sk_durchsicht_aktuell
               WHERE volk_id=%s ORDER BY ereignis_datum DESC,id DESC""",
            (volk_id,),
        )
        return cur.fetchall()
