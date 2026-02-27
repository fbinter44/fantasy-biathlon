import requests
from datetime import datetime
import pandas as pd
import os
import pickle

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
        timeline = []

        # Classements cumulés
        points_general = {}
        points_sprint = {}
        points_pursuit = {}
        points_individual = {}
        points_mass = {}

        for venue in self.venues:
            for ep in venue.epreuves:
                df = ep.results

                # Général
                for _, r in df.iterrows():
                    if r["points"]:
                        points_general[r["ibu_id"]] = int(points_general.get(r["ibu_id"], 0)) + int(r["points"])

                # Discipline
                if ep.discipline == "SP":
                    for _, r in df.iterrows():
                        if r["points"]:
                            points_sprint[r["ibu_id"]] = int(points_sprint.get(r["ibu_id"], 0)) + int(r["points"])

                if ep.discipline == "PU":
                    for _, r in df.iterrows():
                        if r["points"]:
                            points_pursuit[r["ibu_id"]] = int(points_pursuit.get(r["ibu_id"], 0)) + int(r["points"])

                if ep.discipline == "IN":
                    for _, r in df.iterrows():
                        if r["points"]:
                            points_individual[r["ibu_id"]] = int(points_individual.get(r["ibu_id"], 0)) + int(r["points"])

                if ep.discipline == "MS":
                    for _, r in df.iterrows():
                        if r["points"]:
                            points_mass[r["ibu_id"]] = int(points_mass.get(r["ibu_id"], 0)) + int(r["points"])

            timeline.append({
                "venue_id": venue.event_id,
                "start": venue.start_date,
                "end": venue.end_date,
                "general": points_general.copy(),
                "sprint": points_sprint.copy(),
                "pursuit": points_pursuit.copy(),
                "individual": points_individual.copy(),
                "mass": points_mass.copy()
            })

        return timeline



if __name__ == "__main__":
    season = Season()
    season.load_venues()
    season.load_all_results()
    timeline = season.build_ibu_standings_after_each_venue()
    import pdb
    pdb.set_trace()