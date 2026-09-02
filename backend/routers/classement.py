"""
Routes classement fantasy.

GET /classement                     → classement global (toutes ligues confondues)
GET /classement/league/{league_id}  → classement d'une ligue
GET /classement/evolution           → évolution du classement race par race
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.config import Settings, get_settings
from backend.dependencies import get_current_user
from backend.models.standings import PlayerPoints, VenueEvolution
from utils.biathlon_data import VENUES_NAMES
from backend.services.db import get_all_users, get_all_pronostics, get_all_leagues, get_all_race_pronostics
from core.ibu.client import IBUClient
from core.scoring.scoring_service import compute_all_players_points
from core.pronostics.pronostics_loader import load_pronostics_from_records, parse_pronostics
from core.pronostics.pronostics_builder import build_player_bets
from utils.sheets import parse_members   # utilitaire pur, pas de st.secrets

router = APIRouter(prefix="/classement", tags=["classement"])


def _ibu_client(settings: Settings, season: str | None = None) -> IBUClient:
    return IBUClient(season_code=season or settings.ibu_season_code)


def _rank_players(points_map: dict, username_map: dict) -> list[PlayerPoints]:
    ranked = sorted(points_map.values(), key=lambda pp: pp.total_points, reverse=True)
    result = []
    for i, pp in enumerate(ranked, start=1):
        result.append(PlayerPoints(
            user_id=pp.player,
            username=username_map.get(pp.player, pp.player),
            total_points=pp.total_points,
            men_points=pp.total_men_points,
            women_points=pp.total_women_points,
            globe_points=pp.bonus_globes,
            race_points=pp.race_points,
            rank=i,
        ))
    return result


def _load_race_winner_data(settings: Settings, season: str):
    """Charge les pronos course + résultats IBU. Retourne (all_race_pronos, venues)."""
    all_race_pronos = get_all_race_pronostics(settings, season)
    client = _ibu_client(settings, season)
    client.competitions.load_venues_results()
    return all_race_pronos, client.competitions.venues


def _add_race_points(points_map: dict, all_race_pronos: dict, venues: list) -> None:
    """Injecte les points course dans chaque PlayerPoints du map."""
    for user_id, pp in points_map.items():
        user_pronos = all_race_pronos.get(user_id, {})
        pp.add_race_winner_points(user_pronos, venues)
        pp.compute_total_points()  # recalcul avec race_points inclus


@router.get("", response_model=list[PlayerPoints])
def global_classement(
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
):
    s = season or settings.ibu_season_code
    users = get_all_users(settings)
    all_member_ids = [u["user_id"] for u in users]
    username_map = {u["user_id"]: u["username"] for u in users}

    records = get_all_pronostics(settings, s)
    df = load_pronostics_from_records(records)
    df_league = df[df["user_id"].isin(all_member_ids)]
    top5_h, top5_f, globes = parse_pronostics(df_league)
    predictions = build_player_bets(top5_h, top5_f, globes)

    client = _ibu_client(settings, s)
    men_st, women_st = client.load_standings()
    points_map = compute_all_players_points(predictions, men_st, women_st)

    all_race_pronos, venues = _load_race_winner_data(settings, s)
    _add_race_points(points_map, all_race_pronos, venues)

    return _rank_players(points_map, username_map)


@router.get("/league/{league_id}", response_model=list[PlayerPoints])
def league_classement(
    league_id: str,
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
):
    from backend.services.db import get_league_by_id
    s = season or settings.ibu_season_code
    league = get_league_by_id(league_id, settings)
    if not league:
        raise HTTPException(status_code=404, detail="Ligue introuvable.")

    member_ids = parse_members(league["members"])
    users = get_all_users(settings)
    username_map = {u["user_id"]: u["username"] for u in users}

    records = get_all_pronostics(settings, s)
    df = load_pronostics_from_records(records)
    df_league = df[df["user_id"].isin(member_ids)]
    top5_h, top5_f, globes = parse_pronostics(df_league)
    predictions = build_player_bets(top5_h, top5_f, globes)

    client = _ibu_client(settings, s)
    men_st, women_st = client.load_standings()
    points_map = compute_all_players_points(predictions, men_st, women_st)

    all_race_pronos, venues = _load_race_winner_data(settings, s)
    _add_race_points(points_map, all_race_pronos, venues)

    return _rank_players(points_map, username_map)


@router.get("/evolution", response_model=list[VenueEvolution])
def classement_evolution(
    season: str = Query(None),
    settings: Settings = Depends(get_settings),
):
    s = season or settings.ibu_season_code
    users = get_all_users(settings)
    all_member_ids = [u["user_id"] for u in users]
    username_map = {u["user_id"]: u["username"] for u in users}

    records = get_all_pronostics(settings, s)
    df = load_pronostics_from_records(records)
    df_league = df[df["user_id"].isin(all_member_ids)]
    top5_h, top5_f, globes = parse_pronostics(df_league)
    predictions = build_player_bets(top5_h, top5_f, globes)

    client = _ibu_client(settings, s)
    client.compute_evolutive_standings()

    # Pronos course chargés une seule fois
    all_race_pronos = get_all_race_pronostics(settings, s)

    evolution = []
    for venue_i, standings_by_gender in client.cumulated_standings.items():
        venue = client.competitions.venues[venue_i - 1]
        location = venue.epreuves[0].location if venue.epreuves else ""
        name = VENUES_NAMES.get(location, location)

        men_st = standings_by_gender["Men"]
        women_st = standings_by_gender["Women"]
        points_map = compute_all_players_points(predictions, men_st, women_st)

        # Points course uniquement pour les venues 1..i (progressif)
        venues_so_far = client.competitions.venues[:venue_i]
        _add_race_points(points_map, all_race_pronos, venues_so_far)

        evolution.append(VenueEvolution(
            index=venue_i,
            name=name,
            start_date=str(venue.start_date),
            end_date=str(venue.end_date),
            players=_rank_players(points_map, username_map),
        ))

    return sorted(evolution, key=lambda v: v.index)
