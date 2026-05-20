"""
Page : Tous les pronostics des joueurs

Affiche :
- Top 5 Hommes
- Top 5 Femmes
- Vainqueurs des globes

Lecture depuis Google Sheets → feuille "Pronostics".
"""

import streamlit as st
import pandas as pd

from utils.ui_components import sidebar_menu, user_header
from utils.sheets import read_all, extract_unique_ids
from utils.biathlon_data import athlete_label
from utils.sheets import build_biathlete_summary
from utils.auth import get_mapping_id_to_name, convert_league_id_to_name, get_league_members
from utils.visualisation_utils import globe_card, top5_card
from core.scoring.scoring_service import load_players_data


# ---------------------------------------------------------
# 1) Configuration de la page
# ---------------------------------------------------------

st.session_state["current_page"] = "2b_Pronostics_Biathlete"
st.set_page_config(page_title="Focus Biathlète", layout="wide")

sidebar_menu()
user_id = st.session_state.get("user")
if user_id:
    id_to_name = get_mapping_id_to_name()
    username = id_to_name[user_id]
else:
    username = None
club_id = st.session_state.get("current_league")
club_name = convert_league_id_to_name(club_id)
user_header(username, club_name)

if not user_id:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

st.title("🔎 Focus sur un(e) biathlète")


# ---------------------------------------------------------
# 2) Lecture des données Google Sheets
# ---------------------------------------------------------

records = read_all("Pronostics")
df = pd.DataFrame(records)
df["username"] = df["user_id"].map(id_to_name)

league_members = get_league_members(club_id)

if not records:
    st.info("Aucun pronostic n’a encore été enregistré.")
    st.stop()

try:
    players_predictions = load_players_data(league_members)
except KeyError as e:
    if str(e) == "'NO_PRONOS'":
        st.info(
            "Aucun joueur n’a encore rempli ses pronostics.\n\n"
            "👉 Commence par saisir les tiens dans la page **Voir/Modifier mes pronos**."
        )
        st.stop()
    else:
        raise

unique_ids = extract_unique_ids(records, league_members)
id_to_name = {id: athlete_label(id) for id in unique_ids}

selected_id = st.selectbox(
    "Sélectionne un(e) biathlète",
    options=list(id_to_name.keys()),
    format_func=lambda id: id_to_name[id]
)


# ---------------------------------------------------------
# 3) Affichage des statistiques
# ---------------------------------------------------------

biathlete_summary = build_biathlete_summary(players_predictions, user_id, selected_id)

if biathlete_summary.gender == "Men":
    top5_card("Top 5 Hommes", biathlete_summary.top_info)
else:
    top5_card("Top 5 Femmes", biathlete_summary.top_info)

col1, col2 = st.columns(2)

with col1:
    globe_card("Sprint", round(biathlete_summary.sprint_info.ratio_selection * 100), biathlete_summary.sprint_info.user_choice)
    globe_card("Individuel", round(biathlete_summary.ind_info.ratio_selection * 100), biathlete_summary.ind_info.user_choice)

with col2:
    globe_card("Poursuite", round(biathlete_summary.pursuit_info.ratio_selection * 100), biathlete_summary.pursuit_info.user_choice)
    globe_card("Mass Start", round(biathlete_summary.ms_info.ratio_selection * 100), biathlete_summary.ms_info.user_choice)
