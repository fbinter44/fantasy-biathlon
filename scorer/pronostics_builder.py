from scorer.player_bet import PlayerBet

def build_player_bets(top5_h, top5_f, players_list, globes):
    predictions = {}

    for i, player_name in enumerate(players_list):
        bet = PlayerBet(player_name)

        bet.load_predictions(
            top5_h[player_name],
            top5_f[player_name],
            {"Men": globes["Sprint"]["H"][i], "Women": globes["Sprint"]["F"][i]},
            {"Men": globes["Poursuite"]["H"][i], "Women": globes["Poursuite"]["F"][i]},
            {"Men": globes["Individuel"]["H"][i], "Women": globes["Individuel"]["F"][i]},
            {"Men": globes["Mass-start"]["H"][i], "Women": globes["Mass-start"]["F"][i]},
        )

        predictions[player_name] = bet

    return predictions
