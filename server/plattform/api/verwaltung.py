# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Endpunkte der Stammdaten-Pflege (Phase C, Teil 1). Alle schreibend: Sitzung + CSRF-Token + passende Herkunft
(PLT26-04, ADR-0003 Nr. 10). Zeiten mit Zeitzone; die Oberfläche rechnet die Eingabe aus Ortszeit um."""
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from . import stammdaten as sd

ZONEN = Literal["brutnest", "deckel", "aussen", "waage", "flugloch", "boden", "luft_stand", "elektronik", "funk"]
ARTEN = Literal["stockwaage", "beep_base", "wetter", "boden", "sonstiges"]


class Zeitpunkt(BaseModel):
    zeit: datetime

    @field_validator("zeit")
    @classmethod
    def mit_zone(cls, v):
        if v is not None and v.tzinfo is None:
            raise ValueError("Zeitzone fehlt (z. B. 2026-10-20T14:30:00+02:00)")
        return v.astimezone(timezone.utc) if v is not None else v


class Text(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class StandDaten(Text):
    ort_oeffentlich: Optional[str] = Field(default=None, max_length=80)


class BeuteDaten(BaseModel):
    bezeichnung: str = Field(min_length=1, max_length=80)
    beutentyp: Optional[str] = Field(default=None, max_length=80)
    rahmenmass: Optional[str] = Field(default=None, max_length=40)
    brutzargen: Optional[int] = Field(default=None, ge=0, le=9)
    honigzargen: Optional[int] = Field(default=None, ge=0, le=9)
    rahmen: Optional[int] = Field(default=None, ge=0, le=99)


class VolkNeu(Zeitpunkt, Text):
    zeit: datetime
    stand_id: int
    platz: Optional[int] = Field(default=None, ge=0, le=999)
    beute: BeuteDaten
    notiz: Optional[str] = Field(default=None, max_length=2000)


class VolkDaten(Text):
    notiz: Optional[str] = Field(default=None, max_length=2000)


class Umsetzen(Zeitpunkt):
    beute: Optional[BeuteDaten] = None
    beute_id: Optional[int] = None
    stand_id: Optional[int] = None
    platz: Optional[int] = Field(default=None, ge=0, le=999)


class Aufloesen(Zeitpunkt):
    art: Literal["aufloesung", "vereinigung"] = "aufloesung"
    ziel_volk_id: Optional[int] = None
    notiz: Optional[str] = Field(default=None, max_length=2000)


class Aufstellen(Zeitpunkt):
    stand_id: int
    platz: Optional[int] = Field(default=None, ge=0, le=999)


class Konfiguration(Zeitpunkt):
    brutzargen: Optional[int] = Field(default=None, ge=0, le=9)
    honigzargen: Optional[int] = Field(default=None, ge=0, le=9)
    rahmen: Optional[int] = Field(default=None, ge=0, le=99)
    notiz: Optional[str] = Field(default=None, max_length=500)


class GeraetDaten(BaseModel):
    name: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")   # TTN-Gerätename
    art: ARTEN
    modell: Optional[str] = Field(default=None, max_length=80)
    dev_eui: Optional[str] = Field(default=None, pattern=r"^([0-9A-Fa-f]{16})?$")


class GeraetAendern(BaseModel):
    art: ARTEN
    modell: Optional[str] = Field(default=None, max_length=80)
    dev_eui: Optional[str] = Field(default=None, pattern=r"^([0-9A-Fa-f]{16})?$")


class Zuordnen(Zeitpunkt):
    volk_id: Optional[int] = None
    stand_id: Optional[int] = None


class KanalNeu(Zeitpunkt):
    quellfeld: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.\[\]-]+$")
    messgroesse: str = Field(min_length=1, max_length=40)
    zone: ZONEN
    bezeichnung: Optional[str] = Field(default=None, max_length=80)
    hoehe_cm: Optional[float] = None
    tiefe_cm: Optional[float] = None
    faktor: float = 1.0
    versatz: float = 0.0
    sensor: Optional[str] = Field(default=None, max_length=120)
    kalibrierung: Optional[str] = Field(default=None, max_length=200)
    status: Literal["geprueft", "ungeprueft"] = "ungeprueft"


class Vorlage(Zeitpunkt):
    vorlage: str


class Messgroesse(BaseModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=80)
    einheit: str = Field(max_length=20)
    semantik: Literal["momentan", "intervallsumme", "spitze", "zaehler", "zirkulaer", "status", "unbekannte_summe"]
    verdichtung: Literal["mittel", "median", "summe", "max", "min", "letzter", "vektor", "keine"]
    achse: str = Field(min_length=1, max_length=40)
    darstellung: Literal["linie", "balken", "punkte", "stufe", "pfeile"] = "linie"
    farbe: Optional[str] = Field(default=None, pattern=r"^(#[0-9a-fA-F]{6})?$")
    oeffentlich: bool = False


def router(lesen, schreiben, nachtragen=None):
    """lesen/schreiben: Abhängigkeiten, die einen Cursor liefern (schreiben: mit Sitzung, CSRF und Commit).
    scope="function": Der Commit läuft vor dem Senden der Antwort, ein fehlgeschlagener Commit wird also gemeldet."""
    r = APIRouter(prefix="/api/verwaltung")

    @r.get("")
    def uebersicht(zeit: Optional[str] = None, cur=Depends(lesen)):
        t = datetime.fromisoformat(zeit).astimezone(timezone.utc) if zeit else datetime.now(timezone.utc)
        return sd.uebersicht(cur, t)

    @r.post("/katalog/standard")
    def katalog(cur=Depends(schreiben, scope="function")):
        return {"neu": sd.katalog_uebernehmen(cur)}

    @r.post("/messgroessen")
    def messgroesse(d: Messgroesse, cur=Depends(schreiben, scope="function")):
        sd.messgroesse_speichern(cur, d.model_dump())
        return {"code": d.code}

    @r.post("/staende")
    def stand_neu(d: StandDaten, cur=Depends(schreiben, scope="function")):
        return {"id": sd.stand_anlegen(cur, d.name, d.ort_oeffentlich)}

    @r.put("/staende/{stand_id}")
    def stand_aendern(stand_id: int, d: StandDaten, cur=Depends(schreiben, scope="function")):
        sd.stand_aendern(cur, stand_id, d.name, d.ort_oeffentlich)
        return {"id": stand_id}

    @r.post("/voelker")
    def volk_neu(d: VolkNeu, cur=Depends(schreiben, scope="function")):
        v, b = sd.volk_anlegen(cur, d.name, d.zeit, d.stand_id, d.platz, d.beute.model_dump(), d.notiz)
        return {"id": v, "beute_id": b}

    @r.put("/voelker/{volk_id}")
    def volk_aendern(volk_id: int, d: VolkDaten, cur=Depends(schreiben, scope="function")):
        sd.volk_aendern(cur, volk_id, d.name, d.notiz)
        return {"id": volk_id}

    @r.post("/voelker/{volk_id}/umsetzen")
    def umsetzen(volk_id: int, d: Umsetzen, cur=Depends(schreiben, scope="function")):
        if (d.beute is None) == (d.beute_id is None):
            raise HTTPException(422, "entweder neue Beute (beute) oder vorhandene (beute_id) angeben")
        b = sd.volk_umsetzen(cur, volk_id, d.zeit, d.beute.model_dump() if d.beute else None, d.beute_id, d.stand_id, d.platz)
        return {"beute_id": b}

    @r.post("/voelker/{volk_id}/aufloesen")
    def aufloesen(volk_id: int, d: Aufloesen, cur=Depends(schreiben, scope="function")):
        return {"zuordnungen_beendet": sd.volk_aufloesen(cur, volk_id, d.zeit, d.ziel_volk_id, d.art, d.notiz)}

    @r.post("/beuten/{beute_id}/aufstellen")
    def aufstellen(beute_id: int, d: Aufstellen, cur=Depends(schreiben, scope="function")):
        sd.beute_aufstellen(cur, beute_id, d.zeit, d.stand_id, d.platz)
        return {"id": beute_id}

    @r.post("/beuten/{beute_id}/konfiguration")
    def konfiguration(beute_id: int, d: Konfiguration, cur=Depends(schreiben, scope="function")):
        sd.beute_konfigurieren(cur, beute_id, d.zeit, d.brutzargen, d.honigzargen, d.rahmen, d.notiz)
        return {"id": beute_id}

    @r.post("/geraete")
    def geraet_neu(d: GeraetDaten, cur=Depends(schreiben, scope="function")):
        return {"id": sd.geraet_anlegen(cur, d.name, d.art, d.modell, d.dev_eui)}

    @r.put("/geraete/{geraet_id}")
    def geraet_aendern(geraet_id: int, d: GeraetAendern, cur=Depends(schreiben, scope="function")):
        sd.geraet_aendern(cur, geraet_id, d.art, d.modell, d.dev_eui)
        return {"id": geraet_id}

    @r.post("/geraete/{geraet_id}/zuordnen")
    def zuordnen(geraet_id: int, d: Zuordnen, cur=Depends(schreiben, scope="function")):
        return {"beendet": sd.geraet_zuordnen(cur, geraet_id, d.zeit, d.volk_id, d.stand_id)}

    @r.post("/geraete/{geraet_id}/kanaele")
    def kanal_neu(geraet_id: int, d: KanalNeu, cur=Depends(schreiben, scope="function")):
        return {"id": sd.kanal_anlegen(cur, geraet_id, d.zeit, d.quellfeld, d.messgroesse, d.zone, d.bezeichnung,
                                       d.hoehe_cm, d.tiefe_cm, d.faktor, d.versatz, d.sensor, d.kalibrierung,
                                       d.zeit if d.kalibrierung else None, d.status)}

    @r.post("/geraete/{geraet_id}/vorlage")
    def vorlage(geraet_id: int, d: Vorlage, cur=Depends(schreiben, scope="function")):
        neu: List[int] = sd.vorlage_anwenden(cur, geraet_id, d.vorlage, d.zeit)
        return {"kanaele": neu}

    @r.post("/kanaele/{kanal_id}/beenden")
    def kanal_beenden(kanal_id: int, d: Zeitpunkt, cur=Depends(schreiben, scope="function")):
        sd.kanal_beenden(cur, kanal_id, d.zeit)
        return {"id": kanal_id}

    @r.post("/geraete/{geraet_id}/nachtragen")
    def nachtragen_endpunkt(geraet_id: int, cur=Depends(schreiben, scope="function")):
        if nachtragen is None:
            raise HTTPException(409, "Nachtragen nicht eingerichtet: in plattform_config.toml [protokolle] lora_log/wetter_log "
                                     "angeben oder server/datenbank/importer.py --nachtragen aufrufen")
        cur.execute("SELECT name FROM geraet WHERE id = %s", (geraet_id,))
        g = cur.fetchone()
        if g is None:
            raise HTTPException(404, "geraet unbekannt")
        return nachtragen(g["name"])

    return r
