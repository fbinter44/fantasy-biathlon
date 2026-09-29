"""Assemble les DataFrames issus de parse_pronostics() en objets PlayerBet,
un par joueur — la structure attendue par le moteur de scoring."""

from core.pronostics.player_bet import PlayerBet

def build_player_bets(top5_h, top5_f, globes):
    """top5_h/top5_f/globes : DataFrames indexés par user_id (voir
    parse_pronostics). Retourne {user_id: PlayerBet}."""
    predictions = {}

    for player_id in top5_h.index:
        bet = PlayerBet(player_id)
        bet.load_predictions(
            top5_h.loc[player_id],
            top5_f.loc[player_id],
            globes.loc[player_id][["globe_sprint_h", "globe_sprint_f"]],
            globes.loc[player_id][["globe_pursuit_h", "globe_pursuit_f"]],
            globes.loc[player_id][["globe_individual_h", "globe_individual_f"]],
            globes.loc[player_id][["globe_mass_start_h", "globe_mass_start_f"]]
        )
        predictions[player_id] = bet

    return predictions
