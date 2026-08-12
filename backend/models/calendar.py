"""
Modèles Pydantic — Calendrier & Résultats IBU.
"""

from pydantic import BaseModel


class RaceInfo(BaseModel):
    race_id: str
    short_desc: str
    discipline: str          # "sprint" | "pursuit" | "individual" | "mass_start"
    discipline_display: str  # "Sprint" | "Poursuite" | "Individuel" | "Mass Start"
    gender: str              # "Men" | "Women"
    start_time: str          # ISO 8601 UTC
    is_past: bool


class VenueInfo(BaseModel):
    event_id: str
    location: str
    start_date: str          # ISO date
    end_date: str            # ISO date
    races: list[RaceInfo]


class RaceResult(BaseModel):
    rank: int
    name: str
    ibu_id: str
    nation: str
    flag: str
    points: float
