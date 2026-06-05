"""
Routes athlètes — données statiques issues de biathletes_data/athletes_info.json.

GET /athletes              → liste complète
GET /athletes/{ibu_id}     → un athlète
GET /athletes?gender=M|W   → filtré par genre
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from utils.biathlon_data import ATHLETES_BY_IBUID, FLAGS, athlete_label

router = APIRouter(prefix="/athletes", tags=["athletes"])


class AthleteResponse(BaseModel):
    ibu_id: str
    family_name: str
    given_name: str
    nation: str
    flag: str
    gender: str   # "M" | "W"
    label: str    # ex: "🇫🇷 Fillon Maillet Quentin"


def _to_response(ibu_id: str, info: dict) -> AthleteResponse:
    return AthleteResponse(
        ibu_id=ibu_id,
        family_name=info["FamilyName"],
        given_name=info["GivenName"],
        nation=info["NAT"],
        flag=FLAGS.get(info["NAT"], "🏳️"),
        gender=info["GenderId"],
        label=athlete_label(ibu_id),
    )


@router.get("", response_model=list[AthleteResponse])
def list_athletes(gender: Optional[str] = Query(None, regex="^[MW]$")):
    athletes = [
        _to_response(ibu_id, info)
        for ibu_id, info in ATHLETES_BY_IBUID.items()
        if gender is None or info["GenderId"] == gender
    ]
    return sorted(athletes, key=lambda a: a.family_name)


@router.get("/{ibu_id}", response_model=AthleteResponse)
def get_athlete(ibu_id: str):
    info = ATHLETES_BY_IBUID.get(ibu_id)
    if not info:
        raise HTTPException(status_code=404, detail="Athlète introuvable.")
    return _to_response(ibu_id, info)
