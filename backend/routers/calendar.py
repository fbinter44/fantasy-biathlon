"""
Routes calendrier et résultats officiels IBU.

GET /calendar                    → liste des venues avec leurs courses (auth requise)
GET /calendar/{race_id}/results  → résultats top 40 / top 30 mass start (auth requise)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.config import Settings, get_settings
from backend.dependencies import get_current_user
from backend.models.calendar import RaceInfo, RaceResult, VenueInfo
from core.ibu.client import IBUClient
from utils.biathlon_data import DISCIPLINE_MAP, GENDERS_CODES, FLAGS, VENUES_NAMES

router = APIRouter(prefix="/calendar", tags=["calendar"])

DISCIPLINE_DISPLAY = {
    "SP": "Sprint",
    "PU": "Poursuite",
    "MS": "Mass Start",
    "IN": "Individuel",
    "SI": "Individuel",
}

# Mass start : 30 participants max, autres : top 40
TOP_LIMIT = {"MS": 30}
DEFAULT_TOP = 40


def _build_client(settings: Settings, season: str | None = None) -> IBUClient:
    return IBUClient(season_code=season or settings.ibu_season_code)


@router.get("", response_model=list[VenueInfo])
def get_calendar(
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
    _user_id: str = Depends(get_current_user),
):
    """Retourne toutes les venues de la saison avec leurs épreuves individuelles."""
    client = _build_client(settings, season)
    client.competitions.load_venues()

    now = datetime.now(timezone.utc)
    venues_out = []

    for venue in client.competitions.venues:
        if not venue.epreuves:
            continue

        races = []
        for ep in venue.epreuves:
            gender = GENDERS_CODES.get(ep.category, ep.category)
            discipline_key = DISCIPLINE_MAP.get(ep.discipline, ep.discipline)
            discipline_display = DISCIPLINE_DISPLAY.get(ep.discipline, ep.discipline)

            races.append(RaceInfo(
                race_id=ep.race_id,
                short_desc=ep.short_desc,
                discipline=discipline_key,
                discipline_display=discipline_display,
                gender=gender,
                start_time=ep.start_time.isoformat(),
                is_past=ep.start_time <= now,
            ))

        # Tri chronologique
        races.sort(key=lambda r: r.start_time)

        # Nom de lieu simplifié si dispo dans le mapping
        raw_location = venue.epreuves[0].location
        location = VENUES_NAMES.get(raw_location, raw_location)

        venues_out.append(VenueInfo(
            event_id=venue.event_id,
            location=location,
            start_date=venue.start_date.isoformat(),
            end_date=venue.end_date.isoformat(),
            races=races,
        ))

    return venues_out


@router.get("/{race_id}/results", response_model=list[RaceResult])
def get_race_results(
    race_id: str,
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
    _user_id: str = Depends(get_current_user),
):
    """Retourne les résultats d'une course passée (top 40, top 30 pour la mass start)."""
    client = _build_client(settings, season)
    client.competitions.load_venues()

    # Recherche de l'épreuve
    target = None
    for venue in client.competitions.venues:
        for ep in venue.epreuves:
            if ep.race_id == race_id:
                target = ep
                break
        if target:
            break

    if target is None:
        raise HTTPException(status_code=404, detail="Course introuvable.")

    now = datetime.now(timezone.utc)
    if target.start_time > now:
        raise HTTPException(status_code=400, detail="Cette course n'a pas encore eu lieu.")

    target.load_results()

    if target.results is None or target.results.empty:
        return []

    limit = TOP_LIMIT.get(target.discipline, DEFAULT_TOP)
    df = target.results.head(limit)

    results = []
    for _, row in df.iterrows():
        nation = str(row.get("nation", ""))
        results.append(RaceResult(
            rank=int(row.get("rank", 0)),
            name=str(row.get("name", "")),
            ibu_id=str(row.get("ibu_id", "")),
            nation=nation,
            flag=FLAGS.get(nation, "🏳️"),
            points=float(row.get("points", 0) or 0),
        ))

    return results
