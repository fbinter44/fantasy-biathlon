"""
Chargement des pronostics joueurs depuis Google Sheets.

Responsabilités :
- Lire la feuille "Pronostics"
- Normaliser les données
- Retourner des structures prêtes pour le scoring
"""

import pandas as pd
from utils.sheets import read_all


def load_pronostics_from_gsheet() -> pd.DataFrame:
    """Retourne la feuille Pronostics sous forme de DataFrame."""
    records = read_all("Pronostics")
    if not records:
        raise ValueError("Aucun pronostic trouvé.")
    return pd.DataFrame(records)


def parse_pronostics(df: pd.DataFrame):
    """
    Transforme la DataFrame brute en structures prêtes pour PlayerBet.
    Retourne :
        - top5_hommes : dict joueur → [id1,id2,id3,id4,id5]
        - top5_femmes : dict joueur → [id1,id2,id3,id4,id5]
        - players_list : liste des joueurs
        - globes_winners : dict structuré
    """

    # Liste des joueurs
    players_list = df["player"].tolist()

    # --- TOP 5 HOMMES & FEMMES (vectorisé) ---
    top5_hommes = (
        df.set_index("player")["top5_h"]
        .str.split(",", expand=False)
        .to_dict()
    )

    top5_femmes = (
        df.set_index("player")["top5_f"]
        .str.split(",", expand=False)
        .to_dict()
    )

    # --- GLOBES (vectorisé) ---
    globes_winners = {
        "Sprint": {
            "H": df["globe_sprint_h"].tolist(),
            "F": df["globe_sprint_f"].tolist(),
        },
        "Poursuite": {
            "H": df["globe_pursuit_h"].tolist(),
            "F": df["globe_pursuit_f"].tolist(),
        },
        "Individuel": {
            "H": df["globe_individual_h"].tolist(),
            "F": df["globe_individual_f"].tolist(),
        },
        "Mass-start": {
            "H": df["globe_mass_start_h"].tolist(),
            "F": df["globe_mass_start_f"].tolist(),
        },
    }

    return top5_hommes, top5_femmes, players_list, globes_winners
