import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from utils.ui import sidebar_menu, user_header
from utils.config import athlete_label, split_top5

st.set_page_config(page_title="Tous les pronostics", layout="wide")

sidebar_menu()
user_header()

user = st.session_state.get("user")
if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

st.title("📊 Tous les pronostics des joueurs")

# Connexion Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["sheets"]["sheet_id"]).worksheet("Pronostics")

# Récupération des données
records = sheet.get_all_records()

if not records:
    st.info("Aucun pronostic n’a encore été enregistré.")
    st.stop()

df = pd.DataFrame(records)

# Renommage des colonnes
df = df.rename(columns={
    "player": "Joueur",
    "top5_h": "Top 5 Hommes",
    "top5_f": "Top 5 Femmes",
    "globe_sprint_h": "Sprint H",
    "globe_sprint_f": "Sprint F",
    "globe_pursuit_h": "Poursuite H",
    "globe_pursuit_f": "Poursuite F",
    "globe_individual_h": "Individuel H",
    "globe_individual_f": "Individuel F",
    "globe_mass_start_h": "Mass Start H",
    "globe_mass_start_f": "Mass Start F",
})

# Sélecteur d’affichage
mode = st.radio(
    "Afficher :",
    ["Top 5 H", "Top 5 F", "Vainqueurs de globes"],
    horizontal=True
)

# Filtre joueurs
joueurs = sorted(df["Joueur"].unique())
selection = st.multiselect(
    "Filtrer les joueurs :",
    joueurs,
    default=joueurs
)
df = df[df["Joueur"].isin(selection)]

# -----------------------------
# TOP 5 — transformation en colonnes 1er → 5e
# -----------------------------

# Hommes
df[["H_1", "H_2", "H_3", "H_4", "H_5"]] = df["Top 5 Hommes"].apply(
    lambda s: pd.Series(split_top5(s))
)

# Femmes
df[["F_1", "F_2", "F_3", "F_4", "F_5"]] = df["Top 5 Femmes"].apply(
    lambda s: pd.Series(split_top5(s))
)

# Conversion IBUId → noms + drapeaux
for col in ["H_1","H_2","H_3","H_4","H_5","F_1","F_2","F_3","F_4","F_5"]:
    df[col] = df[col].apply(athlete_label)

# Renommage lisible
df = df.rename(columns={
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

# -----------------------------
# AFFICHAGE SELON LE MODE
# -----------------------------

if mode == "Top 5 H":
    st.subheader("Top 5 Hommes")
    st.data_editor(
        df[["Joueur", "1er", "2e", "3e", "4e", "5e"]],
        use_container_width=True,
        hide_index=True
    )

elif mode == "Top 5 F":
    st.subheader("Top 5 Femmes")
    st.data_editor(
        df[["Joueur", "1ère", "2e ", "3e ", "4e ", "5e "]],
        use_container_width=True,
        hide_index=True
    )

else:
    # Globes
    df["Sprint H"] = df["Sprint H"].apply(athlete_label)
    df["Sprint F"] = df["Sprint F"].apply(athlete_label)
    df["Poursuite H"] = df["Poursuite H"].apply(athlete_label)
    df["Poursuite F"] = df["Poursuite F"].apply(athlete_label)
    df["Individuel H"] = df["Individuel H"].apply(athlete_label)
    df["Individuel F"] = df["Individuel F"].apply(athlete_label)
    df["Mass Start H"] = df["Mass Start H"].apply(athlete_label)
    df["Mass Start F"] = df["Mass Start F"].apply(athlete_label)

    st.subheader("Vainqueurs de globes")
    st.data_editor(
        df[[
            "Joueur",
            "Sprint H", "Sprint F",
            "Poursuite H", "Poursuite F",
            "Individuel H", "Individuel F",
            "Mass Start H", "Mass Start F"
        ]],
        use_container_width=True,
        hide_index=True
    )