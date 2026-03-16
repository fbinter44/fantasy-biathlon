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
unique_names = [athlete_label(id) for id in unique_ids]

selected_name = st.selectbox(
        "Sélectionne un(e) biathlète",
        options=unique_names,
        format_func=lambda x: x  # affiche le nom, garde l'ID
    )
