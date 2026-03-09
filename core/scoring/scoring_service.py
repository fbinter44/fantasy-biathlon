from core.pronostics.pronostics_loader import load_pronostics_from_gsheet, parse_pronostics
from core.pronostics.pronostics_builder import build_player_bets
from .player_points import PlayerPoints

def load_players_data():
    df = load_pronostics_from_gsheet()
    top5_h, top5_f, globes = parse_pronostics(df)
    return build_player_bets(top5_h, top5_f, globes)

def compute_player_point(bet, standings_men, standings_women):
    pp = PlayerPoints(bet.player)
    pp.compute_total_men_points(bet.top_men, standings_men.general)
    pp.compute_total_women_points(bet.top_women, standings_women.general)
    pp.compute_bonus_globes_points(bet, standings_men, standings_women)
    pp.compute_total_points()
    return pp

def compute_all_players_points(predictions, standings_men, standings_women):
    return {
        player: compute_player_point(predictions[player], standings_men, standings_women)
        for player in predictions
    }
