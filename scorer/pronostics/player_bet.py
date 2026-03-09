class GlobeWinners:
    """
    Représente les vainqueurs d'un globe issus des pronostics d'un joueur :
    - discipline/spécialité
    - vainqueur hommes
    - vainqueur femmes
    """

    def __init__(self, discipline, winner_men, winner_women):
        self.discipline = discipline
        self.winner_men = winner_men
        self.winner_women = winner_women


class PlayerBet:
    """
    Représente les pronostics d’un joueur :
    - Top 5 hommes
    - Top 5 femmes
    - Vainqueurs des globes (H/F)
    """

    def __init__(self, name):
        self.player = name
        self.top_men = None
        self.top_women = None
        self.sprint_winners = None
        self.pursuit_winners = None
        self.individual_winners = None
        self.mass_start_winners = None

    def load_predictions(self, top_men, top_women, sp, pu, ind, ms):
        self.top_men = top_men
        self.top_women = top_women
        self.sprint_winners = GlobeWinners("Sprint", sp["globe_sprint_h"], sp["globe_sprint_f"])
        self.pursuit_winners = GlobeWinners("Poursuite", pu["globe_pursuit_h"], pu["globe_pursuit_f"])
        self.individual_winners = GlobeWinners("Individuel", ind["globe_individual_h"], ind["globe_individual_f"])
        self.mass_start_winners = GlobeWinners("Mass-start", ms["globe_mass_start_h"], ms["globe_mass_start_f"])
