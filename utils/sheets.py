"""
Module utilitaire pour accéder aux différentes feuilles Google Sheets.

Responsabilités :
- Initialisation du client Google Sheets
- Accès simplifié aux worksheets
- Fonctions utilitaires de lecture/écriture
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

from utils.cache_helpers import CACHE_PRONOS_DIR, load_from_cache, save_to_cache
from utils.biathlon_data import DISCIPLINES_WINNERS, BIATHLETES_F, BIATHLETES_H


# ---------------------------------------------------------
# 1) Initialisation du client Google Sheets
# ---------------------------------------------------------

def _get_gspread_client():
    """
    Initialise et retourne un client gspread authentifié.
    Utilise les credentials stockés dans st.secrets.
    """
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    return gspread.authorize(creds)


# ---------------------------------------------------------
# 2) Accès à une worksheet
# ---------------------------------------------------------

def get_sheet(name: str):
    """
    Retourne une worksheet par son nom.
    Exemple : get_sheet("Pronostics")
    """
    client = _get_gspread_client()
    sheet_id = st.secrets["sheets"]["sheet_id"]
    return client.open_by_key(sheet_id).worksheet(name)


# ---------------------------------------------------------
# 3) Fonctions utilitaires
# ---------------------------------------------------------

def read_all(name: str):
    """
    Lit toutes les lignes d'une feuille et retourne une liste de dicts.
    Equivalent à sheet.get_all_records().
    """
    # 1) Essayer le cache local
    cached = load_from_cache(CACHE_PRONOS_DIR, "pronos.json")
    if cached is not None:
        return cached
    
    # 2) Sinon lire Google Sheets
    sheet = get_sheet(name)
    data = sheet.get_all_records()

    # 3) Sauvegarder dans le cache
    save_to_cache(CACHE_PRONOS_DIR, "pronos.json", data)

    return data


def append_row(name: str, row: list):
    """
    Ajoute une ligne à la fin de la feuille.
    """
    sheet = get_sheet(name)
    sheet.append_row(row)


def update_cell(name: str, row: int, col: int, value):
    """
    Met à jour une cellule (ligne, colonne).
    """
    sheet = get_sheet(name)
    sheet.update_cell(row, col, value)


def get_player_row(sheet, player_name):
    players = sheet.col_values(1)  # colonne "player"
    if player_name in players:
        row_index = players.index(player_name) + 1
        row_values = sheet.row_values(row_index)
        return row_index, row_values
    return None, None


def extract_unique_ids(data):
    unique_ids = set()

    for entry in data:
        for key, value in entry.items():
            if key == "player":
                continue  # on ignore le nom du joueur

            # Certains champs contiennent plusieurs IDs séparés par des virgules
            ids = value.split(",")
            for id_ in ids:
                unique_ids.add(id_.strip())

    return unique_ids


def build_biathlete_summary(pronos, my_user, biathlete_id):
    biathlete_summary = BiathleteSummary(biathlete_id)
    nb_total_players = len(pronos)
    globe_suffix = "winner_men" if biathlete_id in BIATHLETES_H else "winner_women"
    top_men_stats = {"1er": 0, "2ème": 0, "3ème": 0, "4ème": 0, "5ème": 0, "total": 0, "nb_total_players": nb_total_players}
    top_women_stats = {"1er": 0, "2ème": 0, "3ème": 0, "4ème": 0, "5ème": 0, "total": 0, "nb_total_players": nb_total_players}
    for disc in DISCIPLINES_WINNERS:
        user_choice = False
        nb_players = 0
        place_in_top5 = 0
        for user in pronos:
            user_pronos = pronos[user]
            if disc == "general":
                if user_pronos.top_men.p1 == biathlete_id:
                    top_men_stats["1er"] += 1
                    top_men_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 1
                elif user_pronos.top_men.p2 == biathlete_id:
                    top_men_stats["2ème"] += 1
                    top_men_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 2
                elif user_pronos.top_men.p3 == biathlete_id:
                    top_men_stats["3ème"] += 1
                    top_men_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 3
                elif user_pronos.top_men.p4 == biathlete_id:
                    top_men_stats["4ème"] += 1
                    top_men_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 4
                elif user_pronos.top_men.p5 == biathlete_id:
                    top_men_stats["5ème"] += 1
                    top_men_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 5
                if user_pronos.top_women.p1 == biathlete_id:
                    top_women_stats["1er"] += 1
                    top_women_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 1
                elif user_pronos.top_women.p2 == biathlete_id:
                    top_women_stats["2ème"] += 1
                    top_women_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 2
                elif user_pronos.top_women.p3 == biathlete_id:
                    top_women_stats["3ème"] += 1
                    top_women_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 3
                elif user_pronos.top_women.p4 == biathlete_id:
                    top_women_stats["4ème"] += 1
                    top_women_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 4
                elif user_pronos.top_women.p5 == biathlete_id:
                    top_women_stats["5ème"] += 1
                    top_women_stats["total"] += 1
                    if my_user == user:
                        place_in_top5 = 5
            else:
                globe_winner_id = getattr(getattr(user_pronos, DISCIPLINES_WINNERS[disc]), globe_suffix)
                if globe_winner_id == biathlete_id:
                    if my_user == user:
                        user_choice = True
                    nb_players += 1
        if disc == "sprint":
            biathlete_summary.set_sprint_info(user_choice, nb_players, nb_players / nb_total_players)
        elif disc == "pursuit":
            biathlete_summary.set_pursuit_info(user_choice, nb_players, nb_players / nb_total_players)
        elif disc == "individual":
            biathlete_summary.set_indiv_info(user_choice, nb_players, nb_players / nb_total_players)
        elif disc == "mass_start":
            biathlete_summary.set_ms_info(user_choice, nb_players, nb_players / nb_total_players)
        elif disc == "general":
            if biathlete_id in BIATHLETES_H:
                biathlete_summary.set_top_info(top_men_stats, place_in_top5)
            else:
                biathlete_summary.set_top_info(top_women_stats, place_in_top5)
    return biathlete_summary


class BiathleteSummary():
    def __init__(self, id):
        self.biathlete_id = id
        self.sprint_info = None
        self.pursuit_info = None
        self.ind_info = None
        self.ms_info = None
        self.top_info = None
        if self.biathlete_id in BIATHLETES_H:
            self.gender = "Men"
        else:
            self.gender = "Women"
    
    def set_sprint_info(self, user_choice, nb_players, ratio):
        self.sprint_info = GlobeInfo("Sprint", user_choice, nb_players, ratio)

    def set_pursuit_info(self, user_choice, nb_players, ratio):
        self.pursuit_info = GlobeInfo("Poursuite", user_choice, nb_players, ratio)

    def set_indiv_info(self, user_choice, nb_players, ratio):
        self.ind_info = GlobeInfo("Individuel", user_choice, nb_players, ratio)

    def set_ms_info(self, user_choice, nb_players, ratio):
        self.ms_info = GlobeInfo("Mass Start", user_choice, nb_players, ratio)

    def set_top_info(self, top_stats, my_place):
        self.top_info = TopInfo(top_stats, my_place)


class GlobeInfo():
    def __init__(self, disc, user_choice, nb_players, ratio):
        self.disc = disc
        self.user_choice = user_choice
        self.nb_selected_players = nb_players
        self.ratio_selection = ratio

class TopInfo():
    def __init__(self, top_stats, my_place):
        self.top_stats = top_stats
        self.my_place = my_place        
