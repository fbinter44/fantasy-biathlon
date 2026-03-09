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
        self.sprint_winners = sp
        self.pursuit_winners = pu
        self.individual_winners = ind
        self.mass_start_winners = ms
