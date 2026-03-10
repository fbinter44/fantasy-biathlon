from .current_standings_api import IBUCurrentStandingsAPI


class IBUCurrentStandings:
    """
    Standings finaux (ou en cours) d'une saison, par genre.
    Utilise IBUCupResultsAPI pour charger les top 10.
    """

    def __init__(self, gender, season_code="2526", client=None):
        self.gender = gender
        self.season_code = season_code

        self.general = None
        self.sprint = None
        self.pursuit = None
        self.individual = None
        self.mass_start = None

        self._api = IBUCurrentStandingsAPI(season_code, client=client)

    def load_all(self):
        """
        Charge les standings top 10 pour toutes les disciplines.
        """
        self.general = self._api.get_results(self.gender, "General")
        self.sprint = self._api.get_results(self.gender, "Sprint")
        self.pursuit = self._api.get_results(self.gender, "Pursuit")
        self.individual = self._api.get_results(self.gender, "Individual")
        self.mass_start = self._api.get_results(self.gender, "Mass Start")

    def __repr__(self):
        return f"<BiathlonStandings {self.gender} {self.season_code}>"
