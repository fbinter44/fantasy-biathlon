from datetime import datetime, timezone

from .current_standings import IBUCurrentStandings
from .competitions_api import IBUCompetitionsAPI
from .season_results import IBUSeasonResultsBuilder
from.evolutive_standings import IBUEvolutiveStandings


class IBUClient:
    """
    Point d'entrée unique pour toutes les données IBU.
    """

    def __init__(self, season_code="2526"):
        self.season_code = season_code
        self.current_men_standings = IBUCurrentStandings("Men", season_code, client=self)
        self.current_women_standings = IBUCurrentStandings("Women", season_code, client=self)
        self.competitions = IBUCompetitionsAPI(season_code)
        self.season_results = IBUSeasonResultsBuilder(season_code)

        self.cumulated_scores = None
        self.cumulated_standings = {}
    
    def load_standings(self):
        men = self.current_men_standings
        women = self.current_women_standings
        men.load_all()
        women.load_all()
        return men, women

    def load_results(self):
        self.competitions.load_venues_results()

    def compute_cumulated_scores(self):
        if not self.competitions.venues:
            self.load_results()
        self.cumulated_scores = self.season_results.build(self.competitions.venues)
    
    def compute_evolutive_standings(self):
        if not self.cumulated_scores:
            self.compute_cumulated_scores()
        nb_venues = self.competitions.nb_venues
        for i in range(1, nb_venues + 1):
            self.cumulated_standings[i] = {}
            men_evolutive_standings = IBUEvolutiveStandings("Men", i, self.cumulated_scores, self.season_code)
            men_evolutive_standings.load_all()
            women_evolutive_standings = IBUEvolutiveStandings("Women", i, self.cumulated_scores, self.season_code)
            women_evolutive_standings.load_all()
            self.cumulated_standings[i]["Men"] = men_evolutive_standings
            self.cumulated_standings[i]["Women"] = women_evolutive_standings

    def get_last_race_end(self):
        """
        Retourne la date/heure de la dernière course terminée.
        """
        if not self.competitions.venues:
            self.load_results()

        # Récupérer toutes les épreuves
        all_races = []
        for v in self.competitions.venues:
            for ep in v.epreuves:
                all_races.append(ep)

        # Filtrer uniquement les courses passées
        now = datetime.now(timezone.utc)
        past_races = [ep for ep in all_races if ep.start_time <= now]

        if not past_races:
            return None  # aucune course encore terminée

        # Retourner la dernière course terminée
        return max(ep.start_time for ep in past_races)

