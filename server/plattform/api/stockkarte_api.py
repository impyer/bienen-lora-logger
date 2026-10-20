# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Philipp Schnabel
"""Endpunkte der Stockkarte (Phase C, Teil 2). Schreiben wie in der Verwaltung nur mit Sitzung, CSRF-Token und
passender Herkunft; Commit vor der Antwort (scope="function")."""
from datetime import date, datetime, timezone
from typing import Dict, List, Literal, Optional, Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from . import stockkarte as sk

GENAUIGKEIT = Literal["exakt", "geschaetzt", "nur_datum"]
MASSNAHMEN = Literal["behandlung", "fuetterung", "ernte", "zarge_auf", "zarge_ab", "umsetzen", "tarieren", "sonstiges"]
Wert = Union[bool, int, float, str, None]


def _utc(v):
    if v is not None and v.tzinfo is None:
        raise ValueError("Zeitzone fehlt (z. B. 2026-10-20T14:30:00+02:00)")
    return v.astimezone(timezone.utc) if v is not None else v


class MitZeit(BaseModel):
    @field_validator("zeit", "von", "bis", check_fields=False)
    @classmethod
    def mit_zone(cls, v):
        return _utc(v)


class DurchsichtNeu(MitZeit):
    volk_ids: List[int] = Field(min_length=1, max_length=50)
    zeit: datetime
    zeitgenauigkeit: GENAUIGKEIT = "exakt"
    checkliste_version_id: Optional[int] = None
    notiz: Optional[str] = Field(default=None, max_length=4000)
    werte: Dict[str, Wert] = Field(default_factory=dict)


class DurchsichtAendern(MitZeit):
    zeit: datetime
    zeitgenauigkeit: Optional[GENAUIGKEIT] = None
    notiz: Optional[str] = Field(default=None, max_length=4000)
    werte: Dict[str, Wert] = Field(default_factory=dict)


class MassnahmeDaten(MitZeit):
    art: MASSNAHMEN
    von: datetime
    bis: Optional[datetime] = None
    zeitgenauigkeit: Optional[GENAUIGKEIT] = None
    menge: Optional[float] = Field(default=None, ge=0)
    einheit: Optional[str] = Field(default=None, max_length=20)
    mittel: Optional[str] = Field(default=None, max_length=120)
    notiz: Optional[str] = Field(default=None, max_length=2000)


class MassnahmeNeu(MassnahmeDaten):
    volk_ids: List[int] = Field(min_length=1, max_length=50)
    durchsicht_id: Optional[int] = None


class VarroaDaten(MitZeit):
    methode: Literal["windel", "puderzucker", "auswaschung"]
    von: datetime
    bis: datetime
    milben: int = Field(ge=0, le=100000)
    anmerkung: Optional[str] = Field(default=None, max_length=2000)
    zeitgenauigkeit: Optional[GENAUIGKEIT] = None


class VarroaNeu(VarroaDaten):
    volk_ids: List[int] = Field(min_length=1, max_length=50)


class AufgabeNeu(BaseModel):
    faellig_am: date
    text: str = Field(min_length=1, max_length=500)
    volk_ids: List[int] = Field(default_factory=list, max_length=50)
    stand_id: Optional[int] = None
    durchsicht_id: Optional[int] = None


class Erledigt(MitZeit):
    zeit: datetime
    erledigt: bool = True


class Gueltig(MitZeit):
    zeit: datetime


def router(lesen, schreiben):
    r = APIRouter(prefix="/api/stockkarte")
    S = Depends(schreiben, scope="function")

    @r.get("/checklisten")
    def checklisten(cur=Depends(lesen)):
        return sk.checklisten(cur)

    @r.post("/checkliste/standard")
    def checkliste_standard(d: Gueltig, cur=S):
        return {"version_id": sk.checkliste_uebernehmen(cur, d.zeit)}

    @r.post("/durchsichten")
    def durchsicht_neu(d: DurchsichtNeu, cur=S):
        return {"ids": sk.durchsicht_anlegen(cur, d.volk_ids, d.zeit, d.zeitgenauigkeit, d.checkliste_version_id, d.notiz, d.werte)}

    @r.put("/durchsichten/{durchsicht_id}")
    def durchsicht_aendern(durchsicht_id: int, d: DurchsichtAendern, cur=S):
        return {"zeitgenauigkeit": sk.durchsicht_aendern(cur, durchsicht_id, d.zeit, d.zeitgenauigkeit, d.notiz, d.werte)}

    @r.delete("/durchsichten/{durchsicht_id}")
    def durchsicht_loeschen(durchsicht_id: int, cur=S):
        sk.durchsicht_loeschen(cur, durchsicht_id)
        return {"geloescht": durchsicht_id}

    @r.post("/massnahmen")
    def massnahme_neu(d: MassnahmeNeu, cur=S):
        return {"ids": sk.massnahme_anlegen(cur, d.volk_ids, d.art, d.von, d.bis, d.zeitgenauigkeit or "exakt", d.menge,
                                            d.einheit, d.mittel, d.notiz, d.durchsicht_id)}

    @r.put("/massnahmen/{massnahme_id}")
    def massnahme_aendern(massnahme_id: int, d: MassnahmeDaten, cur=S):
        sk.massnahme_aendern(cur, massnahme_id, d.art, d.von, d.bis, d.zeitgenauigkeit, d.menge, d.einheit, d.mittel, d.notiz)
        return {"id": massnahme_id}

    @r.delete("/massnahmen/{massnahme_id}")
    def massnahme_loeschen(massnahme_id: int, cur=S):
        sk.loeschen(cur, "massnahme", massnahme_id)
        return {"geloescht": massnahme_id}

    @r.post("/varroa")
    def varroa_neu(d: VarroaNeu, cur=S):
        return {"ids": sk.varroa_anlegen(cur, d.volk_ids, d.methode, d.von, d.bis, d.milben, d.anmerkung, d.zeitgenauigkeit or "exakt")}

    @r.put("/varroa/{varroa_id}")
    def varroa_aendern(varroa_id: int, d: VarroaDaten, cur=S):
        sk.varroa_aendern(cur, varroa_id, d.methode, d.von, d.bis, d.milben, d.anmerkung, d.zeitgenauigkeit)
        return {"id": varroa_id}

    @r.delete("/varroa/{varroa_id}")
    def varroa_loeschen(varroa_id: int, cur=S):
        sk.loeschen(cur, "varroa_messung", varroa_id)
        return {"geloescht": varroa_id}

    @r.get("/eintrag/{art}/{eintrag_id}")
    def eintrag(art: Literal["durchsicht", "massnahme", "varroa"], eintrag_id: int, cur=Depends(lesen)):
        return sk.eintrag(cur, art, eintrag_id)

    @r.get("/aufgaben")
    def aufgaben(alle: bool = False, volk_id: Optional[int] = None, cur=Depends(lesen)):
        return sk.aufgaben(cur, not alle, volk_id)

    @r.post("/aufgaben")
    def aufgabe_neu(d: AufgabeNeu, cur=S):
        return {"ids": sk.aufgabe_anlegen(cur, d.faellig_am, d.text, d.volk_ids, d.stand_id, d.durchsicht_id)}

    @r.post("/aufgaben/{aufgabe_id}/erledigt")
    def aufgabe_erledigt(aufgabe_id: int, d: Erledigt, cur=S):
        sk.aufgabe_erledigt(cur, aufgabe_id, d.zeit, d.erledigt)
        return {"id": aufgabe_id}

    @r.delete("/aufgaben/{aufgabe_id}")
    def aufgabe_loeschen(aufgabe_id: int, cur=S):
        sk.loeschen(cur, "aufgabe", aufgabe_id)
        return {"geloescht": aufgabe_id}

    return r
