from pydantic import BaseModel
from typing import Optional


class AthleteStanding(BaseModel):
    rank: int
    ibu_id: str
    name: str
    nation: str
    flag: str
    points: float


class DisciplineStandings(BaseModel):
    discipline: str
    discipline_display: str
    athletes: list[AthleteStanding]


class StandingsResponse(BaseModel):
    gender: str          # "Men" | "Women"
    season_code: str
    disciplines: list[DisciplineStandings]


class SeasonProgress(BaseModel):
    discipline: str
    races_done: int
    races_total: int


class PlayerPoints(BaseModel):
    user_id: str
    username: str
    total_points: int
    men_points: int
    women_points: int
    globe_points: int
    rank: Optional[int] = None
