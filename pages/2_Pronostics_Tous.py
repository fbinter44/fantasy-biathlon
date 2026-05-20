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
from utils.biathlon_data import athlete_label, split_top5, COLUMN_RENAME, GLOBE_COLS_H, GLOBE_COLS_F
from utils.sheets import read_all
from utils.auth import get_mapping_id_to_name, convert_league_id_to_name, get_league_members
from utils.table_display import df_to_html, table_all_pronos_style


# ---------------------------------------------------------
# 1) Configuration de la page et style des tableaux
# ---------------------------------------------------------

st.session_state["current_page"] = "2_Pronostics_Tous"
st.set_page_config(page_title="Tous les pronostics", layout="wide")

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

st.title("🧮 Tous les pronostics des joueurs")

st.markdown(table_all_pronos_style(username), unsafe_allow_html=True)


# ---------------------------------------------------------
# 2) Lecture des données Google Sheets
# ---------------------------------------------------------

records = read_all("Pronostics")

if not records:
    st.info("Aucun pronostic n’a encore été enregistré.")
    st.stop()

df = pd.DataFrame(records)
df["username"] = df["user_id"].map(id_to_name)

league_members = get_league_members(club_id)
df_league = df[df["user_id"].isin(league_members)]


# ---------------------------------------------------------
# 3) Renommage des colonnes
# ---------------------------------------------------------

df_league = df_league.rename(columns=COLUMN_RENAME)


# ---------------------------------------------------------
# 4) Sélecteurs d'affichage
# ---------------------------------------------------------

mode = st.radio(
    "Afficher :",
    ["Top 5 H", "Top 5 F", "Vainqueurs de globes H", "Vainqueurs de globes F"],
    horizontal=True
)

joueurs = sorted(df_league["username"].unique())
selection = st.multiselect(
    "Filtrer les joueurs :",
    joueurs,
    default=joueurs
)

df_league = df_league[df_league["username"].isin(selection)]


# ---------------------------------------------------------
# 5) Transformation des TOP 5
# ---------------------------------------------------------

# Hommes
df_league[["H_1", "H_2", "H_3", "H_4", "H_5"]] = df_league["Top 5 Hommes"].apply(
    lambda s: pd.Series(split_top5(s))
)

# Femmes
df_league[["F_1", "F_2", "F_3", "F_4", "F_5"]] = df_league["Top 5 Femmes"].apply(
    lambda s: pd.Series(split_top5(s))
)

# Conversion IBUId → noms + drapeaux
for col in ["H_1","H_2","H_3","H_4","H_5","F_1","F_2","F_3","F_4","F_5"]:
    df_league[col] = df_league[col].apply(athlete_label)

# Renommage lisible
df_league = df_league.rename(columns={
    "username": "Joueur",
    "H_1": "1er",
    "H_2": "2e",
    "H_3": "3e",
    "H_4": "4e",
    "H_5": "5e",
    "F_1": "1ère",
    "F_2": "2e ",
    "F_3": "3e ",
    "F_4": "4e ",
    "F_5": "5e ",
})


# ---------------------------------------------------------
# 6) Affichage selon le mode
# ---------------------------------------------------------

if mode == "Top 5 H":
    st.subheader("Top 5 Hommes")
    df_subset = df_league[["Joueur", "1er", "2e", "3e", "4e", "5e"]]
    st.markdown(df_to_html(df_subset, user_id), unsafe_allow_html=True)

elif mode == "Top 5 F":
    st.subheader("Top 5 Femmes")
    df_subset = df_league[["Joueur", "1ère", "2e", "3e", "4e", "5e"]]
    st.markdown(df_to_html(df_subset, user_id), unsafe_allow_html=True)

elif mode == "Vainqueurs de globes H":
    # Conversion IBUId → labels
    for col in GLOBE_COLS_H:
        df_league[col] = df_league[col].apply(athlete_label)

    st.subheader("Vainqueurs de globes")
    df_subset = df_league[["Joueur"] + GLOBE_COLS_H]
    st.markdown(df_to_html(df_subset, user_id), unsafe_allow_html=True)

elif mode == "Vainqueurs de globes F":
    # Conversion IBUId → labels
    for col in GLOBE_COLS_F:
        df_league[col] = df_league[col].apply(athlete_label)

    st.subheader("Vainqueurs de globes")
    df_subset = df_league[["Joueur"] + GLOBE_COLS_F]
    st.markdown(df_to_html(df_subset, user_id), unsafe_allow_html=True)
