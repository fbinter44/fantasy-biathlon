import requests
import pandas as pd
import pickle
import os
from datetime import datetime, timezone
import json

from utils.cache_helpers import (
    CACHE_VENUES_DIR, CACHE_RESULTS_DIR,
    should_refresh_after_race, should_refresh_calendar, save_pickle_atomic,
)
from utils.biathlon_data import RELAY_IDS, NB_VENUES_BY_SEASON, DISCIPLINE_MAP, GENDERS_CODES, DISCIPLINES_WINNERS


# ---------------------------------------------------------
# EPREUVE (une course)
# ---------------------------------------------------------

class Epreuve:
    def __init__(self, race_id, short_desc, discipline, category, location, start_time, venue):
        self.race_id = race_id
        self.short_desc = short_desc
        self.discipline = discipline
        self.category = category
        self.location = location
        self.start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        self.date = self.start_time.date()
        self.venue = venue
        self.results = None
        self.cache_timestamp = None

    @property
    def cache_path(self):
        os.makedirs(CACHE_RESULTS_DIR, exist_ok=True)
        return os.path.join(CACHE_RESULTS_DIR, f"{self.race_id}.pkl")
    
    def should_refresh(self):
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "rb") as f:
                data = pickle.load(f)
                self.cache_timestamp = data.get("timestamp")

        return should_refresh_after_race(self.start_time, self.cache_timestamp)

    def load_results(self, force_refresh=False):
        # 1) Retrieve from cache if possible
        if not force_refresh and not self.should_refresh() and os.path.exists(self.cache_path):
            with open(self.cache_path, "rb") as f:
                data = pickle.load(f)
                self.results = data["results"]
                self.cache_timestamp = data.get("timestamp")
                return
        # 2) Otherwise request to the API and save to cache
        url = f"https://bw.biathlonresults.com/modules/sportapi/api/Results?RaceId={self.race_id}&Language=en"
        data = requests.get(url).json()
        rows = data["Results"]
        df = pd.DataFrame(
            {
                "rank": [r["Rank"] for r in rows],
                "name": [r["Name"] for r in rows],
                "ibu_id": [r["IBUId"] for r in rows],
                "nation": [r["Nat"] for r in rows],
                "points": [r["WC"] for r in rows],
            }
        )
        self.results = df

        save_pickle_atomic(self.cache_path, {"results": df, "timestamp": datetime.now(timezone.utc)})

        # Mise à jour du fichier de json qui stocke les dates de mise à jour des classements
        if self.should_refresh():
            state_file = "users_info/results_state.json"
            os.makedirs("users_info", exist_ok=True)
            if not os.path.exists(state_file):
                with open(state_file, "w") as f:
                    json.dump({"results_version": 1, "users_seen": {}}, f)  # fichier JSON vide
            state = json.load(open(state_file))
            state["results_version"] += 1
            json.dump(state, open(state_file, "w"))


    def top40(self):
            """Retourne le top 40."""
            return self.results.head(40)


# ---------------------------------------------------------
# VENUE (un week-end de compétitions)
# ---------------------------------------------------------

class CompetitionVenue:
    BASE_URL = "https://bw.biathlonresults.com/modules/sportapi/api/Competitions"

    def __init__(self, season_code, event_id):
        self.season_code = season_code
        self.event_id = event_id
        self.epreuves = []
        self.start_date = None
        self.end_date = None

    @property
    def cache_path(self):
        os.makedirs(CACHE_VENUES_DIR, exist_ok=True)
        return os.path.join(CACHE_VENUES_DIR, f"BT{self.season_code}SWRLCP{self.event_id}.pkl")
    
    def load_epreuves(self, force_refresh=False):
        # 1) Lire le cache s'il existe, pour connaître sa date et sa fraîcheur
        cached_epreuves = []
        cache_timestamp = None
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "rb") as f:
                data = pickle.load(f)
            cache_timestamp = data.get("timestamp")
            for c in data["epreuves"]:
                cached_epreuves.append(
                    Epreuve(
                        c["race_id"], c["short_desc"], c["discipline"],
                        c["category"], c["location"], c["start_time"], self
                    )
                )

        venue_start = min((e.start_time for e in cached_epreuves), default=None)

        # 2) Cache utilisable : venue passée (figée), ou pas encore due à un refresh
        if not force_refresh and cached_epreuves and not should_refresh_calendar(venue_start, cache_timestamp):
            self.epreuves = cached_epreuves
        # 3) Sinon → requête à l'API et mise à jour du cache
        else:
            url = f"{self.BASE_URL}?EventId=BT{self.season_code}SWRLCP{self.event_id}&Language=EN"
            data = requests.get(url).json()

            raw = []
            self.epreuves = []
            for c in data:
                if c["DisciplineId"] in RELAY_IDS:
                    continue

                ep = Epreuve(
                    c["RaceId"], c["ShortDescription"], c["DisciplineId"],
                    c["catId"], c["Location"], c["StartTime"], self
                )
                self.epreuves.append(ep)

                raw.append(
                    {
                        "race_id": c["RaceId"],
                        "short_desc": c["ShortDescription"],
                        "discipline": c["DisciplineId"],
                        "category": c["catId"],
                        "location": c["Location"],
                        "start_time": c["StartTime"],
                    }
                )

            save_pickle_atomic(self.cache_path, {"epreuves": raw, "timestamp": datetime.now(timezone.utc)})

        dates = [e.date for e in self.epreuves]
        self.start_date = min(dates)
        self.end_date = max(dates)

    def load_all_results(self):
        for e in self.epreuves:
            e.load_results()

    def __repr__(self):
        return f"<CompetitionWeekEnd {self.event_id} ({self.start_date} → {self.end_date})>"


# ---------------------------------------------------------
# API COMPETITIONS (point d'entrée)
# ---------------------------------------------------------

class IBUCompetitionsAPI:
    """
    API pour charger toutes les venues d'une saison.
    """

    def __init__(self, season_code):
        self.season_code = season_code

        # Nombre de venues par saison
        self.nb_venues = NB_VENUES_BY_SEASON[season_code]

        self.venues = []
        self.results_loaded = False
        self.progress_by_discipline = {
            "Men": {
                disc: {"total_races": 0, "finished_races": 0}
                for disc in DISCIPLINES_WINNERS.keys()
                }, 
            "Women": {
                disc: {"total_races": 0, "finished_races": 0}
                for disc in DISCIPLINES_WINNERS.keys()
                }, 
            }

    def load_venues(self, force=False):
        for i in range(1, self.nb_venues + 1):
            event_id = f"{i:02d}"
            venue = CompetitionVenue(self.season_code, event_id)
            venue.load_epreuves(force_refresh=force)
            self.venues.append(venue)

    def load_venues_results(self):
        if not self.venues:
            self.load_venues()
        for v in self.venues:
            v.load_all_results()
        self.results_loaded = True

    def compute_progress_by_discipline(self):
        if not self.results_loaded:
            self.load_venues_results()
        for venue in self.venues:
            for ep in venue.epreuves:
                gender = ep.category
                disc = ep.discipline
                GENDERS_CODES[gender]
                self.progress_by_discipline[GENDERS_CODES[gender]][DISCIPLINE_MAP[disc]]["total_races"] += 1
                self.progress_by_discipline[GENDERS_CODES[gender]]["general"]["total_races"] += 1
                if not ep.top40().empty:
                    self.progress_by_discipline[GENDERS_CODES[gender]][DISCIPLINE_MAP[disc]]["finished_races"] += 1
                    self.progress_by_discipline[GENDERS_CODES[gender]]["general"]["finished_races"] += 1
