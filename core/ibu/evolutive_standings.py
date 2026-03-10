import pandas as pd
import json


class IBUEvolutiveStandings:
    """
    Standings finaux (ou en cours) d'une saison, par genre.
    Utilise IBUCupResultsAPI pour charger les top 10.
    """

    def __init__(self, gender, venue_number, timeline, season_code="2526"):
        self.gender = gender
        self.season_code = season_code
        self.venue_number = venue_number
        self.timeline = timeline

        self.general = None
        self.sprint = None
        self.pursuit = None
        self.individual = None
        self.mass_start = None

        # Chargement des infos athlètes (pour déterminer le genre)
        with open("biathletes_data/athletes_info.json", encoding="utf-8") as f:
            self.athletes = json.load(f)

    def load_all(self):
        """
        Charge les standings top 10 pour toutes les disciplines.
        """
        snapshot = self.timeline[self.venue_number - 1]

        # On convertit les dicts en DataFrames identiques à get_cup_results()
        self.general = self._dict_to_df(snapshot["standings"]["general"][self.gender])
        self.sprint = self._dict_to_df(snapshot["standings"]["sprint"][self.gender])
        self.pursuit = self._dict_to_df(snapshot["standings"]["pursuit"][self.gender])
        self.individual = self._dict_to_df(snapshot["standings"]["individual"][self.gender])
        self.mass_start = self._dict_to_df(snapshot["standings"]["mass_start"][self.gender])

    def _dict_to_df(self, d):
        rows = sorted(d.items(), key=lambda x: x[1], reverse=True)[:10]

        return pd.DataFrame([
            {
                "id": ibu_id,
                "rank": str(i + 1),
                "name": self.athletes[ibu_id]["FamilyName"] + " " + self.athletes[ibu_id]["GivenName"],
                "nation": self.athletes[ibu_id]["NAT"],
                "points": pts
            }
            for i, (ibu_id, pts) in enumerate(rows)
        ])
