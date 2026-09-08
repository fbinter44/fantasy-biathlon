from core.pronostics.pronostics_loader import parse_pronostics
from core.pronostics.pronostics_builder import build_player_bets
from .player_points import PlayerPoints

def compute_player_point(bet, standings_men, standings_women):
    pp = PlayerPoints(bet.player)
    pp.compute_total_men_points(bet.top_men, standings_men.general.head(10))
    pp.compute_total_women_points(bet.top_women, standings_women.general.head(10))
    pp.compute_bonus_globes_points(bet, standings_men, standings_women)
    pp.compute_total_points()
    return pp

def compute_all_players_points(predictions, standings_men, standings_women):
    return {
        player: compute_player_point(predictions[player], standings_men, standings_women)
        for player in predictions
    }

