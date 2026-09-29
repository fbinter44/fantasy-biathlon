from .current_standings_api import IBUCurrentStandingsAPI


class IBUCurrentStandings:
    """
    Standings actuels (en direct) d'une saison, par genre — récupérés en
    interrogeant l'API IBU en temps réel via IBUCurrentStandingsAPI.
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
        self.general = self._api.get_results(self.gender, "General", top=20)
        self.sprint = self._api.get_results(self.gender, "Sprint", top=20)
        self.pursuit = self._api.get_results(self.gender, "Pursuit", top=20)
        self.individual = self._api.get_results(self.gender, "Individual", top=20)
        self.mass_start = self._api.get_results(self.gender, "Mass Start", top=20)

    def __repr__(self):
        return f"<BiathlonStandings {self.gender} {self.season_code}>"
