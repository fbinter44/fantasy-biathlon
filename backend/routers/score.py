"""
Décomposition détaillée du score d'un joueur.

GET /score/{user_id}  → ScoreBreakdown (auth requise)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from backend.config import Settings, get_settings
from backend.dependencies import get_current_user
from backend.models.score import (
    ScoreBreakdown, AthleteScoreDetail, GlobeScoreDetail, RaceScoreDetail,
)
from backend.services.db import (
    get_user_by_id, get_pronostics_by_user, get_race_pronostics_by_user,
)
from core.ibu.client import IBUClient
from core.pronostics.pronostics_loader import load_pronostics_from_records, parse_pronostics
from core.pronostics.pronostics_builder import build_player_bets
from core.scoring.points_table import POINTS_TABLE
from utils.biathlon_data import ATHLETES_BY_IBUID, VENUES_NAMES
from utils.biathlon_data import DISCIPLINE_MAP, GENDERS_CODES

router = APIRouter(prefix="/score", tags=["score"])

DISCIPLINE_DISPLAY_MAP = {
    "sprint":     "Sprint",
    "pursuit":    "Poursuite",
    "individual": "Individuel",
    "mass_start": "Mass Start",
}

GLOBE_DISCIPLINES = [
    ("sprint",     "Sprint",     "sprint_winners"),
    ("pursuit",    "Poursuite",  "pursuit_winners"),
    ("individual", "Individuel", "individual_winners"),
    ("mass_start", "Mass Start", "mass_start_winners"),
]

EPREUVE_DISPLAY = {
    "SP": "Sprint", "PU": "Poursuite", "MS": "Mass Start", "IN": "Individuel", "SI": "Individuel",
}


def _athlete_name(ibu_id: str) -> str:
    info = ATHLETES_BY_IBUID.get(ibu_id)
    if not info:
        return ibu_id
    return f"{info['FamilyName']} {info['GivenName']}"


def _athlete_nation(ibu_id: str) -> str:
    info = ATHLETES_BY_IBUID.get(ibu_id)
    return info.get("NAT", "") if info else ""


def _build_athlete_details(
    top_list,          # Series p1..p5 avec les IBU IDs dans l'ordre
    df_general,        # DataFrame classement général (id, rank, …)
) -> tuple[list[AthleteScoreDetail], int]:
    details = []
    total = 0
    for predicted_rank, ibu_id in enumerate(top_list, start=1):
        if not ibu_id:
            continue
        row = df_general[df_general["id"] == ibu_id] if df_general is not None else None
        if row is None or row.empty:
            actual_rank = None
            pts = 0
            bonus = False
        else:
            actual_rank = int(row.iloc[0]["rank"])
            if actual_rank > len(POINTS_TABLE):
                pts = 0
                bonus = False
            else:
                pts = POINTS_TABLE[actual_rank - 1]
                bonus = (actual_rank == predicted_rank)
                if bonus:
                    pts += 50
        total += pts
        details.append(AthleteScoreDetail(
            predicted_rank=predicted_rank,
            ibu_id=ibu_id,
            name=_athlete_name(ibu_id),
            nation=_athlete_nation(ibu_id),
            actual_rank=actual_rank,
            points=pts,
            exact_rank_bonus=bonus,
        ))
    return details, total


def _build_globe_details(
    bet,
    standings_men,
    standings_women,
) -> tuple[list[GlobeScoreDetail], int]:
    details = []
    total = 0
    for disc_key, disc_display, bet_attr in GLOBE_DISCIPLINES:
        bet_glob = getattr(bet, bet_attr, None)
        if bet_glob is None:
            continue
        for gender, predicted_ibu, df_st in [
            ("Men",   bet_glob.winner_men,   getattr(standings_men,  disc_key, None)),
            ("Women", bet_glob.winner_women, getattr(standings_women, disc_key, None)),
        ]:
            if not predicted_ibu:
                continue
            actual_leader_ibu = None
            actual_leader_name = None
            if df_st is not None and not df_st.empty:
                leader_row = df_st[df_st["rank"] == "1"]
                if not leader_row.empty:
                    actual_leader_ibu = str(leader_row.iloc[0]["id"])
                    actual_leader_name = _athlete_name(actual_leader_ibu)
            correct = (predicted_ibu == actual_leader_ibu) if actual_leader_ibu else False
            pts = 50 if correct else 0
            total += pts
            details.append(GlobeScoreDetail(
                discipline=disc_key,
                discipline_display=disc_display,
                gender=gender,
                predicted_ibu_id=predicted_ibu,
                predicted_name=_athlete_name(predicted_ibu),
                actual_leader_ibu_id=actual_leader_ibu,
                actual_leader_name=actual_leader_name,
                points=pts,
                correct=correct,
            ))
    return details, total


def _build_race_details(
    race_pronos: dict,
    venues: list,
) -> tuple[list[RaceScoreDetail], int]:
    details = []
    total = 0
    now = datetime.now(timezone.utc)
    for venue in venues:
        raw_location = venue.epreuves[0].location if venue.epreuves else ""
        location = VENUES_NAMES.get(raw_location, raw_location)
        for ep in venue.epreuves:
            if ep.start_time > now:
                continue  # course future — pas de résultat
            predicted_ibu = race_pronos.get(ep.race_id)
            if not predicted_ibu:
                continue  # pas de prono pour cette course
            winner_ibu = None
            winner_name = None
            if ep.results is not None and not ep.results.empty:
                w_row = ep.results[ep.results["rank"].astype(str) == "1"]
                if not w_row.empty:
                    winner_ibu = str(w_row.iloc[0]["ibu_id"])
                    winner_name = _athlete_name(winner_ibu)
            correct = (predicted_ibu == winner_ibu) if winner_ibu else False
            pts = 10 if correct else 0
            total += pts
            gender = GENDERS_CODES.get(ep.category, ep.category)
            details.append(RaceScoreDetail(
                race_id=ep.race_id,
                location=location,
                discipline_display=EPREUVE_DISPLAY.get(ep.discipline, ep.discipline),
                gender=gender,
                date=ep.start_time.date().isoformat(),
                predicted_ibu_id=predicted_ibu,
                predicted_name=_athlete_name(predicted_ibu),
                winner_ibu_id=winner_ibu,
                winner_name=winner_name,
                points=pts,
                correct=correct,
            ))
    return details, total


@router.get("/{user_id}", response_model=ScoreBreakdown)
def get_score_breakdown(
    user_id: str,
    settings: Settings = Depends(get_settings),
    _caller: str = Depends(get_current_user),
):
    # Vérification que l'utilisateur existe
    user = get_user_by_id(user_id, settings)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    # Pronostics saison
    prono_record = get_pronostics_by_user(user_id, settings)
    if not prono_record:
        # Pas de pronos saison → scores à zéro, on renvoie quand même la structure
        return ScoreBreakdown(
            user_id=user_id,
            username=user["username"],
            total_points=0, men_points=0, women_points=0,
            globe_points=0, race_points=0,
            men_athletes=[], women_athletes=[], globes=[], races=[],
        )

    records = [prono_record]
    from core.pronostics.pronostics_loader import load_pronostics_from_records, parse_pronostics
    df = load_pronostics_from_records(records)
    top5_h, top5_f, globes_df = parse_pronostics(df)
    predictions = build_player_bets(top5_h, top5_f, globes_df)
    bet = predictions.get(user_id)
    if not bet:
        return ScoreBreakdown(
            user_id=user_id, username=user["username"],
            total_points=0, men_points=0, women_points=0,
            globe_points=0, race_points=0,
            men_athletes=[], women_athletes=[], globes=[], races=[],
        )

    # Standings IBU
    client = IBUClient(season_code=settings.ibu_season_code)
    men_st, women_st = client.load_standings()

    # Détail saison
    men_details, men_pts = _build_athlete_details(bet.top_men, men_st.general)
    women_details, women_pts = _build_athlete_details(bet.top_women, women_st.general)

    # Détail globes
    globe_details, globe_pts = _build_globe_details(bet, men_st, women_st)

    # Pronos course + résultats
    race_pronos = get_race_pronostics_by_user(user_id, settings)
    client.competitions.load_venues_results()
    race_details, race_pts = _build_race_details(race_pronos, client.competitions.venues)

    total = men_pts + women_pts + globe_pts + race_pts

    return ScoreBreakdown(
        user_id=user_id,
        username=user["username"],
        total_points=total,
        men_points=men_pts,
        women_points=women_pts,
        globe_points=globe_pts,
        race_points=race_pts,
        men_athletes=men_details,
        women_athletes=women_details,
        globes=globe_details,
        races=race_details,
    )
