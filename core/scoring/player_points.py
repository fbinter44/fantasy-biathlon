from .compute_points import compute_regular_points, compute_globe_winner_bonus

class PlayerPoints:
    def __init__(self, name):
        self.player = name
        self.total_points = 0
        self.total_men_points = 0
        self.total_women_points = 0
        self.bonus_right_place = 0
        self.bonus_globes = 0
        self.details_men = {}
        self.details_women = {}

    def compute_total_men_points(self, top_men, men_general):
        total, bonus, details = compute_regular_points(top_men, men_general)
        self.total_men_points = total
        self.details_men = details
        self.bonus_right_place += bonus

    def compute_total_women_points(self, top_women, women_general):
        total, bonus, details = compute_regular_points(top_women, women_general)
        self.total_women_points = total
        self.details_women = details
        self.bonus_right_place += bonus

    def compute_bonus_globes_points(self, bet, standings_men, standings_women):
        total = 0

        for discipline in ["sprint", "pursuit", "individual", "mass_start"]:
            pred = getattr(bet, f"{discipline}_winners")
            men_df = getattr(standings_men, discipline)
            women_df = getattr(standings_women, discipline)

            b_men, b_women = compute_globe_winner_bonus(pred, men_df, women_df)
            total += b_men + b_women

        self.bonus_globes = total

    def compute_total_points(self):
        self.total_points = (
            self.total_men_points +
            self.total_women_points +
            self.bonus_globes
        )
