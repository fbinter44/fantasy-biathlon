import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st


class PlayerBet:
    def __init__(self, name):
        self.player = name
        self.top_men = None
        self.top_women = None
        self.sprint_winners = None
        self.pursuit_winners = None
        self.individual_winners = None
        self.mass_start_winners = None

    def load_predictions(self, top_men, top_women, sp_winners, pu_winners, in_winners, ms_winners):
        self.top_men = top_men
        self.top_women = top_women
        self.sprint_winners = sp_winners
        self.pursuit_winners = pu_winners
        self.individual_winners = in_winners
        self.mass_start_winners = ms_winners


def load_pronostics_from_gsheet():
    # Scopes nécessaires
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Authentification via secrets
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    # Ouverture de la Google Sheet
    sheet = client.open_by_key(st.secrets["sheets"]["sheet_id"]).worksheet("Pronostics")

    # Récupération des données
    data = sheet.get_all_records()

    # Conversion en DataFrame
    df = pd.DataFrame(data)

    return df


def load_players_data_from_gsheet():
    df = load_pronostics_from_gsheet()

    # Liste des joueurs
    try:
        players_list = df["player"].tolist()
    except KeyError:
        raise KeyError("NO_PRONOS")

    # Top 5 hommes
    top_men = {
        row["player"]: row["top5_h"].split(",")
        for _, row in df.iterrows()
    }

    # Top 5 femmes
    top_women = {
        row["player"]: row["top5_f"].split(",")
        for _, row in df.iterrows()
    }

    # Globes
    globes_winners = {
        "Sprint": {
            "H": df["globe_sprint_h"].tolist(),
            "F": df["globe_sprint_f"].tolist()
        },
        "Poursuite": {
            "H": df["globe_pursuit_h"].tolist(),
            "F": df["globe_pursuit_f"].tolist()
        },
        "Individuel": {
            "H": df["globe_individual_h"].tolist(),
            "F": df["globe_individual_f"].tolist()
        },
        "Mass-start": {
            "H": df["globe_mass_start_h"].tolist(),
            "F": df["globe_mass_start_f"].tolist()
        }
    }

    return top_men, top_women, players_list, globes_winners


def get_player_row(sheet, player_name):
    players = sheet.col_values(1)  # colonne "player"
    if player_name in players:
        row_index = players.index(player_name) + 1
        row_values = sheet.row_values(row_index)
        return row_index, row_values
    return None, None

def load_pronostics(path):
    # Lecture brute de la feuille
    df = pd.read_excel(path, sheet_name="Pronostique", header=None)

    # Fonction utilitaire pour extraire un bloc entre deux titres
    def extract_block(start_label, end_label=None):
        start = df[df[0] == start_label].index[0] + 1
        if end_label:
            end = df[df[0] == end_label].index[0]
        else:
            end = len(df)
        return df.iloc[start:end].reset_index(drop=True)

    # --- TOP 5 HOMMES ---
    block_h = extract_block("Classement générale Homme", "Classement générale Femme")
    joueurs = block_h.iloc[:, 0].dropna().tolist()
    top5_hommes = {
        joueur: block_h.iloc[i+1, 1:7].tolist()
        for i, joueur in enumerate(joueurs)
    }

    # --- TOP 5 FEMMES ---
    block_f = extract_block("Classement générale Femme", "Classement petit globe Sprint")
    joueurs_f = block_f.iloc[:, 0].dropna().tolist()
    top5_femmes = {
        joueur: block_f.iloc[i+1, 1:7].tolist()
        for i, joueur in enumerate(joueurs_f)
    }

    # --- PETITS GLOBES ---
    def extract_globe(label):
        block = extract_block(label)
        hommes = block.iloc[1:7, 1].tolist()
        femmes = block.iloc[1:7, 2].tolist()
        return hommes, femmes

    sprint_h, sprint_f = extract_globe("Classement petit globe Sprint")
    poursuite_h, poursuite_f = extract_globe("Classement petit globe Poursuite")
    individuel_h, individuel_f = extract_globe("Classement petit globe Individuel")
    mass_h, mass_f = extract_globe("Classement petit globe Mass start")

    petits_globes = {
        "Sprint": {"H": sprint_h, "F": sprint_f},
        "Poursuite": {"H": poursuite_h, "F": poursuite_f},
        "Individuel": {"H": individuel_h, "F": individuel_f},
        "Mass-start": {"H": mass_h, "F": mass_f},
    }

    return top5_hommes, top5_femmes, joueurs, petits_globes


def fill_player_predictions(top_men, top_women, players_list, globes_winners):
    predictions = {}
    for i, player_name in enumerate(players_list):
        player_bet = PlayerBet(player_name)
        personal_top_men = top_men[player_name]
        personal_top_women = top_women[player_name]
        sp_winners = {
            "Men": globes_winners["Sprint"]["H"][i],
            "Women": globes_winners["Sprint"]["F"][i]
        }
        pu_winners = {
            "Men": globes_winners["Poursuite"]["H"][i],
            "Women": globes_winners["Poursuite"]["F"][i]
        }
        in_winners = {
            "Men": globes_winners["Individuel"]["H"][i],
            "Women": globes_winners["Individuel"]["F"][i]
        }
        ms_winners = {
            "Men": globes_winners["Mass-start"]["H"][i],
            "Women": globes_winners["Mass-start"]["F"][i]
        }
        player_bet.load_predictions(personal_top_men, personal_top_women, sp_winners, pu_winners, in_winners, ms_winners)
        predictions[player_name] = player_bet
    return predictions


if __name__ == "__main__":
    path = "game_predictions.xlsx"
    top5_h, top5_f, players, globes = load_pronostics(path)
    fill_player_predictions(top5_h, top5_f, players, globes)
