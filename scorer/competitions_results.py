import requests
from datetime import datetime
import pandas as pd
import os
import pickle
import json

RELAY_IDS = ["RL", "SR"]

NB_VENUES_BY_SEASON = {
    '2526': 9,
    '2627': 10,
    '2728': 9
}

CACHE_VENUES_DIR = "cache_venues"
CACHE_RESULTS_DIR = "cache_results"
os.makedirs(CACHE_VENUES_DIR, exist_ok=True)
os.makedirs(CACHE_RESULTS_DIR, exist_ok=True)


class Epreuve:
    def __init__(self, race_id, short_desc, discipline, category, location, start_time, venue):
        self.race_id = race_id
        self.short_desc = short_desc
        self.discipline = discipline
        self.category = category
        self.location = location
        self.date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date()
        self.venue = venue
        self.results = None

    @property
    def cache_path(self):
        return os.path.join(CACHE_RESULTS_DIR, f"{self.race_id}.pkl")
    
    def should_refresh(self):
        today = datetime.now().date()
        return self.date >= today and self.venue.start_date <= today

    def load_results(self, force_refresh=False):
        # 1) Retrieve from cache if possible
        if not force_refresh and not self.should_refresh() and os.path.exists(self.cache_path):
            with open(self.cache_path, "rb") as f:
                data = pickle.load(f)
                self.results = data["results"]
        # 2) Otherwise request to the API and save to cache
        else:
            url = f"https://bw.biathlonresults.com/modules/sportapi/api/Results?RaceId={self.race_id}&Language=en"
            data = requests.get(url).json()
            rows = data["Results"]
            df_results = pd.DataFrame([{
                "rank": r["Rank"],
                "name": r["Name"],
                "ibu_id": r["IBUId"],
                "nation": r["Nat"],
                "points": r["WC"]
            } for r in rows])
            self.results = df_results

            with open(self.cache_path, "wb") as f:
                pickle.dump({"results": df_results}, f)


    def top40(self):
            """Retourne le top 40."""
            return self.results.head(40)


class CompetitionVenue:
    def __init__(self, season, event_id):
        self.season = season
        self.event_id = event_id
        self.epreuves = []
        self.start_date = None
        self.end_date = None

    @property
    def cache_path(self):
        return os.path.join(CACHE_VENUES_DIR, f"BT{self.season}SWRLCP{self.event_id}.pkl")
    
    def load_epreuves(self, force_refresh=False):
        # 1) Retrieve from cache if possible
        if not force_refresh and os.path.exists(self.cache_path):
            with open(self.cache_path, "rb") as f:
                data = pickle.load(f)
            for c in data["epreuves"]:
                ep = Epreuve(
                    race_id=c["race_id"],
                    short_desc=c["short_desc"],
                    discipline=c["discipline"],
                    category=c["category"],
                    location=c["location"],
                    start_time=c["start_time"],
                    venue=self
                )
                self.epreuves.append(ep)
            dates = [e.date for e in self.epreuves]
            self.start_date = min(dates)
            self.end_date = max(dates)
        # 2) Otherwise request to the API and save to cache
        else:
            url = f"https://bw.biathlonresults.com/modules/sportapi/api/Competitions?EventId=BT{self.season}SWRLCP{self.event_id}&Language=EN"
            data = requests.get(url).json()

            raw_epreuves = []
            for c in data:
                if c["DisciplineId"] in RELAY_IDS:
                    continue
                ep = Epreuve(
                    race_id=c["RaceId"],
                    short_desc=c["ShortDescription"],
                    discipline=c["DisciplineId"],
                    category=c["catId"],
                    start_time=c["StartTime"],
                    location=c["Location"],
                    venue=self
                )
                self.epreuves.append(ep)

                raw_epreuves.append({
                "race_id": c["RaceId"],
                "short_desc": c["ShortDescription"],
                "discipline": c["DisciplineId"],
                "category": c["catId"],
                "location": c["Location"],
                "start_time": c["StartTime"]
                })

            
            dates = [e.date for e in self.epreuves]
            self.start_date = min(dates)
            self.end_date = max(dates)

            with open(self.cache_path, "wb") as f:
                pickle.dump({"epreuves": raw_epreuves}, f)

    def load_all_results(self):
        for e in self.epreuves:
            e.load_results()

    def __repr__(self):
        return f"<CompetitionWeekEnd {self.event_id} ({self.start_date} → {self.end_date})>"
    

class Season:
    def __init__(self, season_code='2526'):
        self.season_code = season_code
        self.nb_venues = NB_VENUES_BY_SEASON[season_code]
        self.venues = []
        self.timeline = {}

    def load_athletes_info(self, path="biathletes/athletes_info.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.athletes_info = json.load(f)

    def load_venues(self):
        for i in range(1, self.nb_venues + 1):
            event_id = f"{i:02d}"
            venue = CompetitionVenue(self.season_code, event_id)
            venue.load_epreuves()
            self.venues.append(venue)

    def load_all_results(self):
        for v in self.venues:
            v.load_all_results()

    def all_venues(self):
        for v in self.venues:
            for ep in v.epreuves:
                yield ep

    def __repr__(self):
        return f"<Saison {self.season_code} ({len(self.venues)} weekends)>"
    
    def build_ibu_standings_after_each_venue(self):
        # Classements cumulés
        points_general_men = {}
        points_sprint_men = {}
        points_pursuit_men = {}
        points_individual_men = {}
        points_mass_men = {}
        points_general_women = {}
        points_sprint_women = {}
        points_pursuit_women = {}
        points_individual_women = {}
        points_mass_women = {}

        self.load_athletes_info()

        for i, venue in enumerate(self.venues):
            for ep in venue.epreuves:
                df = ep.results

                # Général
                for _, r in df.iterrows():
                    if r["points"]:
                        if self.athletes_info[r["ibu_id"]]['GenderId'] == "M":
                            points_general_men[r["ibu_id"]] = int(points_general_men.get(r["ibu_id"], 0)) + int(r["points"])
                        else:
                            points_general_women[r["ibu_id"]] = int(points_general_women.get(r["ibu_id"], 0)) + int(r["points"])

                # Discipline
                if ep.discipline == "SP":
                    for _, r in df.iterrows():
                        if r["points"]:
                            if self.athletes_info[r["ibu_id"]]['GenderId'] == "M":
                                points_sprint_men[r["ibu_id"]] = int(points_sprint_men.get(r["ibu_id"], 0)) + int(r["points"])
                            else:
                                points_sprint_women[r["ibu_id"]] = int(points_sprint_women.get(r["ibu_id"], 0)) + int(r["points"])

                if ep.discipline == "PU":
                    for _, r in df.iterrows():
                        if r["points"]:
                            if self.athletes_info[r["ibu_id"]]['GenderId'] == "M":
                                points_pursuit_men[r["ibu_id"]] = int(points_pursuit_men.get(r["ibu_id"], 0)) + int(r["points"])
                            else:
                                points_pursuit_women[r["ibu_id"]] = int(points_pursuit_women.get(r["ibu_id"], 0)) + int(r["points"])
                if ep.discipline == "IN" or ep.discipline == "SI":
                    for _, r in df.iterrows():
                        if r["points"]:
                            if self.athletes_info[r["ibu_id"]]['GenderId'] == "M":
                                points_individual_men[r["ibu_id"]] = int(points_individual_men.get(r["ibu_id"], 0)) + int(r["points"])
                            else:
                                points_individual_women[r["ibu_id"]] = int(points_individual_women.get(r["ibu_id"], 0)) + int(r["points"])

                if ep.discipline == "MS":
                    for _, r in df.iterrows():
                        if r["points"]:
                            if self.athletes_info[r["ibu_id"]]['GenderId'] == "M":
                                points_mass_men[r["ibu_id"]] = int(points_mass_men.get(r["ibu_id"], 0)) + int(r["points"])
                            else:
                                points_mass_women[r["ibu_id"]] = int(points_mass_women.get(r["ibu_id"], 0)) + int(r["points"])

            self.timeline[i] = {
                "venue_id": venue.event_id,
                "start": venue.start_date,
                "end": venue.end_date,
                "general_men": points_general_men.copy(),
                "general_women": points_general_women.copy(),
                "sprint_men": points_sprint_men.copy(),
                "sprint_women": points_sprint_women.copy(),
                "pursuit_men": points_pursuit_men.copy(),
                "pursuit_women": points_pursuit_women.copy(),
                "individual_men": points_individual_men.copy(),
                "individual_women": points_individual_women.copy(),
                "mass_men": points_mass_men.copy(),
                "mass_women": points_mass_women.copy()
            }


if __name__ == "__main__":
    season = Season()
    season.load_venues()
    season.load_all_results()
    season.build_ibu_standings_after_each_venue()
    import pdb
    pdb.set_trace()