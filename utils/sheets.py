"""
Fonctions utilitaires partagées (anciennement Google Sheets).

Les fonctions d'accès à Google Sheets (gspread/Streamlit) ont été supprimées :
le backend FastAPI lit les données depuis PostgreSQL via backend/services/db.py.
Ce module ne conserve que des utilitaires purs sans dépendances externes.
"""

import uuid

from utils.biathlon_data import DISCIPLINES_WINNERS, BIATHLETES_H


def extract_unique_ids(data, league_members):
    unique_ids = set()

    for entry in data:
        for key, value in entry.items():
            if key == "user_id":
                if value not in league_members:
                    break
                else:
                    continue
            if key == "username":
                continue  # on ignore le user_id et le username

            # Certains champs contiennent plusieurs IDs séparés par des virgules
            ids = value.split(",")
            for id_ in ids:
                unique_ids.add(id_.strip())

    return unique_ids


# ---------------------------------------------------------
# 4) Fonctions liées aux ligues
# ---------------------------------------------------------

def parse_members(m):
    if not m:
        return []
    if isinstance(m, list):
        return m
    return [x.strip() for x in str(m).split(",") if x.strip()]


def get_all_leagues():
    records = read_all("Leagues")
    return records if records else []


def generate_unique_league_id(existing_ids):
    while True:
        league_id = str(uuid.uuid4())[:8]
        if league_id not in existing_ids:
            return league_id


def create_league(name, owner):
    leagues = read_all("Leagues")
    existing_ids = {row["league_id"] for row in leagues}
    league_id = generate_unique_league_id(existing_ids)
    row = {
        league_id,
        name,
        owner,
        owner,
    }
    append_row("Leagues", row)
    return league_id



# ---------------------------------------------------------
# 5) Autres
# ---------------------------------------------------------

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
