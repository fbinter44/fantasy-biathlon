from pydantic import BaseModel
from typing import Optional


class AthleteScoreDetail(BaseModel):
    predicted_rank: int        # rang prédit par le joueur (1-5)
    ibu_id: str
    name: str
    nation: str
    actual_rank: Optional[int] # rang réel dans le classement général (None si hors top 20)
    points: int
    exact_rank_bonus: bool     # True si rang prédit == rang réel (+50 bonus)


class GlobeScoreDetail(BaseModel):
    discipline: str            # clé interne (sprint, pursuit, …)
    discipline_display: str
    gender: str                # "Men" | "Women"
    predicted_ibu_id: str
    predicted_name: str
    actual_leader_ibu_id: Optional[str]
    actual_leader_name: Optional[str]
    points: int
    correct: bool


class RaceScoreDetail(BaseModel):
    race_id: str
    location: str
    discipline_display: str
    gender: str
    date: str                  # ISO date (YYYY-MM-DD)
    predicted_ibu_id: str
    predicted_name: str
    winner_ibu_id: Optional[str]
    winner_name: Optional[str]
    points: int
    correct: bool


class ScoreBreakdown(BaseModel):
    user_id: str
    username: str
    total_points: int
    men_points: int
    women_points: int
    globe_points: int
    race_points: int
    men_athletes: list[AthleteScoreDetail]
    women_athletes: list[AthleteScoreDetail]
    globes: list[GlobeScoreDetail]
    races: list[RaceScoreDetail]
