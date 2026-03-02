from scorer.results_scrapping import get_cup_results
import pandas as pd
from scorer.competitions_results import Season


class BiathlonStandings:

    def __init__(self, gender):
        self.gender = gender
        self.general = None
        self.sprint = None
        self.pursuit = None
        self.individual = None
        self.mass_start = None

    def load_all(self):
        self.sprint = get_cup_results(self.gender, "Sprint")
        self.pursuit = get_cup_results(self.gender, "Pursuit")
        self.mass_start = get_cup_results(self.gender, "Mass Start")
        self.individual = get_cup_results(self.gender, "Individual")
        self.general = get_cup_results(self.gender, "General")


class BiathlonTempStandings:
    def __init__(self, season, gender, venue_number):
        self.season = season              # <— ajouté ici
        self.gender = gender
        self.venue_number = venue_number  # 1-based index

        self.general = None
        self.sprint = None
        self.pursuit = None
        self.individual = None
        self.mass_start = None

    def load(self):
        # On récupère le snapshot déjà calculé dans Season
        snapshot = self.season.timeline[self.venue_number - 1]

        gender_suffix = "men" if self.gender.lower() == "men" else "women"

        # On convertit les dicts en DataFrames identiques à get_cup_results()
        self.general = self._dict_to_df(snapshot[f"general_{gender_suffix}"])
        self.sprint = self._dict_to_df(snapshot[f"sprint_{gender_suffix}"])
        self.pursuit = self._dict_to_df(snapshot[f"pursuit_{gender_suffix}"])
        self.individual = self._dict_to_df(snapshot[f"individual_{gender_suffix}"])
        self.mass_start = self._dict_to_df(snapshot[f"mass_{gender_suffix}"])

    def _dict_to_df(self, d):
        rows = sorted(d.items(), key=lambda x: x[1], reverse=True)[:10]

        return pd.DataFrame([
            {
                "id": ibu_id,
                "rank": str(i + 1),
                "name": self.season.athletes_info[ibu_id]["FamilyName"] + " " + self.season.athletes_info[ibu_id]["GivenName"],
                "nation": self.season.athletes_info[ibu_id]["NAT"],
                "points": pts
            }
            for i, (ibu_id, pts) in enumerate(rows)
        ])

if __name__ == "__main__":
    # men_results = BiathlonStandings("Men")
    # men_results.load_all()
    season = Season("2526")
    season.load_venues()
    season.load_all_results()
    season.build_ibu_standings_after_each_venue()
    # standings = BiathlonTempStandings(season, "Men", 6)
    # standings.load()
    women_standings = BiathlonTempStandings(season, "Women", 6)
    women_standings.load()
