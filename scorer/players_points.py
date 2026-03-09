from scorer.pronostics_loader import load_pronostics_from_gsheet, parse_pronostics
from scorer.pronostics_builder import build_player_bets
from scorer.results_data import BiathlonStandings


POINTS_TABLE = [90, 75, 65, 55, 50, 45, 41, 37, 34, 31]


class PlayerPoints():
    def __init__(self, name):
        self.player = name
        self.total_points = 0
        self.total_men_points = 0
        self.detailed_men_points = 0
        self.total_women_points = 0
        self.detailed_women_points = 0
        self.bonus_right_place = 0
        self.bonus_globes = 0
    
    def compute_total_men_points(self, top_men, men_general):
        total, total_bonus, details = compute_points(top_men, men_general)
        self.total_men_points = total
        self.detailed_men_points = details
        self.bonus_right_place = total_bonus

    def compute_total_women_points(self, top_women, women_general):
        total, total_bonus, details = compute_points(top_women, women_general)
        self.total_women_points = total
        self.detailed_women_points = details
        self.bonus_right_place += total_bonus

    def compute_bonus_globes_points(self, player, standings_men, standings_women):
        # import pdb
        # pdb.set_trace()
        sprint_men, _ = compute_globe_winner_bonus(player.sprint_winners, standings_men.sprint)
        sprint_women, _ = compute_globe_winner_bonus(player.sprint_winners, standings_women.sprint)
        pursuit_men, _ = compute_globe_winner_bonus(player.pursuit_winners, standings_men.pursuit)
        pursuit_women, _ = compute_globe_winner_bonus(player.pursuit_winners, standings_women.pursuit)
        indiv_men, _ = compute_globe_winner_bonus(player.individual_winners, standings_men.individual)
        indiv_women, _ = compute_globe_winner_bonus(player.individual_winners, standings_women.individual)
        mass_men, _ = compute_globe_winner_bonus(player.mass_start_winners, standings_men.mass_start)
        mass_women, _ = compute_globe_winner_bonus(player.mass_start_winners, standings_women.mass_start)
        total = sprint_men + sprint_women + pursuit_men + pursuit_women + indiv_men + indiv_women + mass_men + mass_women
        self.bonus_globes = total

    def compute_total_points(self):
        self.total_points = self.total_men_points + self.total_women_points + self.bonus_globes


def compute_points(pred_list, df_top10):
    points_table = [90, 75, 65, 55, 50, 45, 41, 37, 34, 31]

    df_top10 = df_top10.copy()
    candidate_ids = df_top10["id"].tolist()

    total = 0
    total_bonus = 0
    details = {}

    for predicted_rank, athlete in enumerate(pred_list, start=1):
        if athlete not in candidate_ids:
            details[athlete] = 0
            continue

        # retrouver la ligne correspondante
        row = df_top10[df_top10["id"] == athlete].iloc[0]
        real_rank = row["rank"]

        # points du barème
        pts = points_table[int(real_rank) - 1]

        # bonus si position correcte
        if int(real_rank) == predicted_rank:
            pts += 50
            total_bonus += 50

        details[athlete] = pts
        total += pts

    return total, total_bonus, details


def compute_globe_winner_bonus(pred_winners: dict, df_top10):
    """
    pred_winners: dict {'Men': 'Eric Perrot', 'Women': 'Franziska Preuss'}
    df_top10: DataFrame avec colonnes ['name', 'rank']
    """
    # Normalisation des noms du top 10
    df_top10 = df_top10.copy()

    if df_top10.empty:
        return 0, {}

    # On récupère le vainqueur réel (rank = 1)
    real_winner_row = df_top10[df_top10["rank"] == "1"].iloc[0]

    real_winner_id = real_winner_row["id"]

    # # Liste des noms normalisés pour fuzzy matching
    # candidate_norms = df_top10["norm"].tolist()

    results = {}
    total_bonus = 0

    for category, predicted_id in pred_winners.items():
        if predicted_id == real_winner_id:
            results[category] = 50
            total_bonus += 50
        else:
            results[category] = 0

    return total_bonus, results


def load_players_data():
    df_pronos = load_pronostics_from_gsheet()
    top5_h, top5_f, players, globes = parse_pronostics(df_pronos)
    players_predictions = build_player_bets(top5_h, top5_f, players, globes)
    return players_predictions


def compute_all_players_points(predictions, standings_men, standings_women):
    scoring_summary = {}
    for player in predictions:
        player_with_points = compute_player_point(predictions[player], standings_men, standings_women)
        scoring_summary[player] = player_with_points
    return scoring_summary


def compute_player_point(player, standings_men, standings_women):
    player_points = PlayerPoints(player.player)
    player_points.compute_total_men_points(player.top_men, standings_men.general)
    player_points.compute_total_women_points(player.top_women, standings_women.general)
    player_points.compute_bonus_globes_points(player, standings_men, standings_women)
    player_points.compute_total_points()
    return player_points


if __name__ == "__main__":
    players_predictions = load_players_data()
    standings_men = BiathlonStandings("Men")
    standings_men.load_all()
    standings_women = BiathlonStandings("Women")
    standings_women.load_all()
    scoring_summary = compute_all_players_points(players_predictions, standings_men, standings_women)
