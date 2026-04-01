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
from core.scoring.scoring_service import load_players_data


# ---------------------------------------------------------
# 1) Configuration de la page
# ---------------------------------------------------------

st.session_state["current_page"] = "2b_Pronostics_Biathlete"
st.set_page_config(page_title="Focus Biathlète", layout="wide")

sidebar_menu()
user_header()

user = st.session_state.get("user")
if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

st.title("📊 Focus sur un(e) biathlète")


# ---------------------------------------------------------
# 2) Lecture des données Google Sheets
# ---------------------------------------------------------

try:
    players_predictions = load_players_data()
except KeyError as e:
    if str(e) == "'NO_PRONOS'":
        st.info(
            "Aucun joueur n’a encore rempli ses pronostics.\n\n"
            "👉 Commence par saisir les tiens dans la page **Voir/Modifier mes pronos**."
        )
        st.stop()
    else:
        raise

records = read_all("Pronostics")

if not records:
    st.info("Aucun pronostic n’a encore été enregistré.")
    st.stop()

unique_ids = extract_unique_ids(records)
id_to_name = {id: athlete_label(id) for id in unique_ids}

selected_id = st.selectbox(
    "Sélectionne un(e) biathlète",
    options=list(id_to_name.keys()),
    format_func=lambda id: id_to_name[id]
)


# ---------------------------------------------------------
# 3) Chargements des pronos
# ---------------------------------------------------------

biathlete_summary = build_biathlete_summary(players_predictions, user, selected_id)
sprint_recap = biathlete_summary.sprint_info.format_globe_sentence()
pursuit_recap = biathlete_summary.pursuit_info.format_globe_sentence()
indiv_recap = biathlete_summary.ind_info.format_globe_sentence()
mass_recap = biathlete_summary.ms_info.format_globe_sentence()
st.write(sprint_recap)
st.write(pursuit_recap)
st.write(indiv_recap)
st.write(mass_recap)
import pdb
pdb.set_trace()

