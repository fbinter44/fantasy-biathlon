"""
Routes pronostics course par course.

GET  /race-pronostics          → {race_id: ibu_id} pour l'utilisateur connecté
PUT  /race-pronostics/{race_id} → définit le vainqueur pronostiqué d'une course
DELETE /race-pronostics/{race_id} → supprime le pronostic d'une course
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.config import Settings, get_settings
from backend.dependencies import get_current_user
from backend.models.race_pronostics import RacePronosticBody, RacePronosticsResponse
from backend.services.db import (
    get_race_pronostics_by_user,
    upsert_race_pronostic,
    delete_race_pronostic,
)
from core.ibu.client import IBUClient

router = APIRouter(prefix="/race-pronostics", tags=["race-pronostics"])


def _find_race(race_id: str, settings: Settings, season: str):
    """Cherche une épreuve dans le calendrier IBU. Lève 404 si introuvable."""
    client = IBUClient(season_code=season)
    client.competitions.load_venues()
    for venue in client.competitions.venues:
        for ep in venue.epreuves:
            if ep.race_id == race_id:
                return ep
    raise HTTPException(status_code=404, detail="Course introuvable.")


@router.get("", response_model=RacePronosticsResponse)
def get_my_race_pronostics(
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
    user_id: str = Depends(get_current_user),
):
    s = season or settings.ibu_season_code
    pronos = get_race_pronostics_by_user(user_id, settings, s)
    return RacePronosticsResponse(pronos=pronos)


@router.put("/{race_id}", response_model=RacePronosticsResponse)
def set_race_pronostic(
    race_id: str,
    body: RacePronosticBody,
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
    user_id: str = Depends(get_current_user),
):
    s = season or settings.ibu_season_code
    ep = _find_race(race_id, settings, s)

    # Refus si la course est déjà passée (protection côté serveur)
    if ep.start_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Cette course est déjà passée, le pronostic ne peut plus être modifié.",
        )

    upsert_race_pronostic(user_id, race_id, body.ibu_id, settings, s)
    pronos = get_race_pronostics_by_user(user_id, settings, s)
    return RacePronosticsResponse(pronos=pronos)


@router.delete("/{race_id}", status_code=204)
def delete_my_race_pronostic(
    race_id: str,
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
    user_id: str = Depends(get_current_user),
):
    s = season or settings.ibu_season_code
    ep = _find_race(race_id, settings, s)
    if ep.start_time <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Course déjà passée.")
    delete_race_pronostic(user_id, race_id, settings, s)
