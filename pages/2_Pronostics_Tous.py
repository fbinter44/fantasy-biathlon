import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from utils.ui import sidebar_menu, user_header

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

# Mise en forme
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
    "globe_mass_h": "Mass Start H",
    "globe_mass_f": "Mass Start F",
})

st.dataframe(df, use_container_width=True)