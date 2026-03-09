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
        - globes_winners : dict structuré
    """

    # --- TOP 5 HOMMES & FEMMES (vectorisé) ---
    df_men = df[['player', 'top5_h']]
    df_men['top5_h'] = df_men["top5_h"].str.split(",")
    df_men_cleaned = df_men.join(df_men["top5_h"].apply(pd.Series).rename(columns=lambda i: f"p{i+1}"))
    df_men_cleaned.drop("top5_h", axis=1, inplace=True)
    df_men_cleaned.set_index("player", inplace=True)

    df_women = df[['player', 'top5_f']]
    df_women['top5_f'] = df_women["top5_f"].str.split(",")
    df_women_cleaned = df_women.join(df_women["top5_f"].apply(pd.Series).rename(columns=lambda i: f"p{i+1}"))
    df_women_cleaned.drop("top5_f", axis=1, inplace=True)
    df_women_cleaned.set_index("player", inplace=True)

    # --- GLOBES (vectorisé) ---
    globes_winners = df.drop(["top5_h", "top5_f"], axis=1)
    globes_winners.set_index("player", inplace=True)

    return df_men_cleaned, df_women_cleaned, globes_winners
