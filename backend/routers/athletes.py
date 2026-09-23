"""
Routes athlètes — données statiques issues de biathletes_data/athletes_info.json.

GET /athletes              → liste complète, actuels en tête (voir _priority_ibu_ids)
GET /athletes/{ibu_id}     → un athlète
GET /athletes?gender=M|W   → filtré par genre
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from backend.config import Settings, get_settings
from backend.services.classement_cache import get_or_compute
from core.ibu.client import IBUClient
from utils.biathlon_data import ATHLETES_BY_IBUID, FLAGS, athlete_label, previous_season_code
from utils.cache_helpers import CACHE_ATHLETES_DIR

router = APIRouter(prefix="/athletes", tags=["athletes"])

_STANDINGS_ATTRS = ("general", "sprint", "pursuit", "individual", "mass_start")


class AthleteResponse(BaseModel):
    ibu_id: str
    family_name: str
    given_name: str
    nation: str
    flag: str
    gender: str   # "M" | "W"
    label: str    # ex: "🇫🇷 Fillon Maillet Quentin"
    is_active: bool = False  # a couru en saison courante ou précédente


def _compute_priority_ibu_ids(season: str, client: IBUClient) -> tuple[set[str], set[str]]:
    """
    Deux niveaux de priorité pour faire remonter les biathlètes plausibles en
    tête des listes déroulantes de pronostics, plutôt que les ~11 000
    licenciés IBU de toute l'histoire (dont beaucoup de retraités) :
      1) top_ids : top 20 des standings — l'élite, la plus probable
      2) participant_ids : tous les participants aux courses de la saison —
         le peloton complet, plus large que le seul top 20
    Sur la saison courante ET la précédente, pour ne jamais avoir un résultat
    vide pendant la trêve, avant que la nouvelle saison n'ait produit de
    données. Coûteux (relit tous les résultats de courses de 2 saisons) —
    voir get_or_compute côté appelant pour la mise en cache.
    """
    top_ids: set[str] = set()
    participant_ids: set[str] = set()

    for s in {season, previous_season_code(season)}:
        c = client if s == season else IBUClient(season_code=s)

        men_st, women_st = c.load_standings()
        for standings_obj in (men_st, women_st):
            for attr in _STANDINGS_ATTRS:
                df = getattr(standings_obj, attr, None)
                if df is not None and not df.empty:
                    top_ids.update(df["id"].tolist())

        c.competitions.load_venues_results()
        for venue in c.competitions.venues:
            for ep in venue.epreuves:
                if ep.results is not None and not ep.results.empty:
                    participant_ids.update(ep.results["ibu_id"].tolist())

    return top_ids, participant_ids


def _priority_ibu_ids(season: str) -> tuple[set[str], set[str]]:
    client = IBUClient(season_code=season)
    return get_or_compute(
        f"priority_ibu_ids_{season}.pkl",
        client,
        ["priority_ibu_ids"],  # pas de "sujets" à faire varier ici, seule la fraîcheur IBU compte
        lambda: _compute_priority_ibu_ids(season, client),
        cache_dir=CACHE_ATHLETES_DIR,
    )


def _to_response(ibu_id: str, info: dict, is_active: bool = False) -> AthleteResponse:
    return AthleteResponse(
        ibu_id=ibu_id,
        family_name=info["FamilyName"],
        given_name=info["GivenName"],
        nation=info["NAT"],
        flag=FLAGS.get(info["NAT"], "🏳️"),
        gender=info["GenderId"],
        label=athlete_label(ibu_id),
        is_active=is_active,
    )


@router.get("", response_model=list[AthleteResponse])
def list_athletes(
    gender: Optional[str] = Query(None, pattern="^[MW]$"),
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
):
    s = season or settings.ibu_season_code
    top_ids, participant_ids = _priority_ibu_ids(s)

    def _priority(ibu_id: str) -> int:
        if ibu_id in top_ids:
            return 0
        if ibu_id in participant_ids:
            return 1
        return 2

    ranked = [
        (_priority(ibu_id), _to_response(ibu_id, info, _priority(ibu_id) < 2))
        for ibu_id, info in ATHLETES_BY_IBUID.items()
        if gender is None or info["GenderId"] == gender
    ]
    # Top standings, puis participants de la saison, puis le reste — alphabétique dans chaque groupe
    ranked.sort(key=lambda pair: (pair[0], pair[1].family_name))
    return [a for _, a in ranked]


@router.get("/{ibu_id}", response_model=AthleteResponse)
def get_athlete(
    ibu_id: str,
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
):
    info = ATHLETES_BY_IBUID.get(ibu_id)
    if not info:
        raise HTTPException(status_code=404, detail="Athlète introuvable.")
    s = season or settings.ibu_season_code
    top_ids, participant_ids = _priority_ibu_ids(s)
    return _to_response(ibu_id, info, ibu_id in top_ids or ibu_id in participant_ids)
