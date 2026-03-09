from core.pronostics.player_bet import PlayerBet

def build_player_bets(top5_h, top5_f, globes):
    predictions = {}

    for player_name in top5_h.index:
        bet = PlayerBet(player_name)
        bet.load_predictions(
            top5_h.loc[player_name],
            top5_f.loc[player_name],
            globes.loc[player_name][["globe_sprint_h", "globe_sprint_f"]],
            globes.loc[player_name][["globe_pursuit_h", "globe_pursuit_f"]],
            globes.loc[player_name][["globe_individual_h", "globe_individual_f"]],
            globes.loc[player_name][["globe_mass_start_h", "globe_mass_start_f"]]
        )
        predictions[player_name] = bet

    return predictions
