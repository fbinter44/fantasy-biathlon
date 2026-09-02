"""
Routes classements IBU officiels.

GET /standings/{gender}            → classements actuels (Men | Women)
GET /standings/{gender}/progress   → avancement de la saison par discipline
"""

from fastapi import APIRouter, HTTPException, Depends, Query

from backend.config import Settings, get_settings
from backend.models.standings import StandingsResponse, DisciplineStandings, AthleteStanding, SeasonProgress
from utils.biathlon_data import DISCIPLINES_DISPLAY, FLAGS, ATHLETES_BY_IBUID
from core.ibu.client import IBUClient

router = APIRouter(prefix="/standings", tags=["standings"])


def _build_client(settings: Settings, season: str | None = None) -> IBUClient:
    return IBUClient(season_code=season or settings.ibu_season_code)


def _athlete_standing(rank: int, row) -> AthleteStanding:
    ibu_id = str(row.get("id", ""))
    nation = row.get("nation", "")
    return AthleteStanding(
        rank=rank,
        ibu_id=ibu_id,
        name=row.get("name", ""),
        nation=nation,
        flag=FLAGS.get(nation, "🏳️"),
        points=float(row.get("points", 0)),
    )


@router.get("/{gender}", response_model=StandingsResponse)
def get_standings(
    gender: str,
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
):
    if gender not in ("Men", "Women"):
        raise HTTPException(status_code=400, detail="gender doit être 'Men' ou 'Women'.")

    client = _build_client(settings, season)
    men_st, women_st = client.load_standings()
    standings_obj = men_st if gender == "Men" else women_st

    disciplines = []
    for attr, display in DISCIPLINES_DISPLAY:
        df = getattr(standings_obj, attr, None)
        if df is None or df.empty:
            continue
        athletes = [
            _athlete_standing(i + 1, row)
            for i, row in enumerate(df.head(20).to_dict("records"))
        ]
        disciplines.append(DisciplineStandings(
            discipline=attr,
            discipline_display=display,
            athletes=athletes,
        ))

    return StandingsResponse(
        gender=gender,
        season_code=settings.ibu_season_code,
        disciplines=disciplines,
    )


@router.get("/{gender}/progress", response_model=list[SeasonProgress])
def get_season_progress(
    gender: str,
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
):
    if gender not in ("Men", "Women"):
        raise HTTPException(status_code=400, detail="gender doit être 'Men' ou 'Women'.")

    client = _build_client(settings, season)
    client.load_results()
    client.get_season_progress()

    result = []
    for disc, attr in [("sprint", "sprint"), ("pursuit", "pursuit"),
                       ("individual", "individual"), ("mass_start", "mass_start")]:
        prog = client.season_progress.get(gender, {}).get(disc, {})
        result.append(SeasonProgress(
            discipline=disc,
            races_done=prog.get("done", 0),
            races_total=prog.get("total", 0),
        ))
    return result
