from datetime import datetime, timezone

from .current_standings import IBUCurrentStandings
from .competitions_api import IBUCompetitionsAPI
from .season_results import IBUSeasonResultsBuilder
from.evolutive_standings import IBUEvolutiveStandings


class IBUClient:
    """
    Point d'entrée unique pour toutes les données IBU.

    Deux familles de méthodes, à ne pas mélanger :
      - load_standings() / load_results() : lecture directe (standings
        actuels, résultats de courses) via les API IBU en direct.
      - compute_cumulated_scores() / compute_evolutive_standings() :
        reconstruction historique venue par venue (utilisée par
        /classement/evolution), qui s'enchaîne dans cet ordre précis —
        chaque étape déclenche la précédente si besoin (cumulated_scores
        charge les résultats s'ils ne le sont pas déjà, evolutive_standings
        calcule cumulated_scores s'il n'existe pas encore) donc appeler
        directement compute_evolutive_standings() suffit dans la plupart
        des cas.
    """

    def __init__(self, season_code="2526"):
        self.season_code = season_code
        self.current_men_standings = IBUCurrentStandings("Men", season_code, client=self)
        self.current_women_standings = IBUCurrentStandings("Women", season_code, client=self)
        self.competitions = IBUCompetitionsAPI(season_code)
        self.season_results = IBUSeasonResultsBuilder(season_code)

        self.cumulated_scores = None
        self.cumulated_standings = {}
        self.season_progress = {}
    
    def load_standings(self):
        men = self.current_men_standings
        women = self.current_women_standings
        men.load_all()
        women.load_all()
        return men, women

    def load_results(self):
        self.competitions.load_venues_results()

    def get_season_progress(self):
        self.competitions.compute_progress_by_discipline()
        self.season_progress = self.competitions.progress_by_discipline

    def compute_cumulated_scores(self):
        """Construit self.cumulated_scores : timeline des standings cumulés
        venue par venue (voir IBUSeasonResultsBuilder.build), en s'assurant
        d'abord que les résultats de courses sont chargés."""
        if not self.competitions.venues:
            self.load_results()
        self.cumulated_scores = self.season_results.build(self.competitions.venues)

    def compute_evolutive_standings(self):
        """Remplit self.cumulated_standings : {index_venue: {"Men"/"Women":
        IBUEvolutiveStandings}} pour CHAQUE venue du calendrier de la saison
        (passées et futures), reconstruit à partir de self.cumulated_scores.
        Une venue future a un snapshot identique à la précédente (aucun
        point n'a pu s'y ajouter) — c'est à l'appelant de filtrer les venues
        sans résultat réel si besoin (voir /classement/evolution)."""
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

